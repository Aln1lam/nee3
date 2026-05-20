"""
PCAP 文件存储和管理模块
仅处理流量包文件的存储、查询、清理等基础功能
实际的流量捕获在代理层面进行（类似GZCTF的RecordableNetworkStream）
"""

import logging
import struct
import time
from datetime import datetime, timedelta
from pathlib import Path
import ipaddress
import socket
import threading

logger = logging.getLogger(__name__)


class TrafficCaptureManager:
    """PCAP 文件管理器 - 简化版本"""
    
    def __init__(self, captures_dir="captures"):
        """
        初始化 PCAP 文件管理器
        
        Args:
            captures_dir: PCAP 文件存储目录
        """
        self.base_dir = Path(captures_dir)
        self.base_dir.mkdir(exist_ok=True)
        logger.info(f"✓ PCAP storage initialized: {self.base_dir}")
    
    @property
    def captures_dir(self):
        """为了向后兼容"""
        return self.base_dir
    
    def get_capture_path(self, challenge_id, team_id, user_id, timestamp=None):
        """
        生成标准的 PCAP 存储路径
        
        目录结构: captures/challenge_{challenge_id}_team_{team_id}_user_{user_id}/
        文件名: {timestamp}.pcap
        
        Args:
            challenge_id: 题目 ID
            team_id: 队伍 ID  
            user_id: 用户 ID
            timestamp: 时间戳（用于文件名），默认使用当前时间
        
        Returns:
            Path: 完整的文件路径
        """
        # 构建母文件夹名称
        folder_name = f"challenge_{challenge_id}_team_{team_id}_user_{user_id}"
        capture_dir = self.base_dir / folder_name
        capture_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名（仅包含时间）
        if timestamp is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        filename = f"{timestamp}.pcap"
        return capture_dir / filename
    
    def list_captures(self, challenge_id=None, team_id=None, user_id=None):
        """
        列出存储的 PCAP 文件
        
        Args:
            challenge_id: 过滤题目 ID（可选）
            team_id: 过滤队伍 ID（可选）
            user_id: 过滤用户 ID（可选）
        
        Returns:
            list: PCAP 文件信息列表
        """
        captures = []
        
        # 构建搜索模式（使用与 get_capture_path 一致的目录结构）
        if challenge_id and team_id and user_id:
            # 搜索特定用户的 PCAP 文件
            folder_pattern = f"challenge_{challenge_id}_team_{team_id}_user_{user_id}"
            search_pattern = self.base_dir.glob(f"{folder_pattern}/*.pcap")
        elif challenge_id and team_id:
            # 搜索特定题目和队伍的所有用户的 PCAP 文件
            search_pattern = self.base_dir.glob(f"challenge_{challenge_id}_team_{team_id}_user_*/*.pcap")
        elif challenge_id:
            # 搜索特定题目的所有 PCAP 文件
            search_pattern = self.base_dir.glob(f"challenge_{challenge_id}_team_*_user_*/*.pcap")
        else:
            # 搜索所有 PCAP 文件
            search_pattern = self.base_dir.glob(f"challenge_*_team_*_user_*/*.pcap")
        
        for pcap_file in search_pattern:
            try:
                file_stat = pcap_file.stat()
                
                # 从文件夹名中解析 ID
                folder_name = pcap_file.parent.name
                capture_info = {
                    "file": pcap_file.name,
                    "path": str(pcap_file.relative_to(self.base_dir)),
                    "size": file_stat.st_size,
                    "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                }
                
                # 解析文件夹名格式: challenge_<id>_team_<id>_user_<id>
                try:
                    parts = folder_name.split('_')
                    if len(parts) >= 6:
                        capture_info["challenge_id"] = int(parts[1])
                        capture_info["team_id"] = int(parts[3])
                        capture_info["user_id"] = int(parts[5])
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse capture folder name {folder_name}: {e}")
                
                captures.append(capture_info)
                
            except Exception as e:
                logger.error(f"Error reading PCAP file {pcap_file}: {e}")
                continue
        
        # 按修改时间排序（最新的在前）
        captures.sort(key=lambda x: x.get("modified", ""), reverse=True)
        
        return captures
    
    def cleanup_old_captures(self, days=30):
        """
        清理超过指定天数的 PCAP 文件
        
        Args:
            days: 保留天数（默认30天）
        
        Returns:
            dict: 清理统计 {"deleted": count, "freed_bytes": bytes}
        """
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        freed_bytes = 0
        
        for pcap_file in self.base_dir.glob("*/*/*.pcap"):
            try:
                file_stat = pcap_file.stat()
                file_time = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_time < cutoff_time:
                    freed_bytes += file_stat.st_size
                    pcap_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old PCAP: {pcap_file}")
                    
            except Exception as e:
                logger.error(f"Error deleting PCAP {pcap_file}: {e}")
        
        logger.info(f"PCAP cleanup: deleted {deleted_count} files, freed {freed_bytes/1024/1024:.1f} MB")
        
        return {
            "deleted": deleted_count,
            "freed_bytes": freed_bytes
        }
    
    def get_capture_file(self, challenge_id, team_id, user_id, filename):
        """
        获取特定的 PCAP 文件路径（用于下载）
        
        Args:
            challenge_id: 题目 ID
            team_id: 队伍 ID
            user_id: 用户 ID
            filename: 文件名
        
        Returns:
            Path: 文件路径（如果存在）或 None
        """
        folder_name = f"challenge_{challenge_id}_team_{team_id}_user_{user_id}"
        file_path = self.base_dir / folder_name / filename
        
        if file_path.exists() and file_path.suffix == ".pcap":
            return file_path
        
        return None
    
    def save_capture_record(self, challenge_id, instance_id, team_id, user_id, file_path, file_size=0):
        """
        保存流量捕获记录到数据库
        
        Args:
            challenge_id: 题目 ID
            instance_id: 实例 ID
            team_id: 队伍 ID
            user_id: 用户 ID
            file_path: 文件路径（相对于 captures 目录）
            file_size: 文件大小（字节）
        
        Returns:
            PcapCapture: 创建的数据库记录对象，或 None（如果导入失败）
        """
        try:
            from backend.server.db_models import PcapCapture
            from backend.server.extensions import db
            
            # 检查是否已存在
            existing = PcapCapture.query.filter_by(
                challenge_id=challenge_id,
                instance_id=instance_id,
                user_id=user_id
            ).first()
            
            if existing:
                # 更新现有记录
                existing.file_path = file_path
                existing.file_size = file_size
                existing.is_completed = True
                existing.completed_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Updated PCAP capture record: {file_path}")
                return existing
            else:
                # 创建新记录
                capture_record = PcapCapture(
                    challenge_id=challenge_id,
                    instance_id=instance_id,
                    team_id=team_id,
                    user_id=user_id,
                    file_path=file_path,
                    file_size=file_size,
                    is_completed=True,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow()
                )
                db.session.add(capture_record)
                db.session.commit()
                logger.info(f"Created PCAP capture record: {file_path}")
                return capture_record
                
        except ImportError:
            logger.warning("Failed to import PcapCapture model, skipping database record")
            return None
        except Exception as e:
            logger.error(f"Error saving PCAP capture record: {e}")
            return None
    
    def start_capture(self, container_id, instance_id, user_id, challenge_id, 
                     target_port, team_id=None, enable_traffic_capture=True, 
                     duration_seconds=3600, challenge_name="Unknown"):
        """
        启动流量捕获代理
        
        Args:
            container_id: 容器ID
            instance_id: 实例ID
            user_id: 用户ID
            challenge_id: 题目ID
            target_port: 容器实际映射的端口（如43978）
            team_id: 队伍ID（可选）
            enable_traffic_capture: 是否启用捕获
            duration_seconds: 捕获时长（秒）
            challenge_name: 题目名称
        
        Returns:
            dict: 包含代理端口和PCAP路径的信息
        """
        if not enable_traffic_capture:
            logger.info(f"Traffic capture disabled for instance {instance_id}")
            return {"status": "disabled"}
        
        try:
            # 生成PCAP文件路径
            pcap_path = self.get_capture_path(challenge_id, team_id or user_id, user_id)
            logger.info(f"PCAP path: {pcap_path}")
            
            # 创建PcapWriter
            pcap_writer = PcapWriter(pcap_path)
            
            # 为该instance分配一个代理端口（动态分配：53000 + instance_id）
            proxy_port = 53000 + instance_id
            
            # 创建TCP代理
            proxy = TCPTrafficProxy(
                listen_port=proxy_port,
                target_host='127.0.0.1',
                target_port=target_port,
                pcap_writer=pcap_writer
            )
            
            # 在后台线程启动代理
            proxy_thread = threading.Thread(
                target=proxy.start,
                daemon=True,
                name=f"proxy-{instance_id}"
            )
            proxy_thread.start()
            
            # 保存代理信息（便于之后停止）
            # 注：实际应用中可能需要存储proxy对象供后续停止使用
            
            logger.info(
                f"✓ Traffic capture started for instance {instance_id} "
                f"(challenge={challenge_id}, team={team_id}, proxy_port={proxy_port})"
            )
            
            return {
                "status": "started",
                "instance_id": instance_id,
                "proxy_port": proxy_port,
                "target_port": target_port,
                "pcap_path": str(pcap_path.relative_to(self.base_dir)),
                "challenge_id": challenge_id
            }
        
        except Exception as e:
            logger.error(f"Failed to start traffic capture for instance {instance_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


class PcapWriter:
    """最小化 PCAP 写入器（以 UDP 负载记录流量）"""

    _DUMMY_MAC = b"\x00\x11\x00\x11\x00\x11"

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 确保路径是 Path 对象
        if not isinstance(self.file_path, Path):
            self.file_path = Path(self.file_path)
        
        try:
            self._file = open(self.file_path, "ab")
            logger.info(f"✓ PcapWriter opened: {self.file_path}")
        except Exception as e:
            logger.error(f"✗ Failed to open PCAP file {self.file_path}: {e}")
            raise

        if self.file_path.stat().st_size == 0:
            self._write_global_header()
            logger.info(f"✓ PCAP global header written to {self.file_path}")

    def _write_global_header(self):
        # PCAP Global Header (little-endian)
        header = struct.pack(
            "<IHHIIII",
            0xA1B2C3D4,  # magic
            2, 4,        # version
            0, 0,        # thiszone, sigfigs
            65535,       # snaplen
            1            # linktype Ethernet
        )
        self._file.write(header)
        self._file.flush()  # 立即刷新全局头部

    def write_packet(self, src_ip, src_port, dst_ip, dst_port, payload: bytes):
        frame = self._build_ethernet_ipv4_udp(src_ip, src_port, dst_ip, dst_port, payload)
        ts = time.time()
        ts_sec = int(ts)
        ts_usec = int((ts - ts_sec) * 1_000_000)
        pkt_header = struct.pack("<IIII", ts_sec, ts_usec, len(frame), len(frame))
        self._file.write(pkt_header)
        self._file.write(frame)
        self._file.flush()  # 立即刷新到磁盘

    def _build_ethernet_ipv4_udp(self, src_ip, src_port, dst_ip, dst_port, payload: bytes) -> bytes:
        # Ethernet
        eth_header = self._DUMMY_MAC + self._DUMMY_MAC + struct.pack("!H", 0x0800)

        # IPv4
        src_ip_bytes = ipaddress.IPv4Address(src_ip).packed
        dst_ip_bytes = ipaddress.IPv4Address(dst_ip).packed
        total_length = 20 + 8 + len(payload)
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45, 0x00, total_length, 0, 0, 64, 17, 0, src_ip_bytes, dst_ip_bytes
        )
        checksum = self._ip_checksum(ip_header)
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            0x45, 0x00, total_length, 0, 0, 64, 17, checksum, src_ip_bytes, dst_ip_bytes
        )

        # UDP (IPv4 checksum can be 0)
        udp_length = 8 + len(payload)
        udp_header = struct.pack("!HHHH", int(src_port), int(dst_port), udp_length, 0)

        return eth_header + ip_header + udp_header + payload

    @staticmethod
    def _ip_checksum(data: bytes) -> int:
        if len(data) % 2 == 1:
            data += b"\x00"
        total = 0
        for i in range(0, len(data), 2):
            total += (data[i] << 8) + data[i + 1]
        while total > 0xFFFF:
            total = (total & 0xFFFF) + (total >> 16)
        return (~total) & 0xFFFF

    def flush(self):
        """刷新缓冲区到磁盘"""
        if self._file:
            self._file.flush()
    
    def close(self):
        if self._file:
            self._file.flush()
            self._file.close()


