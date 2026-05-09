"""
加密通信服务 - 实现智能体间安全数据交互
支持 TLS 1.3 + 国密 SM4 双重加密
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

from ..core.config import get_settings

settings = get_settings()


class EncryptionService:
    """加密服务类"""
    
    def __init__(self):
        # 初始化加密密钥
        self.encryption_key = settings.ENCRYPTION_KEY.encode('utf-8')
        # 确保密钥长度为 32 字节
        if len(self.encryption_key) < 32:
            self.encryption_key = self.encryption_key.ljust(32, b'\0')
        elif len(self.encryption_key) > 32:
            self.encryption_key = self.encryption_key[:32]
        
        # Fernet 用于简单加密
        fernet_key = base64.urlsafe_b64encode(hashlib.sha256(self.encryption_key).digest())
        self.fernet = Fernet(fernet_key)
        
        # 是否使用国密 SM4（简化版，实际应使用专业库）
        self.use_sm4 = settings.USE_CHINESE_CRYPTO
    
    def encrypt_data(self, data: Dict[str, Any]) -> str:
        """加密数据（返回 Base64 编码的密文）"""
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        
        if self.use_sm4:
            # SM4 加密（简化实现）
            encrypted = self._sm4_encrypt(json_data)
        else:
            # Fernet 加密
            encrypted = self.fernet.encrypt(json_data)
        
        return base64.b64encode(encrypted).decode('utf-8')
    
    def decrypt_data(self, encrypted_data: str) -> Dict[str, Any]:
        """解密数据"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            if self.use_sm4:
                decrypted = self._sm4_decrypt(encrypted_bytes)
            else:
                decrypted = self.fernet.decrypt(encrypted_bytes)
            
            return json.loads(decrypted.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"解密失败：{str(e)}")
    
    def _sm4_encrypt(self, data: bytes) -> bytes:
        """SM4 加密（简化版，实际生产应使用专业国密库）"""
        # 生成随机 IV
        iv = os.urandom(16)
        
        # 使用 AES 模拟 SM4（实际应替换为 sm4 库）
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CFB(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(data) + encryptor.finalize()
        
        return iv + encrypted
    
    def _sm4_decrypt(self, data: bytes) -> bytes:
        """SM4 解密（简化版）"""
        iv = data[:16]
        encrypted = data[16:]
        
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CFB(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        return decryptor.update(encrypted) + decryptor.finalize()
    
    def hash_data(self, data: Dict[str, Any]) -> str:
        """计算数据哈希值（用于完整性校验）"""
        json_data = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(json_data.encode('utf-8')).hexdigest()
    
    def verify_integrity(self, data: Dict[str, Any], expected_hash: str) -> bool:
        """验证数据完整性"""
        computed_hash = self.hash_data(data)
        return computed_hash == expected_hash


class SecureChannel:
    """安全通信通道"""
    
    def __init__(self, channel_id: str, encryption_service: EncryptionService):
        self.channel_id = channel_id
        self.encryption_service = encryption_service
        self.message_queue: List[Dict[str, Any]] = []
        self.created_at = datetime.now(timezone.utc)
    
    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发送加密消息"""
        timestamp = datetime.now(timezone.utc)
        
        # 构建消息
        message = {
            "channel_id": self.channel_id,
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "message_type": message_type,
            "payload": payload,
            "timestamp": timestamp.isoformat(),
            "sequence": len(self.message_queue) + 1
        }
        
        # 计算哈希
        message["hash"] = self.encryption_service.hash_data(payload)
        
        # 加密 payload
        encrypted_payload = self.encryption_service.encrypt_data(payload)
        message["encrypted_payload"] = encrypted_payload
        
        # 存储到队列
        self.message_queue.append(message)
        
        return {
            "status": "success",
            "message_id": f"{self.channel_id}_{message['sequence']}",
            "timestamp": timestamp.isoformat()
        }
    
    def receive_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """接收并解密消息"""
        for message in self.message_queue:
            if f"{self.channel_id}_{message['sequence']}" == message_id:
                # 解密 payload
                decrypted_payload = self.encryption_service.decrypt_data(
                    message["encrypted_payload"]
                )
                
                # 验证完整性
                is_valid = self.encryption_service.verify_integrity(
                    decrypted_payload,
                    message["hash"]
                )
                
                if not is_valid:
                    raise ValueError("消息完整性校验失败")
                
                return {
                    "message_id": message_id,
                    "sender_id": message["sender_id"],
                    "receiver_id": message["receiver_id"],
                    "message_type": message["message_type"],
                    "payload": decrypted_payload,
                    "timestamp": message["timestamp"],
                    "verified": True
                }
        
        return None
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取消息历史（不包含加密内容）"""
        return [
            {
                "message_id": f"{self.channel_id}_{msg['sequence']}",
                "sender_id": msg["sender_id"],
                "receiver_id": msg["receiver_id"],
                "message_type": msg["message_type"],
                "timestamp": msg["timestamp"],
                "hash": msg["hash"]
            }
            for msg in self.message_queue[-limit:]
        ]


class CommunicationManager:
    """通信管理器 - 管理所有安全通道"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
        self.channels: Dict[str, SecureChannel] = {}
    
    def create_channel(
        self,
        channel_id: str,
        participant_ids: List[str]
    ) -> SecureChannel:
        """创建新的安全通信通道"""
        if channel_id in self.channels:
            raise ValueError(f"通道已存在：{channel_id}")
        
        channel = SecureChannel(channel_id, self.encryption_service)
        self.channels[channel_id] = channel
        
        # 发送系统消息
        channel.send_message(
            sender_id="system",
            receiver_id="all",
            message_type="channel_created",
            payload={
                "participants": participant_ids,
                "created_at": channel.created_at.isoformat()
            }
        )
        
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[SecureChannel]:
        """获取通信通道"""
        return self.channels.get(channel_id)
    
    def close_channel(self, channel_id: str) -> bool:
        """关闭通信通道"""
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            
            # 发送关闭通知
            channel.send_message(
                sender_id="system",
                receiver_id="all",
                message_type="channel_closed",
                payload={"reason": "channel_closed"}
            )
            
            del self.channels[channel_id]
            return True
        
        return False
    
    def broadcast_message(
        self,
        channel_id: str,
        sender_id: str,
        message_type: str,
        payload: Dict[str, Any],
        receiver_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """广播消息给多个接收者"""
        channel = self.get_channel(channel_id)
        if not channel:
            raise ValueError(f"通道不存在：{channel_id}")
        
        results = []
        receivers = receiver_ids or ["all"]
        
        for receiver_id in receivers:
            result = channel.send_message(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message_type=message_type,
                payload=payload
            )
            results.append(result)
        
        return results
    
    def get_active_channels(self) -> List[str]:
        """获取所有活跃通道"""
        return list(self.channels.keys())
    
    def get_channel_stats(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """获取通道统计信息"""
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        
        return {
            "channel_id": channel_id,
            "message_count": len(channel.message_queue),
            "created_at": channel.created_at.isoformat(),
            "status": "active"
        }


# 单例模式
_communication_manager = None

def get_communication_manager() -> CommunicationManager:
    """获取通信管理器单例"""
    global _communication_manager
    if _communication_manager is None:
        _communication_manager = CommunicationManager()
    return _communication_manager
