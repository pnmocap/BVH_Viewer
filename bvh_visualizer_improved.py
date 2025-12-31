# Standard library imports
import csv
import json
import math
import os
import sys
from datetime import datetime

# Third-party library imports
import colorsys
import matplotlib.pyplot as plt
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import tkinter as tk
from tkinter import filedialog, Listbox, Checkbutton, IntVar, messagebox

# Note: GLUT imports removed to avoid NullFunctionError on systems without freeglut.dll
# Using Pygame's native 2D rendering for UI and Text overlay

# ======================== Real-time Mode Integration Modules ========================
# Local module imports (motion capture and recording)
try:
    from mocap_connector import (
        MocapConnector, 
        ConnectionState, 
        CapturePhase, 
        CalibrationState
    )
    MOCAP_SDK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: MocapAPI modules not available: {e}")
    MOCAP_SDK_AVAILABLE = False
    MocapConnector = None
    ConnectionState = None
    CapturePhase = None
    CalibrationState = None

try:
    from axis_studio_connector import (
        AxisStudioConnector, 
        AxisStudioConnectionState
    )
    AXIS_STUDIO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Axis Studio connector not available: {e}")
    AXIS_STUDIO_AVAILABLE = False
    AxisStudioConnector = None
    AxisStudioConnectionState = None

try:
    from recording_manager import RecordingManager
    RECORDING_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Recording manager not available: {e}")
    RECORDING_AVAILABLE = False
    RecordingManager = None


# ======================== UI Configuration Constants ========================
# These constants can be easily modified for future UI redesign without changing logic

class UIConfig:
    """UI layout and appearance configuration"""
    
    # Window settings
    WINDOW_SCALE_FACTOR = 0.75  # Window size = 75% of screen resolution
    DEFAULT_TARGET_FPS = 60
    
    # Camera settings
    CAMERA_FOV = 45  # Field of view in degrees
    CAMERA_NEAR_CLIP = 0.1
    CAMERA_FAR_CLIP = 1000.0
    CAMERA_INIT_Y = -100.0
    CAMERA_INIT_Z = -300.0
    
    # Mouse control sensitivity
    MOUSE_PAN_SENSITIVITY = 0.2
    MOUSE_ROTATE_SENSITIVITY = 0.15
    MOUSE_ZOOM_STEP = 10.0
    
    # UI Colors (RGB tuples 0-1)
    COLOR_BACKGROUND = (1.0, 1.0, 1.0, 1.0)  # White
    COLOR_MODE_OFFLINE = (0.8, 0.8, 0.8)  # Gray
    COLOR_MODE_MOCAP = (0.4, 0.8, 0.4)  # Green
    COLOR_MODE_SECAP = (0.4, 0.7, 0.9)  # Blue
    COLOR_CONNECTED = (0.4, 0.8, 0.4)  # Green
    COLOR_RECORDING = (0.9, 0.3, 0.3)  # Red
    COLOR_TEXT_BLACK = (0.0, 0.0, 0.0)
    
    # Button dimensions
    BUTTON_WIDTH = 80
    BUTTON_HEIGHT = 30
    BUTTON_MARGIN = 10
    
    # Text rendering
    FONT_SIZE_DEFAULT = 12
    FONT_SIZE_TITLE = 16


class AppMode:
    """Application mode enumeration"""
    OFFLINE = "offline"     # 离线模式 (加载BVH文件)
    MOCAP = "mocap"         # Mocap模式 (MocapAPI 直接连接动捕设备)
    SECAP = "secap"         # Secap模式 (Axis Studio BVH 广播)


class AppState:
    """
    Global application state manager.
    
    This class maintains the current mode (Offline/Mocap/Secap) and manages
    the lifecycle of various connectors and managers.
    
    Attributes:
        mode: Current application mode (AppMode.OFFLINE/MOCAP/SECAP)
        mocap_connector: Connection manager for Mocap mode
        axis_studio_connector: Connection manager for Secap mode
        recording_manager: Shared recording manager for both real-time modes
        realtime_joints: Joint data for real-time rendering
    """
    mode = AppMode.OFFLINE
    
    # Mocap 模式连接器
    mocap_connector = None
    
    # Secap 模式连接器
    axis_studio_connector = None
    
    # 录制管理器（两种实时模式共用）
    recording_manager = None
    
    # 实时模式相关的关节数据（用于渲染）
    realtime_joints = {}
    
    @classmethod
    def init_mocap_mode(cls):
        """
        Initialize Mocap mode modules.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not MOCAP_SDK_AVAILABLE:
            print("Error: MocapAPI SDK not available")
            return False
        if cls.mocap_connector is None:
            cls.mocap_connector = MocapConnector()
        if cls.recording_manager is None and RECORDING_AVAILABLE:
            cls.recording_manager = RecordingManager()
        return True
    
    @classmethod
    def init_secap_mode(cls):
        """
        Initialize Secap mode modules.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not AXIS_STUDIO_AVAILABLE:
            print("Error: Axis Studio connector not available")
            return False
        if cls.axis_studio_connector is None:
            cls.axis_studio_connector = AxisStudioConnector()
        if cls.recording_manager is None and RECORDING_AVAILABLE:
            cls.recording_manager = RecordingManager()
        return True
    
    @classmethod
    def cleanup(cls):
        """
        Clean up all resources (connections, listeners, etc.).
        
        This method should be called before application exit to ensure
        proper cleanup of network connections and resources.
        """
        # 清理 Mocap 连接
        if cls.mocap_connector and cls.mocap_connector.is_connected:
            cls.mocap_connector.disconnect()
        # 清理 Axis Studio 连接
        if cls.axis_studio_connector and cls.axis_studio_connector.is_listening:
            cls.axis_studio_connector.stop_listening()
# ======================== 实时模式集成模块结束 ========================

# ======================== 网球动作分析模块 (矩阵式交互控制版) ========================
from matplotlib.widgets import CheckButtons
import matplotlib.cm as cm # 用于生成颜色

