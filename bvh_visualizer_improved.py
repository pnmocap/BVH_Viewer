import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import os
import sys
import tkinter as tk
from tkinter import filedialog, Listbox, Checkbutton, IntVar, messagebox
import math
import csv
import colorsys
try:
    from OpenGL.GLUT import *
except ImportError:
    print("Warning: PyOpenGL-accelerate is not installed. GLUT may not be available.")
    print("Please install PyOpenGL-accelerate: pip install PyOpenGL_accelerate")
    from OpenGL.GLUT import *

# BVH Joint Class
class Joint:
    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        self.parent = parent
        self.offset = np.zeros(3)
        self.channels = []
        self.channel_indices = {}
        self.matrix = np.identity(4)
        self.end_site = None
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        self.acceleration = np.zeros(3)
        self.rom = {'Xrotation': [float('inf'), float('-inf')],
                    'Yrotation': [float('inf'), float('-inf')],
                    'Zrotation': [float('inf'), float('-inf')]}
        self.anatomical_angles = {} 
        self.channel_start_index = 0  # 保存通道起始索引
    
    def add_child(self, child):
        self.children.append(child)
    
    def set_offset(self, offset):
        self.offset = np.array(offset)
    
    def set_channels(self, channels, channel_start_index):
        self.channels = channels
        self.channel_start_index = channel_start_index
        for i, channel in enumerate(channels):
            self.channel_indices[channel] = channel_start_index + i
    
    def set_end_site(self, end_site):
        self.end_site = np.array(end_site)

