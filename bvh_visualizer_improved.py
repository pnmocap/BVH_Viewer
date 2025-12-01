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
        self.channel_start_index = 0  # Store channel start index
    
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

# Get joint world coordinates
def get_world_position(joint):
    return joint.matrix[:3, 3]

# Update joint matrices
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

# Calculate anatomical angles (full-body adjacent joint vector angles, including fingers)
def calculate_anatomical_angles(joints):
    angles = {}
    # Universal vector angle calculation function (core: parent->current->child joint vector angle)
    def get_vector_angle(parent_joint_name, current_joint_name, child_joint_name):
        """
        parent_joint_name: Parent joint (vector 1 start point)
        current_joint_name: Current joint (angle vertex, child node of adjacent joint pair)
        child_joint_name: Child joint (vector 2 end point)
        Returns: Vector angle formed by three joints (degrees, rounded to 2 decimal places)
        """
        # Check if all three joints exist in BVH data
        if (parent_joint_name in joints and 
            current_joint_name in joints and 
            child_joint_name in joints):
            # Get world coordinates of three joints
            p_parent = get_world_position(joints[parent_joint_name])  # Parent joint (vector 1 start)
            p_current = get_world_position(joints[current_joint_name])  # Current joint (angle vertex)
            p_child = get_world_position(joints[child_joint_name])  # Child joint (vector 2 end)
            
            # Calculate two vectors: vertex->parent, vertex->child
            vec_parent = p_parent - p_current
            vec_child = p_child - p_current
            
            # Avoid calculation errors from zero-length vectors
            if np.linalg.norm(vec_parent) > 1e-6 and np.linalg.norm(vec_child) > 1e-6:
                cos_theta = np.dot(vec_parent, vec_child) / (np.linalg.norm(vec_parent) * np.linalg.norm(vec_child))
                cos_theta = np.clip(cos_theta, -1.0, 1.0)  # Clamp cos value range to avoid calculation errors
                angle = np.degrees(np.arccos(cos_theta))
                return round(angle, 2)  # Round to 2 decimal places for cleaner data
        # Return None when joint doesn't exist/vector is invalid (filtered later)
        return None
    
    # -------------------------- Key: Iterate through all adjacent joint pairs (including fingers) --------------------------
    # Based on CUSTOM_JOINT_ORDER, ensure iteration order matches the bone structure
    for joint_name in CUSTOM_JOINT_ORDER:
        # Skip non-existent joints (to avoid KeyError)
        if joint_name not in joints:
            continue
        current_joint = joints[joint_name]
        
        # 1. Skip the root joint with no parent (e.g., Hips, no "adjacent parent joint")
        if current_joint.parent is None:
            continue
        parent_joint_name = current_joint.parent.name  # Adjacent parent joint name
        
        # 2. Iterate through all children of the current joint (each child corresponds to an "adjacent child joint")
        for child_joint in current_joint.children:
            child_joint_name = child_joint.name
            # Skip if child joint doesn't exist (theoretically won't happen, but for safety)
            if child_joint_name not in joints:
                continue
            
            # 3. Generate angle name: ParentJointName_CurrentJointName (consistent with RightUpArm_RightForeArm style)
            # Example: RightArm (Parent) → RightForeArm (Current) → RightHand (Child) → Angle Name = RightArm_RightForeArm
            angle_name = f"{parent_joint_name}_{joint_name}"
            
            # 4. Calculate the vector angle for this adjacent joint pair
            angle_value = get_vector_angle(
                parent_joint_name=parent_joint_name,
                current_joint_name=joint_name,
                child_joint_name=child_joint_name
            )
            
            # 5. Keep only valid angles (filter out None values)
            if angle_value is not None:
                angles[angle_name] = angle_value
    
    # -------------------------- Retain original back bend and head down angles (supplement non-adjacent key angles) --------------------------
    # Back Bend Angle (Hips→Spine→Spine2): Non-adjacent but important, calculated separately
    angles['Hips_Spine'] = get_vector_angle(
        parent_joint_name='Hips',
        current_joint_name='Spine',
        child_joint_name='Spine2'
    )
    # Head Down Angle (Spine2→Neck→Head): Non-adjacent but important, calculated separately
    angles['Spine2_Neck'] = get_vector_angle(
        parent_joint_name='Spine2',
        current_joint_name='Neck',
        child_joint_name='Head'
    )
    
    # Filter out all invalid angles (remove entries with value None)
    return {key: val for key, val in angles.items() if val is not None}

