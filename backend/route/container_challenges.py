"""
Docker容器题目管理路由
包含：启动、停止、查询容器实例
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from backend.server.extensions import db
from backend.server.db_models import (
    CtfChallenge, CtfGameInstance, User, CtfChallengeSubmission
)
from backend.server.traffic_capture import get_traffic_manager, record_http_exchange
from backend.services.flag_generator import ContainerFlagService
import docker
import logging
import requests
import re
import subprocess
import os
import threading
import ipaddress
import socket

bp = Blueprint("container", __name__)
logger = logging.getLogger(__name__)


def _normalize_ipv4(address, fallback="127.0.0.1"):
    try:
        return str(ipaddress.IPv4Address(address))
    except Exception:
        return fallback


def _build_raw_http_request(method, path, headers, body: bytes):
    lines = [f"{method} {path} HTTP/1.1"]
    has_length = False
    for key, value in headers.items():
        if key.lower() == "content-length":
            has_length = True
        lines.append(f"{key}: {value}")
    if not has_length:
        lines.append(f"Content-Length: {len(body)}")
    lines.append("")
    header_bytes = ("\r\n".join(lines) + "\r\n").encode("utf-8")
    return header_bytes + body


def _build_raw_http_response(status_code, reason, headers, body: bytes):
    lines = [f"HTTP/1.1 {status_code} {reason}"]
    has_length = False
    for key, value in headers.items():
        if key.lower() == "content-length":
            has_length = True
        lines.append(f"{key}: {value}")
    if not has_length:
        lines.append(f"Content-Length: {len(body)}")
    lines.append("")
    header_bytes = ("\r\n".join(lines) + "\r\n").encode("utf-8")
    return header_bytes + body


def _is_port_listening(host, port, timeout=0.3):
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _start_capture_proxy_thread(app, challenge_id, instance_id, team_id, user_id, container_port, proxy_port):
    def start_proxy():
        logger.info(f"[DEBUG] Proxy thread started for challenge {challenge_id}, instance {instance_id}")
        try:
            with app.app_context():
                from backend.server.traffic_capture import TrafficCaptureManager, PcapWriter
                from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
                import requests as req_lib
                from requests.adapters import HTTPAdapter

                manager = TrafficCaptureManager()
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                pcap_path = manager.get_capture_path(challenge_id, team_id, user_id, timestamp)
                pcap_writer = PcapWriter(pcap_path)

                # Reuse upstream HTTP connections to avoid frequent socket churn on Windows.
                upstream = req_lib.Session()
                adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=0)
                upstream.mount("http://", adapter)

                # 每次代理启动都创建一条抓包记录，便于区分不同会话
                manager.save_capture_record(
                    challenge_id=challenge_id,
                    instance_id=instance_id,
                    team_id=team_id,
                    user_id=user_id,
                    file_path=str(pcap_path.relative_to(manager.base_dir)),
                    file_size=0
                )

                class ProxyHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        self._proxy_request()

                    def do_HEAD(self):
                        self._proxy_request()

                    def do_POST(self):
                        self._proxy_request()

                    def do_PUT(self):
                        self._proxy_request()

                    def do_DELETE(self):
                        self._proxy_request()

                    def _proxy_request(self):
                        try:
                            logger.info(f"[PROXY] {self.command} {self.path} from {self.client_address[0]}:{self.client_address[1]}")

                            target_url = f"http://127.0.0.1:{container_port}{self.path}"

                            content_length = int(self.headers.get('Content-Length', 0))
                            request_body = self.rfile.read(content_length) if content_length > 0 else b""

                            headers = dict(self.headers)
                            headers.pop('Host', None)
                            headers.pop('Proxy-Connection', None)
                            headers['Connection'] = 'close'

                            resp = upstream.request(
                                method=self.command,
                                url=target_url,
                                data=request_body,
                                headers=headers,
                                timeout=(5, 30),
                                allow_redirects=False
                            )

                            try:
                                request_raw = _build_raw_http_request(
                                    self.command, self.path, dict(self.headers), request_body
                                )
                                response_raw = _build_raw_http_response(
                                    resp.status_code, resp.reason or "OK", dict(resp.headers), resp.content
                                )
                                pcap_writer.write_packet("127.0.0.1", proxy_port, "127.0.0.1", container_port, request_raw)
                                pcap_writer.write_packet("127.0.0.1", container_port, "127.0.0.1", proxy_port, response_raw)
                                pcap_writer.flush()
                                logger.debug(f"✓ Captured {self.command} {self.path} ({len(request_raw)} + {len(response_raw)} bytes)")
                            except Exception as pcap_error:
                                logger.error(f"Failed to write PCAP packet: {pcap_error}")

                            self.send_response(resp.status_code)
                            for k, v in resp.headers.items():
                                # Let requests decode payload and rebuild safe downstream headers.
                                if k.lower() not in ['content-encoding', 'transfer-encoding', 'connection', 'content-length', 'server', 'date']:
                                    self.send_header(k, v)
                            if self.command == 'HEAD' and resp.headers.get('Content-Length'):
                                self.send_header('Content-Length', resp.headers.get('Content-Length'))
                            else:
                                self.send_header('Content-Length', str(len(resp.content)))
                            self.send_header('Connection', 'close')
                            self.end_headers()
                            if self.command != 'HEAD':
                                self.wfile.write(resp.content)
                            self.close_connection = True

                        except Exception as e:
                            logger.error(f"Proxy error: {e}")
                            self.send_error(502, "Bad Gateway")

                    def log_message(self, format, *args):
                        pass

                server = ThreadingHTTPServer(('127.0.0.1', proxy_port), ProxyHandler)

                logger.info(f"✓ Proxy started on port {proxy_port} WITH traffic capture")
                logger.info(f"  ├─ Container port: {container_port}")
                logger.info(f"  ├─ PCAP: {pcap_path}")
                logger.info(f"  ├─ User accesses via: http://localhost:{proxy_port}")
                logger.info(f"  └─ Instance ID: {instance_id}")
                logger.info(f"[PROXY] Server listening on http://127.0.0.1:{proxy_port}")
                server.serve_forever()

        except Exception as e:
            logger.error(f"Failed to start proxy: {e}")
            import traceback
            traceback.print_exc()

    thread = threading.Thread(target=start_proxy, daemon=True)
    thread.start()
    logger.info(f"Starting proxy thread: {proxy_port} -> {container_port} (instance {instance_id})")





# ======================== 容器启动 ========================

@bp.route("/start/<int:challenge_id>", methods=["POST"])
@jwt_required()
def start_container(challenge_id):
    """
    启动Docker容器
    
    逻辑：
    1. 如果用户已有该题的运行容器 → 返回管理界面
    2. 如果用户在1分钟内创建过容器 → 返回429错误
    3. 否则 → 创建并启动新容器
    
    返回:
    {
        "success": true,
        "action_type": "manage",  // 成功创建
        "data": {容器信息}
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        # 检查是否支持容器
        if not challenge.docker_image:
            return jsonify({"success": False, "message": "该题目不支持容器"}), 400

        # ========== 第一步：检查是否已有运行的容器（确保同一题只有一个） ==========
        # 先清理所有该用户该题目的其他 running 实例
        other_running = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).all()
        
        existing = None
        docker_client = docker.from_env()
        
        for inst in other_running:
            # 检查容器是否真的还在运行
            container_exists = False
            try:
                container = docker_client.containers.get(inst.container_id)
                if container.status == 'running':
                    container_exists = True
            except:
                pass
            
            if not container_exists:
                # 容器已不存在，清理数据库
                inst.is_running = False
                db.session.commit()
            else:
                # 容器还在，检查是否过期
                if inst.expires_at and inst.expires_at < datetime.utcnow():
                    try:
                        container.stop(timeout=5)
                        container.remove(force=True)
                    except:
                        pass
                    inst.is_running = False
                    db.session.commit()
                else:
                    # 容器仍新鲜，保留它
                    existing = inst
                    break
        
        if existing:
            # 后端重启后 daemon 代理线程会丢失，这里按需自动拉起代理
            from flask import current_app
            proxy_port = existing.tcpdump_pid if (existing.tcpdump_pid and existing.tcpdump_pid > 10000) else (
                (existing.port + 10000) if existing.port else None
            )
            if existing.port and proxy_port and not _is_port_listening("127.0.0.1", proxy_port):
                app = current_app._get_current_object()
                team_id = user.team_id if user.team_id else user_id
                _start_capture_proxy_thread(
                    app=app,
                    challenge_id=challenge_id,
                    instance_id=existing.id,
                    team_id=team_id,
                    user_id=user_id,
                    container_port=existing.port,
                    proxy_port=proxy_port
                )
                existing.connection_url = f"http://localhost:{proxy_port}"
                existing.tcpdump_pid = proxy_port
                db.session.commit()

            # 容器仍在运行，直接返回
            return jsonify({
                "success": True,
                "action_type": "manage",
                "data": existing.to_dict(),
                "message": "容器已运行"
            }), 200

        # ========== 第二步：如果没有运行的容器，检查启动间隔限制 ==========
        # 防止用户频繁创建容器（查询同一题目的最后一个实例）
        last_container = CtfGameInstance.query.filter_by(
            user_id=user_id,
            challenge_id=challenge_id
        ).order_by(
            CtfGameInstance.started_at.desc()
        ).first()
        
        if last_container and last_container.started_at:
            time_since_last = datetime.utcnow() - last_container.started_at
            min_interval = timedelta(minutes=1)
            
            if time_since_last < min_interval:
                wait_time = int((min_interval - time_since_last).total_seconds())
                logger.warning(f"用户 {user_id} 试图快速创建题目 {challenge_id} 的容器，上次创建仅 {time_since_last.total_seconds():.1f} 秒前")
                return jsonify({
                    "success": False,
                    "message": f"容器创建过于频繁，请在 {wait_time} 秒后重试",
                    "wait_seconds": wait_time
                }), 429

        # ========== 第三步：创建新容器 ==========
        instance = CtfGameInstance(
            challenge_id=challenge_id,
            user_id=user_id,
            container_image=challenge.docker_image,
            is_running=True,
            started_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

        db.session.add(instance)
        db.session.flush()

        # ========== 生成动态Flag（如果有模板）==========
        dynamic_flag = None
        if challenge.flag_template:
            # 获取game对象用于生成team hash
            from backend.server.db_models import CtfGame
            game = CtfGame.query.get(challenge.game_id)
            team_hash_salt = game.team_hash_salt if game else None
            
            dynamic_flag = ContainerFlagService.generate_dynamic_flag(
                flag_template=challenge.flag_template,
                challenge_id=challenge_id,
                user_id=user_id,
                game_id=challenge.game_id,
                team_id=user.team_id if user.team_id else user_id,
                team_hash_salt=team_hash_salt
            )
            instance.dynamic_flag = dynamic_flag
            logger.info(f"✓ Dynamic flag generated for challenge {challenge_id}, user {user_id}")
        else:
            # 静态flag
            dynamic_flag = challenge.flag
            instance.dynamic_flag = dynamic_flag

        # 启动Docker容器
        try:
            docker_client = docker.from_env()
            
            # 获取可用端口
            used_ports = set()
            containers = CtfGameInstance.query.filter_by(is_running=True).all()
            for c in containers:
                if c.port:
                    used_ports.add(c.port)
            
            port = None
            for p in range(8000, 9000):
                if p not in used_ports:
                    port = p
                    break

            if not port:
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "message": "可用端口不足"
                }), 503

            instance.port = port

            # 准备环境变量，包括动态flag
            env_vars = [
                f'FLAG={dynamic_flag}',
                f'CHALLENGE_ID={challenge_id}',
                f'USER_ID={user_id}',
                f'TEAM_ID={user.team_id if user.team_id else user_id}'
            ]

            # 启动容器，注入FLAG环境变量
            logger.info(f"[Container] Starting container for challenge {challenge_id}, user {user_id}")
            logger.info(f"[Container] Image: {challenge.docker_image}")
            logger.info(f"[Container] Dynamic flag generated: {dynamic_flag[:30]}... ({len(dynamic_flag)} chars)")
            logger.info(f"[Container] Flag template: {challenge.flag_template}")
            
            # 检查占位符是否已替换
            if dynamic_flag and ('[' in dynamic_flag or ']' in dynamic_flag):
                logger.error(f"[Container] ERROR: Flag still contains placeholders: {dynamic_flag}")
                db.session.rollback()
                return jsonify({
                    "success": False,
                    "message": "Flag生成错误：占位符未被替换"
                }), 500
            
            container = docker_client.containers.run(
                challenge.docker_image,
                detach=True,
                ports={"80/tcp": ("127.0.0.1", port)} if not challenge.docker_port else {f"{challenge.docker_port}/tcp": ("127.0.0.1", port)},
                name=f"ctf-{challenge_id}-{user_id}-{instance.id}",
                remove=False,
                environment=env_vars  # 注入环境变量
            )

            instance.container_id = container.id
            
            # 所有容器都使用代理（可选是否捕获流量）
            proxy_port = port + 10000  # 容器在 8000，代理在 18000
            instance.connection_url = f"http://localhost:{proxy_port}"
            instance.tcpdump_pid = proxy_port  # 存储代理端口

            from flask import current_app
            app = current_app._get_current_object()
            team_id = user.team_id if user.team_id else user_id
            _start_capture_proxy_thread(
                app=app,
                challenge_id=challenge_id,
                instance_id=instance.id,
                team_id=team_id,
                user_id=user_id,
                container_port=port,
                proxy_port=proxy_port
            )
            
            db.session.commit()

            return jsonify({
                "success": True,
                "action_type": "manage",
                "data": instance.to_dict(),
                "message": "✅ 容器启动成功！"
            }), 201

        except docker.errors.ImageNotFound as e:
            logger.error(f"Docker镜像不存在: {str(e)}")
            instance.is_running = False
            db.session.commit()
            return jsonify({
                "success": False,
                "message": f"镜像不存在: {challenge.docker_image}"
            }), 400
        except docker.errors.DockerException as e:
            logger.error(f"Docker启动失败: {str(e)}")
            instance.is_running = False
            db.session.commit()
            return jsonify({
                "success": False,
                "message": f"容器启动失败: {str(e)}"
            }), 503

    except Exception as e:
        db.session.rollback()
        logger.error(f"启动容器异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 容器停止 ========================

@bp.route("/stop/<int:instance_id>", methods=["POST"])
@jwt_required()
def stop_container(instance_id):
    """
    停止Docker容器
    
    返回:
    {
        "success": true,
        "message": "容器已销毁，可以重新启动"
    }
    """
    try:
        user_id = get_jwt_identity()
        try:
            user_id_int = int(user_id)
        except Exception:
            user_id_int = user_id
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"success": False, "message": "实例不存在"}), 404

        if instance.user_id != user_id_int:
            return jsonify({"success": False, "message": "无权操作"}), 403

        # 停止Docker容器
        if instance.container_id:
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                
                # 先尝试优雅停止（10秒超时）
                try:
                    logger.info(f"Stopping container {instance.container_id[:12]}...")
                    container.stop(timeout=10)
                    logger.info(f"Container stopped successfully")
                except Exception as stop_error:
                    logger.warning(f"Graceful stop failed: {stop_error}, forcing kill...")
                    # 强制杀死容器
                    container.kill()
                
                # 删除容器
                try:
                    container.remove(force=True)
                    logger.info(f"Container removed successfully")
                except Exception as remove_error:
                    logger.warning(f"Container remove failed: {remove_error}")
                    
            except docker.errors.NotFound:
                logger.warning(f"Container {instance.container_id} not found (already removed)")
            except Exception as e:
                logger.error(f"停止容器失败: {str(e)}")
                # 继续标记为已停止（即使容器操作失败也要更新数据库状态）

        # 停止流量捕获代理（如果有）
        if hasattr(instance, 'tcpdump_pid') and instance.tcpdump_pid and instance.tcpdump_pid > 10000:
            # tcpdump_pid > 10000 说明存的是代理端口，不是真的 PID
            # 代理服务器是 daemon 线程，容器停止后自动结束
            logger.info(f"Capture proxy on port {instance.tcpdump_pid} will stop automatically")
        elif hasattr(instance, 'capture_packets') and hasattr(instance, 'capture_pcap_path'):
            try:
                from scapy.all import wrpcap
                packets = instance.capture_packets
                if packets and len(packets) > 0:
                    wrpcap(instance.capture_pcap_path, packets)
                    logger.info(f"Saved {len(packets)} packets to {instance.capture_pcap_path}")
                else:
                    logger.info("No packets captured")
            except Exception as e:
                logger.warning(f"Failed to save captured packets: {e}")

        instance.is_running = False
        instance.expires_at = None
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "✓ 容器已停止并删除"
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"停止容器异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 获取容器状态 ========================