# BVH File Parser
def parse_bvh(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None, {}, [], 0, 0
    lines = [line.strip() for line in lines]
    root_joint = None
    joints = {}
    stack = []
    line_index = 0
    channel_count = 0
    while line_index < len(lines) and lines[line_index] != 'MOTION':
        line = lines[line_index]
        parts = line.split()
        if not parts:
            line_index += 1
            continue
        if parts[0] == 'HIERARCHY':
            line_index += 1
            continue
        elif parts[0] == 'ROOT' or parts[0] == 'JOINT':
            joint_name = parts[1]
            new_joint = Joint(joint_name, parent=stack[-1] if stack else None)
            if not root_joint:
                root_joint = new_joint
            joints[joint_name] = new_joint
            if stack:
                stack[-1].add_child(new_joint)
            stack.append(new_joint)
            line_index += 1
        elif parts[0] == '{':
            line_index += 1
        elif parts[0] == 'OFFSET':
            offset = [float(p) for p in parts[1:]]
            stack[-1].set_offset(offset)
            line_index += 1
        elif parts[0] == 'CHANNELS':
            num_channels = int(parts[1])
            channels = parts[2:]
            stack[-1].set_channels(channels, channel_count)
            channel_count += num_channels
            line_index += 1
        elif parts[0] == 'End' and parts[1] == 'Site':
            line_index += 2
            end_site = [float(p) for p in lines[line_index].split()[1:]]
            stack[-1].set_end_site(end_site)
            line_index += 2
        elif parts[0] == '}':
            if stack:
                stack.pop()
            line_index += 1
        else:
            line_index += 1
    
    motion_data = []
    frames = 0
    frame_time = 0.0
    while line_index < len(lines):
        line = lines[line_index]
        parts = line.split()
        if not parts:
            line_index += 1
            continue
        if parts[0] == 'MOTION':
            line_index += 1
        elif parts[0] == 'Frames:':
            frames = int(parts[1])
            line_index += 1
        elif parts[0] == 'Frame' and parts[1] == 'Time:':
            frame_time = float(parts[2])
            line_index += 1
        else:
            motion_data.append([float(p) for p in parts])
            line_index += 1
    return root_joint, joints, motion_data, frames, frame_time

# 获取关节世界坐标
def get_world_position(joint):
    return joint.matrix[:3, 3]

# 更新关节矩阵
def update_joint_matrices(joint, frame_data, all_joints):
    if joint.parent is None:
        pos_x = frame_data[joint.channel_indices.get('Xposition', -1)] if 'Xposition' in joint.channels else 0
        pos_y = frame_data[joint.channel_indices.get('Yposition', -1)] if 'Yposition' in joint.channels else 0
        pos_z = frame_data[joint.channel_indices.get('Zposition', -1)] if 'Zposition' in joint.channels else 0
        
        T = np.identity(4)
        T[0, 3] = pos_x
        T[1, 3] = pos_y
        T[2, 3] = pos_z
        joint.matrix = T
    else:
        joint.matrix = all_joints[joint.parent.name].matrix @ np.array([
            [1, 0, 0, joint.offset[0]],
            [0, 1, 0, joint.offset[1]],
            [0, 0, 1, joint.offset[2]],
            [0, 0, 0, 1]
        ])
    for channel in joint.channels:
        if 'rotation' in channel:
            axis = channel[0]
            angle = frame_data[joint.channel_indices[channel]]
            
            R = np.identity(4)
            angle_rad = np.radians(angle)
            c = np.cos(angle_rad)
            s = np.sin(angle_rad)
            
            if axis == 'X':
                R = np.array([
                    [1, 0, 0, 0],
                    [0, c, -s, 0],
                    [0, s, c, 0],
                    [0, 0, 0, 1]
                ])
            elif axis == 'Y':
                R = np.array([
                    [c, 0, s, 0],
                    [0, 1, 0, 0],
                    [-s, 0, c, 0],
                    [0, 0, 0, 1]
                ])
            elif axis == 'Z':
                R = np.array([
                    [c, -s, 0, 0],
                    [s, c, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ])
            
            joint.matrix = joint.matrix @ R
    for child in joint.children:
        update_joint_matrices(child, frame_data, all_joints)

# 计算解剖学角度
# 计算解剖学角度（仅保留向量夹角，新增弯腰/低头角度）
# 计算解剖学角度（确保包含大臂小臂角度计算）
# 计算解剖学角度（全关节相邻向量夹角：含全身+手指每节）
def calculate_anatomical_angles(joints):
    angles = {}
    # 通用向量夹角计算函数（核心：父关节→当前关节→子关节，构成向量夹角）
    def get_vector_angle(parent_joint_name, current_joint_name, child_joint_name):
        """
        parent_joint_name: 父关节（向量1起点）
        current_joint_name: 当前关节（夹角顶点，相邻关节对的子节点）
        child_joint_name: 子关节（向量2终点）
        返回：三个关节构成的向量夹角（度，保留2位小数）
        """
        # 检查三个关节是否都存在于BVH数据中
        if (parent_joint_name in joints and 
            current_joint_name in joints and 
            child_joint_name in joints):
            # 获取三个关节的世界坐标
            p_parent = get_world_position(joints[parent_joint_name])  # 父关节（向量1起点）
            p_current = get_world_position(joints[current_joint_name])# 当前关节（夹角顶点）
            p_child = get_world_position(joints[child_joint_name])    # 子关节（向量2终点）
            
            # 计算两个向量：顶点→父关节、顶点→子关节
            vec_parent = p_parent - p_current
            vec_child = p_child - p_current
            
            # 避免向量长度为0导致计算错误
            if np.linalg.norm(vec_parent) > 1e-6 and np.linalg.norm(vec_child) > 1e-6:
                cos_theta = np.dot(vec_parent, vec_child) / (np.linalg.norm(vec_parent) * np.linalg.norm(vec_child))
                cos_theta = np.clip(cos_theta, -1.0, 1.0)  # 限制cos值范围，避免计算误差
                angle = np.degrees(np.arccos(cos_theta))
                return round(angle, 2)  # 保留2位小数，数据更简洁
        # 关节不存在/向量无效时返回None（后续过滤）
        return None
    
    # -------------------------- 关键：遍历所有相邻关节对（含手指）--------------------------
    # 基于自定义关节顺序CUSTOM_JOINT_ORDER，确保遍历顺序与骨骼结构一致
    for joint_name in CUSTOM_JOINT_ORDER:
        # 跳过不存在的关节（避免KeyError）
        if joint_name not in joints:
            continue
        current_joint = joints[joint_name]
        
        # 1. 跳过无父关节的根关节（如Hips，无“相邻父关节”）
        if current_joint.parent is None:
            continue
        parent_joint_name = current_joint.parent.name  # 相邻父关节名
        
        # 2. 遍历当前关节的所有子关节（每个子关节对应一个“相邻子关节”）
        for child_joint in current_joint.children:
            child_joint_name = child_joint.name
            # 跳过子关节不存在的情况（理论上不会发生，保险处理）
            if child_joint_name not in joints:
                continue
            
            # 3. 生成角度名称：父关节名_当前关节名（与RightUpArm_RightForeArm风格一致）
            # 例：RightArm（父）→RightForeArm（当前）→RightHand（子）→角度名=RightArm_RightForeArm
            angle_name = f"{parent_joint_name}_{joint_name}"
            
            # 4. 计算该相邻关节对的向量夹角
            angle_value = get_vector_angle(
                parent_joint_name=parent_joint_name,
                current_joint_name=joint_name,
                child_joint_name=child_joint_name
            )
            
            # 5. 只保留有效角度（过滤None值）
            if angle_value is not None:
                angles[angle_name] = angle_value
    
    # -------------------------- 保留原有弯腰、低头角度（补充非相邻关键角度）--------------------------
    # 弯腰角度（Hips→Spine→Spine2）：非相邻但重要，单独计算
    angles['Hips_Spine'] = get_vector_angle(
        parent_joint_name='Hips',
        current_joint_name='Spine',
        child_joint_name='Spine2'
    )
    # 低头角度（Spine2→Neck→Head）：非相邻但重要，单独计算
    angles['Spine2_Neck'] = get_vector_angle(
        parent_joint_name='Spine2',
        current_joint_name='Neck',
        child_joint_name='Head'
    )
    
    # 过滤所有无效角度（删除值为None的条目）
    return {key: val for key, val in angles.items() if val is not None}

# 计算运动学数据
def calculate_kinematics(joints, all_frames_data, frame_time):
    num_frames = len(all_frames_data)
    
    positions_per_frame = []
    anatomical_angles_per_frame = []
    
    for frame_data in all_frames_data:
        temp_joints = {}
        for name, joint in joints.items():
            temp_joints[name] = Joint(joint.name, parent=joint.parent)
            temp_joints[name].set_offset(joint.offset)
            temp_joints[name].set_channels(joint.channels, joint.channel_start_index)
            if joint.end_site is not None:
                temp_joints[name].set_end_site(joint.end_site)
        for name, joint in joints.items():
            for child in joint.children:
                if child.name in temp_joints:
                    temp_joints[name].add_child(temp_joints[child.name])
        temp_root = temp_joints[list(joints.keys())[0]]
        
        update_joint_matrices(temp_root, frame_data, temp_joints)
        
        frame_positions = {name: get_world_position(joint) for name, joint in temp_joints.items()}
        positions_per_frame.append(frame_positions)
        
        frame_anatomical_angles = calculate_anatomical_angles(temp_joints)
        anatomical_angles_per_frame.append(frame_anatomical_angles)
    velocities_per_frame = []
    accelerations_per_frame = []
    
    for i in range(num_frames):
        current_velocities = {}
        current_accelerations = {}
        
        for name in joints:
            if i == 0 or i == 1:
                current_velocities[name] = np.zeros(3)
                current_accelerations[name] = np.zeros(3)
            else:
                pos_diff = positions_per_frame[i][name] - positions_per_frame[i-1][name]
                velocity = pos_diff / frame_time
                current_velocities[name] = velocity
                
                vel_diff = current_velocities[name] - velocities_per_frame[i-1][name]
                acceleration = vel_diff / frame_time
                current_accelerations[name] = acceleration
        velocities_per_frame.append(current_velocities)
        accelerations_per_frame.append(current_accelerations)
    return positions_per_frame, velocities_per_frame, accelerations_per_frame, anatomical_angles_per_frame

# 自定义骨骼渲染顺序
CUSTOM_JOINT_ORDER = [
    'Hips',
    'RightUpLeg', 'RightLeg', 'RightFoot',
    'LeftUpLeg', 'LeftLeg', 'LeftFoot',
    'Spine', 'Spine1', 'Spine2',
    'Neck', 'Neck1', 'Head',
    'RightShoulder', 'RightArm', 'RightForeArm', 'RightHand',
    'RightHandThumb1', 'RightHandThumb2', 'RightHandThumb3',
    'RightinHandindex', 'RightHandindex1', 'RightHandindex2', 'RightHandindex3',
    'RightlnHandMiddle', 'RightHandMiddle1', 'RightHandMiddle2', 'RightHandMiddle3',
    'RightinHandRing', 'RightHandRing1', 'RightHandRing2', 'RightHandRing3',
    'RightinHandPinky', 'RightHandPinky1', 'RightHandPinky2', 'RightHandPinky3',
    'LeftShoulder', 'LeftArm', 'LeftForeArm', 'LeftHand',
    'LeftHandThumb1', 'LeftHandThumb2', 'LeftHandThumb3',
    'LeftinHandindex', 'LeftHandindex1', 'LeftHandindex2', 'LeftHandindex3',
    'LeftinHandMiddle', 'LeftHandMiddle1', 'LeftHandMiddle2', 'LeftHandMiddle3',
    'LeftinHandRing', 'LeftHandRing1', 'LeftHandRing2', 'LeftHandRing3',
    'LeftinHandPinky', 'LeftHandPinky1', 'LeftHandPinky2', 'LeftHandPinky3',
    'Spine3'
]

# 重构骨骼渲染函数
def draw_skeleton_custom_order(joints):
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints:
            continue
        joint = joints[joint_name]
        
        # 渲染当前关节（球体）
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        joint_pos = joint.matrix[:3, 3]
        glTranslatef(joint_pos[0], joint_pos[1], joint_pos[2])
        quad = gluNewQuadric()
        gluSphere(quad, 2.5 * 0.4, 16, 16)
        gluDeleteQuadric(quad)
        glPopMatrix()
        
        # 绘制当前关节与父关节的连接线条
        if joint.parent is not None and joint.parent.name in joints:
            parent_joint = joints[joint.parent.name]
            parent_pos = parent_joint.matrix[:3, 3]
            
            glLineWidth(2.0)
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINES)
            glVertex3f(*parent_pos)
            glVertex3f(*joint_pos)
            glEnd()
        
        # 绘制End Site（如手指末端）
        if joint.end_site is not None:
            end_site_pos = joint.matrix @ np.append(joint.end_site, 1.0)
            end_site_pos = end_site_pos[:3]
            
            glLineWidth(2.0)
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINES)
            glVertex3f(*joint_pos)
            glVertex3f(*end_site_pos)
            glEnd()
            
            glPushMatrix()
            glTranslatef(end_site_pos[0], end_site_pos[1], end_site_pos[2])
            quad = gluNewQuadric()
            gluSphere(quad, 2.5 * 0.3, 16, 16)
            gluDeleteQuadric(quad)
            glPopMatrix()