# Calculate Kinematics Data
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

    # Initialize with zeros for the first frame's velocity and acceleration
    velocities_per_frame = [{name: np.zeros(3) for name in joints}] 
    accelerations_per_frame = [{name: np.zeros(3) for name in joints}] 

    # Calculate velocity for frame 1 onwards (assuming initial velocity/acceleration are zero)
    for i in range(1, num_frames):
        current_velocities = {}
        current_accelerations = {}
        
        # Calculate velocity for current frame i
        for name in joints:
            pos_diff = positions_per_frame[i][name] - positions_per_frame[i-1][name]
            velocity = pos_diff / frame_time
            current_velocities[name] = velocity
            
            # Calculate acceleration for current frame i
            vel_diff = current_velocities[name] - velocities_per_frame[i-1][name]
            acceleration = vel_diff / frame_time
            current_accelerations[name] = acceleration
            
        velocities_per_frame.append(current_velocities)
        accelerations_per_frame.append(current_accelerations)

    return positions_per_frame, velocities_per_frame, accelerations_per_frame, anatomical_angles_per_frame

# Custom Skeleton Drawing Order
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
    'LeftinHandPinky', 'LeftHandPinky2', 'LeftHandPinky2', 'LeftHandPinky3',
    'Spine3'
]

# Redefined Skeleton Drawing Function
def draw_custom_skeleton(joints):
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints:
            continue
        joint = joints[joint_name]
        
        # Render current joint (Sphere)
        glColor3f(0.0, 0.0, 0.0)
        glPushMatrix()
        joint_pos = joint.matrix[:3, 3]
        glTranslatef(joint_pos[0], joint_pos[1], joint_pos[2])
        quad = gluNewQuadric()
        gluSphere(quad, 2.5 * 0.4, 16, 16)
        gluDeleteQuadric(quad)
        glPopMatrix()
        
        # Draw connection line between current joint and parent joint
        if joint.parent is not None and joint.parent.name in joints:
            parent_joint = joints[joint.parent.name]
            parent_pos = parent_joint.matrix[:3, 3]
            
            glLineWidth(2.0)
            glColor3f(0.0, 0.0, 0.0)
            glBegin(GL_LINES)
            glVertex3f(*parent_pos)
            glVertex3f(*joint_pos)
            glEnd()
        
        # Draw End Site (e.g., finger tips)
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

# Draw right-angle rectangle
def draw_rectangle(x, y, width, height, color):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

# Left Position Panel
def draw_position_panel(display, current_positions, joints):
    panel_x = 10
    panel_y = display[1] - 60  # Located below the buttons
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

    # Calculate total width of data columns
    joint_name_col_start = panel_x + 10
    X_COL_START = joint_name_col_start + 120
    Y_COL_START = X_COL_START + 62
    Z_COL_START = Y_COL_START + 60
    data_column_width = Z_COL_START - joint_name_col_start + 60  # Assume Z column data width is 60, adjust as needed

    # Calculate horizontal center position for the title
    title_text = "All Joints - Position (m)"
    title_width = len(title_text) * 8  # Assume character width is 8, adjust as needed
    title_x = joint_name_col_start + (data_column_width - title_width) // 2

    # Draw panel title
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font)
    current_y = panel_y - line_height

    # Iterate joints by custom order
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_positions:
            continue
        # Draw joint name
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font)
        # Convert cm to m, keep 4 decimal places
        pos = current_positions[joint_name] / 100
        x_text = f"X:{pos[0]:.4f}"
        y_text = f"Y:{pos[1]:.4f}"
        z_text = f"Z:{pos[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font)
        current_y -= line_height
        if current_y < 50:  # 50 pixels margin at the bottom
            break

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# Right Velocity Panel (Fixed parameter errors, aligned with the left panel)
def draw_velocity_panel(display, current_velocities, joints):
    panel_x = display[0] - 330  # 330 pixels width reserved on the right
    panel_y = display[1] - 60  # Aligned with the top of the Position panel
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

    # Calculate total width of data columns
    joint_name_col_start = panel_x + 10
    X_COL_START = joint_name_col_start + 120
    Y_COL_START = X_COL_START + 62
    Z_COL_START = Y_COL_START + 60
    data_column_width = Z_COL_START - joint_name_col_start + 60  # Assume Z column data width is 60, adjust as needed

    # Calculate horizontal center position for the title
    title_text = "All Joints - Velocity (m/s)"
    title_width = len(title_text) * 8  # Assume character width is 8, adjust as needed
    title_x = joint_name_col_start + (data_column_width - title_width) // 2

    # Draw panel title
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font)
    current_y = panel_y - line_height

    # Iterate joints by custom order
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_velocities:
            continue
        # Draw joint name
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font)
        # Convert cm/s to m/s, keep 4 decimal places
        vel = current_velocities[joint_name] / 100
        x_text = f"X:{vel[0]:.4f}"
        y_text = f"Y:{vel[1]:.4f}"
        z_text = f"Z:{vel[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font)
        current_y -= line_height
        if current_y < 50:  # 50 pixels margin at the bottom
            break

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# Draw Axes and Labels
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