@bp.route("/status/<int:challenge_id>", methods=["GET"])
@jwt_required()
def get_container_status(challenge_id):
    """
    获取用户该题目的容器状态及可用操作
    
    返回:
    {
        "success": true,
        "has_container": true,
        "action_type": "start" | "manage",
        "data": {
            "instance_id": 1,
            "container_id": "abc123...",
            "connection_url": "http://localhost:8080",
            "port": 8080,
            "is_running": true,
            "expires_at": "2024-01-01T12:00:00",
            "time_remaining_seconds": 3600,
            "status": "running"
        },
        "actions": [  // 可用的操作
            {"name": "extend", "label": "延时1小时"},
            {"name": "destroy", "label": "销毁容器"}
        ]
    }
    """
    try:
        user_id = get_jwt_identity()
        challenge = CtfChallenge.query.get(challenge_id)
        
        logger.info(f"[STATUS] user_id={user_id}, challenge_id={challenge_id}")

        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).first()
        
        logger.info(f"[STATUS] Found instance: {instance.id if instance else None}, running={instance.is_running if instance else None}")

        # 检查容器是否已过期
        if instance and instance.expires_at and instance.expires_at < datetime.utcnow():
            # 清理过期容器
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
            except:
                pass
            
            instance.is_running = False
            db.session.commit()
            instance = None

        if not instance:
            # 无容器，返回"开启容器"状态
            return jsonify({
                "success": True,
                "has_container": False,
                "action_type": "start",
                "data": None,
                "actions": [],
                "message": "无运行的容器"
            }), 200

        # 有容器，返回"查看容器"状态和可用操作
        time_remaining = None
        if instance.expires_at:
            time_remaining = (instance.expires_at - datetime.utcnow()).total_seconds()
            if time_remaining < 0:
                time_remaining = 0

        data = instance.to_dict()
        data['time_remaining_seconds'] = int(time_remaining) if time_remaining is not None else None
        data['status'] = 'running' if instance.is_running else 'stopped'

        # 计算可用操作
        actions = []
        if instance.is_running and instance.expires_at:
            # 检查是否还可以延期
            original = instance.started_at
            max_expire = original + timedelta(hours=4)
            if instance.expires_at < max_expire:
                actions.append({"name": "extend", "label": "延时1小时", "icon": "⏱️"})
        
        # 销毁操作总是可用的
        actions.append({"name": "destroy", "label": "销毁容器", "icon": "🗑️", "confirm": True})

        return jsonify({
            "success": True,
            "has_container": True,
            "action_type": "manage",
            "data": data,
            "actions": actions,
            "message": "容器运行中"
        }), 200

    except Exception as e:
        logger.error(f"获取容器状态异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 获取容器实例 ========================

@bp.route("/instance/<int:challenge_id>", methods=["GET"])
@jwt_required()
def get_container_instance(challenge_id):
    """
    获取用户该题目的运行实例
    
    返回:
    {
        "success": true,
        "data": {
            "instance_id": 1,
            "container_id": "abc123...",
            "connection_url": "http://localhost:8080",
            "port": 8080,
            "is_running": true,
            "expires_at": "2024-01-01T12:00:00"
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        challenge = CtfChallenge.query.get(challenge_id)

        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).first()

        # 检查容器是否已过期
        if instance and instance.expires_at and instance.expires_at < datetime.utcnow():
            # 清理过期容器
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                container.stop(timeout=5)
                container.remove(force=True)
            except:
                pass
            
            instance.is_running = False
            db.session.commit()
            instance = None

        if not instance:
            return jsonify({
                "success": False,
                "data": None,
                "message": "无运行的实例"
            }), 200

        return jsonify({
            "success": True,
            "data": instance.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"获取容器实例异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 容器时间扩展 ========================

@bp.route("/extend/<int:instance_id>", methods=["POST"])
@jwt_required()
def extend_container(instance_id):
    """
    扩展容器运行时间（再延长1小时）
    
    返回:
    {
        "success": true,
        "message": "容器已延期1小时",
        "data": {
            "expires_at": "2024-01-01T14:00:00"
        }
    }
    """
    try:
        user_id = get_jwt_identity()
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"success": False, "message": "实例不存在"}), 404

        if instance.user_id != user_id:
            return jsonify({"success": False, "message": "无权操作"}), 403

        if not instance.is_running:
            return jsonify({"success": False, "message": "容器未运行"}), 400

        # 最多延期3次（总共4小时 = 初始1小时 + 延期3小时）
        if instance.expires_at:
            original = instance.started_at
            current_expire = instance.expires_at
            max_expire = original + timedelta(hours=4)  # 改为最多4小时总时长
            
            if current_expire >= max_expire:
                return jsonify({
                    "success": False,
                    "message": "已达到最大延期时间（最多可用4小时）"
                }), 400

        # 延长1小时
        instance.expires_at = instance.expires_at + timedelta(hours=1) if instance.expires_at else datetime.utcnow() + timedelta(hours=1)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "容器已延期1小时",
            "data": {
                "expires_at": instance.expires_at.isoformat() if instance.expires_at else None
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"扩展容器异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 容器Flag提交 ========================

@bp.route("/submit-flag", methods=["POST"])
@jwt_required()
def submit_container_flag():
    """
    提交容器题目Flag
    
    请求体:
    {
        "challenge_id": 1,
        "flag": "flag{...}",
        "team_id": 1  # 可选
    }
    
    返回:
    {
        "success": true,
        "correct": true,
        "message": "✓ 答案正确！",
        "container_closed": false
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401

        data = request.get_json()
        challenge_id = data.get("challenge_id")
        flag = data.get("flag", "").strip()

        if not challenge_id or not flag:
            return jsonify({"success": False, "message": "参数不完整"}), 400

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        # ========== 验证Flag（支持动态flag）==========
        # 首先尝试找到该用户该题的运行中容器实例
        instance = CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            user_id=user_id,
            is_running=True
        ).first()
        
        # 判断是动态flag还是静态flag
        is_correct = False
        if instance and instance.dynamic_flag:
            # 有动态flag，验证提交的flag是否与动态flag匹配
            is_correct = (flag.strip() == instance.dynamic_flag.strip())
            logger.info(f"容器题目 flag 验证: challenge_id={challenge_id}, user_id={user_id}, "
                       f"submitted={flag[:20]}..., expected={instance.dynamic_flag[:20]}..., correct={is_correct}")
        else:
            # 回退到静态flag验证
            is_correct = (flag == challenge.flag)
            logger.info(f"静态题目 flag 验证: challenge_id={challenge_id}, user_id={user_id}, correct={is_correct}")

        if is_correct:
            # 检查是否已提交过正确答案
            existing = CtfChallengeSubmission.query.filter_by(
                challenge_id=challenge_id,
                user_id=user_id,
                is_correct=True
            ).first()

            if not existing:
                submission = CtfChallengeSubmission(
                    challenge_id=challenge_id,
                    user_id=user_id,
                    answer=flag,
                    is_correct=True,
                    submitted_at=datetime.utcnow()
                )
                db.session.add(submission)
                db.session.commit()

            # 关闭容器
            container_closed = False
            if instance:
                try:
                    docker_client = docker.from_env()
                    container = docker_client.containers.get(instance.container_id)
                    container.stop()
                    container.remove()
                except:
                    pass

                instance.is_running = False
                db.session.commit()
                container_closed = True

            return jsonify({
                "success": True,
                "correct": True,
                "message": "✓ 答案正确！",
                "container_closed": container_closed,
                "points": challenge.points,
                "data": {
                    "submission": {
                        "challenge_id": challenge_id,
                        "answer": flag,
                        "is_correct": True,
                        "submitted_at": datetime.utcnow().isoformat()
                    }
                }
            }), 200

        else:
            # 记录错误提交
            submission = CtfChallengeSubmission(
                challenge_id=challenge_id,
                user_id=user_id,
                answer=flag,
                is_correct=False,
                submitted_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.commit()

            return jsonify({
                "success": True,
                "correct": False,
                "message": "✗ 答案错误"
            }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交容器Flag异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# ======================== 调试工具（仅开发环境）========================

@bp.route("/debug/<int:instance_id>", methods=["GET"])
@jwt_required()
def debug_instance(instance_id):
    """
    调试端点：检查容器的 flag 配置
    
    用途：
    - 查看容器的动态 flag
    - 查看容器的环境变量
    - 验证 flag 是否正确注入
    
    注意：生产环境应该禁用此端点！
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # 仅管理员可用
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "权限不足"
            }), 403
        
        instance = CtfGameInstance.query.get(instance_id)
        if not instance:
            return jsonify({
                "success": False,
                "message": "实例不存在"
            }), 404
        
        result = {
            "instance_id": instance_id,
            "challenge_id": instance.challenge_id,
            "user_id": instance.user_id,
            "is_running": instance.is_running,
            "started_at": instance.started_at.isoformat() if instance.started_at else None,
            "dynamic_flag": instance.dynamic_flag,
            "container_id": instance.container_id,
            "port": instance.port
        }
        
        # 检查flag中是否有占位符
        if instance.dynamic_flag:
            has_placeholders = '[' in instance.dynamic_flag or ']' in instance.dynamic_flag
            result["flag_status"] = "ERROR: Contains placeholders" if has_placeholders else "OK"
            result["flag_length"] = len(instance.dynamic_flag)
        
        # 如果容器正在运行，获取环境变量
        if instance.is_running and instance.container_id:
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                
                # 获取容器配置
                env_list = container.attrs.get('Config', {}).get('Env', [])
                
                # 提取 FLAG 相关的环境变量
                flag_envs = {}
                for env in env_list:
                    if 'FLAG' in env:
                        key, value = env.split('=', 1)
                        flag_envs[key] = value
                
                result["container_status"] = container.status
                result["container_env"] = flag_envs
                
                # 验证环境变量是否与数据库一致
                if 'FLAG' in flag_envs:
                    result["env_match"] = flag_envs['FLAG'] == instance.dynamic_flag
                else:
                    result["env_match"] = False
                    result["error"] = "FLAG environment variable not found in container"
                    
            except docker.errors.NotFound:
                result["container_status"] = "not_found"
                result["error"] = "Container not found in Docker"
            except Exception as e:
                result["container_error"] = str(e)
        
        # 获取题目信息
        challenge = CtfChallenge.query.get(instance.challenge_id)
        if challenge:
            result["challenge_info"] = {
                "title": challenge.title,
                "flag_template": challenge.flag_template,
                "docker_image": challenge.docker_image,
                "challenge_type": challenge.challenge_type
            }
        
        return jsonify({
            "success": True,
            "data": result
        }), 200
        
    except Exception as e:
        logger.error(f"调试实例异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@bp.route("/test-flag-generation", methods=["POST"])
@jwt_required()
def test_flag_generation():
    """
    测试 flag 生成功能
    
    用途：验证 flag 模板是否能正确生成 flag
    
    请求体：
    {
        "flag_template": "flag{hello_[TEAM_HASH]}",
        "challenge_id": 1,
        "user_id": 1,
        "team_id": 1
    }
    """
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # 仅管理员可用
        if not user or not user.is_admin:
            return jsonify({
                "success": False,
                "message": "权限不足"
            }), 403
        
        data = request.get_json()
        flag_template = data.get('flag_template')
        
        if not flag_template:
            return jsonify({
                "success": False,
                "message": "flag_template 参数缺失"
            }), 400
        
        # 使用提供的参数或默认值
        test_challenge_id = data.get('challenge_id', 1)
        test_user_id = data.get('user_id', user_id)
        test_team_id = data.get('team_id', user.team_id if user.team_id else user_id)
        test_game_id = data.get('game_id', 1)
        
        # 尝试生成 flag
        generated_flag = ContainerFlagService.generate_dynamic_flag(
            flag_template=flag_template,
            challenge_id=test_challenge_id,
            user_id=test_user_id,
            game_id=test_game_id,
            team_id=test_team_id,
            team_hash_salt="test_salt_123"
        )
        
        # 检查占位符
        has_placeholders = '[' in generated_flag or ']' in generated_flag
        
        return jsonify({
            "success": True,
            "data": {
                "flag_template": flag_template,
                "generated_flag": generated_flag,
                "has_placeholders": has_placeholders,
                "status": "ERROR: Placeholders not replaced" if has_placeholders else "OK",
                "flag_length": len(generated_flag),
                "test_params": {
                    "challenge_id": test_challenge_id,
                    "user_id": test_user_id,
                    "team_id": test_team_id,
                    "game_id": test_game_id
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"测试flag生成异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ======================== 容器代理 ========================

@bp.route("/proxy/<int:instance_id>", methods=["GET", "POST", "PUT", "DELETE"])
@jwt_required()
def proxy_container(instance_id):
    """
    代理访问容器内的Web服务
    
    查询参数:
    ?path=/index.html - 访问的路径
    
    返回: 来自容器的响应
    """
    try:
        user_id = get_jwt_identity()
        try:
            user_id_int = int(user_id)
        except Exception:
            user_id_int = user_id
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"success": False, "message": "实例不存在"}), 404

        if instance.user_id != user_id_int:
            return jsonify({"success": False, "message": "无权操作"}), 403

        if not instance.is_running:
            return jsonify({"success": False, "message": "容器未运行"}), 400

        # 构建代理URL
        path = request.args.get("path", "/")
        proxy_url = f"http://localhost:{instance.port}{path}"

        # 转发请求到容器
        try:
            # 准备请求头
            headers = {}
            for header, value in request.headers:
                # 跳过某些头部
                if header.lower() not in ['host', 'connection', 'content-length']:
                    headers[header] = value

            # 发送代理请求
            if request.method == "GET":
                resp = requests.get(proxy_url, headers=headers, timeout=30)
            elif request.method == "POST":
                resp = requests.post(proxy_url, data=request.get_data(), headers=headers, timeout=30)
            elif request.method == "PUT":
                resp = requests.put(proxy_url, data=request.get_data(), headers=headers, timeout=30)
            elif request.method == "DELETE":
                resp = requests.delete(proxy_url, headers=headers, timeout=30)
            else:
                return jsonify({"success": False, "message": "不支持的方法"}), 405

            # 记录流量（GZCTF 方式：代理层面记录请求/响应）
            try:
                challenge = CtfChallenge.query.get(instance.challenge_id)
                if challenge and challenge.enable_traffic_capture:
                    manager = get_traffic_manager()
                    user = User.query.get(user_id)
                    team_id = getattr(instance, "team_id", None) or (user.team_id if user else 0) or 0
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    pcap_path = manager.get_capture_path(
                        instance.challenge_id,
                        team_id,
                        user_id,
                        timestamp=timestamp
                    )

                    source_ip = _normalize_ipv4(request.remote_addr or "0.0.0.0")
                    source_port = int(request.environ.get("REMOTE_PORT", 0) or 0)
                    dest_ip = _normalize_ipv4("127.0.0.1")
                    dest_port = int(instance.port)

                    request_body = request.get_data() or b""
                    request_bytes = _build_raw_http_request(request.method, path, headers, request_body)
                    response_body = resp.content or b""
                    response_bytes = _build_raw_http_response(
                        resp.status_code,
                        resp.reason or "OK",
                        resp.headers,
                        response_body
                    )

                    record_http_exchange(
                        pcap_path,
                        (source_ip, source_port),
                        (dest_ip, dest_port),
                        request_bytes,
                        response_bytes
                    )
            except Exception as e:
                logger.warning(f"PCAP capture skipped: {e}")

            # 返回容器的响应
            response = Response(resp.content, status=resp.status_code)
            
            # 复制容器响应的某些头部
            for header, value in resp.headers.items():
                if header.lower() not in ['connection', 'content-encoding', 'transfer-encoding']:
                    response.headers[header] = value

            return response

        except requests.exceptions.Timeout:
            return jsonify({
                "success": False,
                "message": "容器请求超时"
            }), 504
        except requests.exceptions.ConnectionError:
            return jsonify({
                "success": False,
                "message": "无法连接到容器，请检查容器是否正常运行"
            }), 503
        except Exception as e:
            logger.error(f"代理请求失败: {str(e)}")
            return jsonify({
                "success": False,
                "message": f"代理请求失败: {str(e)}"
            }), 500

    except Exception as e:
        logger.error(f"代理容器异常: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