# 绘制直角矩形
def draw_rect(x, y, width, height, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

# 左侧Position面板
def draw_position_panel(display, current_positions, joints):
    panel_x = 10
    panel_y = display[1] - 60  # 位于按钮下方
    line_height = 18
    title_font = GLUT_BITMAP_HELVETICA_18
    content_font = GLUT_BITMAP_HELVETICA_12
    title_color = (0.0, 0.0, 0.0)
    content_color = (0.0, 0.0, 0.0)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # 计算数据列的总宽度
    joint_name_col_start = panel_x + 10
    X_COL_START = joint_name_col_start + 120
    Y_COL_START = X_COL_START + 62
    Z_COL_START = Y_COL_START + 60
    data_column_width = Z_COL_START - joint_name_col_start + 60  # 假设Z列数据宽度为60，可根据实际调整

    # 计算标题的水平居中位置
    title_text = "All Joints - Position (m)"
    title_width = len(title_text) * 8  # 假设每个字符宽度为8，根据实际字体调整
    title_x = joint_name_col_start + (data_column_width - title_width) // 2

    # 绘制面板标题
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font)
    current_y = panel_y - line_height

    # 按自定义顺序遍历关节
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_positions:
            continue
        # 绘制关节名称
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font)
        # cm转m，保留4位小数
        pos = current_positions[joint_name] / 100
        x_text = f"X:{pos[0]:.4f}"
        y_text = f"Y:{pos[1]:.4f}"
        z_text = f"Z:{pos[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font)
        current_y -= line_height
        if current_y < 50:  # 底部留50像素
            break

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# 右侧Velocity面板
# 右侧Velocity面板（修复参数错误，与左侧面板对齐）
def draw_velocity_panel(display, current_velocities, joints):
    panel_x = display[0] - 330  # 右侧预留330像素宽度
    panel_y = display[1] - 60  # 与Position面板顶部对齐
    line_height = 18
    title_font = GLUT_BITMAP_HELVETICA_18
    content_font = GLUT_BITMAP_HELVETICA_12
    title_color = (0.0, 0.0, 0.0)
    content_color = (0.0, 0.0, 0.0)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)

    # 计算数据列的总宽度
    joint_name_col_start = panel_x + 10
    X_COL_START = joint_name_col_start + 120
    Y_COL_START = X_COL_START + 62
    Z_COL_START = Y_COL_START + 60
    data_column_width = Z_COL_START - joint_name_col_start + 60  # 假设Z列数据宽度为60，可根据实际调整

    # 计算标题的水平居中位置
    title_text = "All Joints - Velocity (m/s)"
    title_width = len(title_text) * 8  # 假设每个字符宽度为8，根据实际字体调整
    title_x = joint_name_col_start + (data_column_width - title_width) // 2

    # 绘制面板标题
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font)
    current_y = panel_y - line_height

    # 按自定义顺序遍历关节
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_velocities:
            continue
        # 绘制关节名称
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font)
        # cm/s转m/s，保留4位小数
        vel = current_velocities[joint_name] / 100
        x_text = f"X:{vel[0]:.4f}"
        y_text = f"Y:{vel[1]:.4f}"
        z_text = f"Z:{vel[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font)
        current_y -= line_height
        if current_y < 50:  # 底部留50像素
            break

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# 绘制坐标轴及标签
def draw_axes_and_labels():
    modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    
    axis_length = 16.67
    label_offset = 21.0
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(axis_length, 0.0, 0.0)
    glEnd()
    try:
        x_pos_3d = gluProject(label_offset, 0, 0, modelview_matrix, projection_matrix, viewport)
        glWindowPos2d(x_pos_3d[0], x_pos_3d[1])
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('X'))
    except ValueError:
        pass
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, axis_length, 0.0)
    glEnd()
    try:
        y_pos_3d = gluProject(0, label_offset, 0, modelview_matrix, projection_matrix, viewport)
        glWindowPos2d(y_pos_3d[0], y_pos_3d[1])
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('Y'))
    except ValueError:
        pass
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, axis_length)
    glEnd()
    try:
        z_pos_3d = gluProject(0, 0, label_offset, modelview_matrix, projection_matrix, viewport)
        glWindowPos2d(z_pos_3d[0], z_pos_3d[1])
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('Z'))
    except ValueError:
        pass

# 绘制网格
def draw_grid():
    glPushMatrix()
    glLineWidth(1.0)
    glColor3f(0.8, 0.8, 0.8)
    
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i * 50, 0, -500)
        glVertex3f(i * 50, 0, 500)
        glVertex3f(-500, 0, i * 50)
        glVertex3f(500, 0, i * 50)
    glEnd()
    glPopMatrix()