# Draw Grid
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

# Draw 2D Text
def draw_text_2d(x, y, text, color, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(*color)
    glWindowPos2d(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))

# -------------------------- Optimization: Joint Trajectory Drawing Function (Solid line -> Green small dots, only visible during playback) --------------------------
def draw_joint_trajectories(show_trajectories, selected_joints, joint_trajectories, joint_colors, current_frame):
    if not show_trajectories or not selected_joints or not joint_trajectories:
        return
    
    glDisable(GL_DEPTH_TEST)  # Trajectory displays above the skeleton
    glColor3f(0.0, 1.0, 0.0)  # Fixed green color
    glPointSize(1.0)          # Point size (1 pixel, subtle)
    
    for joint_name in selected_joints:
        if joint_name not in joint_trajectories:
            continue
        trajectory = joint_trajectories[joint_name]
        if len(trajectory) < 1:
            continue
        
        # Only draw points up to and including the current frame (accumulates as playback progresses)
        glBegin(GL_POINTS)
        for i in range(0, current_frame + 1):
            if i >= len(trajectory):
                break
            pos = trajectory[i]
            glVertex3f(*pos)
        glEnd()
    
    glEnable(GL_DEPTH_TEST)

# -------------------------- Trajectory Settings Window (Joint multi-select + switch) --------------------------
def open_trajectory_settings(joints, all_joint_positions, show_trajectories, selected_joints, joint_trajectories, joint_colors):
    if not joints or not all_joint_positions:
        tk.Tk().withdraw()
        tk.messagebox.showwarning("Hint", "Please load a BVH file first!")
        return
    
    # Create new Tkinter window
    settings_win = tk.Tk()
    settings_win.title("Joint Trajectory Settings")
    settings_win.geometry("300x400")
    
    # Trajectory master switch
    show_var = IntVar(value=1 if show_trajectories else 0)
    show_checkbox = Checkbutton(
        settings_win,
        text="Show Joint Trajectories",
        variable=show_var,
        font=("Arial", 10)
    )
    show_checkbox.pack(pady=10, anchor="w", padx=20)
    
    # Joint multi-select list
    tk.Label(settings_win, text="Select Joints (multiple allowed):", font=("Arial", 10)).pack(anchor="w", padx=20)
    listbox = Listbox(
        settings_win,
        selectmode=tk.MULTIPLE,  # Enable multi-select
        font=("Arial", 9),
        height=15
    )
    # Load all joint names (by custom order)
    joint_names = [name for name in CUSTOM_JOINT_ORDER if name in joints]
    for idx, name in enumerate(joint_names):
        listbox.insert(idx, name)
        # Pre-select joints that were previously selected
        if name in selected_joints:
            listbox.selection_set(idx)
    listbox.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
    
    # Confirm button logic
    def confirm_settings():
        nonlocal show_trajectories, selected_joints, joint_trajectories, joint_colors
        
        # 1. Update trajectory switch state
        show_trajectories = bool(show_var.get())
        
        # 2. Update selected joints
        selected_indices = listbox.curselection()
        selected_joints = [joint_names[idx] for idx in selected_indices]
        
        # 3. Build trajectory data for selected joints (extract from all_joint_positions)
        joint_trajectories.clear()
        for joint_name in selected_joints:
            trajectory = []
            for frame_pos in all_joint_positions:
                # Extract the position of this joint in the current frame
                pos = frame_pos.get(joint_name, np.zeros(3))
                trajectory.append(pos)
            joint_trajectories[joint_name] = trajectory
        
        # 4. Assign a unique color to each selected joint (HSV color wheel for distinctness)
        joint_colors.clear()
        num_joints = len(selected_joints)
        for idx, joint_name in enumerate(selected_joints):
            hue = idx / num_joints if num_joints > 0 else 0  # Even distribution of hue
            saturation = 0.7  # Saturation
            value = 0.8  # Brightness
            # Convert HSV to RGB (simplified calculation)
            color = colorsys.hsv_to_rgb(hue, saturation, value)
            joint_colors[joint_name] = color
        
        settings_win.destroy()
    
    # Confirm button
    confirm_btn = tk.Button(
        settings_win,
        text="Confirm",
        command=confirm_settings,
        font=("Arial", 10),
        width=10
    )
    confirm_btn.pack(pady=10)
    
    settings_win.mainloop()
    # Return updated data (for variable synchronization in main function)
    return show_trajectories, selected_joints, joint_trajectories, joint_colors

