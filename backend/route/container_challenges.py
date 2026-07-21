"""
Docker容器题目管理路由（兼容别名）

选手侧主路径请使用：
  GET  /api/challenges/<id>/container-status
  POST /api/challenges/<id>/start-container
  POST /api/challenges/instances/<id>/stop
  POST /api/challenges/instances/<id>/extend

本蓝图挂载在 /api/container/*，供旧前端与脚本回退调用。
"""
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from backend.server.extensions import db
from backend.server.db_models import (
    CtfChallenge, CtfGameInstance, User, CtfChallengeSubmission
)
from backend.server.traffic_capture import get_traffic_manager, record_http_exchange
from backend.services.flag_generator import ContainerFlagService, ensure_team_hash_salt
from backend.server.container_access import build_connection_url, normalize_connection_url
from backend.server.container_ports import allocate_host_port
from backend.services.container_traffic import maybe_start_traffic_capture
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


@bp.after_request
def _deprecation_headers(response):
    """标记兼容别名即将弃用，引导客户端改用 /api/challenges/*。"""
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/challenges>; rel="successor-version"'
    response.headers["Warning"] = '299 - "/api/container/* is deprecated; use /api/challenges/*"'
    return response


def _resolve_user(user_id):
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        uid = user_id
    user = User.query.get(uid)
    return user, uid


def _find_running_instance(challenge_id, user, user_id):
    if user and user.team_id:
        return CtfGameInstance.query.filter_by(
            challenge_id=challenge_id,
            team_id=user.team_id,
            is_running=True,
        ).first()
    return CtfGameInstance.query.filter_by(
        challenge_id=challenge_id,
        user_id=user_id,
        is_running=True,
    ).first()


from backend.server.security_helpers import user_can_manage_instance
from backend.services.permission_service import PermissionService, GamePermission
from backend.middleware_refactored import rate_limit


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





def _container_start_rate_key():
    try:
        return f"container:start:{get_jwt_identity()}"
    except Exception:
        return "container:start:anon"


# ======================== 容器启动 ========================

