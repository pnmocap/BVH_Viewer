"""
Axis Studio BVH 数据连接器 (Secap 模式)
通过 UDP 接收 Axis Studio 广播的实时 BVH 数据

与 MocapConnector (Mocap 模式) 完全解耦：
- Mocap 模式：使用 MocapAPI 直接与动捕设备通信（TCP/UDP 双向）
- Secap 模式：仅通过 UDP 单向接收 Axis Studio 的 BVH 广播
"""
import threading
import time
from typing import Optional, Dict
import numpy as np

try:
    from mocap_api import (
        MCPApplication, MCPSettings, MCPAvatar, MCPJoint,
        MCPBvhData, MCPBvhRotation, MCPEventType
    )
    AXIS_STUDIO_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Axis Studio API not available: {e}")
    AXIS_STUDIO_API_AVAILABLE = False


class AxisStudioConnectionState:
    """Axis Studio 连接状态"""
    DISCONNECTED = 0      # 未连接（未监听 UDP）
    LISTENING = 1         # 正在监听 UDP 广播
    RECEIVING = 2         # 正在接收数据
    ERROR = -1            # 错误状态


class AxisStudioConnector:
    """
    Axis Studio BVH 数据连接器
    
    功能：
    1. 监听指定 UDP 端口，接收 Axis Studio 广播的 BVH 数据
    2. 解析实时关节数据（位置 + 四元数旋转）
    3. 提供统一的数据接口供 Visualizer 渲染
    
    与 MocapConnector 的区别：
    - 不需要设备连接/校准流程
    - 只要 Axis Studio 在广播，立即可用
    - 无需发送命令（单向接收）
    """
    
    def __init__(self):
        self.app = None
        self.settings = None
        self.is_listening = False
        self.is_receiving_data = False
        self.latest_frame_data = None
        self._lock = threading.Lock()
        self.connection_state = AxisStudioConnectionState.DISCONNECTED
        
        # 网络配置
        self.udp_port = 7012  # Axis Studio 默认 BVH 广播端口
        
        # 帧率统计
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # 数据接收状态
        self.last_data_time = None
        self.data_timeout = 5.0  # 5秒无数据视为断开
    
    def configure(self, udp_port: int = 7012):
        """
        配置 UDP 监听端口
        
        参数:
            udp_port: UDP 端口号（默认 7012，Axis Studio 标准端口）
        """
        self.udp_port = udp_port
    
    def start_listening(self) -> tuple:
        """
        开始监听 Axis Studio BVH 广播
        
        返回:
            (success: bool, message: str)
        """
        if not AXIS_STUDIO_API_AVAILABLE:
            return False, "Axis Studio API not available"
        
        try:
            self.connection_state = AxisStudioConnectionState.LISTENING
            
            # 创建应用和设置
            self.app = MCPApplication()
            self.settings = MCPSettings()
            
            # 配置 BVH 数据格式（与 Axis Studio 保持一致）
            self.settings.set_bvh_data(MCPBvhData.Binary)
            self.settings.set_bvh_rotation(MCPBvhRotation.YXZ)  # 通常为 YXZ 或 XYZ
            
            # 设置 UDP 监听端口（关键：只接收，不发送）
            self.settings.set_udp(self.udp_port)
            
            self.app.set_settings(self.settings)
            success, msg = self.app.open()
            
            if success:
                self.is_listening = True
                self.last_data_time = time.time()
                print(f"[AxisStudioConnector] Listening on UDP port {self.udp_port}")
                print(f"[AxisStudioConnector] Waiting for Axis Studio BVH broadcast...")
                return True, f"Listening on UDP:{self.udp_port}"
            else:
                self.connection_state = AxisStudioConnectionState.ERROR
                return False, f"Failed to listen: {msg}"
                
        except Exception as e:
            self.connection_state = AxisStudioConnectionState.ERROR
            return False, str(e)
    
    def stop_listening(self):
        """停止监听 BVH 广播"""
        try:
            if self.app:
                self.app.close()
            self.is_listening = False
            self.is_receiving_data = False
            self.connection_state = AxisStudioConnectionState.DISCONNECTED
            print("[AxisStudioConnector] Stopped listening")
        except Exception as e:
            print(f"[AxisStudioConnector] Stop listening error: {e}")
    
    def poll_and_update(self) -> Optional[Dict]:
        """
        轮询并更新数据
        
        返回:
            最新的帧数据，格式为:
            {
                'joints': {
                    'Hips': {'position': (x,y,z), 'rotation': (w,x,y,z)},
                    'RightUpLeg': {...},
                    ...
                },
                'timestamp': float
            }
        """
        if not self.is_listening or not self.app:
            return None
        
        frame_data = None
        
        try:
            events = self.app.poll_next_event()
            
            for evt in events:
                if evt.event_type == MCPEventType.AvatarUpdated:
                    # 标记正在接收数据
                    if not self.is_receiving_data:
                        self.is_receiving_data = True
                        self.connection_state = AxisStudioConnectionState.RECEIVING
                        print("[AxisStudioConnector] Started receiving BVH data from Axis Studio")
                    
                    # 解析 Avatar 数据
                    frame_data = self._parse_avatar(evt.event_data.avatar_handle)
                    frame_data['timestamp'] = evt.timestamp
                    
                    # 更新帧率统计
                    self._update_fps()
                    
                    # 更新最后接收时间
                    self.last_data_time = time.time()
                    
                elif evt.event_type == MCPEventType.RigidBodyUpdated:
                    pass  # Axis Studio BVH 模式通常不包含刚体数据
                elif evt.event_type == MCPEventType.Error:
                    print(f"[AxisStudioConnector] Error event: {evt.event_data.error}")
            
            if frame_data:
                with self._lock:
                    self.latest_frame_data = frame_data
            
            # 检查数据超时
            if self.is_receiving_data and self.last_data_time:
                elapsed = time.time() - self.last_data_time
                if elapsed > self.data_timeout:
                    print(f"[AxisStudioConnector] No data received for {self.data_timeout}s - Axis Studio might have stopped broadcasting")
                    self.is_receiving_data = False
                    self.connection_state = AxisStudioConnectionState.LISTENING
            
        except Exception as e:
            print(f"[AxisStudioConnector] Poll error: {e}")
        
        return frame_data
    
    def _parse_avatar(self, avatar_handle) -> Dict:
        """
        解析 Avatar 数据为字典格式
        
        与 MocapConnector 的实现相同，但属于独立模块
        """
        avatar = MCPAvatar(avatar_handle)
        joints_data = {}
        
        try:
            for joint in avatar.get_joints():
                name = joint.get_name()
                pos = joint.get_local_position()  # (x, y, z)
                rot = joint.get_local_rotation()  # (w, x, y, z)
                
                joints_data[name] = {
                    'position': pos if pos else (0.0, 0.0, 0.0),
                    'rotation': rot if rot else (1.0, 0.0, 0.0, 0.0)
                }
        except Exception as e:
            print(f"[AxisStudioConnector] Parse avatar error: {e}")
        
        return {'joints': joints_data}
    
    def _update_fps(self):
        """更新帧率统计"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def get_latest_frame(self) -> Optional[Dict]:
        """获取最新的帧数据（线程安全）"""
        with self._lock:
            return self.latest_frame_data
    
    def get_connection_status_text(self) -> str:
        """获取连接状态文本"""
        if self.connection_state == AxisStudioConnectionState.DISCONNECTED:
            return "Not Listening"
        elif self.connection_state == AxisStudioConnectionState.LISTENING:
            return "Waiting for Data..."
        elif self.connection_state == AxisStudioConnectionState.RECEIVING:
            return f"Receiving ({self.current_fps:.1f} FPS)"
        elif self.connection_state == AxisStudioConnectionState.ERROR:
            return "Error"
        return "Unknown"
    
    def is_ready_for_recording(self) -> bool:
        """
        检查是否准备好录制
        
        Secap 模式：只要在接收数据就可以录制
        """
        return self.is_receiving_data
    
    def get_status_info(self) -> Dict:
        """
        获取详细状态信息
        
        返回:
            {
                'listening': bool,
                'receiving': bool,
                'fps': float,
                'port': int,
                'last_data_age': float  # 秒
            }
        """
        return {
            'listening': self.is_listening,
            'receiving': self.is_receiving_data,
            'fps': self.current_fps,
            'port': self.udp_port,
            'last_data_age': time.time() - self.last_data_time if self.last_data_time else None
        }


# ======================== 测试代码 ========================
def test_axis_studio_receiver():
    """
    测试 Axis Studio BVH 接收
    
    使用方法：
    1. 启动 Axis Studio
    2. 设置 -> BVH数据广播 -> 启用 UDP 广播（端口 7012）
    3. 运行此脚本
    4. 在 Axis Studio 中进行校准和动作捕捉
    """
    print("=" * 60)
    print("Axis Studio BVH Receiver Test")
    print("=" * 60)
    print("Please ensure:")
    print("1. Axis Studio is running")
    print("2. BVH broadcast is enabled (Settings -> BVH Data Broadcast)")
    print("3. UDP port is set to 7012")
    print("=" * 60)
    
    connector = AxisStudioConnector()
    connector.configure(udp_port=7012)
    
    success, msg = connector.start_listening()
    if not success:
        print(f"Failed to start listening: {msg}")
        return
    
    print(f"\nListening... Press Ctrl+C to stop")
    
    try:
        while True:
            frame_data = connector.poll_and_update()
            
            if frame_data:
                joints = frame_data.get('joints', {})
                print(f"\r[{connector.current_fps:.1f} FPS] Received {len(joints)} joints", end='')
                
                # 显示 Hips 位置（示例）
                if 'Hips' in joints:
                    hips_pos = joints['Hips']['position']
                    print(f" | Hips: ({hips_pos[0]:.2f}, {hips_pos[1]:.2f}, {hips_pos[2]:.2f})", end='')
            
            time.sleep(0.001)
    
    except KeyboardInterrupt:
        print("\n\nStopping...")
        connector.stop_listening()
        print("Test completed")


if __name__ == '__main__':
    test_axis_studio_receiver()