# Draw 2D UI
def draw_2d_ui(display, current_frame, frames, is_playing, fps, load_btn_rect, export_btn_rect, trajectory_btn_rect, play_pause_btn_rect, timeline_rect, bvh_fps=0, bvh_total_frames=0):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    # 1. Load Button
    load_x = load_btn_rect.x
    load_y = display[1] - load_btn_rect.y - load_btn_rect.height
    load_width = load_btn_rect.width
    load_height = load_btn_rect.height
    draw_rectangle(load_x, load_y, load_width, load_height, (0.8, 0.8, 0.8))
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
    
    # 2. Export Button
    export_x = export_btn_rect.x
    export_y = display[1] - export_btn_rect.y - export_btn_rect.height
    export_width = export_btn_rect.width
    export_height = export_btn_rect.height
    draw_rectangle(export_x, export_y, export_width, export_height, (0.8, 0.8, 0.8))
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
    
    # 3. Trajectory Settings Button
    traj_x = trajectory_btn_rect.x
    traj_y = display[1] - trajectory_btn_rect.y - trajectory_btn_rect.height
    traj_width = trajectory_btn_rect.width
    traj_height = trajectory_btn_rect.height
    draw_rectangle(traj_x, traj_y, traj_width, traj_height, (0.8, 0.8, 0.8))
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
    
    # Timeline drawing
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
    
    # Play/Pause Button
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
    
    # BVH Data Information Display
    if bvh_fps > 0 and bvh_total_frames > 0:
        bvh_info_text = f"BVH Data: {bvh_fps:.0f}HZ, {bvh_total_frames - 1}Frames"
        draw_text_2d(10, 30, bvh_info_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    # Software FPS display
    fps_text = f"BVH Viewer: {int(fps)} FPS"
    draw_text_2d(10, 10, fps_text, (0.0, 0.0, 0.0), font=GLUT_BITMAP_HELVETICA_12)
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# Draw Joint Angle Label
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

# Unproject
def unproject(winX, winY, winZ=0.0):
    modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
    projection = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)
    obj_point = gluUnProject(winX, winY, winZ, modelview, projection, viewport)
    return obj_point