class TennisAnalyzer:
    """网球动作分析器 - 支持多部位、多历史文件的矩阵式交互对比"""
    HISTORY_FILE = "tennis_analysis_history.json"

    # ... (euler_to_matrix, calculate_angular_velocities 等方法保持不变，为节省篇幅略去) ...
    # 请确保保留这两个核心计算方法，直接复制之前的即可，或者只替换 show_custom_plot 及其辅助部分
    # 为了方便您复制，这里完整提供修改后的类结构

    @staticmethod
    def get_analysis_options():
        """弹出对话框，获取左右手/脚的配置 (代码保持不变)"""
        options = {}
        dialog = tk.Tk()
        dialog.title("Analysis Settings")
        dialog.geometry("300x250")
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 250) // 2
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="Racket Hand (击球手):", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        hand_var = tk.StringVar(value="Right")
        frame_hand = tk.Frame(dialog)
        frame_hand.pack()
        tk.Radiobutton(frame_hand, text="Right Hand", variable=hand_var, value="Right").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_hand, text="Left Hand", variable=hand_var, value="Left").pack(side=tk.LEFT, padx=10)

        tk.Label(dialog, text="Drive Leg (发力腿):", font=("Arial", 10, "bold")).pack(pady=(15, 5))
        leg_var = tk.StringVar(value="Right")
        frame_leg = tk.Frame(dialog)
        frame_leg.pack()
        tk.Radiobutton(frame_leg, text="Right Leg", variable=leg_var, value="Right").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(frame_leg, text="Left Leg", variable=leg_var, value="Left").pack(side=tk.LEFT, padx=10)

        def on_confirm():
            options['hand'] = hand_var.get()
            options['leg'] = leg_var.get()
            dialog.destroy()
        def on_cancel():
            options.clear()
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Analyze", command=on_confirm, bg="#ddffdd", width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Cancel", command=on_cancel, bg="#ffdddd", width=10).pack(side=tk.LEFT, padx=10)
        dialog.wait_window()
        return options

    @staticmethod
    def euler_to_matrix(angles, order):
        rads = np.radians(angles)
        def get_rot_mat(axis, theta):
            c, s = np.cos(theta), np.sin(theta)
            if axis == 'Xrotation': return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
            elif axis == 'Yrotation': return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
            elif axis == 'Zrotation': return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
            return np.eye(3)
        R = np.eye(3)
        for i, axis_name in enumerate(order):
            R = R @ get_rot_mat(axis_name, rads[i])
        return R

    @staticmethod
    def calculate_angular_velocities(joints, motion_data, frame_time, hand_side="Right", leg_side="Right"):
        target_joints = {
            '1. Thigh': f'{leg_side}UpLeg',
            '2. Hips': 'Hips',
            '3. Chest': 'Spine2',
            '4. Arm': f'{hand_side}Arm',
            '5. Forearm': f'{hand_side}ForeArm',
            '6. Hand': f'{hand_side}Hand'
        }
        num_frames = len(motion_data)
        velocities = {k: [] for k in target_joints.keys()}
        
        joint_info = {}
        for label, name in target_joints.items():
            final_name = name
            if name not in joints:
                continue
            raw_channels = joints[final_name].channels
            rot_channels = [c for c in raw_channels if 'rotation' in c]
            if not rot_channels: continue
            indices = [joints[final_name].channel_indices[c] for c in rot_channels]
            joint_info[label] = {'indices': indices, 'order': rot_channels}

        for i in range(2, num_frames):
            for label, info in joint_info.items():
                curr_angles = [motion_data[i][idx] for idx in info['indices']]
                prev_angles = [motion_data[i-1][idx] for idx in info['indices']]
                R_curr = TennisAnalyzer.euler_to_matrix(curr_angles, info['order'])
                R_prev = TennisAnalyzer.euler_to_matrix(prev_angles, info['order'])
                R_diff = R_prev.T @ R_curr
                trace = np.clip(np.trace(R_diff), -1.0, 3.0)
                theta_deg = np.degrees(np.arccos((trace - 1) / 2))
                velocities[label].append(theta_deg / frame_time)

        velocities['meta_config'] = {'hand': hand_side, 'leg': leg_side}
        return velocities

    @staticmethod
    def load_history():
        if os.path.exists(TennisAnalyzer.HISTORY_FILE):
            try:
                with open(TennisAnalyzer.HISTORY_FILE, 'r') as f: return json.load(f)
            except: pass
        return []

    @staticmethod
    def save_to_history(velocities, filename="Current_Session"):
        data_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename,
            "data": velocities
        }
        history = TennisAnalyzer.load_history()
        history.append(data_entry)
        if len(history) > 50: history = history[-50:] 
        with open(TennisAnalyzer.HISTORY_FILE, 'w') as f: json.dump(history, f)
        return history

    @staticmethod
    def open_history_manager():
        history = TennisAnalyzer.load_history()
        win = tk.Tk()
        win.title("Tennis Analysis Manager")
        win.geometry("600x500")

        lbl = tk.Label(win, text="Select records to compare.\nLAST selected is the 'Main Subject'.", font=("Arial", 10), pady=10)
        lbl.pack()

        frame_list = tk.Frame(win)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar = tk.Scrollbar(frame_list); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = Listbox(frame_list, selectmode=tk.MULTIPLE, yscrollcommand=scrollbar.set, font=("Courier New", 10))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)

        def refresh_list():
            listbox.delete(0, tk.END)
            for i, entry in enumerate(reversed(history)):
                config = entry['data'].get('meta_config', {'hand':'?', 'leg':'?'})
                display_text = f"[{entry['timestamp']}] {entry['filename']} (H:{config['hand']}/L:{config['leg']})"
                listbox.insert(tk.END, display_text)
            if listbox.size() > 0: listbox.selection_set(0)

        refresh_list()

        btn_frame = tk.Frame(win, pady=10)
        btn_frame.pack(fill=tk.X)

        def delete_selected():
            nonlocal history
            selected_indices = listbox.curselection()
            if not selected_indices: return
            indices_to_delete = [len(history) - 1 - i for i in selected_indices]
            indices_to_delete.sort(reverse=True)
            if not messagebox.askyesno("Confirm", f"Delete {len(indices_to_delete)} records?"): return
            for idx in indices_to_delete:
                if 0 <= idx < len(history): del history[idx]
            with open(TennisAnalyzer.HISTORY_FILE, 'w') as f: json.dump(history, f)
            refresh_list()

        def plot_selected():
            selected_ui_indices = listbox.curselection()
            if not selected_ui_indices: return
            data_indices = [len(history) - 1 - i for i in selected_ui_indices]
            data_indices.sort()
            final_selection = [history[i] for i in data_indices]
            win.destroy()
            TennisAnalyzer.show_custom_plot(final_selection)

        tk.Button(btn_frame, text="Delete Selected", bg="#ffdddd", command=delete_selected).pack(side=tk.LEFT, padx=20)
        tk.Button(btn_frame, text="Generate Plot", bg="#ddffdd", command=plot_selected, font=("Arial", 11, "bold")).pack(side=tk.RIGHT, padx=20)
        win.mainloop()

    @staticmethod
    def show_custom_plot(entries):
        """
        绘制图表 (矩阵式交互控制版)
        - 左上：控制显示的部位 (Parts)
        - 左下：控制显示的文件 (Files)
        - 核心逻辑：Line Visible = Part_Checked AND File_Checked
        """
        if not entries: return

        # 布局：左侧两块用于Checkbox，中间图表，右侧信息
        fig = plt.figure(figsize=(16, 9))
        gs = fig.add_gridspec(2, 3, width_ratios=[0.15, 0.65, 0.2], height_ratios=[0.5, 0.5]) 
        
        # 1. 控件区域
        ax_check_parts = fig.add_subplot(gs[0, 0])
        ax_check_files = fig.add_subplot(gs[1, 0])
        ax_check_parts.axis('off'); ax_check_parts.set_title("Body Parts", fontsize=10, fontweight='bold')
        ax_check_files.axis('off'); ax_check_files.set_title("Data Sources", fontsize=10, fontweight='bold')
        
        # 2. 图表区域 (跨两行)
        ax_plot = fig.add_subplot(gs[:, 1])
        
        # 3. 文本区域 (跨两行)
        ax_text = fig.add_subplot(gs[:, 2])
        ax_text.axis('off')

        # === 数据准备 ===
        main_entry = entries[-1] # 最新的作为Current
        ref_entries = entries[:-1] # 其他作为History

        # 部位颜色配置 (仅用于 Current 数据)
        part_colors = {
            '1. Thigh': '#8B4513', '2. Hips': '#FF9900', '3. Chest': '#33CC33',
            '4. Arm': '#3366FF', '5. Forearm': '#00CCCC', '6. Hand': '#CC0000'
        }
        part_keys = list(part_colors.keys())

        # 历史文件颜色配置 (用于 History 数据)
        # 使用 colormap 生成不同的颜色
        hist_colors = plt.cm.tab10(np.linspace(0, 1, len(ref_entries))) if len(ref_entries) > 0 else []

        # === 核心：绘图并建立索引 ===
        # 结构: all_lines = [ {'line': obj, 'text': obj, 'part': 'Hand', 'file': 'Current'}, ... ]
        all_lines_data = []
        peak_info_main = {} # 用于右侧显示的Current峰值

        # A. 绘制历史数据 (所有部位)
        for i, entry in enumerate(ref_entries):
            fname = entry['filename']
            file_label = f"Hist {i+1}: {fname[:10]}.." # 缩短文件名
            color = hist_colors[i]
            
            data = entry['data']
            if not data: continue
            
            # 取第一列数据做X轴
            first_key = next(iter(data))
            frames = range(1, len(data[first_key]) + 1) if first_key in data else []

            for part in part_keys:
                if part in data and data[part]:
                    vals = data[part]
                    # 确保帧数匹配
                    xs = range(1, len(vals)+1)
                    plt.sca(ax_plot)
                    # 历史数据用虚线，统一颜色
                    l, = plt.plot(xs, vals, linestyle='--', color=color, alpha=0.6, linewidth=1)
                    
                    # 记录对象
                    all_lines_data.append({
                        'lines': [l], # 可能还会有别的元素
                        'part': part,
                        'file': file_label
                    })

        # B. 绘制当前数据 (Main)
        current_label = "Current (Main)"
        curr_data = main_entry['data']
        if curr_data:
            first_key = next(iter(curr_data))
            # 兼容：如果数据里没有meta_config等key
            valid_keys = [k for k in curr_data.keys() if k in part_colors]
            if valid_keys:
                max_len = len(curr_data[valid_keys[0]])
                frames = range(1, max_len + 1)

                for part in part_keys:
                    if part in curr_data and curr_data[part]:
                        vals = curr_data[part]
                        
                        max_val = max(vals)
                        max_frame = vals.index(max_val) + 1
                        peak_info_main[part] = (max_frame, max_val)
                        
                        line_color = part_colors[part]
                        
                        plt.sca(ax_plot)
                        l, = plt.plot(frames, vals, label=part, color=line_color, linewidth=2.5)
                        p, = plt.plot(max_frame, max_val, 'o', color=line_color, markersize=6)
                        
                        # 标签错位
                        y_offset = 15 if 'Hand' in part or 'Arm' in part else 25
                        t = plt.annotate(
                            f'{int(max_val)}\nF{max_frame}', 
                            xy=(max_frame, max_val), xytext=(0, y_offset), 
                            textcoords='offset points', ha='center', fontsize=8, fontweight='bold',
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=line_color, alpha=0.9)
                        )
                        
                        all_lines_data.append({
                            'lines': [l, p, t],
                            'part': part,
                            'file': current_label
                        })

        # === C. 创建 CheckButtons ===
        
        # 1. 部位开关
        check_parts = CheckButtons(ax_check_parts, part_keys, [True]*len(part_keys))
        # 设置颜色以便区分
        for i, lbl in enumerate(check_parts.labels):
            lbl.set_color(part_colors.get(lbl.get_text(), 'black'))
            lbl.set_fontsize(8)

        # 2. 文件开关
        file_labels = [current_label] + [f"Hist {i+1}: {e['filename'][:10]}.." for i, e in enumerate(ref_entries)]
        check_files = CheckButtons(ax_check_files, file_labels, [True]*len(file_labels))
        # 设置颜色
        check_files.labels[0].set_fontweight('bold') # Current 加粗
        for i, lbl in enumerate(check_files.labels[1:]): # History 设为对应颜色
            lbl.set_color(hist_colors[i])
            lbl.set_fontsize(8)

        # === D. 交互回调 ===
        def update_visibility(label=None):
            # 获取当前所有 CheckBox 的状态
            # check.get_status() 返回布尔值列表
            active_parts = [lbl.get_text() for lbl, state in zip(check_parts.labels, check_parts.get_status()) if state]
            active_files = [lbl.get_text() for lbl, state in zip(check_files.labels, check_files.get_status()) if state]
            
            # 遍历所有绘图对象，设置可见性
            for item in all_lines_data:
                is_visible = (item['part'] in active_parts) and (item['file'] in active_files)
                for gfx_obj in item['lines']:
                    gfx_obj.set_visible(is_visible)
            
            plt.draw()

        check_parts.on_clicked(update_visibility)
        check_files.on_clicked(update_visibility)

        # === E. 右侧信息面板 (仅显示Current) ===
        config = curr_data.get('meta_config', {})
        info_text = f"Main: {main_entry['filename'][:20]}\n"
        info_text += f"H:{config.get('hand','?')}/L:{config.get('leg','?')}\n"
        info_text += "-" * 25 + "\n"
        
        info_text += "[Peak Values]\n"
        info_text += f"{'Part':<9} {'Frm':<4} {'Vel'}\n"
        info_text += "-" * 25 + "\n"
        
        sorted_peaks = []
        for part in part_keys:
            if part in peak_info_main:
                frame, val = peak_info_main[part]
                sorted_peaks.append((part, frame))
                part_name = part.split('. ')[1]
                info_text += f"{part_name:<9} {frame:<4} {int(val)}\n"
        
        info_text += "\n[Timing Intervals]\n"
        for i in range(len(sorted_peaks) - 1):
            curr_part, curr_frame = sorted_peaks[i]
            next_part, next_frame = sorted_peaks[i+1]
            diff = next_frame - curr_frame
            p1 = curr_part.split('. ')[1]
            p2 = next_part.split('. ')[1]
            sign = "+" if diff > 0 else ""
            info_text += f"{p1}->{p2}: {sign}{diff}\n"

        ax_text.text(0, 1.0, info_text, transform=ax_text.transAxes, fontsize=10, 
                     verticalalignment='top', fontfamily='monospace')

        # 保存引用防止GC
        fig.check_parts = check_parts
        fig.check_files = check_files

        ax_plot.set_title(f"Tennis Kinetic Chain Analysis", fontsize=16)
        ax_plot.set_xlabel("Frame Index", fontsize=12)
        ax_plot.set_ylabel("Angular Velocity (deg/s)", fontsize=12)
        ax_plot.grid(True, linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.show()
# ======================== 模块结束 ========================

# 全局变量：当前加载的BVH文件路径
current_bvh_file_path = None

# Overlay Manager Class for high-performance 2D rendering
class OverlayManager:
    def __init__(self):
        self.surface = None
        self.width = 0
        self.height = 0
        self.font_cache = {}
        self.texture_id = None

    def update_display_size(self, width, height):
        if self.width != width or self.height != height:
            self.width = width
            self.height = height
            self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
            if self.texture_id is not None:
                glDeleteTextures([self.texture_id])
            self.texture_id = glGenTextures(1)

    def clear(self):
        if self.surface:
            self.surface.fill((0, 0, 0, 0))

    def draw_text(self, x, y, text, color, size=18):
        if not self.surface: return
        if size not in self.font_cache:
            try:
                self.font_cache[size] = pygame.font.SysFont("Arial", size)
            except:
                self.font_cache[size] = pygame.font.Font(None, size)
        
        font = self.font_cache[size]
        text_surf = font.render(text, True, color)
        
        # OpenGL coordinates (x, y) where y=0 is bottom.
        # Pygame coordinates (x, y) where y=0 is top.
        # Convert OpenGL y to Pygame y: y_pygame = height - y - text_height
        
        self.surface.blit(text_surf, (x, self.height - y - text_surf.get_height()))

    def render(self):
        if not self.surface: return
        
        # Use NEAREST for crisp text on overlay
        texture_data = pygame.image.tostring(self.surface, "RGBA", 1)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(self.width, 0)
        glTexCoord2f(1, 1); glVertex2f(self.width, self.height)
        glTexCoord2f(0, 1); glVertex2f(0, self.height)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glDisable(GL_BLEND)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

overlay_manager = OverlayManager()

# BVH Joint Class
class Joint:
    """
    Represents a single joint in the BVH skeleton hierarchy.
    
    Attributes:
        name (str): Joint name
        parent (Joint): Parent joint in hierarchy
        children (list): Child joints
        offset (np.ndarray): Offset from parent (3D vector)
        channels (list): Animation channels (e.g., ['Xrotation', 'Yrotation'])
        matrix (np.ndarray): 4x4 transformation matrix
        position (np.ndarray): World position
        velocity (np.ndarray): Linear velocity
        acceleration (np.ndarray): Linear acceleration
        rom (dict): Range of motion for rotational channels
        anatomical_angles (dict): Calculated anatomical angles
    """
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
    """
    Parse a BVH (BioVision Hierarchy) file.
    
    Args:
        file_path (str): Path to the BVH file
    
    Returns:
        tuple: (root_joint, joints_dict, motion_data, num_frames, frame_time)
            - root_joint (Joint): Root joint of the skeleton
            - joints_dict (dict): Dictionary mapping joint names to Joint objects
            - motion_data (list): List of frames, each frame is a list of channel values
            - num_frames (int): Total number of frames
            - frame_time (float): Time per frame in seconds
        
        Returns (None, {}, [], 0, 0) if parsing fails.
    """
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
    title_font_size = 18
    content_font_size = 12
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
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font_size)
    current_y = panel_y - line_height

    # Iterate joints by custom order
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_positions:
            continue
        # Draw joint name
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font_size)
        # Convert cm to m, keep 4 decimal places
        pos = current_positions[joint_name] / 100
        x_text = f"X:{pos[0]:.4f}"
        y_text = f"Y:{pos[1]:.4f}"
        z_text = f"Z:{pos[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font_size)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font_size)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font_size)
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
    title_font_size = 18
    content_font_size = 12
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
    draw_text_2d(title_x, panel_y, title_text, title_color, title_font_size)
    current_y = panel_y - line_height

    # Iterate joints by custom order
    for joint_name in CUSTOM_JOINT_ORDER:
        if joint_name not in joints or joint_name not in current_velocities:
            continue
        # Draw joint name
        draw_text_2d(joint_name_col_start, current_y, joint_name, content_color, content_font_size)
        # Convert cm/s to m/s, keep 4 decimal places
        vel = current_velocities[joint_name] / 100
        x_text = f"X:{vel[0]:.4f}"
        y_text = f"Y:{vel[1]:.4f}"
        z_text = f"Z:{vel[2]:.4f}"
        draw_text_2d(X_COL_START, current_y, x_text, content_color, content_font_size)
        draw_text_2d(Y_COL_START, current_y, y_text, content_color, content_font_size)
        draw_text_2d(Z_COL_START, current_y, z_text, content_color, content_font_size)
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
        draw_text_2d(x_pos_3d[0], x_pos_3d[1], "X", (1.0, 0.0, 0.0), 18)
    except ValueError:
        pass
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, axis_length, 0.0)
    glEnd()
    try:
        y_pos_3d = gluProject(0, label_offset, 0, modelview_matrix, projection_matrix, viewport)
        draw_text_2d(y_pos_3d[0], y_pos_3d[1], "Y", (0.0, 1.0, 0.0), 18)
    except ValueError:
        pass
    glColor3f(0.0, 0.0, 1.0)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, axis_length)
    glEnd()
    try:
        z_pos_3d = gluProject(0, 0, label_offset, modelview_matrix, projection_matrix, viewport)
        draw_text_2d(z_pos_3d[0], z_pos_3d[1], "Z", (0.0, 0.0, 1.0), 18)
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
def draw_text_2d(x, y, text, color, font_size=18):
    """Draw 2D text using OverlayManager"""
    # Normalize color to 0-255 for Pygame
    c = (int(color[0]*255), int(color[1]*255), int(color[2]*255))
    overlay_manager.draw_text(x, y, text, c, font_size)

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
    draw_text_2d(load_text_x, load_text_y, load_text, (0.0, 0.0, 0.0), font_size=12)
    
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
    draw_text_2d(export_text_x, export_text_y, export_text, (0.0, 0.0, 0.0), font_size=12)
    
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
    draw_text_2d(traj_text_x, traj_text_y, traj_text, (0.0, 0.0, 0.0), font_size=12)
    
    # Timeline drawing
    if frames > 0:
        draw_text_2d(timeline_rect.x - 10, timeline_rect.y, "0", (0.0, 0.0, 0.0), font_size=12)
        draw_text_2d(timeline_rect.x + timeline_rect.width + 10, timeline_rect.y, str(frames - 1), (0.0, 0.0, 0.0), font_size=12)
        frame_text = f"Frame: {current_frame}"
        draw_text_2d((display[0] - len(frame_text)*8) // 2, timeline_rect.y + timeline_rect.height + 5, frame_text, (0.0, 0.0, 0.0), font_size=12)
        
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
        draw_text_2d(10, 30, bvh_info_text, (0.0, 0.0, 0.0), font_size=12)
    # Software FPS display
    fps_text = f"BVH Viewer: {int(fps)} FPS"
    draw_text_2d(10, 10, fps_text, (0.0, 0.0, 0.0), font_size=12)
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

# ======================== 绘制实时模式UI ========================
def draw_realtime_ui(display, mode_btn_rect, connect_btn_rect, record_btn_rect, calibrate_btn_rect, export_bvh_btn_rect):
    """
    绘制实时模式相关的UI按钮和状态信息
    支持 Mocap 和 Secap 两种模式
    """
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display[0], 0, display[1], -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    
    # 1. Mode Button (模式切换按钮：Offline / Mocap / Secap)
    mode_x = mode_btn_rect.x
    mode_y = display[1] - mode_btn_rect.y - mode_btn_rect.height
    mode_width = mode_btn_rect.width
    mode_height = mode_btn_rect.height
    # 根据当前模式设置按钮颜色
    if AppState.mode == AppMode.MOCAP:
        mode_color = (0.4, 0.8, 0.4)  # 绿色表示 Mocap 模式
    elif AppState.mode == AppMode.SECAP:
        mode_color = (0.4, 0.7, 0.9)  # 蓝色表示 Secap 模式
    else:
        mode_color = (0.8, 0.8, 0.8)  # 灰色表示离线模式
    draw_rectangle(mode_x, mode_y, mode_width, mode_height, mode_color)
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(mode_x, mode_y)
    glVertex2f(mode_x + mode_width, mode_y)
    glVertex2f(mode_x + mode_width, mode_y + mode_height)
    glVertex2f(mode_x, mode_y + mode_height)
    glEnd()
    if AppState.mode == AppMode.MOCAP:
        mode_text = "Mocap"
    elif AppState.mode == AppMode.SECAP:
        mode_text = "Secap"
    else:
        mode_text = "Offline"
    mode_text_width = len(mode_text) * 8
    mode_text_height = 12
    mode_text_x = mode_x + (mode_width - mode_text_width) / 2 + 8
    mode_text_y = mode_y + (mode_height + mode_text_height) / 2 - 10
    draw_text_2d(mode_text_x, mode_text_y, mode_text, (0.0, 0.0, 0.0), font_size=12)
    
    # 2. Connect Button (连接按钮 - Mocap/Secap 模式共用)
    conn_x = connect_btn_rect.x
    conn_y = display[1] - connect_btn_rect.y - connect_btn_rect.height
    conn_width = connect_btn_rect.width
    conn_height = connect_btn_rect.height
    # 根据连接状态设置按钮颜色
    is_connected = False
    if AppState.mode == AppMode.MOCAP and AppState.mocap_connector:
        is_connected = AppState.mocap_connector.is_connected
    elif AppState.mode == AppMode.SECAP and AppState.axis_studio_connector:
        is_connected = AppState.axis_studio_connector.is_listening
    
    conn_color = (0.4, 0.8, 0.4) if is_connected else (0.8, 0.8, 0.8)
    draw_rectangle(conn_x, conn_y, conn_width, conn_height, conn_color)
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(conn_x, conn_y)
    glVertex2f(conn_x + conn_width, conn_y)
    glVertex2f(conn_x + conn_width, conn_y + conn_height)
    glVertex2f(conn_x, conn_y + conn_height)
    glEnd()
    
    # 按钮文本根据模式调整
    if AppState.mode == AppMode.MOCAP:
        conn_text = "Disconnect" if is_connected else "Connect"
    elif AppState.mode == AppMode.SECAP:
        conn_text = "Stop" if is_connected else "Listen"
    else:
        conn_text = "N/A"
    conn_text_width = len(conn_text) * 8
    conn_text_height = 12
    conn_text_x = conn_x + (conn_width - conn_text_width) / 2 + 8
    conn_text_y = conn_y + (conn_height + conn_text_height) / 2 - 10
    draw_text_2d(conn_text_x, conn_text_y, conn_text, (0.0, 0.0, 0.0), font_size=12)
    
    # 3. Record Button (录制按钮 - 两种模式共用)
    rec_x = record_btn_rect.x
    rec_y = display[1] - record_btn_rect.y - record_btn_rect.height
    rec_width = record_btn_rect.width
    rec_height = record_btn_rect.height
    # 根据录制状态设置按钮颜色
    if AppState.recording_manager and AppState.recording_manager.is_recording:
        rec_color = (0.9, 0.3, 0.3)  # 红色表示正在录制
    else:
        rec_color = (0.8, 0.8, 0.8)  # 灰色表示未录制
    draw_rectangle(rec_x, rec_y, rec_width, rec_height, rec_color)
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(rec_x, rec_y)
    glVertex2f(rec_x + rec_width, rec_y)
    glVertex2f(rec_x + rec_width, rec_y + rec_height)
    glVertex2f(rec_x, rec_y + rec_height)
    glEnd()
    rec_text = "Stop" if (AppState.recording_manager and AppState.recording_manager.is_recording) else "Record"
    rec_text_width = len(rec_text) * 8
    rec_text_height = 12
    rec_text_x = rec_x + (rec_width - rec_text_width) / 2 + 8
    rec_text_y = rec_y + (rec_height + rec_text_height) / 2 - 10
    draw_text_2d(rec_text_x, rec_text_y, rec_text, (0.0, 0.0, 0.0), font_size=12)
    
    # 4. Calibrate Button (校准按钮 - 仅 Mocap 模式可用)
    cal_x = calibrate_btn_rect.x
    cal_y = display[1] - calibrate_btn_rect.y - calibrate_btn_rect.height
    cal_width = calibrate_btn_rect.width
    cal_height = calibrate_btn_rect.height
    # 根据采集阶段和校准状态设置按钮颜色（仅 Mocap 模式）
    if AppState.mode == AppMode.MOCAP and AppState.mocap_connector:
        capture_phase = AppState.mocap_connector.capture_phase
        cal_state = AppState.mocap_connector.calibration_state
        
        if capture_phase == CapturePhase.CALIBRATED and cal_state == CalibrationState.COMPLETED:
            cal_color = (0.4, 0.8, 0.4)  # 绿色表示已校准
        elif cal_state in [CalibrationState.PREPARING, CalibrationState.COUNTDOWN, CalibrationState.IN_PROGRESS]:
            cal_color = (0.9, 0.7, 0.2)  # 橙色表示校准中
        elif capture_phase == CapturePhase.READY:
            cal_color = (0.3, 0.7, 0.9)  # 蓝色表示可以校准
        elif capture_phase == CapturePhase.STABILIZING:
            cal_color = (0.7, 0.7, 0.7)  # 灰色表示稳定化中
        elif cal_state == CalibrationState.FAILED:
            cal_color = (0.9, 0.3, 0.3)  # 红色表示校准失败
        else:
            cal_color = (0.8, 0.8, 0.8)  # 灰色
    else:
        # Secap 模式不需要校准，按钮置灰
        cal_color = (0.6, 0.6, 0.6)
    draw_rectangle(cal_x, cal_y, cal_width, cal_height, cal_color)
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(cal_x, cal_y)
    glVertex2f(cal_x + cal_width, cal_y)
    glVertex2f(cal_x + cal_width, cal_y + cal_height)
    glVertex2f(cal_x, cal_y + cal_height)
    glEnd()
    cal_text = "Calibrate" if AppState.mode == AppMode.MOCAP else "N/A"
    cal_text_width = len(cal_text) * 8
    cal_text_height = 12
    cal_text_x = cal_x + (cal_width - cal_text_width) / 2 + 8
    cal_text_y = cal_y + (cal_height + cal_text_height) / 2 - 10
    draw_text_2d(cal_text_x, cal_text_y, cal_text, (0.0, 0.0, 0.0), font_size=12)
    
    # 5. Export BVH Button (导出BVH按钮)
    exp_x = export_bvh_btn_rect.x
    exp_y = display[1] - export_bvh_btn_rect.y - export_bvh_btn_rect.height
    exp_width = export_bvh_btn_rect.width
    exp_height = export_bvh_btn_rect.height
    draw_rectangle(exp_x, exp_y, exp_width, exp_height, (0.8, 0.8, 0.8))
    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(exp_x, exp_y)
    glVertex2f(exp_x + exp_width, exp_y)
    glVertex2f(exp_x + exp_width, exp_y + exp_height)
    glVertex2f(exp_x, exp_y + exp_height)
    glEnd()
    exp_text = "Export BVH"
    exp_text_width = len(exp_text) * 8
    exp_text_height = 12
    exp_text_x = exp_x + (exp_width - exp_text_width) / 2 + 8
    exp_text_y = exp_y + (exp_height + exp_text_height) / 2 - 10
    draw_text_2d(exp_text_x, exp_text_y, exp_text, (0.0, 0.0, 0.0), font_size=12)
    
    # 6. 状态信息显示
    status_y = 50  # 状态信息显示在左下角
    
    # 显示模式信息
    if AppState.mode == AppMode.MOCAP:
        mode_info = f"Mode: MOCAP"
        draw_text_2d(10, status_y, mode_info, (0.0, 0.5, 0.0), font_size=12)
        status_y += 15
        
        # 显示 Mocap 连接状态
        if AppState.mocap_connector:
            if AppState.mocap_connector.is_connected:
                conn_info = f"Status: Connected ({AppState.mocap_connector.device_ip}:{AppState.mocap_connector.device_port})"
                draw_text_2d(10, status_y, conn_info, (0.0, 0.5, 0.0), font_size=12)
            else:
                conn_info = "Status: Disconnected"
                draw_text_2d(10, status_y, conn_info, (0.5, 0.0, 0.0), font_size=12)
            status_y += 15
            
            # Mocap 模式的采集阶段和校准状态
            if AppState.mocap_connector.is_connected:
                status_msg = AppState.mocap_connector.get_overall_status_message()
                if status_msg:
                    capture_phase = AppState.mocap_connector.capture_phase
                    cal_state = AppState.mocap_connector.calibration_state
                    
                    if capture_phase == CapturePhase.CALIBRATED and cal_state == CalibrationState.COMPLETED:
                        msg_color = (0.0, 0.6, 0.0)
                    elif cal_state in [CalibrationState.PREPARING, CalibrationState.COUNTDOWN, CalibrationState.IN_PROGRESS]:
                        msg_color = (0.8, 0.5, 0.0)
                    elif capture_phase == CapturePhase.STABILIZING:
                        msg_color = (0.0, 0.4, 0.8)
                    elif capture_phase == CapturePhase.READY:
                        msg_color = (0.0, 0.6, 0.3)
                    elif cal_state == CalibrationState.FAILED:
                        msg_color = (0.8, 0.0, 0.0)
                    else:
                        msg_color = (0.5, 0.5, 0.5)
                    draw_text_2d(10, status_y, status_msg, msg_color, font_size=12)
                    status_y += 15
    
    elif AppState.mode == AppMode.SECAP:
        mode_info = f"Mode: SECAP (Axis Studio)"
        draw_text_2d(10, status_y, mode_info, (0.0, 0.4, 0.8), font_size=12)
        status_y += 15
        
        # 显示 Secap 状态
        if AppState.axis_studio_connector:
            status_text = AppState.axis_studio_connector.get_connection_status_text()
            port_info = f"UDP Port: {AppState.axis_studio_connector.udp_port}"
            
            if AppState.axis_studio_connector.is_listening:
                status_color = (0.0, 0.5, 0.0) if AppState.axis_studio_connector.is_receiving_data else (0.5, 0.5, 0.0)
                draw_text_2d(10, status_y, f"Status: {status_text}", status_color, font_size=12)
                status_y += 15
                draw_text_2d(10, status_y, port_info, (0.0, 0.4, 0.8), font_size=12)
                status_y += 15
                
                if not AppState.axis_studio_connector.is_receiving_data:
                    hint = "⚠️ Please start BVH broadcast in Axis Studio"
                    draw_text_2d(10, status_y, hint, (0.8, 0.5, 0.0), font_size=12)
                    status_y += 15
            else:
                draw_text_2d(10, status_y, "Status: Not Listening", (0.5, 0.0, 0.0), font_size=12)
                status_y += 15
    
    # 显示录制状态（两种模式共用）
    if AppState.recording_manager and AppState.recording_manager.is_recording:
        rec_info = f"Recording: {AppState.recording_manager.get_frame_count()} frames"
        draw_text_2d(10, status_y, rec_info, (0.9, 0.0, 0.0), font_size=12)
        status_y += 15
    
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
# ======================== 绘制实时模式UI结束 ========================

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
        angle_text = f"{angle_deg:.1f}°"
        draw_text_2d(text_pos_2d[0], text_pos_2d[1], angle_text, (0, 0, 0), 12)
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
    """
    Main application entry point.
    
    Initializes the pygame window, sets up OpenGL rendering context,
    and runs the main event loop for the BVH viewer application.
    
    The application supports three modes:
    - Offline: Load and playback BVH files
    - Mocap: Real-time motion capture from devices
    - Secap: Real-time data from Axis Studio broadcast
    """
    pygame.init()
    
    # Calculate window size based on screen resolution
    screen_info = pygame.display.Info()
    target_display_width = int(screen_info.current_w * UIConfig.WINDOW_SCALE_FACTOR)
    target_display_height = int(screen_info.current_h * UIConfig.WINDOW_SCALE_FACTOR)
    display = (target_display_width, target_display_height)
    
    # Initialize window with OpenGL support
    screen = pygame.display.set_mode(display, DOUBLEBUF | OPENGL | pygame.RESIZABLE)
    pygame.display.set_caption("BVH 3D Viewer")
    
    # Initialize overlay size
    overlay_manager.update_display_size(display[0], display[1])
    
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
    
    # ======================== 新增实时模式按钮 ========================
    mode_btn_rect = pygame.Rect(
        trajectory_btn_rect.x + trajectory_btn_rect.width + 20,  # 加大间隔作为分隔
        btn_y, 100, btn_height
    )  # 模式切换按钮
    
    connect_btn_rect = pygame.Rect(
        mode_btn_rect.x + mode_btn_rect.width + 10,
        btn_y, 100, btn_height
    )  # 连接/断开按钮
    
    record_btn_rect = pygame.Rect(
        connect_btn_rect.x + connect_btn_rect.width + 10,
        btn_y, 80, btn_height
    )  # 录制按钮
    
    # ======================== 校准按钮 ========================
    calibrate_btn_rect = pygame.Rect(
        record_btn_rect.x + record_btn_rect.width + 10,
        btn_y, 90, btn_height
    )  # 校准按钮
    # ======================== 校准按钮结束 ========================
    
    export_bvh_btn_rect = pygame.Rect(
        calibrate_btn_rect.x + calibrate_btn_rect.width + 10,
        btn_y, 100, btn_height
    )  # 导出BVH按钮
    
    # ======================== 网球分析按钮 ========================
    tennis_btn_rect = pygame.Rect(
        export_bvh_btn_rect.x + export_bvh_btn_rect.width + 10,
        btn_y, 110, btn_height
    )  # 网球动作分析按钮
    # ======================== 新增按钮结束 ========================
    
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
            global current_bvh_file_path
            current_bvh_file_path = file_path  # 保存文件路径供网球分析使用
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
    
    # ======================== 实时模式辅助函数 ========================
    def toggle_mode():
        """
        模式切换：Offline -> Mocap -> Secap -> Offline 循环
        
        Offline: 加载 BVH 文件
        Mocap: MocapAPI 直接连接动捕设备
        Secap: Axis Studio BVH 广播
        """
        # 关闭当前模式的连接
        if AppState.mode == AppMode.MOCAP:
            if AppState.mocap_connector and AppState.mocap_connector.is_connected:
                AppState.mocap_connector.stop_capture()
                AppState.mocap_connector.disconnect()
        elif AppState.mode == AppMode.SECAP:
            if AppState.axis_studio_connector and AppState.axis_studio_connector.is_listening:
                AppState.axis_studio_connector.stop_listening()
        
        # 停止录制（如果正在录制）
        if AppState.recording_manager and AppState.recording_manager.is_recording:
            AppState.recording_manager.stop_recording()
        
        # 切换到下一个模式
        if AppState.mode == AppMode.OFFLINE:
            # Offline -> Mocap
            if AppState.init_mocap_mode():
                AppState.mode = AppMode.MOCAP
                print("[Mode] Switched to MOCAP mode")
            else:
                print("[Mode] Failed to switch to MOCAP mode - SDK not available")
        elif AppState.mode == AppMode.MOCAP:
            # Mocap -> Secap
            if AppState.init_secap_mode():
                AppState.mode = AppMode.SECAP
                print("[Mode] Switched to SECAP mode (Axis Studio)")
            else:
                print("[Mode] Failed to switch to SECAP mode - connector not available")
        elif AppState.mode == AppMode.SECAP:
            # Secap -> Offline
            AppState.mode = AppMode.OFFLINE
            print("[Mode] Switched to OFFLINE mode")
    
    def toggle_connection():
        """
        切换连接状态
        
        Mocap 模式：Connect/Disconnect 设备
        Secap 模式：Listen/Stop UDP 广播
        """
        if AppState.mode == AppMode.MOCAP:
            if not AppState.mocap_connector:
                return
            
            if not AppState.mocap_connector.is_connected:
                # 连接并启动采集
                success, msg = AppState.mocap_connector.connect()
                if success:
                    AppState.mocap_connector.start_capture()
                    print(f"[Mocap] Connected and capturing")
                else:
                    print(f"[Mocap] Connection failed: {msg}")
            else:
                # 断开连接
                AppState.mocap_connector.stop_capture()
                AppState.mocap_connector.disconnect()
                print("[Mocap] Disconnected")
        
        elif AppState.mode == AppMode.SECAP:
            if not AppState.axis_studio_connector:
                return
            
            if not AppState.axis_studio_connector.is_listening:
                # 开始监听 UDP 广播
                success, msg = AppState.axis_studio_connector.start_listening()
                if success:
                    print(f"[Secap] Listening on UDP port {AppState.axis_studio_connector.udp_port}")
                    print("[Secap] Waiting for Axis Studio BVH broadcast...")
                else:
                    print(f"[Secap] Failed to start listening: {msg}")
            else:
                # 停止监听
                AppState.axis_studio_connector.stop_listening()
                print("[Secap] Stopped listening")
    
    def toggle_recording():
        """
        切换录制状态
        
        Mocap 模式：仅在校准完成后才能录制
        Secap 模式：只要在接收数据就可以录制
        """
        if AppState.mode not in [AppMode.MOCAP, AppMode.SECAP] or not AppState.recording_manager:
            return
        
        # 检查是否可以录制
        can_record = False
        
        if AppState.mode == AppMode.MOCAP:
            # Mocap 模式：需要连接并已校准
            if AppState.mocap_connector and AppState.mocap_connector.is_connected:
                can_record = AppState.mocap_connector.is_ready_for_record()
                if not can_record and not AppState.recording_manager.is_recording:
                    capture_phase = AppState.mocap_connector.capture_phase
                    if capture_phase == CapturePhase.STABILIZING:
                        print(f"[Recording] Cannot record - still stabilizing")
                    elif capture_phase == CapturePhase.READY:
                        print("[Recording] Cannot record - please calibrate first")
                    else:
                        print("[Recording] Cannot record - not ready")
                    return
        
        elif AppState.mode == AppMode.SECAP:
            # Secap 模式：只要在接收数据就可以录制
            if AppState.axis_studio_connector:
                can_record = AppState.axis_studio_connector.is_ready_for_recording()
                if not can_record and not AppState.recording_manager.is_recording:
                    print("[Recording] Cannot record - not receiving data from Axis Studio")
                    print("[Recording] Please check: 1) BVH broadcast is enabled 2) Axis Studio is calibrated")
                    return
        
        # 切换录制状态
        if not AppState.recording_manager.is_recording:
            if can_record:
                AppState.recording_manager.start_recording(fps=60.0)
                print("[Recording] Started")
        else:
            AppState.recording_manager.stop_recording()
            print("[Recording] Stopped")
    
    def start_calibration():
        """
        开始校准流程 - 仅 Mocap 模式可用
        
        Secap 模式不需要校准（Axis Studio 中已完成校准）
        """
        if AppState.mode != AppMode.MOCAP or not AppState.mocap_connector:
            print("[Calibration] Only available in Mocap mode")
            return
        if not AppState.mocap_connector.is_connected:
            print("[Calibration] Not connected")
            return
        
        # 检查采集阶段
        capture_phase = AppState.mocap_connector.capture_phase
        if capture_phase == CapturePhase.STABILIZING:
            remaining = AppState.mocap_connector.stabilize_remaining
            print(f"[Calibration] Cannot start - still stabilizing ({int(remaining)}s remaining)")
            return
        elif capture_phase == CapturePhase.CALIBRATED:
            print("[Calibration] Already calibrated - recalibration available")
        
        # 检查是否可以开始校准
        if AppState.mocap_connector.can_start_calibration():
            AppState.mocap_connector.start_calibration()
        else:
            print("[Calibration] Cannot start - calibration in progress or not ready")
    
    def export_bvh_dialog():
        """Export recorded data to BVH file"""
        if not AppState.recording_manager or AppState.recording_manager.get_frame_count() == 0:
            print("[Export] No recording data to export")
            return
        
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".bvh",
            filetypes=[("BVH files", "*.bvh")],
            title="Export BVH File"
        )
        root.destroy()
        
        if file_path:
            success = AppState.recording_manager.export_to_bvh(file_path)
            if success:
                print(f"[Export] BVH exported to: {file_path}")
            else:
                print("[Export] BVH export failed")
    
    def update_realtime_joints(frame_data, target_joints, root_joint):
        """
        Update joint matrices based on real-time motion capture data.
        
        This function applies hierarchical transformations to update all joints
        in the skeleton based on incoming real-time data from Mocap or Secap modes.
        
        Design principles:
        - Root joint (Hips): Uses real-time position as world translation
        - Child joints: Use predefined bone lengths from RecordingManager.DEFAULT_OFFSETS
        - Local rotation: Uses quaternions from SDK
        - World matrix: Computed recursively as M_world = M_parent @ T(offset) @ R(quat)
        
        Args:
            frame_data (dict): Frame data containing 'joints' dictionary
            target_joints (dict): Dictionary of Joint objects to update
            root_joint (Joint): Root joint of the skeleton
        """
        if (not frame_data) or ('joints' not in frame_data) or (root_joint is None):
            return
        
        frame_joints = frame_data['joints']
        
        def quat_to_rot3x3(w, x, y, z):
            """四元数转 3×3 旋转矩阵"""
            return np.array([
                [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w)],
                [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y)]
            ], dtype=float)
        
        def update_joint(joint):
            # 取当前关节的实时数据（可能缺失）
            data = frame_joints.get(joint.name, {})
            rot = data.get('rotation', (1.0, 0.0, 0.0, 0.0))  # (w, x, y, z)
            w, x, y, z = rot
            
            # 构建 4×4 旋转矩阵
            R3 = quat_to_rot3x3(w, x, y, z)
            R4 = np.identity(4, dtype=float)
            R4[:3, :3] = R3
            
            if joint.parent is None:
                # 根关节：使用实时 position 作为世界平移
                pos = np.array(data.get('position', (0.0, 0.0, 0.0)), dtype=float)
                T = np.identity(4, dtype=float)
                T[:3, 3] = pos
                joint.matrix = T @ R4
            else:
                # 子关节：使用预定义骨长 offset（RecordingManager.DEFAULT_OFFSETS 已写入 joint.offset）
                parent_matrix = target_joints[joint.parent.name].matrix
                T = np.identity(4, dtype=float)
                T[:3, 3] = joint.offset  # 单位：cm，与离线 BVH 一致
                joint.matrix = parent_matrix @ T @ R4
            
            # 递归更新子节点
            for child in joint.children:
                update_joint(child)
        
        update_joint(root_joint)
    
    def init_realtime_skeleton():
        """
        Initialize skeleton structure for real-time mode.
        
        Creates a standard skeleton hierarchy with predefined bone lengths
        suitable for real-time motion capture visualization. This skeleton
        matches the structure used by RecordingManager for BVH export.
        
        The skeleton is stored in the nonlocal 'joints' and 'root_joint' variables.
        """
        nonlocal joints, root_joint
        
        # 定义关节层级（与 RecordingManager.JOINT_HIERARCHY 保持一致）
        joint_hierarchy = {
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
        
        joints.clear()
        
        # 创建所有关节，并写入默认 offset（骨长），单位 cm
        for joint_name in joint_hierarchy.keys():
            parent_name = joint_hierarchy[joint_name]
            parent = joints.get(parent_name) if parent_name else None
            joint = Joint(joint_name, parent=parent)
            
            # 使用 RecordingManager 中的默认偏移（若不存在则为 0）
            try:
                from recording_manager import RecordingManager
                offset = RecordingManager.DEFAULT_OFFSETS.get(joint_name, (0.0, 0.0, 0.0))
            except ImportError:
                offset = (0.0, 0.0, 0.0)
            joint.set_offset(offset)
            
            joints[joint_name] = joint
            if parent:
                parent.add_child(joint)
        
        root_joint = joints.get('Hips')
        return joints, root_joint
    # ======================== 实时模式辅助函数结束 ========================
    
    reset_view()
    running = True
    while running:
        overlay_manager.clear()
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
                overlay_manager.update_display_size(event.w, event.h)
                
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
                    # ======================== 新增按钮事件处理 ========================
                    elif mode_btn_rect.collidepoint(event.pos):
                        toggle_mode()
                    elif connect_btn_rect.collidepoint(event.pos):
                        toggle_connection()
                    elif record_btn_rect.collidepoint(event.pos):
                        toggle_recording()
                    elif calibrate_btn_rect.collidepoint(event.pos):
                        start_calibration()  # 校准按钮
                    elif export_bvh_btn_rect.collidepoint(event.pos):
                        export_bvh_dialog()
                    # ======================== 网球分析按钮事件 ========================
                    # ======================== 网球分析按钮事件 ========================
                    # ======================== 网球分析按钮事件 ========================
                    elif tennis_btn_rect.collidepoint(event.pos):
                        if frames > 0 and len(motion_data) > 0:
                            # 1. 弹出选项窗口 (选择左右手/脚)
                            options = TennisAnalyzer.get_analysis_options()
                            
                            # 如果用户点击了 Cancel 或直接关闭窗口，options 为空，停止执行
                            if not options:
                                print("[System] Analysis cancelled.")
                            else:
                                print(f"[System] Starting Analysis ({options['hand']} Hand, {options['leg']} Leg)...")
                                
                                # 2. 计算当前数据的角速度 (传入左右侧配置)
                                velocities = TennisAnalyzer.calculate_angular_velocities(
                                    joints, motion_data, frame_time, 
                                    hand_side=options['hand'], 
                                    leg_side=options['leg']
                                )
                                
                                # 3. 获取文件名
                                try:
                                    current_fname = os.path.basename(current_bvh_file_path) if current_bvh_file_path else "Session_Data"
                                except:
                                    current_fname = "Session_Data"
                                
                                # 4. 自动保存当前记录到历史文件
                                TennisAnalyzer.save_to_history(velocities, current_fname)
                                
                                # 5. 打开历史管理器窗口
                                TennisAnalyzer.open_history_manager()
                            
                        else:
                            print("[System] Error: Please load a BVH file first.")

                    # ======================== 新增按钮事件结束 ========================
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
                # ======================== 新增快捷键 ========================
                if event.key == pygame.K_m:  # M: Toggle mode
                    toggle_mode()
                if event.key == pygame.K_c:  # C: Toggle connection
                    toggle_connection()
                if event.key == pygame.K_r:  # R: Toggle recording
                    toggle_recording()
                if event.key == pygame.K_e:  # E: Export BVH
                    export_bvh_dialog()
                if event.key == pygame.K_k:  # K: Calibrate
                    start_calibration()  # 使用新的校准流程
                # ======================== 新增快捷键结束 ========================
        
        # Rendering Process (Optimized for real-time when scaling)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glFlush()  # New: Force clear buffer command to execute instantly, preventing black screen due to delay
        glMatrixMode(GL_MODELVIEW)
        
        glPushMatrix()
        draw_grid()
        draw_axes_and_labels()
        
        # ======================== 实时模式渲染处理 ========================
        # Mocap 模式：MocapAPI 直接连接动捕设备
        if AppState.mode == AppMode.MOCAP and AppState.mocap_connector:
            # 只要连接就持续轮询数据 (修复: 不再检查is_capturing,因为需要轮询才能设置is_capturing)
            if AppState.mocap_connector.is_connected:
                # 轮询获取最新数据
                frame_data = AppState.mocap_connector.poll_and_update()
                
                if frame_data:
                    # 初始化骨骼结构（如果还没有）
                    if not joints or root_joint is None:
                        init_realtime_skeleton()
                    
                    # 按层级更新关节矩阵（根关节 + 子关节）
                    update_realtime_joints(frame_data, joints, root_joint)
                    
                    # 如果正在录制，记录这一帧
                    if AppState.recording_manager and AppState.recording_manager.is_recording:
                        AppState.recording_manager.record_frame(frame_data['joints'])
                
                # 渲染骨骼
                if joints:
                    draw_custom_skeleton(joints)
        
        # Secap 模式：通过 Axis Studio BVH 广播接收数据
        elif AppState.mode == AppMode.SECAP and AppState.axis_studio_connector:
            # 只要在监听就持续轮询数据
            if AppState.axis_studio_connector.is_listening:
                # 轮询获取最新数据
                frame_data = AppState.axis_studio_connector.poll_and_update()
                
                if frame_data:
                    # 初始化骨骼结构（如果还没有）
                    if not joints or root_joint is None:
                        init_realtime_skeleton()
                    
                    # 按层级更新关节矩阵（根关节 + 子关节）
                    update_realtime_joints(frame_data, joints, root_joint)
                    
                    # 如果正在录制，记录这一帧
                    if AppState.recording_manager and AppState.recording_manager.is_recording:
                        AppState.recording_manager.record_frame(frame_data['joints'])
                
                # 渲染骨骼
                if joints:
                    draw_custom_skeleton(joints)
        # ======================== 实时模式渲染结束 ========================
        
        # 离线模式渲染 (Offline mode rendering)
        elif AppState.mode == AppMode.OFFLINE and root_joint and len(motion_data) > 0:
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
        
        # ======================== 绘制实时模式UI按钮 ========================
        draw_realtime_ui(
            display,
            mode_btn_rect,
            connect_btn_rect,
            record_btn_rect,
            calibrate_btn_rect,
            export_bvh_btn_rect
        )
        # ======================== 绘制实时模式UI结束 ========================
        
        # ======================== 绘制网球分析按钮 ========================
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
        glOrtho(0, display[0], 0, display[1], -1, 1)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glDisable(GL_DEPTH_TEST)

        # 绘制按钮背景 (淡黄色 #EEDD82)
        tx = tennis_btn_rect.x
        ty = display[1] - tennis_btn_rect.y - tennis_btn_rect.height
        draw_rectangle(tx, ty, tennis_btn_rect.width, tennis_btn_rect.height, (0.93, 0.87, 0.51))
        
        # 绘制按钮边框 (黑色)
        glColor3f(0, 0, 0); glLineWidth(1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(tx, ty); glVertex2f(tx + tennis_btn_rect.width, ty)
        glVertex2f(tx + tennis_btn_rect.width, ty + tennis_btn_rect.height); glVertex2f(tx, ty + tennis_btn_rect.height)
        glEnd()

        # 绘制按钮文字
        t_label = "Tennis Analyze"
        label_x = tx + (tennis_btn_rect.width - len(t_label)*7) / 2
        label_y = ty + (tennis_btn_rect.height - 12) / 2 + 2
        draw_text_2d(label_x, label_y, t_label, (0, 0, 0), 12)

        # 恢复 3D 状态
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION); glPopMatrix()
        glMatrixMode(GL_MODELVIEW); glPopMatrix()
        # ======================== 网球分析按钮绘制结束 ========================
        
        # Draw Position and Velocity Panels
        if all_joint_positions and all_joint_velocities and frames > 0:
            if 0 <= current_frame < len(all_joint_positions) and 0 <= current_frame < len(all_joint_velocities):
                current_positions = all_joint_positions[current_frame]
                current_velocities = all_joint_velocities[current_frame]
                draw_position_panel(display, current_positions, joints)
                draw_velocity_panel(display, current_velocities, joints)
        
        overlay_manager.render()
        pygame.display.flip()
        
        if is_playing and frame_time > 0:
            target_fps = 1.0 / frame_time
        
        clock.tick(target_fps)

if __name__ == '__main__':
    main()