# 绘制2D文本
def draw_text_2d(x, y, text, color, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(*color)
    glWindowPos2d(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

# -------------------------- 优化：关节轨迹绘制函数（实线→绿色小点，仅播放时显示） --------------------------
def draw_joint_trajectories(show_trajectories, selected_joints, joint_trajectories, joint_colors, current_frame):
    if not show_trajectories or not selected_joints or not joint_trajectories:
        return
    
    glDisable(GL_DEPTH_TEST)  # 轨迹在骨骼上方显示
    glColor3f(0.0, 1.0, 0.0)  # 固定绿色
    glPointSize(1.0)          # 点大小（3像素，精致不突兀）
    
    for joint_name in selected_joints:
        if joint_name not in joint_trajectories:
            continue
        trajectory = joint_trajectories[joint_name]
        if len(trajectory) < 1:
            continue
        
        # 仅绘制当前帧及之前的点（随播放进度累积）
        glBegin(GL_POINTS)
        for i in range(0, current_frame + 1):
            if i >= len(trajectory):
                break
            pos = trajectory[i]
            glVertex3f(*pos)
        glEnd()
    
    glEnable(GL_DEPTH_TEST)

# -------------------------- 轨迹设置窗口（关节多选+开关） --------------------------
def open_trajectory_settings(joints, all_joint_positions, show_trajectories, selected_joints, joint_trajectories, joint_colors):
    if not joints or not all_joint_positions:
        tk.Tk().withdraw()
        tk.messagebox.showwarning("提示", "请先加载BVH文件！")
        return
    
    # 新建Tkinter窗口
    settings_win = tk.Tk()
    settings_win.title("关节轨迹设置")
    settings_win.geometry("300x400")
    
    # 轨迹总开关
    show_var = IntVar(value=1 if show_trajectories else 0)
    show_checkbox = Checkbutton(
        settings_win,
        text="显示关节轨迹",
        variable=show_var,
        font=("Arial", 10)
    )
    show_checkbox.pack(pady=10, anchor="w", padx=20)
    
    # 关节多选列表
    tk.Label(settings_win, text="选择关节（可多选）：", font=("Arial", 10)).pack(anchor="w", padx=20)
    listbox = Listbox(
        settings_win,
        selectmode=tk.MULTIPLE,  # 支持多选
        font=("Arial", 9),
        height=15
    )
    # 加载所有关节名（按自定义顺序）
    joint_names = [name for name in CUSTOM_JOINT_ORDER if name in joints]
    for idx, name in enumerate(joint_names):
        listbox.insert(idx, name)
        # 已选中的关节默认勾选
        if name in selected_joints:
            listbox.selection_set(idx)
    listbox.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
    
    # 确认按钮逻辑
    def confirm_settings():
        nonlocal show_trajectories, selected_joints, joint_trajectories, joint_colors
        
        # 1. 更新轨迹开关状态
        show_trajectories = bool(show_var.get())
        
        # 2. 更新选中的关节
        selected_indices = listbox.curselection()
        selected_joints = [joint_names[idx] for idx in selected_indices]
        
        # 3. 构建选中关节的轨迹数据（从all_joint_positions提取）
        joint_trajectories.clear()
        for joint_name in selected_joints:
            trajectory = []
            for frame_pos in all_joint_positions:
                # 提取该关节在当前帧的位置
                pos = frame_pos.get(joint_name, np.zeros(3))
                trajectory.append(pos)
            joint_trajectories[joint_name] = trajectory
        
        # 4. 为每个选中关节分配专属颜色（HSV色轮，区分明显）
        joint_colors.clear()
        num_joints = len(selected_joints)
        for idx, joint_name in enumerate(selected_joints):
            hue = idx / num_joints if num_joints > 0 else 0  # 色调均匀分布
            saturation = 0.7  # 饱和度
            value = 0.8  # 明度
            # HSV转RGB（简化计算）
            color = colorsys.hsv_to_rgb(hue, saturation, value)
            joint_colors[joint_name] = color
        
        settings_win.destroy()
    
    # 确认按钮
    confirm_btn = tk.Button(
        settings_win,
        text="确认",
        command=confirm_settings,
        font=("Arial", 10),
        width=10
    )
    confirm_btn.pack(pady=10)
    
    settings_win.mainloop()
    # 返回更新后的数据（用于主函数变量同步）
    return show_trajectories, selected_joints, joint_trajectories, joint_colors

# 绘制2D UI
def draw_2d_ui(display, current_frame, frames, is_playing, fps, load_btn_rect, export_btn_rect, trajectory_btn_rect, play_pause_btn_rect, timeline_rect, bvh_fps=0, bvh_total_frames=0):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    # 1. Load按钮
    load_x = load_btn_rect.x
    load_y = display[1] - load_btn_rect.y - load_btn_rect.height
    load_width = load_btn_rect.width
    load_height = load_btn_rect.height
    draw_rect(load_x, load_y, load_width, load_height, (0.8, 0.8, 0.8))
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(load_x, load_y)
    glVertex2f(load_x + load_width, load_y)
    glVertex2f(load_x + load_width, load_y + load_height)
    glVertex2f(load_x, load_y + load_height)
    glEnd()
    load_text = "Load File"
    text_width = len(load_text) * 8
    text_height = 12
    load_text_x = load_x + (load_width - text_width) / 2 + 8  
    load_text_y = load_y + (load_height + text_height) / 2 - 10  
    draw_text_2d(load_text_x, load_text_y, load_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    
    # 2. Export按钮
    export_x = export_btn_rect.x
    export_y = display[1] - export_btn_rect.y - export_btn_rect.height
    export_width = export_btn_rect.width
    export_height = export_btn_rect.height
    draw_rect(export_x, export_y, export_width, export_height, (0.8, 0.8, 0.8))
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(export_x, export_y)
    glVertex2f(export_x + export_width, export_y)
    glVertex2f(export_x + export_width, export_y + export_height)
    glVertex2f(export_x, export_y + export_height)
    glEnd()
    export_text = "Export Data"
    export_text_width = len(export_text) * 8
    export_text_height = 12
    export_text_x = export_x + (export_width - export_text_width) / 2 + 8  
    export_text_y = export_y + (export_height + export_text_height) / 2 - 10 
    draw_text_2d(export_text_x, export_text_y, export_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    
    # 3. 轨迹设置按钮
    traj_x = trajectory_btn_rect.x
    traj_y = display[1] - trajectory_btn_rect.y - trajectory_btn_rect.height
    traj_width = trajectory_btn_rect.width
    traj_height = trajectory_btn_rect.height
    draw_rect(traj_x, traj_y, traj_width, traj_height, (0.8, 0.8, 0.8))
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(traj_x, traj_y)
    glVertex2f(traj_x + traj_width, traj_y)
    glVertex2f(traj_x + traj_width, traj_y + traj_height)
    glVertex2f(traj_x, traj_y + traj_height)
    glEnd()
    traj_text = "Trajectory"
    traj_text_width = len(traj_text) * 8
    traj_text_height = 12
    traj_text_x = traj_x + (traj_width - traj_text_width) / 2 + 8  
    traj_text_y = traj_y + (traj_height + traj_text_height) / 2 - 10 
    draw_text_2d(traj_text_x, traj_text_y, traj_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    
    # 时间轴相关绘制
    if frames > 0:
        draw_text_2d(timeline_rect.x - 10, timeline_rect.y, "0", (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
        draw_text_2d(timeline_rect.x + timeline_rect.width + 10, timeline_rect.y, str(frames - 1), (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
        frame_text = f"Frame: {current_frame}"
        draw_text_2d((display[0] - len(frame_text)*8) // 2, timeline_rect.y + timeline_rect.height + 5, frame_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
        
        glColor3f(0.7, 0.7, 0.7)
        glBegin(GL_QUADS)
        glVertex2f(timeline_rect.x, timeline_rect.y)
        glVertex2f(timeline_rect.x + timeline_rect.width, timeline_rect.y)
        glVertex2f(timeline_rect.x + timeline_rect.width, timeline_rect.y + timeline_rect.height)
        glVertex2f(timeline_rect.x, timeline_rect.y + timeline_rect.height)
        glEnd()
        progress_width = (current_frame / (frames - 1)) * timeline_rect.width if frames > 1 else 0
        glColor3f(0.4, 0.4, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(timeline_rect.x, timeline_rect.y)
        glVertex2f(timeline_rect.x + progress_width, timeline_rect.y)
        glVertex2f(timeline_rect.x + progress_width, timeline_rect.y + timeline_rect.height)
        glVertex2f(timeline_rect.x, timeline_rect.y + timeline_rect.height)
        glEnd()
        
        slider_x = timeline_rect.x + progress_width
        slider_y = timeline_rect.y
        slider_w = 8
        slider_h = 16
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex2f(slider_x - slider_w/2, slider_y - slider_h/2 + timeline_rect.height/2)
        glVertex2f(slider_x + slider_w/2, slider_y - slider_h/2 + timeline_rect.height/2)
        glVertex2f(slider_x + slider_w/2, slider_y + slider_h/2 + timeline_rect.height/2)
        glVertex2f(slider_x - slider_w/2, slider_y + slider_h/2 + timeline_rect.height/2)
        glEnd()
    
    # 播放/暂停按钮
    glColor3f(0.0, 0.0, 0.0)
    if is_playing:
        glBegin(GL_QUADS)
        glVertex2f(play_pause_btn_rect.x, play_pause_btn_rect.y)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width * 0.4, play_pause_btn_rect.y)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width * 0.4, play_pause_btn_rect.y + play_pause_btn_rect.height)
        glVertex2f(play_pause_btn_rect.x, play_pause_btn_rect.y + play_pause_btn_rect.height)
        glEnd()
        glBegin(GL_QUADS)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width * 0.6, play_pause_btn_rect.y)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width, play_pause_btn_rect.y)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width, play_pause_btn_rect.y + play_pause_btn_rect.height)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width * 0.6, play_pause_btn_rect.y + play_pause_btn_rect.height)
        glEnd()
    else:
        glBegin(GL_TRIANGLES)
        glVertex2f(play_pause_btn_rect.x, play_pause_btn_rect.y)
        glVertex2f(play_pause_btn_rect.x, play_pause_btn_rect.y + play_pause_btn_rect.height)
        glVertex2f(play_pause_btn_rect.x + play_pause_btn_rect.width, play_pause_btn_rect.y + play_pause_btn_rect.height/2)
        glEnd()
    
    # BVH数据信息显示
    if bvh_fps > 0 and bvh_total_frames > 0:
        bvh_info_text = f"BVH Data: {bvh_fps:.0f}HZ, {bvh_total_frames - 1}Frames"
        draw_text_2d(10, 30, bvh_info_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    # 软件帧率显示
    fps_text = f"BVH Viewer: {int(fps)} FPS"
    draw_text_2d(10, 10, fps_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# 绘制关节角度标签
def draw_joint_angle_label(joint1_name, joint2_name, joint3_name, joints, display, arc_radius=3.3, color=(0.5, 0.5, 0.5)):
    if joint1_name not in joints or joint2_name not in joints:
        return
    p1 = joints[joint1_name].matrix[:3, 3]
    p2 = joints[joint2_name].matrix[:3, 3]
    
    if joint3_name in joints:
        p3 = joints[joint3_name].matrix[:3, 3]
    else:
        if joints[joint2_name].end_site is not None and len(joints[joint2_name].end_site) == 3:
            end_site_pos = joints[joint2_name].matrix @ np.append(joints[joint2_name].end_site, 1.0)
            p3 = end_site_pos[:3]
        else:
            return
    vec1 = p1 - p2
    vec2 = p3 - p2
    
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return
    vec1_norm = vec1 / np.linalg.norm(vec1)
    vec2_norm = vec2 / np.linalg.norm(vec2)
    
    angle_rad = np.arccos(np.clip(np.dot(vec1_norm, vec2_norm), -1.0, 1.0))
    angle_deg = np.degrees(angle_rad)
    
    axis = np.cross(vec1_norm, vec2_norm)
    if np.linalg.norm(axis) == 0:
        return
    axis = axis / np.linalg.norm(axis)
    start_vector = vec1_norm * arc_radius
    angle_step = 5
    glLineWidth(1.5)
    glColor3f(*color)
    glBegin(GL_LINE_STRIP)
    for i in range(0, int(angle_deg) + 1, angle_step):
        angle_current_rad = np.radians(i)
        
        rotated_vector = start_vector * np.cos(angle_current_rad) + \
                         np.cross(axis, start_vector) * np.sin(angle_current_rad) + \
                         axis * np.dot(axis, start_vector) * (1 - np.cos(angle_current_rad))
        
        arc_point = p2 + rotated_vector
        glVertex3f(*arc_point)
    glEnd()
    text_pos_3d = p2 + (vec1_norm + vec2_norm) / 2.0 * arc_radius * 1.5
    modelview_matrix = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection_matrix = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    
    try:
        text_pos_2d = gluProject(text_pos_3d[0], text_pos_3d[1], text_pos_3d[2], modelview_matrix, projection_matrix, viewport)
        glWindowPos2d(text_pos_2d[0], text_pos_2d[1])
        glColor3f(0.0, 0.0, 0.0)
        angle_text = f"{angle_deg:.1f}°"
        for char in angle_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(char))
    except ValueError:
        pass

# 反投影
def unproject(winX, winY, winZ=0.0):
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    obj_point = gluUnProject(winX, winY, winZ, modelview, projection, viewport)
    return obj_point

# 导出数据
def export_data_dialog(all_joints, all_positions, all_velocities, all_accelerations, all_anatomical_angles):
    root = tk.Tk()
    root.withdraw()
    # 弹出保存对话框，默认CSV格式
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv", 
        filetypes=[("CSV files", "*.csv")],
        title="导出全关节角度数据"
    )
    root.destroy()
    
    if not file_path:
        print("数据导出已取消。")
        return
    try:
        # 用utf-8-sig编码，解决中文/特殊符号（°）编码问题，兼容Excel
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # -------------------------- 1. 构建CSV表头 --------------------------
            header = ['Frame']  # 第一列：帧号
            # 1.1 加入关节位置/速度/加速度（按自定义顺序）
            joint_names = [name for name in CUSTOM_JOINT_ORDER if name in all_joints]
            for joint_name in joint_names:
                header.extend([
                    f'{joint_name}_pos_X(m)',
                    f'{joint_name}_pos_Y(m)',
                    f'{joint_name}_pos_Z(m)',
                    f'{joint_name}_vel_X(m/s)',
                    f'{joint_name}_vel_Y(m/s)',
                    f'{joint_name}_vel_Z(m/s)',
                    f'{joint_name}_accel_X(m/s²)',
                    f'{joint_name}_accel_Y(m/s²)',
                    f'{joint_name}_accel_Z(m/s²)'
                ])
            # 1.2 加入所有关节角度（自动收集，含全身+手指）
            angle_keys = set()
            for frame_angles in all_anatomical_angles:
                if frame_angles:
                    angle_keys.update(frame_angles.keys())
            angle_keys = sorted(angle_keys)  # 排序，确保每次导出顺序一致
            for angle_key in angle_keys:
                header.append(f'{angle_key}(°)')  # 加入角度单位，清晰易懂
            
            # 写入表头
            writer.writerow(header)
            
            # -------------------------- 2. 逐帧写入数据 --------------------------
            num_frames = len(all_positions)
            for frame_idx in range(num_frames):
                row = [frame_idx + 1]  # 帧号从1开始（符合常规习惯）
                
                # 2.1 写入位置/速度/加速度（单位转换：cm→m）
                for joint_name in joint_names:
                    # 从每帧数据中获取关节信息，无数据时用0填充
                    pos = all_positions[frame_idx].get(joint_name, np.zeros(3)) / 100
                    vel = all_velocities[frame_idx].get(joint_name, np.zeros(3)) / 100
                    accel = all_accelerations[frame_idx].get(joint_name, np.zeros(3)) / 100
                    # 保留4位小数，避免数据冗余
                    row.extend([round(val, 4) for val in pos])
                    row.extend([round(val, 4) for val in vel])
                    row.extend([round(val, 4) for val in accel])
                
                # 2.2 写入所有关节角度（含全身+手指）
                current_frame_angles = all_anatomical_angles[frame_idx] if frame_idx < len(all_anatomical_angles) else {}
                for angle_key in angle_keys:
                    # 无角度数据时用NaN填充（便于后续数据分析）
                    angle_val = current_frame_angles.get(angle_key, float('nan'))
                    row.append(angle_val)
                
                # 写入当前帧数据
                writer.writerow(row)
            
            # 导出成功日志（显示导出的角度数量，便于验证）
            print(f"✅ 数据成功导出到：{file_path}")
            print(f"📊 导出内容：")
            print(f"  - 关节数量：{len(joint_names)}个（含全身+手指）")
            print(f"  - 角度数量：{len(angle_keys)}个（所有相邻关节夹角）")
            print(f"  - 总帧数：{num_frames}帧")
    
    except Exception as e:
        print(f"数据导出失败: {e}")

# 主函数
def main():
    pygame.init()
    glutInit()
    
    # -------------------------- 关键修改：读取屏幕分辨率并计算3/4窗口尺寸 --------------------------
    # 1. 获取当前电脑屏幕的原始分辨率（排除任务栏等系统区域，用可用屏幕尺寸更准确）
    screen_info = pygame.display.Info()  # 获取屏幕信息对象
    original_screen_width = screen_info.current_w  # 屏幕可用宽度（像素）
    original_screen_height = screen_info.current_h  # 屏幕可用高度（像素）
    
    # 2. 计算目标窗口尺寸：原始分辨率的3/4（向下取整避免小数像素）
    target_display_width = int(original_screen_width * 0.75)
    target_display_height = int(original_screen_height * 0.75)
    display = (target_display_width, target_display_height)  # 最终窗口尺寸
    
    # 3. 初始化窗口（保留双缓冲、OpenGL、可调整大小特性）
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption("BVH 3D Viewer")  # 窗口标题
    
    # -------------------------- 新增：设置标题栏/缩略图 Logo（原代码保留，仅适配新窗口） --------------------------
    try:
        app_icon = pygame.image.load("app_icon.ico")
        pygame.display.set_icon(app_icon)
    except Exception as e:
        print(f"加载标题栏图标失败：{e}（请确保 app_icon.ico 在脚本目录下）")
    
    # -------------------------- 视图投影适配：基于新窗口尺寸计算宽高比 --------------------------
    glClearColor(1.0, 1.0, 1.0, 1.0) 
    glEnable(GL_DEPTH_TEST)
    
    # 关键：用计算出的窗口尺寸获取宽高比（确保OpenGL投影适配3/4窗口）
    aspect_ratio = display[0] / display[1]  # 宽/高比，用于透视投影
    
    # -------------------------- 以下为原代码（仅保留关联性强的初始化逻辑，无需修改） --------------------------
    root_joint, joints, motion_data, frames, frame_time = None, {}, [], 0, 0
    current_frame = 0
    is_playing = False
    bvh_fps = 0.0
    bvh_total_frames = 0
    target_fps = 60
    clock = pygame.time.Clock()
    left_button_down = False
    middle_button_down = False
    timeline_dragging = False
    last_mouse_pos = (0, 0)
    
    # 轨迹相关变量（原代码保留）
    show_trajectories = False
    selected_joints = []
    joint_trajectories = {}
    joint_colors = {}
    
    # 按钮位置初始化（原代码保留，会随窗口尺寸动态调整）
    btn_y = 10
    btn_height = 25
    load_btn_rect = pygame.Rect(10, btn_y, 90, btn_height)
    export_btn_rect = pygame.Rect(
        load_btn_rect.x + load_btn_rect.width + 10, 
        btn_y, 
        110, 
        btn_height
    )
    trajectory_btn_rect = pygame.Rect(
        export_btn_rect.x + export_btn_rect.width + 10,
        btn_y,
        110,
        btn_height
    )
    play_pause_btn_rect = pygame.Rect(0, 0, 0, 0) 
    timeline_rect = pygame.Rect(0, 0, 0, 0)
    
    all_joint_positions = []
    all_joint_velocities = []
    all_joint_accelerations = []
    all_anatomical_angles = []
    joint_roms = {}
    
    # -------------------------- 视图重置函数适配（确保缩放后透视正确） --------------------------
    def reset_view():
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # 关键：用计算出的aspect_ratio（3/4窗口的宽高比）设置透视投影
        gluPerspective(45, aspect_ratio, 0.1, 1000.0)  # 45°视角，近裁剪面0.1，远裁剪面1000
        glTranslatef(0.0, -100.0, -300)  # 初始相机位置（原代码保留，适配骨骼显示）
    
    # 以下toggle_play_pause、load_file_dialog等函数及后续逻辑均无需修改...
        
    def toggle_play_pause():
        nonlocal is_playing
        is_playing = not is_playing
    
    def load_file_dialog():
        nonlocal root_joint, joints, motion_data, frames, frame_time, current_frame, all_joint_positions, all_joint_velocities, all_joint_accelerations, all_anatomical_angles, joint_roms, bvh_fps, bvh_total_frames
        # 加载新文件时清空旧轨迹数据
        nonlocal show_trajectories, selected_joints, joint_trajectories, joint_colors
        show_trajectories = False
        selected_joints.clear()
        joint_trajectories.clear()
        joint_colors.clear()
        
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(defaultextension=".bvh", filetypes=[("BVH files", "*.bvh")])
        root.destroy()
        
        if file_path:
            root_joint, joints, motion_data, frames, frame_time = parse_bvh(file_path)
            if root_joint:
                motion_data = np.array(motion_data)
                frames = len(motion_data)
                current_frame = 0
                
                bvh_total_frames = frames
                if frame_time > 0:
                    bvh_fps = 1.0 / frame_time
                else:
                    bvh_fps = 0.0
                
                print(f"成功加载文件: {file_path}")
                print(f"BVH Data: {bvh_fps:.0f}HZ, {bvh_total_frames - 1}Frames")
                print(f"帧时间: {frame_time}s")
                
                all_joint_positions, all_joint_velocities, all_joint_accelerations, all_anatomical_angles = calculate_kinematics(joints, motion_data, frame_time)
                print("运动学数据计算完成。")
            else:
                print(f"文件解析失败: {file_path}")
                bvh_fps = 0.0
                bvh_total_frames = 0
    
    reset_view()
    running = True
    while running:
        # 播放按钮位置更新
        play_btn_size = 20
        play_btn_x = (display[0] - play_btn_size) // 2
        play_btn_y = display[1] - 30 - play_btn_size
        play_pause_btn_rect.update(play_btn_x, play_btn_y, play_btn_size, play_btn_size)
        
        # 时间轴位置更新
        timeline_width = display[0] - 200
        timeline_x = (display[0] - timeline_width) // 2
        timeline_height = 8
        timeline_y = play_btn_y - 10 - timeline_height
        timeline_rect.update(timeline_x, timeline_y, timeline_width, timeline_height)
        
        # 事件处理（优化鼠标操作逻辑）
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
 
            # 窗口拉伸事件（修复黑屏+移除GLUT函数，避免闪退）
            elif event.type == pygame.VIDEORESIZE:
                # 更新窗口尺寸和宽高比
                display = (event.w, event.h)
                aspect_ratio = event.w / event.h  # 实时更新宽高比
                
                # 重建窗口：保留双缓冲+硬件加速，避免缓冲区清空
                pygame.display.set_mode(
                    display, 
                    DOUBLEBUF | OPENGL | pygame.RESIZABLE | pygame.HWSURFACE  # 硬件加速减少黑屏
                )
                
                # 重置视图+强制即时重绘（用OpenGL原生命令替代glutPostRedisplay）
                reset_view()
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # 清空旧缓冲
                glFlush()  # 强制OpenGL执行清空命令
                pygame.display.flip()  # 立即刷新Pygame窗口，避免黑屏
                
                # 同步更新UI控件位置（避免缩放后UI错位）
                play_btn_x = (display[0] - play_btn_size) // 2
                play_btn_y = display[1] - 30 - play_btn_size
                play_pause_btn_rect.update(play_btn_x, play_btn_y, play_btn_size, play_btn_size)
                
                timeline_width = display[0] - 200
                timeline_x = (display[0] - timeline_width) // 2
                timeline_y = play_btn_y - 10 - timeline_height
                timeline_rect.update(timeline_x, timeline_y, timeline_width, timeline_height)
            # 鼠标按下事件（左键平移、中键按下恢复、右键旋转、滚轮基于视角缩放）
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_mouse_pos = event.pos
                
                if event.button == 1:
                    left_button_down = True  # 左键平移状态
                elif event.button == 2:
                    reset_view()  # 中键按下恢复初始视图
                elif event.button == 3:
                    middle_button_down = True  # 右键旋转状态
                elif event.button == 4:
                    # 滚轮上滚：基于当前视角放大（靠近画面中心）
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    # 提取相机朝向（视图矩阵第3列，负方向为相机正前方）
                    cam_forward = np.array([-view_matrix[2][0], -view_matrix[2][1], -view_matrix[2][2]])
                    cam_forward = cam_forward / np.linalg.norm(cam_forward)  # 归一化方向
                    glTranslatef(*(cam_forward * 10.0))  # 沿朝向移动（放大）
                elif event.button == 5:
                    # 滚轮下滚：基于当前视角缩小（远离画面中心）
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    cam_forward = np.array([-view_matrix[2][0], -view_matrix[2][1], -view_matrix[2][2]])
                    cam_forward = cam_forward / np.linalg.norm(cam_forward)
                    glTranslatef(*(cam_forward * -10.0))  # 逆朝向移动（缩小）
                
                # 按钮点击逻辑（Load/Export等）不变...
                if event.button == 1:
                    if load_btn_rect.collidepoint(event.pos):
                        load_file_dialog()
                    elif export_btn_rect.collidepoint(event.pos) and frames > 0:
                        export_data_dialog(joints, all_joint_positions, all_joint_velocities, all_joint_accelerations, all_anatomical_angles)
                    elif trajectory_btn_rect.collidepoint(event.pos):
                        updated_vals = open_trajectory_settings(
                            joints, all_joint_positions,
                            show_trajectories, selected_joints,
                            joint_trajectories, joint_colors
                        )
                        if updated_vals:
                            show_trajectories, selected_joints, joint_trajectories, joint_colors = updated_vals
                    elif play_pause_btn_rect.collidepoint(event.pos):
                        toggle_play_pause()
                    elif timeline_rect.collidepoint(event.pos) and frames > 0:
                        timeline_dragging = True
                        is_playing = False
                        current_frame = int((event.pos[0] - timeline_rect.x) / timeline_rect.width * (frames - 1))
            # 鼠标松开事件
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # 左键松开：停止平移（原有逻辑不变）
                    left_button_down = False
                    timeline_dragging = False
                elif event.button == 3:
                    # 右键松开：停止旋转（原中键松开逻辑）
                    middle_button_down = False  # 与按下时的状态变量保持一致
            
            # 鼠标移动事件（左键平移、右键绕中心旋转、时间轴拖动）
            # 鼠标移动事件（左键平移、右键绕火柴人水平旋转、时间轴拖动）
            if event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                rel_x, rel_y = mouse_x - last_mouse_pos[0], mouse_y - last_mouse_pos[1]
                
                # 左键平移（原有逻辑不变，保留）
                if left_button_down and not timeline_dragging:
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    right_axis = np.array([view_matrix[0][0], view_matrix[1][0], view_matrix[2][0]])
                    up_axis = np.array([view_matrix[0][1], view_matrix[1][1], view_matrix[2][1]])
                    translate_x = rel_x * 0.2 * right_axis
                    translate_y = -rel_y * 0.2 * up_axis
                    glTranslatef(translate_x[0], translate_y[1], translate_x[2] + translate_y[2])
                
                # 右键拖动：仅水平绕火柴人（Hips关节）旋转（简化逻辑）
                if middle_button_down and joints:  # 确保已加载关节数据
                    try:
                        # 1. 获取火柴人根关节（Hips，骨盆）的世界坐标（旋转中心）
                        # 若Hips不存在， fallback到第一个关节（兼容不同BVH骨骼命名）
                        target_joint = joints.get('Hips', joints[next(iter(joints.keys()))])
                        joint_world_pos = target_joint.matrix[:3, 3]  # Hips的世界位置
                        
                        # 2. 旋转逻辑：先移到Hips中心→水平旋转→移回原位置
                        glTranslatef(*joint_world_pos)  # 把Hips移到世界原点（旋转中心）
                        # 仅水平旋转（绕Y轴，左右拖动有效，上下拖动无效），速度0.15更平缓
                        glRotatef(rel_x * 0.15, 0, 1, 0)  # 只响应鼠标X轴偏移（左右拖）
                        glTranslatef(-joint_world_pos[0], -joint_world_pos[1], -joint_world_pos[2])  # 移回原位
                    except Exception as e:
                        print(f"绕火柴人旋转异常: {e}")
                        pass
                
                # 时间轴拖动（原有逻辑不变，保留）
                if timeline_dragging and frames > 0:
                    mouse_pos_x = event.pos[0]
                    progress_x = min(max(mouse_pos_x, timeline_rect.x), timeline_rect.right)
                    current_frame = int((progress_x - timeline_rect.x) / timeline_rect.width * (frames - 1))
                
                last_mouse_pos = (mouse_x, mouse_y)
            
            # 键盘事件
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    toggle_play_pause()  # 原有空格播放/暂停逻辑不变
                if event.key == pygame.K_LEFT and frames > 0:
                    current_frame = max(0, current_frame - 1)  # 原有左键帧后退
                if event.key == pygame.K_RIGHT and frames > 0:
                    current_frame = min(frames - 1, current_frame + 1)  # 原有右键帧前进
                # 新增：F键触发恢复初始视图
                if event.key == pygame.K_f:
                    reset_view()
        
        # 渲染流程（仅播放时显示轨迹点）
        # 渲染流程（优化缩放时实时性）
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glFlush()  # 新增：强制清空缓冲命令即时执行，避免延迟导致黑屏
        glMatrixMode(GL_MODELVIEW)
        
        glPushMatrix()
        draw_grid()
        draw_axes_and_labels()
        
        if root_joint and len(motion_data) > 0:
            # 更新关节矩阵（原有逻辑不变）
            if is_playing:
                update_joint_matrices(root_joint, motion_data[current_frame], joints)
                current_frame = (current_frame + 1) % frames
            else:
                update_joint_matrices(root_joint, motion_data[current_frame], joints)
            
            # 绘制骨骼（原有函数，不变）
            draw_skeleton_custom_order(joints)  

            # -------------------------- 替换后的角度显示代码（含大臂小臂+弯腰+低头）--------------------------
            # 1. 大臂-小臂夹角（命名对应 RightUpArm_RightForeArm，红色=右，蓝色=左）
            # 右大臂-右小臂：顶点=RightArm（右大臂），向量1=RightShoulder→RightArm，向量2=RightForeArm→RightArm
            draw_joint_angle_label(
                joint1_name='RightShoulder',  # 向量1起点（右肩）
                joint2_name='RightArm',       # 夹角顶点（右大臂，对应 RightUpArm）
                joint3_name='RightForeArm',   # 向量2终点（右小臂）
                joints=joints, 
                display=display, 
                arc_radius=3.3, 
                color=(0.9, 0.2, 0.2)  # 红色，与原有风格一致
            )
            # 左大臂-左小臂：顶点=LeftArm（左大臂），向量1=LeftShoulder→LeftArm，向量2=LeftForeArm→LeftArm
            draw_joint_angle_label(
                joint1_name='LeftShoulder',   # 向量1起点（左肩）
                joint2_name='LeftArm',        # 夹角顶点（左大臂，对应 LeftUpArm）
                joint3_name='LeftForeArm',    # 向量2终点（左小臂）
                joints=joints, 
                display=display, 
                arc_radius=3.3, 
                color=(0.2, 0.2, 0.9)  # 蓝色，与原有风格一致
            )

            # 2. 弯腰角度（绿色，顶点=Spine（下脊柱），向量1=Hips→Spine，向量2=Spine2→Spine）
            draw_joint_angle_label(
                joint1_name='Hips',       # 向量1起点（骨盆，下半身基准）
                joint2_name='Spine',      # 夹角顶点（下脊柱，弯腰时的弯曲点）
                joint3_name='Spine2',     # 向量2终点（上脊柱，上半身基准）
                joints=joints, 
                display=display, 
                arc_radius=5.0,           # 半径稍大，避免与其他角度重叠
                color=(0.2, 0.9, 0.2)     # 绿色，区分于其他角度
            )

            # 3. 低头角度（黄色，顶点=Neck（颈部），向量1=Spine2→Neck，向量2=Head→Neck）
            draw_joint_angle_label(
                joint1_name='Spine2',     # 向量1起点（上脊柱，躯干基准）
                joint2_name='Neck',       # 夹角顶点（颈部，低头时的弯曲点）
                joint3_name='Head',       # 向量2终点（头部，头部基准）
                joints=joints, 
                display=display, 
                arc_radius=3.3,           # 半径适配颈部区域大小
                color=(0.2, 0.9, 0.2)     # 黄色，醒目且不冲突
            )

            # （可选）保留原有其他必要角度（如髋、膝），若不需要可删除
            draw_joint_angle_label('Hips', 'RightUpLeg', 'RightLeg', joints, display, arc_radius=5.0, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('RightArm', 'RightForeArm', 'RightHand', joints, display, arc_radius=3.3, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('LeftArm', 'LeftForeArm', 'LeftHand', joints, display, arc_radius=3.3, color=(0.2, 0.2, 0.9))
            draw_joint_angle_label('RightUpLeg', 'RightLeg', 'RightFoot', joints, display, arc_radius=5.0, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('Hips', 'LeftUpLeg', 'LeftLeg', joints, display, arc_radius=5.0, color=(0.2, 0.2, 0.9))
            draw_joint_angle_label('LeftUpLeg', 'LeftLeg', 'LeftFoot', joints, display, arc_radius=5.0, color=(0.2, 0.2, 0.9))
            # -------------------------- 替换后的角度显示代码结束 --------------------------

            # 轨迹绘制代码（原有，不变）
            if is_playing:
                draw_joint_trajectories(
                    show_trajectories,
                    selected_joints,
                    joint_trajectories,
                    joint_colors,
                    current_frame
                )                     
        glPopMatrix()
        fps = clock.get_fps() if clock.get_fps() > 0 else 0
        
        # 调整UI坐标
        play_btn_y_bottom_up = 30
        timeline_y_bottom_up = play_btn_y_bottom_up + play_btn_size + 10
        timeline_rect_opengl = pygame.Rect(timeline_rect.x, timeline_y_bottom_up, timeline_rect.width, timeline_rect.height)
        play_pause_btn_rect_opengl = pygame.Rect(play_pause_btn_rect.x, play_btn_y_bottom_up, play_pause_btn_rect.width, play_pause_btn_rect.height)
        
        # 绘制2D UI
        draw_2d_ui(
            display, 
            current_frame, 
            frames, 
            is_playing, 
            fps, 
            load_btn_rect,   # Load按钮
            export_btn_rect, # Export按钮
            trajectory_btn_rect,  # 轨迹设置按钮
            play_pause_btn_rect_opengl, 
            timeline_rect_opengl,
            bvh_fps=bvh_fps,
            bvh_total_frames=bvh_total_frames
        )
        
        # 绘制Position和Velocity面板
        if all_joint_positions and all_joint_velocities and frames > 0:
            if 0 <= current_frame < len(all_joint_positions) and 0 <= current_frame < len(all_joint_velocities):
                current_positions = all_joint_positions[current_frame]
                current_velocities = all_joint_velocities[current_frame]
                draw_position_panel(display, current_positions, joints)
                draw_velocity_panel(display, current_velocities, joints)
        
        pygame.display.flip()
        
        if is_playing and frame_time > 0:
            target_fps = 1.0 / frame_time
        
        clock.tick(target_fps)

if __name__ == '__main__':
    main()