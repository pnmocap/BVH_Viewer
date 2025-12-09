"""
MocapAPI连接管理器
负责与PN-Link设备的通信和数据获取
"""
import threading
import time
from mocap_api import (
    MCPApplication, MCPSettings, MCPAvatar, MCPJoint,
    MCPBvhData, MCPBvhDisplacement, MCPBvhRotation,
    MCPEventType, MCPReplay, EMCPCommand, MCPError,
    MCPCommand, MCPSystem, MCPEventNotify,
    MCPCalibrateMotionProgress, MCPCalibrateMotionProgressStep  # 校准进度相关
)


class ConnectionState:
    """连接状态枚举"""
    DISCONNECTED = 0      # 未连接
    CONNECTING = 1        # 连接中
    CONNECTED = 2         # 已连接
    CAPTURING = 3         # 采集中
    CALIBRATING = 4       # 校准中
    ERROR = -1            # 错误状态


class CapturePhase:
    """
    采集阶段枚举 - 严格遵循SDK流程
    流程: 启动采集 -> 稳定化(20秒静止) -> 就绪(可校准) -> 已校准
    """
    IDLE = 0              # 未启动采集
    STABILIZING = 1       # 采集中，等待稳定化(用户需保持静止20秒)
    READY = 2             # 采集稳定，可以开始校准
    CALIBRATED = 3        # 已完成校准，正常工作中


class CalibrationState:
    """
    校准状态枚举 - 与SDK的MCPCalibrateMotionProgressStep对应
    校准姿势由SDK内置管理，应用程序只需监听进度
    """
    NONE = 0              # 未开始校准
    PREPARING = 1         # SDK准备中 (CalibrateMotionProgressStep_Prepare)
    COUNTDOWN = 2         # SDK倒计时中 (CalibrateMotionProgressStep_Countdown)
    IN_PROGRESS = 3       # SDK校准进行中 (CalibrateMotionProgressStep_Progress)
    COMPLETED = 4         # 校准完成
    FAILED = -1           # 校准失败