# Export Data Dialog
def export_data_dialog(all_joints, all_positions, all_velocities, all_accelerations, all_anatomical_angles):
    root = tk.Tk()
    root.withdraw()
    # Pop up save dialog, default CSV format
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv", 
        filetypes=[("CSV files", "*.csv")],
        title="Export All Joint Angle Data"
    )
    root.destroy()
    
    if not file_path:
        print("Data export cancelled.")
        return
    try:
        # Use utf-8-sig encoding to solve Chinese/special character (°) encoding issues, compatible with Excel
        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # -------------------------- 1. Build CSV Header --------------------------
            header = ['Frame']  # First column: Frame Number
            # 1.1 Add Joint Position/Velocity/Acceleration (by custom order)
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
            # 1.2 Add All Joint Angles (automatically collected, includes full body + fingers)
            angle_keys = set()
            for frame_angles in all_anatomical_angles:
                if frame_angles:
                    angle_keys.update(frame_angles.keys())
            angle_keys = sorted(angle_keys)  # Sort to ensure consistent export order
            for angle_key in angle_keys:
                header.append(f'{angle_key}(°)')  # Add angle unit for clarity
            
            # Write header
            writer.writerow(header)
            
            # -------------------------- 2. Write Data Frame by Frame --------------------------
            num_frames = len(all_positions)
            for frame_idx in range(num_frames):
                row = [frame_idx + 1]  # Frame number starts at 1 (standard convention)
                
                # 2.1 Write Position/Velocity/Acceleration (Unit conversion: cm → m)
                for joint_name in joint_names:
                    # Get joint information from per-frame data, fill with 0 if no data
                    pos = all_positions[frame_idx].get(joint_name, np.zeros(3)) / 100
                    vel = all_velocities[frame_idx].get(joint_name, np.zeros(3)) / 100
                    accel = all_accelerations[frame_idx].get(joint_name, np.zeros(3)) / 100
                    # Keep 4 decimal places to avoid data redundancy
                    row.extend([round(val, 4) for val in pos])
                    row.extend([round(val, 4) for val in vel])
                    row.extend([round(val, 4) for val in accel])
                
                # 2.2 Write All Joint Angles (includes full body + fingers)
                current_frame_angles = all_anatomical_angles[frame_idx] if frame_idx < len(all_anatomical_angles) else {}
                for angle_key in angle_keys:
                    # Fill with NaN if no angle data (for easier later data analysis)
                    angle_val = current_frame_angles.get(angle_key, float('nan'))
                    row.append(angle_val)
                
                # Write current frame data
                writer.writerow(row)
            
            # Export success log (shows number of exported angles for verification)
            print(f"✅ Data successfully exported to: {file_path}")
            print(f"📊 Export content:")
            print(f"  - Number of Joints: {len(joint_names)} (Full body + fingers)")
            print(f"  - Number of Angles: {len(angle_keys)} (All adjacent joint angles)")
            print(f"  - Total Frames: {num_frames} frames")
    
    except Exception as e:
        print(f"Data export failed: {e}")