@bp.route("/start/<int:challenge_id>", methods=["POST"])
@jwt_required()
@rate_limit(key_func=_container_start_rate_key, max_requests=8, window_seconds=60, error_message="启容器过于频繁，请稍后再试")
def start_container(challenge_id):
    """启动 Docker 容器：统一走 container_service + 配额=2。"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401

        challenge = CtfChallenge.query.get(challenge_id)
        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        if not user.is_admin and not PermissionService.check_challenge_permission(
            int(user_id), challenge_id, GamePermission.VIEW_CHALLENGE
        ):
            return jsonify({"success": False, "message": "无权启动该题目容器"}), 403

        if not challenge.docker_image:
            return jsonify({"success": False, "message": "该题目不支持容器"}), 400

        from backend.services.team_service import ensure_user_has_team
        from backend.services.instance_quota import check_can_start_new_instance
        from backend.services.container_start_queue import create_container_queued

        team = ensure_user_has_team(user)
        ok_quota, quota_msg, existing = check_can_start_new_instance(
            user, team, challenge_id=challenge_id,
        )
        if existing:
            return jsonify({
                "success": True,
                "action_type": "manage",
                "data": existing.to_dict(),
                "message": quota_msg or "容器已在运行",
            }), 200
        if not ok_quota:
            return jsonify({"success": False, "message": quota_msg}), 429

        success, instance, msg = create_container_queued(
            challenge=challenge, user=user, team=team, expire_hours=1,
        )
        if not success:
            return jsonify({"success": False, "message": msg or "容器启动失败"}), 500
        return jsonify({
            "success": True,
            "action_type": "manage",
            "data": instance.to_dict(),
            "message": "容器启动成功",
        }), 201
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
        user, user_id = _resolve_user(user_id)
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"success": False, "message": "实例不存在"}), 404

        if not user_can_manage_instance(user, user_id, instance):
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
        user, user_id = _resolve_user(user_id)
        challenge = CtfChallenge.query.get(challenge_id)
        
        logger.info(f"[STATUS] user_id={user_id}, challenge_id={challenge_id}")

        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401

        instance = _find_running_instance(challenge_id, user, user_id)
        
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
        user, user_id = _resolve_user(user_id)
        challenge = CtfChallenge.query.get(challenge_id)

        if not challenge:
            return jsonify({"success": False, "message": "题目不存在"}), 404

        if not user:
            return jsonify({"success": False, "message": "用户不存在"}), 401

        instance = _find_running_instance(challenge_id, user, user_id)

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
        user, user_id = _resolve_user(user_id)
        instance = CtfGameInstance.query.get(instance_id)

        if not instance:
            return jsonify({"success": False, "message": "实例不存在"}), 404

        if not user_can_manage_instance(user, user_id, instance):
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
    """遗留容器提交：转发主路径，统一动态 Flag / 计分 / 竞态保护。"""
    data = request.get_json() or {}
    challenge_id = data.get("challenge_id")
    if not challenge_id:
        return jsonify({"success": False, "message": "缺少 challenge_id"}), 400
    if not (data.get("flag") or data.get("answer")):
        return jsonify({"success": False, "message": "缺少 flag"}), 400
    from backend.route import challenges as challenges_route
    return challenges_route.submit_flag(int(challenge_id))


# ======================== 调试工具（仅开发环境）========================

@bp.route("/debug/<int:instance_id>", methods=["GET"])
@jwt_required()
def debug_instance(instance_id):
    """
    调试端点：检查容器的 flag 配置（仅 DEBUG + 管理员）
    """
    from backend.server import config as app_config
    if not app_config.settings.DEBUG:
        return jsonify({"success": False, "message": "not allowed"}), 403
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
            "has_dynamic_flag": bool(instance.dynamic_flag),
            "container_id": instance.container_id[:12] if instance.container_id else None,
            "port": instance.port
        }

        if instance.dynamic_flag:
            has_placeholders = '[' in instance.dynamic_flag or ']' in instance.dynamic_flag
            result["flag_status"] = "ERROR: Contains placeholders" if has_placeholders else "OK"
            result["flag_length"] = len(instance.dynamic_flag)

        # 不回传明文 FLAG / 环境变量值
        if instance.is_running and instance.container_id:
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(instance.container_id)
                env_list = container.attrs.get('Config', {}).get('Env', [])
                flag_env_keys = []
                for env in env_list:
                    if '=' in env:
                        key, _ = env.split('=', 1)
                        if 'FLAG' in key.upper():
                            flag_env_keys.append(key)
                result["container_status"] = container.status
                result["flag_env_keys"] = flag_env_keys
                result["flag_env_present"] = bool(flag_env_keys)
            except docker.errors.NotFound:
                result["container_status"] = "not_found"
                result["error"] = "Container not found in Docker"
            except Exception as e:
                result["container_error"] = str(e)

        challenge = CtfChallenge.query.get(instance.challenge_id)
        if challenge:
            result["challenge_info"] = {
                "title": challenge.title,
                "has_flag_template": bool(challenge.flag_template),
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
    测试 flag 生成功能（仅 DEBUG + 管理员）
    """
    from flask import current_app
    if not current_app.config.get('DEBUG', False):
        return jsonify({"success": False, "message": "not allowed"}), 403
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
        
        # 尝试生成 flag（仅返回诊断信息，不回传明文 Flag）
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
        return jsonify({
            "success": False,
            "message": "flag generation test failed"
        }), 500


# ======================== 容器代理（已废弃） ========================

@bp.route("/proxy/<int:instance_id>", methods=["GET", "POST", "PUT", "DELETE"])
@jwt_required()
def proxy_container(instance_id):
    """HTTP 代理已移除，请直接访问公网 IP:端口。"""
    return jsonify({
        "success": False,
        "message": "容器 HTTP 代理已停用，请使用题目页显示的公网地址直接连接",
    }), 410