class TCPTrafficProxy:
    """TCP 流量转发代理 - 在本地监听一个端口，转发到目标容器，同时记录所有流量"""
    
    def __init__(self, listen_port, target_host, target_port, pcap_writer):
        """
        初始化TCP代理
        
        Args:
            listen_port: 代理监听的本地端口
            target_host: 目标容器的主机
            target_port: 目标容器的端口
            pcap_writer: PCAP写入器实例
        """
        self.listen_port = listen_port
        self.target_host = target_host
        self.target_port = target_port
        self.pcap_writer = pcap_writer
        self.running = False
        self.server_socket = None
        
    def start(self):
        """启动代理服务器（主线程）"""
        try:
            self.running = True
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('127.0.0.1', self.listen_port))
            self.server_socket.listen(5)
            
            logger.info(f"✓ TCP traffic proxy started: 127.0.0.1:{self.listen_port} -> {self.target_host}:{self.target_port}")
            
            while self.running:
                try:
                    client_sock, client_addr = self.server_socket.accept()
                    thread = threading.Thread(
                        target=self._handle_connection,
                        args=(client_sock, client_addr),
                        daemon=True
                    )
                    thread.start()
                except OSError:
                    # Server socket closed
                    break
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
        except Exception as e:
            logger.error(f"Failed to start TCP proxy on port {self.listen_port}: {e}")
        finally:
            self.stop()
    
    def _handle_connection(self, client_sock, client_addr):
        """处理单个客户端连接"""
        target_sock = None
        try:
            # 连接到目标服务器
            target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_sock.connect((self.target_host, self.target_port))
            
            # 双向转发（后台线程处理反向流量）
            reverse_thread = threading.Thread(
                target=self._forward_traffic,
                args=(target_sock, client_sock, (self.target_host, self.target_port), client_addr),
                daemon=True
            )
            reverse_thread.start()
            
            # 主线程处理正向流量
            self._forward_traffic(client_sock, target_sock, client_addr, (self.target_host, self.target_port))
            
        except Exception as e:
            logger.error(f"Connection error from {client_addr}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            if target_sock:
                try:
                    target_sock.close()
                except:
                    pass
    
    def _forward_traffic(self, src_sock, dst_sock, src_addr, dst_addr):
        """
        转发流量并记录到PCAP
        
        Args:
            src_sock: 源socket
            dst_sock: 目标socket
            src_addr: 源地址 (host, port)
            dst_addr: 目标地址 (host, port)
        """
        try:
            while self.running:
                data = src_sock.recv(4096)
                if not data:
                    break
                
                # 记录数据包到PCAP（模拟为UDP负载）
                try:
                    self.pcap_writer.write_packet(
                        src_addr[0], src_addr[1],
                        dst_addr[0], dst_addr[1],
                        data
                    )
                except Exception as e:
                    logger.error(f"Failed to write PCAP: {e}")
                
                # 转发数据
                try:
                    dst_sock.sendall(data)
                except:
                    break
        except Exception as e:
            logger.error(f"Forward error: {e}")
        finally:
            try:
                dst_sock.close()
            except:
                pass
    
    def stop(self):
        """停止代理"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info(f"TCP traffic proxy stopped on port {self.listen_port}")


def record_http_exchange(pcap_path: Path, source, dest, request_bytes: bytes, response_bytes: bytes):
    """以 GZCTF 的记录方式保存请求/响应（UDP 负载）"""
    writer = PcapWriter(pcap_path)
    try:
        writer.write_packet(source[0], source[1], dest[0], dest[1], request_bytes)
        writer.write_packet(dest[0], dest[1], source[0], source[1], response_bytes)
    finally:
        writer.close()


# 全局实例
_traffic_manager = None


def get_traffic_manager():
    """获取全局的 PCAP 管理器实例"""
    global _traffic_manager
    if _traffic_manager is None:
        _traffic_manager = TrafficCaptureManager()
    return _traffic_manager