# Main function
def main():
    pygame.init()
    glutInit()
    
    # -------------------------- Key Modification: Read screen resolution and calculate 3/4 window size --------------------------
    # 1. Get the original resolution of the current computer screen (use available screen size for better accuracy, excluding taskbar etc.)
    screen_info = pygame.display.Info()  # Get screen info object
    original_screen_width = screen_info.current_w  # Available screen width (pixels)
    original_screen_height = screen_info.current_h  # Available screen height (pixels)
    
    # 2. Calculate target window size: 3/4 of the original resolution (round down to avoid fractional pixels)
    target_display_width = int(original_screen_width * 0.75)
    target_display_height = int(original_screen_height * 0.75)
    display = (target_display_width, target_display_height)  # Final window size
    
    # 3. Initialize window (retain DOUBLEBUF, OPENGL, RESIZABLE features)
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption("BVH 3D Viewer")  # Window title
    
    # -------------------------- New: Set Title Bar/Thumbnail Logo (retained original code, just adapting to the new window) --------------------------
    try:
        app_icon = pygame.image.load("app_icon.ico")
        pygame.display.set_icon(app_icon)
    except Exception as e:
        print(f"Failed to load title bar icon: {e} (Please ensure app_icon.ico is in the script directory)")
    
    # -------------------------- View Projection Adaptation: Calculate aspect ratio based on new window size --------------------------
    glClearColor(1.0, 1.0, 1.0, 1.0) 
    glEnable(GL_DEPTH_TEST)
    
    # Key: Use the calculated window size to get the aspect ratio (ensure OpenGL projection adapts to the 3/4 window)
    aspect_ratio = display[0] / display[1]  # Width/Height ratio, used for perspective projection
    
    # -------------------------- The following is original code (only retaining heavily related initialization logic, no changes needed) --------------------------
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
    
    # Trajectory related variables (retained original code)
    show_trajectories = False
    selected_joints = []
    joint_trajectories = {}
    joint_colors = {}
    
    # Button position initialization (retained original code, will dynamically adjust with window size)
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
    
    # -------------------------- View Reset Function Adaptation (Ensure correct perspective after scaling) --------------------------
    def reset_view():
        nonlocal aspect_ratio # Must be non-local if aspect_ratio is defined outside and modified within another scope
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Key: Use the calculated aspect_ratio (3/4 window's aspect ratio) to set the perspective projection
        gluPerspective(45, aspect_ratio, 0.1, 1000.0)  # 45° FoV, near clip 0.1, far clip 1000
        glTranslatef(0.0, -100.0, -300)  # Initial camera position (retained original code, fits skeleton display)
    
    # The following toggle_play_pause, load_file_dialog, and subsequent logic do not require changes...
        
    def toggle_play_pause():
        nonlocal is_playing
        is_playing = not is_playing
    
    def load_file_dialog():
        nonlocal root_joint, joints, motion_data, frames, frame_time, current_frame, all_joint_positions, all_joint_velocities, all_joint_accelerations, all_anatomical_angles, joint_roms, bvh_fps, bvh_total_frames
        # Clear old trajectory data when loading a new file
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
                
                print(f"Successfully loaded file: {file_path}")
                print(f"BVH Data: {bvh_fps:.0f}HZ, {bvh_total_frames - 1}Frames")
                print(f"Frame Time: {frame_time}s")
                
                all_joint_positions, all_joint_velocities, all_joint_accelerations, all_anatomical_angles = calculate_kinematics(joints, motion_data, frame_time)
                print("Kinematics data calculation complete.")
            else:
                print(f"File parsing failed: {file_path}")
                bvh_fps = 0.0
                bvh_total_frames = 0
    
    reset_view()
    running = True
    while running:
        # Play button position update
        play_btn_size = 20
        play_btn_x = (display[0] - play_btn_size) // 2
        play_btn_y = display[1] - 30 - play_btn_size
        play_pause_btn_rect.update(play_btn_x, play_btn_y, play_btn_size, play_btn_size)
        
        # Timeline position update
        timeline_width = display[0] - 200
        timeline_x = (display[0] - timeline_width) // 2
        timeline_height = 8
        timeline_y = play_btn_y - 10 - timeline_height
        timeline_rect.update(timeline_x, timeline_y, timeline_width, timeline_height)
        
        # Event Handling (Optimized mouse operation logic)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
 
            # Window Resize Event (Fixes black screen + removes GLUT function to prevent crash)
            elif event.type == pygame.VIDEORESIZE:
                # Update window size and aspect ratio
                display = (event.w, event.h)
                aspect_ratio = event.w / event.h  # Real-time aspect ratio update
                
                # Rebuild window: retain DOUBLEBUF + hardware acceleration, prevent buffer clearing
                pygame.display.set_mode(
                    display, 
                    DOUBLEBUF | OPENGL | pygame.RESIZABLE | pygame.HWSURFACE  # Hardware acceleration reduces black screen
                )
                
                # Reset view + force immediate redraw (using native OpenGL commands to replace glutPostRedisplay)
                reset_view()
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  # Clear old buffer
                glFlush()  # Force OpenGL to execute clear command
                pygame.display.flip()  # Immediately refresh Pygame window to prevent black screen
                
                # Synchronize UI control positions (prevent UI misalignment after scaling)
                play_btn_x = (display[0] - play_btn_size) // 2
                play_btn_y = display[1] - 30 - play_btn_size
                play_pause_btn_rect.update(play_btn_x, play_btn_y, play_btn_size, play_btn_size)
                
                timeline_width = display[0] - 200
                timeline_x = (display[0] - timeline_width) // 2
                timeline_y = play_btn_y - 10 - timeline_height
                timeline_rect.update(timeline_x, timeline_y, timeline_width, timeline_height)
            # Mouse Button Down Event (Left-click pan, Middle-click reset, Right-click rotate, Scroll wheel zoom based on view)
            if event.type == pygame.MOUSEBUTTONDOWN:
                last_mouse_pos = event.pos
                
                if event.button == 1:
                    left_button_down = True  # Left-click pan state
                elif event.button == 2:
                    reset_view()  # Middle-click resets to initial view
                elif event.button == 3:
                    middle_button_down = True  # Right-click rotate state
                elif event.button == 4:
                    # Scroll up: Zoom in based on current view (closer to screen center)
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    # Extract camera forward direction (3rd column of view matrix, negative direction is camera forward)
                    cam_forward = np.array([-view_matrix[2][0], -view_matrix[2][1], -view_matrix[2][2]])
                    cam_forward = cam_forward / np.linalg.norm(cam_forward)  # Normalize direction
                    glTranslatef(*(cam_forward * 10.0))  # Move along forward direction (Zoom in)
                elif event.button == 5:
                    # Scroll down: Zoom out based on current view (further from screen center)
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    cam_forward = np.array([-view_matrix[2][0], -view_matrix[2][1], -view_matrix[2][2]])
                    cam_forward = cam_forward / np.linalg.norm(cam_forward)
                    glTranslatef(*(cam_forward * -10.0))  # Move against forward direction (Zoom out)
                
                # Button click logic (Load/Export etc.) remains unchanged...
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
            # Mouse Button Up Event
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Left-click release: Stop panning (original logic remains unchanged)
                    left_button_down = False
                    timeline_dragging = False
                elif event.button == 3:
                    # Right-click release: Stop rotation (original middle-click release logic)
                    middle_button_down = False  # Consistent with down state variable
            
            # Mouse Motion Event (Left-click pan, Right-click horizontal rotation around mannequin, Timeline drag)
            if event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                rel_x, rel_y = mouse_x - last_mouse_pos[0], mouse_y - last_mouse_pos[1]
                
                # Left-click pan (original logic remains unchanged, retained)
                if left_button_down and not timeline_dragging:
                    view_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
                    right_axis = np.array([view_matrix[0][0], view_matrix[1][0], view_matrix[2][0]])
                    up_axis = np.array([view_matrix[0][1], view_matrix[1][1], view_matrix[2][1]])
                    translate_x = rel_x * 0.2 * right_axis
                    translate_y = -rel_y * 0.2 * up_axis
                    glTranslatef(translate_x[0], translate_y[1], translate_x[2] + translate_y[2])
                
                # Right-click drag: Horizontal rotation only around the mannequin (Hips joint) (simplified logic)
                if middle_button_down and joints:  # Ensure joint data is loaded
                    try:
                        # 1. Get the world coordinates of the mannequin's root joint (Hips, pelvis) (rotation center)
                        # Fallback to the first joint if 'Hips' doesn't exist (to support different BVH skeleton names)
                        target_joint = joints.get('Hips', joints[next(iter(joints.keys()))])
                        joint_world_pos = target_joint.matrix[:3, 3]  # Hips world position
                        
                        # 2. Rotation logic: Translate to Hips center → Horizontal rotation → Translate back
                        glTranslatef(*joint_world_pos)  # Move Hips to world origin (rotation center)
                        # Only horizontal rotation (around Y-axis, effective for left/right drag, ignored for up/down drag), speed 0.15 is smoother
                        glRotatef(rel_x * 0.15, 0, 1, 0)  # Only respond to mouse X-axis offset (left/right drag)
                        glTranslatef(-joint_world_pos[0], -joint_world_pos[1], -joint_world_pos[2])  # Translate back to original position
                    except Exception as e:
                        print(f"Exception in rotating around mannequin: {e}")
                        pass
                
                # Timeline Drag (original logic remains unchanged, retained)
                if timeline_dragging and frames > 0:
                    mouse_pos_x = event.pos[0]
                    progress_x = min(max(mouse_pos_x, timeline_rect.x), timeline_rect.right)
                    current_frame = int((progress_x - timeline_rect.x) / timeline_rect.width * (frames - 1))
                
                last_mouse_pos = (mouse_x, mouse_y)
            
            # Keyboard Event
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    toggle_play_pause()  # Original spacebar play/pause logic remains unchanged
                if event.key == pygame.K_LEFT and frames > 0:
                    current_frame = max(0, current_frame - 1)  # Original left arrow frame step back
                if event.key == pygame.K_RIGHT and frames > 0:
                    current_frame = min(frames - 1, current_frame + 1)  # Original right arrow frame step forward
                # New: F key triggers view reset
                if event.key == pygame.K_f:
                    reset_view()
        
        # Rendering Process (Optimized for real-time when scaling)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glFlush()  # New: Force clear buffer command to execute instantly, preventing black screen due to delay
        glMatrixMode(GL_MODELVIEW)
        
        glPushMatrix()
        draw_grid()
        draw_axes_and_labels()
        
        if root_joint and len(motion_data) > 0:
            # Update Joint Matrix (original logic remains unchanged)
            if is_playing:
                update_joint_matrices(root_joint, motion_data[current_frame], joints)
                current_frame = (current_frame + 1) % frames
            else:
                update_joint_matrices(root_joint, motion_data[current_frame], joints)
            
            # Draw Skeleton (original function, unchanged)
            draw_custom_skeleton(joints)  

            # -------------------------- Replaced Angle Display Code (includes upper/forearm + back bend + head down) --------------------------
            # 1. Upper Arm - Forearm Angle (Naming corresponds to RightUpArm_RightForeArm, Red=Right, Blue=Left)
            # Right Upper Arm - Right Forearm: Vertex=RightArm (Upper Arm), Vector 1=RightShoulder→RightArm, Vector 2=RightForeArm→RightArm
            draw_joint_angle_label(
                joint1_name='RightShoulder',  # Vector 1 start (Right Shoulder)
                joint2_name='RightArm',       # Angle Vertex (Right Upper Arm, corresponding to RightUpArm)
                joint3_name='RightForeArm',   # Vector 2 end (Right Forearm)
                joints=joints, 
                display=display, 
                arc_radius=3.3, 
                color=(0.9, 0.2, 0.2)  # Red, consistent with original style
            )
            # Left Upper Arm - Left Forearm: Vertex=LeftArm (Upper Arm), Vector 1=LeftShoulder→LeftArm, Vector 2=LeftForeArm→LeftArm
            draw_joint_angle_label(
                joint1_name='LeftShoulder',   # Vector 1 start (Left Shoulder)
                joint2_name='LeftArm',        # Angle Vertex (Left Upper Arm, corresponding to LeftUpArm)
                joint3_name='LeftForeArm',    # Vector 2 end (Left Forearm)
                joints=joints, 
                display=display, 
                arc_radius=3.3, 
                color=(0.2, 0.2, 0.9)  # Blue, consistent with original style
            )

            # 2. Back Bend Angle (Green, Vertex=Spine (lower spine), Vector 1=Hips→Spine, Vector 2=Spine2→Spine)
            draw_joint_angle_label(
                joint1_name='Hips',       # Vector 1 start (Pelvis, lower body reference)
                joint2_name='Spine',      # Angle Vertex (Lower Spine, bending point)
                joint3_name='Spine2',     # Vector 2 end (Upper Spine, upper body reference)
                joints=joints, 
                display=display, 
                arc_radius=5.0,           # Slightly larger radius to avoid overlap with other angles
                color=(0.2, 0.9, 0.2)     # Green, distinguishes from other angles
            )

            # 3. Head Down Angle (Yellow/Green, Vertex=Neck (neck), Vector 1=Spine2→Neck, Vector 2=Head→Neck)
            draw_joint_angle_label(
                joint1_name='Spine2',     # Vector 1 start (Upper Spine, torso reference)
                joint2_name='Neck',       # Angle Vertex (Neck, bending point for head down)
                joint3_name='Head',       # Vector 2 end (Head, head reference)
                joints=joints, 
                display=display, 
                arc_radius=3.3,           # Radius adapted to the neck area size
                color=(0.2, 0.9, 0.2)     # Yellow/Green, noticeable and non-conflicting
            )

            # (Optional) Retain other necessary angles (e.g., hip, knee), can be removed if not needed
            draw_joint_angle_label('Hips', 'RightUpLeg', 'RightLeg', joints, display, arc_radius=5.0, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('RightArm', 'RightForeArm', 'RightHand', joints, display, arc_radius=3.3, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('LeftArm', 'LeftForeArm', 'LeftHand', joints, display, arc_radius=3.3, color=(0.2, 0.2, 0.9))
            draw_joint_angle_label('RightUpLeg', 'RightLeg', 'RightFoot', joints, display, arc_radius=5.0, color=(0.9, 0.2, 0.2))
            draw_joint_angle_label('Hips', 'LeftUpLeg', 'LeftLeg', joints, display, arc_radius=5.0, color=(0.2, 0.2, 0.9))
            draw_joint_angle_label('LeftUpLeg', 'LeftLeg', 'LeftFoot', joints, display, arc_radius=5.0, color=(0.2, 0.2, 0.9))
            # -------------------------- Replaced Angle Display Code End --------------------------

            # Trajectory Drawing Code (original, unchanged)
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
        
        # Adjust UI coordinates
        play_btn_y_bottom_up = 30
        timeline_y_bottom_up = play_btn_y_bottom_up + play_btn_size + 10
        timeline_rect_opengl = pygame.Rect(timeline_rect.x, timeline_y_bottom_up, timeline_rect.width, timeline_rect.height)
        play_pause_btn_rect_opengl = pygame.Rect(play_pause_btn_rect.x, play_btn_y_bottom_up, play_pause_btn_rect.width, play_pause_btn_rect.height)
        
        # Draw 2D UI
        draw_2d_ui(
            display, 
            current_frame, 
            frames, 
            is_playing, 
            fps, 
            load_btn_rect,   # Load Button
            export_btn_rect, # Export Button
            trajectory_btn_rect,  # Trajectory Settings Button
            play_pause_btn_rect_opengl, 
            timeline_rect_opengl,
            bvh_fps=bvh_fps,
            bvh_total_frames=bvh_total_frames
        )
        
        # Draw Position and Velocity Panels
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