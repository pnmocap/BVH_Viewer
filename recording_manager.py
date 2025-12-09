"""
录制管理器
负责数据录制、回放和BVH导出
"""
import time
import math
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FrameData:
    """单帧数据结构"""
    frame_index: int
    timestamp: float
    joints: Dict[str, Dict] = field(default_factory=dict)  # {name: {position, rotation}}


class RecordingManager:
    """录制管理器 - 负责数据录制、回放和BVH导出"""
    
    # BVH骨骼层级定义（简化版，支持主要关节）
    # 关节顺序与通道对应
    JOINT_ORDER = [
        'Hips',  # 根关节，6通道: Xpos, Ypos, Zpos, Zrot, Xrot, Yrot
        'RightUpLeg', 'RightLeg', 'RightFoot',
        'LeftUpLeg', 'LeftLeg', 'LeftFoot',
        'Spine', 'Spine1', 'Spine2',
        'Neck', 'Head',
        'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
        'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand'
    ]
    
    # 完整关节顺序（包含手指）
    FULL_JOINT_ORDER = [
        'Hips',
        'RightUpLeg', 'RightLeg', 'RightFoot',
        'LeftUpLeg', 'LeftLeg', 'LeftFoot',
        'Spine', 'Spine1', 'Spine2',
        'Neck', 'Neck1', 'Head',
        'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
        'RightHandThumb1', 'RightHandThumb2', 'RightHandThumb3',
        'RightInHandIndex', 'RightHandIndex1', 'RightHandIndex2', 'RightHandIndex3',
        'RightInHandMiddle', 'RightHandMiddle1', 'RightHandMiddle2', 'RightHandMiddle3',
        'RightInHandRing', 'RightHandRing1', 'RightHandRing2', 'RightHandRing3',
        'RightInHandPinky', 'RightHandPinky1', 'RightHandPinky2', 'RightHandPinky3',
        'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand',
        'LeftHandThumb1', 'LeftHandThumb2', 'LeftHandThumb3',
        'LeftInHandIndex', 'LeftHandIndex1', 'LeftHandIndex2', 'LeftHandIndex3',
        'LeftInHandMiddle', 'LeftHandMiddle1', 'LeftHandMiddle2', 'LeftHandMiddle3',
        'LeftInHandRing', 'LeftHandRing1', 'LeftHandRing2', 'LeftHandRing3',
        'LeftInHandPinky', 'LeftHandPinky1', 'LeftHandPinky2', 'LeftHandPinky3',
    ]
    
    # 父子关系定义
    JOINT_HIERARCHY = {
        'Hips': None,
        'RightUpLeg': 'Hips', 'RightLeg': 'RightUpLeg', 'RightFoot': 'RightLeg',
        'LeftUpLeg': 'Hips', 'LeftLeg': 'LeftUpLeg', 'LeftFoot': 'LeftLeg',
        'Spine': 'Hips', 'Spine1': 'Spine', 'Spine2': 'Spine1',
        'Neck': 'Spine2', 'Neck1': 'Neck', 'Head': 'Neck1',
        'RightShoulder': 'Spine2', 'RightArm': 'RightShoulder', 
        'RightForeArm': 'RightArm', 'RightHand': 'RightForeArm',
        'LeftShoulder': 'Spine2', 'LeftArm': 'LeftShoulder',
        'LeftForeArm': 'LeftArm', 'LeftHand': 'LeftForeArm',
    }
    
    # 默认偏移量（单位：cm）
    DEFAULT_OFFSETS = {
        'Hips': (0.0, 0.0, 0.0),
        'RightUpLeg': (-8.5, 0.0, 0.0), 'RightLeg': (0.0, -40.0, 0.0), 'RightFoot': (0.0, -40.0, 0.0),
        'LeftUpLeg': (8.5, 0.0, 0.0), 'LeftLeg': (0.0, -40.0, 0.0), 'LeftFoot': (0.0, -40.0, 0.0),
        'Spine': (0.0, 10.0, 0.0), 'Spine1': (0.0, 10.0, 0.0), 'Spine2': (0.0, 10.0, 0.0),
        'Neck': (0.0, 10.0, 0.0), 'Neck1': (0.0, 5.0, 0.0), 'Head': (0.0, 8.0, 0.0),
        'RightShoulder': (-5.0, 8.0, 0.0), 'RightArm': (-12.0, 0.0, 0.0),
        'RightForeArm': (-25.0, 0.0, 0.0), 'RightHand': (-25.0, 0.0, 0.0),
        'LeftShoulder': (5.0, 8.0, 0.0), 'LeftArm': (12.0, 0.0, 0.0),
        'LeftForeArm': (25.0, 0.0, 0.0), 'LeftHand': (25.0, 0.0, 0.0),
    }
    
    # 末端位点偏移
    END_SITES = {
        'RightFoot': (0.0, -7.85, 14.28),
        'LeftFoot': (0.0, -7.85, 14.28),
        'Head': (0.0, 16.45, 0.0),
        'RightHand': (-8.0, 0.0, 0.0),
        'LeftHand': (8.0, 0.0, 0.0),
    }
    
    def __init__(self):
        self.recorded_frames: List[FrameData] = []
        self.is_recording = False
        self.record_start_time = 0.0
        self.frame_time = 1.0 / 60.0  # 默认60fps
        self._frame_counter = 0
        self.target_fps = 60.0
    
    def start_recording(self, fps: float = 60.0):
        """开始录制"""
        self.recorded_frames.clear()
        self.is_recording = True
        self.record_start_time = time.time()
        self.target_fps = fps
        self.frame_time = 1.0 / fps
        self._frame_counter = 0
        print(f"[RecordingManager] Recording started at {fps} FPS")
    
    def stop_recording(self) -> int:
        """停止录制，返回总帧数"""
        self.is_recording = False
        total_frames = len(self.recorded_frames)
        duration = total_frames * self.frame_time
        print(f"[RecordingManager] Recording stopped. Total: {total_frames} frames, Duration: {duration:.2f}s")
        return total_frames
    
    def record_frame(self, joints_data: Dict):
        """记录一帧数据"""
        if not self.is_recording:
            return
        
        # 深拷贝关节数据
        joints_copy = {}
        for name, data in joints_data.items():
            joints_copy[name] = {
                'position': data.get('position', (0.0, 0.0, 0.0)),
                'rotation': data.get('rotation', (1.0, 0.0, 0.0, 0.0))
            }
        
        frame = FrameData(
            frame_index=self._frame_counter,
            timestamp=time.time() - self.record_start_time,
            joints=joints_copy
        )
        self.recorded_frames.append(frame)
        self._frame_counter += 1
    
    def get_frame_count(self) -> int:
        """获取已录制帧数"""
        return len(self.recorded_frames)
    
    def get_recorded_frame(self, index: int) -> Optional[FrameData]:
        """获取指定帧"""
        if 0 <= index < len(self.recorded_frames):
            return self.recorded_frames[index]
        return None
    
    def get_recording_duration(self) -> float:
        """获取录制时长（秒）"""
        return len(self.recorded_frames) * self.frame_time
    
    @staticmethod
    def quaternion_to_euler_zxy(w: float, x: float, y: float, z: float) -> tuple:
        """
        四元数转欧拉角 (ZXY顺序，BVH标准)
        返回: (z_rot, x_rot, y_rot) 单位：角度
        """
        # 计算欧拉角
        # ZXY顺序的转换
        
        # 计算矩阵元素
        m00 = 1 - 2*y*y - 2*z*z
        m01 = 2*x*y - 2*z*w
        m02 = 2*x*z + 2*y*w
        m10 = 2*x*y + 2*z*w
        m11 = 1 - 2*x*x - 2*z*z
        m12 = 2*y*z - 2*x*w
        m20 = 2*x*z - 2*y*w
        m21 = 2*y*z + 2*x*w
        m22 = 1 - 2*x*x - 2*y*y
        
        # ZXY顺序提取欧拉角
        if abs(m21) < 0.99999:
            x_rot = math.asin(-m21)
            z_rot = math.atan2(m01, m11)
            y_rot = math.atan2(m20, m22)
        else:
            # 万向锁情况
            x_rot = math.copysign(math.pi / 2, -m21)
            z_rot = math.atan2(-m10, m00)
            y_rot = 0
        
        # 转换为角度
        return (
            math.degrees(z_rot),
            math.degrees(x_rot),
            math.degrees(y_rot)
        )
    
    def _generate_hierarchy(self, joints_to_export: List[str]) -> str:
        """生成BVH HIERARCHY部分"""
        lines = ['HIERARCHY']
        
        def write_joint(joint_name: str, indent: int, is_root: bool = False):
            """递归写入关节"""
            prefix = '    ' * indent
            offset = self.DEFAULT_OFFSETS.get(joint_name, (0.0, 0.0, 0.0))
            
            if is_root:
                lines.append(f'{prefix}ROOT {joint_name}')
            else:
                lines.append(f'{prefix}JOINT {joint_name}')
            
            lines.append(f'{prefix}{{')
            lines.append(f'{prefix}    OFFSET {offset[0]:.2f} {offset[1]:.2f} {offset[2]:.2f}')
            
            if is_root:
                lines.append(f'{prefix}    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation')
            else:
                lines.append(f'{prefix}    CHANNELS 3 Zrotation Xrotation Yrotation')
            
            # 获取子关节
            children = [j for j in joints_to_export if self.JOINT_HIERARCHY.get(j) == joint_name]
            
            for child in children:
                write_joint(child, indent + 1)
            
            # 如果没有子关节，添加End Site
            if not children and joint_name in self.END_SITES:
                end_offset = self.END_SITES[joint_name]
                lines.append(f'{prefix}    End Site')
                lines.append(f'{prefix}    {{')
                lines.append(f'{prefix}        OFFSET {end_offset[0]:.2f} {end_offset[1]:.2f} {end_offset[2]:.2f}')
                lines.append(f'{prefix}    }}')
            
            lines.append(f'{prefix}}}')
        
        # 从根关节开始
        write_joint('Hips', 0, is_root=True)
        
        return '\n'.join(lines)
    
    def _generate_frame_line(self, frame: FrameData, joints_to_export: List[str]) -> str:
        """生成单帧的BVH数据行"""
        values = []
        
        for joint_name in joints_to_export:
            joint_data = frame.joints.get(joint_name, {})
            pos = joint_data.get('position', (0.0, 0.0, 0.0))
            rot = joint_data.get('rotation', (1.0, 0.0, 0.0, 0.0))
            
            # 四元数转欧拉角 (w, x, y, z) -> (z_rot, x_rot, y_rot)
            euler = self.quaternion_to_euler_zxy(rot[0], rot[1], rot[2], rot[3])
            
            if joint_name == 'Hips':
                # 根节点有位置通道
                values.extend([pos[0], pos[1], pos[2]])
            
            # 旋转通道 (ZXY顺序)
            values.extend([euler[0], euler[1], euler[2]])
        
        return ' '.join(f'{v:.6f}' for v in values)
    
    def export_to_bvh(self, file_path: str, include_fingers: bool = False) -> bool:
        """
        导出为BVH文件
        
        参数:
            file_path: 输出文件路径
            include_fingers: 是否包含手指关节
        
        返回:
            bool: 是否成功
        """
        if not self.recorded_frames:
            print("[RecordingManager] No frames to export")
            return False
        
        # 确定要导出的关节
        joints_to_export = self.FULL_JOINT_ORDER if include_fingers else self.JOINT_ORDER
        
        # 过滤掉录制数据中不存在的关节
        if self.recorded_frames:
            available_joints = set(self.recorded_frames[0].joints.keys())
            joints_to_export = [j for j in joints_to_export if j in available_joints or j == 'Hips']
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 写入层级结构
                hierarchy = self._generate_hierarchy(joints_to_export)
                f.write(hierarchy)
                f.write('\n')
                
                # 写入运动数据头
                f.write('MOTION\n')
                f.write(f'Frames: {len(self.recorded_frames)}\n')
                f.write(f'Frame Time: {self.frame_time:.6f}\n')
                
                # 写入每帧数据
                for frame in self.recorded_frames:
                    frame_line = self._generate_frame_line(frame, joints_to_export)
                    f.write(frame_line + '\n')
            
            print(f"[RecordingManager] BVH exported to: {file_path}")
            print(f"[RecordingManager] Joints: {len(joints_to_export)}, Frames: {len(self.recorded_frames)}")
            return True
            
        except Exception as e:
            print(f"[RecordingManager] Export failed: {e}")
            return False
    
    def clear(self):
        """清空录制数据"""
        self.recorded_frames.clear()
        self._frame_counter = 0
        self.is_recording = False
        print("[RecordingManager] Recording data cleared")
    
    def get_playback_frame(self, frame_index: int) -> Optional[Dict]:
        """
        获取用于回放的帧数据
        返回格式与录制时相同的joints字典
        """
        frame = self.get_recorded_frame(frame_index)
        if frame:
            return frame.joints
        return None
    
    def get_status_text(self) -> str:
        """获取录制状态文本"""
        if self.is_recording:
            duration = time.time() - self.record_start_time
            return f"Recording: {self._frame_counter} frames ({duration:.1f}s)"
        elif self.recorded_frames:
            return f"Recorded: {len(self.recorded_frames)} frames ({self.get_recording_duration():.1f}s)"
        else:
            return "No recording"