class MocapConnector:
    """MocapAPI连接管理器"""
    
    def __init__(self):
        self.app = None
        self.settings = None
        self.is_connected = False
        self.is_capturing = False
        self.current_command = -1
        self.latest_frame_data = None
        self._lock = threading.Lock()
        self.connection_state = ConnectionState.DISCONNECTED
        
        # 默认网络配置
        self.local_ip = '10.42.0.101'
        self.local_port = 8002
        self.device_ip = '10.42.0.202'
        self.device_port = 8080
        
        # 设备信息
        self.device_version = ""
        self.device_serial = ""
        
        # 帧率统计
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        
        # ======================== 采集阶段管理 ========================
        self.capture_phase = CapturePhase.IDLE
        self.stabilize_start_time = None  # 稳定化开始时间
        self.STABILIZE_DURATION = 20  # 稳定化所需秒数（用户需保持静止20秒）
        self.stabilize_remaining = 0  # 稳定化剩余时间
        # ======================== 采集阶段结束 ========================
        
        # ======================== 校准状态管理 ========================
        self.calibration_state = CalibrationState.NONE
        self.calibration_countdown = 0  # SDK返回的倒计时秒数
        self.calibration_progress = 0   # SDK返回的校准进度 0-100
        self.calibration_pose_name = ""  # SDK返回的当前校准姿势名称
        self.calibration_supported_poses = []  # SDK支持的校准姿势列表
        self._calibration_command_sent = False  # 校准命令是否已发送
        self._calibration_start_time = None  # 校准命令发送时间
        self.CALIBRATION_TIMEOUT = 60  # 校准超时时间(秒)
        # ======================== 校准状态结束 ========================
    
    def configure(self, local_ip: str, local_port: int, device_ip: str, device_port: int):
        """配置网络参数"""
        self.local_ip = local_ip
        self.local_port = local_port
        self.device_ip = device_ip
        self.device_port = device_port
    
    def connect(self) -> tuple:
        """
        建立与设备的连接
        返回: (success: bool, message: str)
        """
        try:
            self.connection_state = ConnectionState.CONNECTING
            
            self.app = MCPApplication()
            self.settings = MCPSettings()
            
            # 配置BVH数据格式
            self.settings.set_bvh_data(MCPBvhData.Binary)
            self.settings.set_bvh_transformation(MCPBvhDisplacement.Enable)
            self.settings.set_bvh_rotation(MCPBvhRotation.YXZ)
            
            # 配置网络
            self.settings.SetSettingsUDPEx(self.local_ip, self.local_port)
            self.settings.SetSettingsUDPServer(self.device_ip, self.device_port)
            
            self.app.set_settings(self.settings)
            success, msg = self.app.open()
            
            if success:
                self.is_connected = True
                self.connection_state = ConnectionState.CONNECTED
                print(f"[MocapConnector] Connected to {self.device_ip}:{self.device_port}")
                return True, "Connected successfully"
            else:
                self.connection_state = ConnectionState.ERROR
                return False, f"Connection failed: {msg}"
                
        except Exception as e:
            self.connection_state = ConnectionState.ERROR
            return False, str(e)
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.is_capturing:
                self.stop_capture()
            if self.app:
                self.app.close()
            self.is_connected = False
            self.is_capturing = False
            self.connection_state = ConnectionState.DISCONNECTED
            print("[MocapConnector] Disconnected")
        except Exception as e:
            print(f"[MocapConnector] Disconnect error: {e}")
    
    def start_capture(self) -> bool:
        """开始采集"""
        if not self.is_connected:
            print("[MocapConnector] Not connected, cannot start capture")
            return False
        # 参考官方: 如果有命令正在执行，不能发送新命令
        if self.current_command != -1:
            print(f"[MocapConnector] Another command ({self.current_command}) is pending")
            return False
        try:
            self.app.queue_command(EMCPCommand.CommandStartCapture)
            self.current_command = EMCPCommand.CommandStartCapture
            print(f"[MocapConnector] Start capture command sent (current_command={self.current_command})")
            return True
        except Exception as e:
            print(f"[MocapConnector] Start capture error: {e}")
            return False
    
    def stop_capture(self) -> bool:
        """停止采集"""
        if not self.is_connected:
            return False
        try:
            self.app.queue_command(EMCPCommand.CommandStopCapture)
            self.current_command = EMCPCommand.CommandStopCapture
            print("[MocapConnector] Stop capture command sent")
            return True
        except Exception as e:
            print(f"[MocapConnector] Stop capture error: {e}")
            return False
    
    def start_calibration(self) -> bool:
        """
        开始校准 - 仅在采集稳定后才能调用
        校准姿势由SDK内置管理，应用程序只需发送命令并监听进度
        参考 mocap_main_base.py 的 check_current_command 和 running_command 逻辑
        """
        print(f"[DEBUG] start_calibration called - is_capturing={self.is_capturing}, capture_phase={self.capture_phase}, current_command={self.current_command}, _calibration_command_sent={self._calibration_command_sent}")
        
        # 校验采集阶段
        if not self.is_capturing:
            print("[Calibration] Not capturing, cannot calibrate")
            return False
        
        if self.capture_phase != CapturePhase.READY:
            print(f"[Calibration] Capture not ready (phase={self.capture_phase}), please wait for stabilization")
            return False
        
        # 关键检查：参考官方 check_current_command - 如果有命令正在执行，不能发送新命令
        if self.current_command != -1:
            print(f"[Calibration] Another command ({self.current_command}) is still pending, cannot send calibration")
            return False
        
        # 防止重复发送校准命令
        if self._calibration_command_sent:
            print("[Calibration] Calibration already in progress")
            return False
        
        try:
            print("[DEBUG] Sending CommandCalibrateMotion...")
            self.app.queue_command(EMCPCommand.CommandCalibrateMotion)
            self.current_command = EMCPCommand.CommandCalibrateMotion
            self.connection_state = ConnectionState.CALIBRATING
            self._calibration_command_sent = True
            self._calibration_start_time = time.time()  # 记录校准开始时间
            self.calibration_state = CalibrationState.PREPARING
            self.calibration_progress = 0
            print(f"[Calibration] Command sent successfully - current_command={self.current_command}")
            print(f"[Calibration] Waiting for SDK response (timeout={self.CALIBRATION_TIMEOUT}s)...")
            return True
        except Exception as e:
            self.calibration_state = CalibrationState.FAILED
            self._calibration_command_sent = False
            self._calibration_start_time = None
            print(f"[Calibration] Error sending command: {e}")
            import traceback
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            return False
    
    def _handle_calibration_progress(self, command_respond):
        """
        处理校准进度事件 (MCPReplay_Running)
        校准姿势由SDK管理（V-Pose, B-Pose, P-Pose, T-Pose, A-Pose, F-Pose等）
        参考 SDK 文档的 handleRunning 实现
        """
        try:
            print(f"[DEBUG] _handle_calibration_progress called")
            
            # 获取校准进度句柄
            calibrate_progress_handle = MCPCommand().get_progress(command_respond._commandHandle)
            print(f"[DEBUG] Got progress handle: {calibrate_progress_handle}")
            
            progress = MCPCalibrateMotionProgress(calibrate_progress_handle)
            
            # 获取支持的校准姿势列表 (由SDK内置管理)
            pose_count = progress.get_count_of_support_poses()
            print(f"[DEBUG] Support pose count: {pose_count}")
            
            self.calibration_supported_poses = []
            for i in range(pose_count):
                pose_name = progress.get_name_of_support_poses(i)
                self.calibration_supported_poses.append(pose_name)
            print(f"[DEBUG] Supported poses: {self.calibration_supported_poses}")
            
            # 获取当前校准步骤和姿势名称 (由SDK控制)
            current_step, pose_name = progress.get_step_current_pose()
            self.calibration_pose_name = pose_name if pose_name else ""
            print(f"[DEBUG] Current step: {current_step}, pose: {self.calibration_pose_name}")
            
            # 检查步骤类型并更新状态
            if current_step == MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Prepare:
                # 准备阶段
                self.calibration_state = CalibrationState.PREPARING
                self.calibration_countdown = 0
                self.calibration_progress = 0
                print(f"[Calibration] Preparing ({self.calibration_pose_name})...")
                
            elif current_step == MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Countdown:
                # 倒计时阶段
                countdown, _ = progress.get_countdown_current_pose()
                self.calibration_state = CalibrationState.COUNTDOWN
                self.calibration_countdown = countdown
                self.calibration_progress = 0
                print(f"[Calibration] Countdown ({self.calibration_pose_name}): {countdown}s")
                
            elif current_step == MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Progress:
                # 校准进行中
                progress_val, _ = progress.get_progress_current_pose()
                self.calibration_state = CalibrationState.IN_PROGRESS
                self.calibration_progress = progress_val
                print(f"[Calibration] Progress ({self.calibration_pose_name}): {progress_val}%")
            else:
                print(f"[Calibration] Unknown step value: {current_step}")
                # 尝试获取所有可能的信息
                print(f"[DEBUG] Step constants: Prepare={MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Prepare}, "
                      f"Countdown={MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Countdown}, "
                      f"Progress={MCPCalibrateMotionProgressStep.CalibrateMotionProgressStep_Progress}")
                
        except Exception as e:
            import traceback
            print(f"[Calibration] Handle progress error: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
    
    def get_phase_message(self) -> str:
        """获取当前采集阶段提示信息 - 用于UI显示"""
        if self.capture_phase == CapturePhase.IDLE:
            return ""
        elif self.capture_phase == CapturePhase.STABILIZING:
            return f"🛡️ 采集稳定化中 - 请保持静止 ({int(self.stabilize_remaining)}秒)"
        elif self.capture_phase == CapturePhase.READY:
            return "✅ 采集稳定 - 请点击 [Calibrate] 开始校准"
        elif self.capture_phase == CapturePhase.CALIBRATED:
            return "✅ 校准完成 - 可以开始录制"
        return ""
    
    def get_calibration_message(self) -> str:
        """获取校准提示信息 - 用于UI显示"""
        pose_display = self.calibration_pose_name if self.calibration_pose_name else "校准姿势"
        
        if self.calibration_state == CalibrationState.NONE:
            return ""
        elif self.calibration_state == CalibrationState.PREPARING:
            return f"🚶 请保持 {pose_display} 姿势 - 准备中..."
        elif self.calibration_state == CalibrationState.COUNTDOWN:
            return f"⏱️ 请保持 {pose_display} 姿势 - {int(self.calibration_countdown)} 秒后开始"
        elif self.calibration_state == CalibrationState.IN_PROGRESS:
            return f"⏳ 校准中 ({pose_display})... {self.calibration_progress}%"
        elif self.calibration_state == CalibrationState.COMPLETED:
            return "✅ 校准完成 - 可以开始录制"
        elif self.calibration_state == CalibrationState.FAILED:
            return "❌ 校准失败 - 请重试"
        return ""
    
    def can_start_calibration(self) -> bool:
        """检查是否可以开始校准 - 仅在采集稳定后才能校准"""
        return (self.is_capturing and 
                self.capture_phase == CapturePhase.READY and
                not self._calibration_command_sent and
                self.calibration_state in [CalibrationState.NONE, 
                                           CalibrationState.COMPLETED,
                                           CalibrationState.FAILED])
    
    def poll_and_update(self) -> dict:
        """
        轮询事件并更新数据
        返回最新的帧数据，格式为:
        {
            'joints': {
                'Hips': {'position': (x,y,z), 'rotation': (w,x,y,z)},
                'RightUpLeg': {...},
                ...
            },
            'timestamp': float
        }
        """
        if not self.is_connected or not self.app:
            return None
        
        frame_data = None
        
        try:
            events = self.app.poll_next_event()
            
            # 调试: 显示非 AvatarUpdated 事件 (仅在校准命令发送后)
            if events and len(events) > 0 and self._calibration_command_sent:
                for evt in events:
                    evt_type_val = evt.event_type
                    if evt_type_val != MCPEventType.AvatarUpdated:  # 只显示非Avatar事件
                        evt_name = "Unknown"
                        if evt_type_val == MCPEventType.CommandReply:
                            evt_name = "CommandReply"
                        elif evt_type_val == MCPEventType.Notify:
                            evt_name = "Notify"
                        elif evt_type_val == MCPEventType.Error:
                            evt_name = "Error"
                        elif evt_type_val == MCPEventType.RigidBodyUpdated:
                            evt_name = "RigidBodyUpdated"
                        print(f"[DEBUG-EVENTS] Event type: {evt_type_val} ({evt_name})")
            
            for evt in events:
                if evt.event_type == MCPEventType.AvatarUpdated:
                    # 参考官方 mocap_main_base.py 第132-135行:
                    # 只有当没有命令执行中，且不在校准过程中时，才处理Avatar数据
                    # if self.current_command != EMCPCommand.CommandCalibrateMotion and self.current_command == -1:
                    
                    # 重要：收到 AvatarUpdated 意味着采集已开始
                    # 如果 current_command 还是 StartCapture，说明 SDK 没发 Result 事件，我们手动重置
                    if self.current_command == EMCPCommand.CommandStartCapture:
                        print("[DEBUG] AvatarUpdated received while StartCapture pending - resetting current_command")
                        self.current_command = -1
                    
                    # 处理Avatar数据更新 - 首次收到时标记采集开始
                    if not self.is_capturing:
                        # 只有当 current_command == -1（无待处理命令）时才设置 is_capturing
                        # 这与官方 capture_key 的逻辑一致
                        if self.current_command == -1:
                            self.is_capturing = True
                            self.connection_state = ConnectionState.CAPTURING
                            # 开始采集稳定化阶段
                            self.capture_phase = CapturePhase.STABILIZING
                            self.stabilize_start_time = time.time()
                            self.stabilize_remaining = self.STABILIZE_DURATION
                            print(f"[MocapConnector] Capturing started - Please stay still for {self.STABILIZE_DURATION} seconds")
                    
                    # 更新稳定化计时 - 只有不在校准中时才更新
                    if self.capture_phase == CapturePhase.STABILIZING and self.current_command != EMCPCommand.CommandCalibrateMotion:
                        elapsed = time.time() - self.stabilize_start_time
                        self.stabilize_remaining = max(0, self.STABILIZE_DURATION - elapsed)
                        
                        if elapsed >= self.STABILIZE_DURATION:
                            # 稳定化完成，可以开始校准
                            self.capture_phase = CapturePhase.READY
                            print("[MocapConnector] Capture stabilized - Ready for calibration")
                    
                    # 校准期间仍然解析数据（用于显示），但不更新 capture 状态
                    frame_data = self._parse_avatar(evt.event_data.avatar_handle)
                    frame_data['timestamp'] = evt.timestamp
                    
                    # 更新帧率统计
                    self._update_fps()
                    
                elif evt.event_type == MCPEventType.Notify:
                    # 处理通知事件
                    self._handle_notify(evt.event_data.notifyData)
                    
                elif evt.event_type == MCPEventType.CommandReply:
                    # 处理命令响应
                    respond = evt.event_data.commandRespond
                    print(f"[DEBUG] CommandReply received: replay_type={respond._replay}, current_command={self.current_command}")
                    
                    if respond._replay == MCPReplay.MCPReplay_Response:
                        print("[DEBUG] MCPReplay_Response - Command acknowledged")
                    elif respond._replay == MCPReplay.MCPReplay_Running:
                        # 校准进度更新
                        print(f"[DEBUG] MCPReplay_Running - Processing calibration progress...")
                        if self.current_command == EMCPCommand.CommandCalibrateMotion:
                            self._handle_calibration_progress(respond)
                        else:
                            print(f"[DEBUG] Ignored Running event - command mismatch")
                    elif respond._replay == MCPReplay.MCPReplay_Result:
                        self._handle_command_result(respond)
                    
                elif evt.event_type == MCPEventType.Error:
                    print(f"[MocapConnector] Error event: {evt.event_data.error}")
            
            if frame_data:
                with self._lock:
                    self.latest_frame_data = frame_data
            
            # ======================== 校准超时检测 ========================
            if self._calibration_command_sent and self._calibration_start_time:
                elapsed = time.time() - self._calibration_start_time
                if elapsed >= self.CALIBRATION_TIMEOUT:
                    print(f"[Calibration] TIMEOUT after {self.CALIBRATION_TIMEOUT}s - No response from SDK")
                    print("[Calibration] Possible causes: device not ready, firmware incompatible, or network issue")
                    self._reset_calibration_state()
            # ======================== 超时检测结束 ========================
            
        except Exception as e:
            print(f"[MocapConnector] Poll error: {e}")
        
        return frame_data
    
    def _parse_avatar(self, avatar_handle) -> dict:
        """解析Avatar数据为字典格式"""
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
            print(f"[MocapConnector] Parse avatar error: {e}")
        
        return {'joints': joints_data}
    
    def _handle_notify(self, notify_data):
        """处理通知事件"""
        try:
            if notify_data._notify == MCPEventNotify.Notify_SystemUpdated:
                system = MCPSystem(notify_data._notifyHandle)
                self.device_version = system.get_master_version()
                self.device_serial = system.get_master_serial_number()
                print(f"[MocapConnector] Device: Version={self.device_version}, Serial={self.device_serial}")
        except Exception as e:
            print(f"[MocapConnector] Handle notify error: {e}")
    
    def _handle_command_result(self, command_respond):
        """处理命令结果 - 参考官方 handleResult"""
        try:
            command = MCPCommand()
            handle = command_respond._commandHandle
            ret_code = command.get_result_code(handle)
            
            print(f"[DEBUG] _handle_command_result: ret_code={ret_code}, current_command={self.current_command}")
            
            if ret_code != 0:
                ret_msg = command.get_result_message(handle)
                print(f"[MocapConnector] Command failed: {ret_msg}")
                if self.current_command == EMCPCommand.CommandCalibrateMotion:
                    self.calibration_state = CalibrationState.FAILED
                    self._calibration_command_sent = False
                    self._calibration_start_time = None
                    self.connection_state = ConnectionState.CAPTURING
                    print("[Calibration] FAILED - resetting state")
            else:
                # 命令成功完成
                if self.current_command == EMCPCommand.CommandStopCapture:
                    self.is_capturing = False
                    self.connection_state = ConnectionState.CONNECTED
                    print("[MocapConnector] StopCapture completed")
                elif self.current_command == EMCPCommand.CommandStartCapture:
                    # StartCapture命令成功 - 参考官方，此时可以开始接收Avatar数据
                    print("[MocapConnector] StartCapture completed - ready to receive avatar data")
                elif self.current_command == EMCPCommand.CommandCalibrateMotion:
                    # 校准完成 - 进入已校准阶段
                    self.connection_state = ConnectionState.CAPTURING
                    self.calibration_state = CalibrationState.COMPLETED
                    self.calibration_progress = 100
                    self.capture_phase = CapturePhase.CALIBRATED
                    self._calibration_command_sent = False
                    self._calibration_start_time = None
                    print("[Calibration] COMPLETED successfully! Ready for recording.")
                print(f"[MocapConnector] Command completed: {self.current_command}")
            
            # 关键：销毁命令句柄并重置 current_command（参考官方）
            command.destroy_command(handle)
            prev_command = self.current_command
            self.current_command = -1
            print(f"[DEBUG] Command {prev_command} finished, current_command reset to -1")
            
        except Exception as e:
            import traceback
            print(f"[MocapConnector] Handle command result error: {e}")
            print(f"[DEBUG] Traceback: {traceback.format_exc()}")
            # 出错时也要重置 current_command
            self.current_command = -1
    
    def _update_fps(self):
        """更新帧率统计"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time
        
        if elapsed >= 1.0:
            self.current_fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def _reset_calibration_state(self):
        """重置校准状态 - 用于超时或失败时恢复"""
        self.calibration_state = CalibrationState.FAILED
        self._calibration_command_sent = False
        self._calibration_start_time = None
        self.calibration_progress = 0
        self.connection_state = ConnectionState.CAPTURING
        self.current_command = -1
        # 保持在 READY 阶段，允许用户重试
        if self.capture_phase != CapturePhase.CALIBRATED:
            self.capture_phase = CapturePhase.READY
        print("[Calibration] State reset - you can try again")
    
    def get_latest_frame(self) -> dict:
        """获取最新的帧数据（线程安全）"""
        with self._lock:
            return self.latest_frame_data
    
    def get_connection_status_text(self) -> str:
        """获取连接状态文本"""
        if self.connection_state == ConnectionState.DISCONNECTED:
            return "Disconnected"
        elif self.connection_state == ConnectionState.CONNECTING:
            return "Connecting..."
        elif self.connection_state == ConnectionState.CONNECTED:
            return "Connected"
        elif self.connection_state == ConnectionState.CALIBRATING:
            return "Calibrating..."
        elif self.connection_state == ConnectionState.ERROR:
            return "Error"
        elif self.connection_state == ConnectionState.CAPTURING:
            # 显示采集阶段详情
            phase_text = {
                CapturePhase.IDLE: "Idle",
                CapturePhase.STABILIZING: f"Stabilizing ({int(self.stabilize_remaining)}s)",
                CapturePhase.READY: "Ready for Calibration",
                CapturePhase.CALIBRATED: f"Calibrated ({self.current_fps:.1f} FPS)"
            }.get(self.capture_phase, "Capturing")
            return phase_text
        return "Unknown"
    
    def is_ready_for_capture(self) -> bool:
        """检查是否准备好开始采集"""
        return self.is_connected and not self.is_capturing
    
    def is_ready_for_record(self) -> bool:
        """检查是否准备好开始录制 - 仅在校准完成后才能录制"""
        return (self.is_capturing and 
                self.capture_phase == CapturePhase.CALIBRATED and
                self.calibration_state == CalibrationState.COMPLETED)
    
    def get_overall_status_message(self) -> str:
        """
        获取综合状态消息 - 用于UI主显示
        根据当前阶段返回适当的提示
        """
        # 优先级: 校准中 > 采集阶段 > 空
        if self.calibration_state not in [CalibrationState.NONE, CalibrationState.COMPLETED]:
            return self.get_calibration_message()
        return self.get_phase_message()
