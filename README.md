# BVH 3D Viewer

A comprehensive 3D motion capture data visualization tool supporting offline BVH file playback, real-time motion capture streaming, and advanced sports motion analysis.

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)](https://www.microsoft.com/windows)

## 🌟 Features Overview

### Core Functionality
- **3D Skeleton Visualization**: Real-time 3D rendering of motion capture data using OpenGL
- **Three Operation Modes**:
  - **Offline Mode**: Load and playback BVH files with full analysis capabilities
  - **Mocap Mode**: Direct connection to Noitom motion capture devices via MocapAPI SDK
  - **Secap Mode**: Receive real-time BVH data broadcast from Axis Studio
- **Real-time Recording**: Capture live motion data at 60 FPS and export to standard BVH format
- **Kinematic Analysis**: Real-time calculation of joint positions, velocities, accelerations, and angles
- **Trajectory Visualization**: Track and display joint movement paths with customizable colors
- **Tennis Motion Analysis**: Specialized biomechanical analysis for tennis serve motions
  - Automatic serve phase detection (preparation, backswing, forward swing, follow-through)
  - Ball contact point detection
  - Racket speed calculation
  - Body segment angle analysis
  - Performance metrics visualization

### Modern UI Design
- **Apple-style Interface**: Inspired by macOS design language with clean aesthetics
- **Glass Morphism Effects**: Translucent panels with subtle blur for depth perception
- **Smooth Animations**: Butter-smooth transitions and hover effects (60 FPS)
- **Intelligent Toast Notifications**: 
  - Color-coded feedback (Gray for Offline, Green for Mocap, Blue for Secap)
  - Auto-dismiss with fade-out animation
  - Non-intrusive positioning (top-right corner)
  - Support for Success, Warning, Error, Info, and Neutral types
- **Enhanced Dropdown Menus**: 
  - Visual mode indicators with colored dots
  - Clear text labels for each option
  - Hover highlights with Apple Blue accent
  - Selected item indicator
  - Smooth expand/collapse animations
- **Responsive Layout**: Adapts to different window sizes gracefully
- **Consistent Color Scheme**: Unified palette across all UI elements

### Interactive Controls
- **Apple-style Modern UI**: Glass effects, smooth animations, and elegant design
- **Intuitive Mode Switching**: Dropdown menu with visual indicators and keyboard shortcuts (Ctrl+1/2/3)
- **Smart Toast Notifications**: Color-coded feedback system (gray/green/blue for different modes)
- **Mouse-based Camera Control**: Pan, rotate, zoom with intuitive gestures
- **Timeline Scrubbing**: Frame-by-frame navigation with visual feedback
- **Real-time Playback Speed**: Adjustable FPS with smooth transitions
- **User Preferences**: Automatic saving of panel states and UI configurations
- **Comprehensive Keyboard Shortcuts**: Fast access to all major functions

## 🛠️ Technical Stack

### Core Technologies
- **Python 3.8+**: Main programming language
- **Pygame 2.1+**: Window management and user input handling
- **PyOpenGL 3.1+**: Hardware-accelerated 3D graphics rendering
- **NumPy 1.21+**: High-performance mathematical computations and matrix operations
- **Matplotlib 3.4+**: Data visualization and plotting

### Motion Capture Integration
- **MocapAPI SDK**: Official Noitom SDK for direct device communication (Mocap mode)
- **Axis Studio Integration**: UDP broadcast receiver for Axis Studio (Secap mode)

### Build Tools
- **PyInstaller**: Standalone executable packaging for Windows distribution

## 📋 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (21H2 or later)
- **Processor**: Intel Core i5 or AMD equivalent
- **Memory**: 4 GB RAM
- **Graphics**: OpenGL 3.3 compatible GPU with 1 GB VRAM
- **Storage**: 500 MB free disk space
- **Display**: 1280x720 resolution

### Recommended Requirements
- **Operating System**: Windows 10/11 (64-bit)
- **Processor**: Intel Core i7 or AMD Ryzen 5
- **Memory**: 8 GB RAM or more
- **Graphics**: Dedicated GPU (NVIDIA GTX 1060 / AMD RX 580 or better)
- **Storage**: 1 GB free disk space
- **Display**: 1920x1080 or higher resolution

### Network Requirements (for Real-time Modes)
- **Mocap Mode**: Local network connection to Noitom motion capture device
  - Default configuration: 10.42.0.101:8002 (local) ↔ 10.42.0.202:8080 (device)
- **Secap Mode**: UDP port 7012 open for receiving Axis Studio broadcast
  - Can operate on same computer (127.0.0.1) or across LAN

## 🚀 Quick Start

### For End Users (Packaged Version)

1. **Download the Distribution Package**
   - Extract `BVH_Viewer_vX.X.zip` to your desired location
   - No Python installation required

2. **Run the Application**
   - Double-click `BVH_Viewer.exe`
   - The application opens with Offline mode active
   - User preferences are automatically loaded from previous session

3. **Choose Your Workflow**:
   - **For BVH File Analysis**:
     1. Click "Load File" button or drag-and-drop a `.bvh` file
     2. Use play controls to view animation
     3. Access "Trajectory" or "Tennis Analysis" for advanced features
   
   - **For Real-time Motion Capture** (requires hardware):
     1. Click **Mode** button and select **Mocap** from dropdown (or press `Ctrl+2`)
     2. Green toast notification confirms mode switch
     3. Click "Connect" button
     4. Wait for 20-second stabilization
     5. Click "Calibrate" and follow on-screen instructions
     6. Click "Record" to start capturing
   
   - **For Axis Studio Integration**:
     1. Start Axis Studio and enable BVH broadcast (UDP port 7012)
     2. Click **Mode** button and select **Secap** (or press `Ctrl+3`)
     3. Blue toast notification confirms mode switch
     4. Click "Listen" to start receiving data
     5. Click "Record" when ready to capture

### For Developers (Source Code)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/BVH_Viewer.git
   cd BVH_Viewer
   ```

2. **Set Up Python Environment** (Python 3.8+ required)
   ```bash
   # Create virtual environment (recommended)
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   
   # For real-time Mocap/Secap modes, also install MocapAPI SDK:
   # (SDK files should be in the project directory or system PATH)
   ```

4. **Run the Application**
   ```bash
   python bvh_visualizer_improved.py
   ```

5. **Development Mode** (with hot reload)
   ```bash
   # Use a file watcher or IDE's run configuration
   # PyCharm: Right-click → Run 'bvh_visualizer_improved'
   # VS Code: F5 to debug
   ```

## 🔨 Building from Source

### Create Standalone Executable (Windows)

1. **Install PyInstaller**
   ```bash
   pip install pyinstaller
   ```

2. **Build the Executable**
   ```bash
   pyinstaller --name="BVH_Viewer" ^
               --windowed ^
               --onefile ^
               --icon=app_icon.ico ^
               --add-data "README.md;." ^
               --add-data "MODE_INTRODUCTION.md;." ^
               --add-data "SECAP_QUICKSTART.md;." ^
               bvh_visualizer_improved.py
   ```

3. **Output Location**
   - Executable: `dist/BVH_Viewer.exe`
   - Distribution folder: `dist/`

### Alternative: Use Build Script (Recommended)

Create a `build.spec` file for more control:

```python
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['bvh_visualizer_improved.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('MODE_INTRODUCTION.md', '.'),
        ('SECAP_QUICKSTART.md', '.'),
        ('app_icon.ico', '.'),
    ],
    hiddenimports=['pygame', 'OpenGL', 'numpy', 'matplotlib'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BVH_Viewer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    icon='app_icon.ico',
)
```

Then build with:
```bash
pyinstaller build.spec
```

## 📚 Project Structure

```
BVH_Viewer/
├── bvh_visualizer_improved.py    # Main application (3700+ lines)
│                                   # - UI rendering and event handling
│                                   # - 3D OpenGL skeleton visualization
│                                   # - Mode management and switching
│                                   # - Kinematic calculations
│                                   # - Tennis motion analysis
│                                   # - User preferences management
│
├── ui/                             # Apple-style UI module
│   ├── __init__.py               # UI components export
│   ├── components.py            # UI components (900+ lines)
│   │                            # - AppleButton, ButtonManager
│   │                            # - ToastManager, Toast notifications
│   │                            # - DropdownMenu with animations
│   │                            # - Panel, StatusIndicator, Timeline
│   ├── renderer.py               # OpenGL rendering functions (920+ lines)
│   │                            # - draw_rounded_rect, draw_circle
│   │                            # - draw_button, draw_toast_manager
│   │                            # - draw_dropdown_menu
│   │                            # - 2D/3D rendering setup
│   ├── colors.py                 # Color definitions and utilities
│   │                            # - AppleUIColors (system colors)
│   │                            # - EnhancedVisuals (gradients, glass effects)
│   └── metrics.py                # UI metrics and constants
│                              # - AppleUIMetrics (sizes, spacing)
│                              # - Animation parameters
│
├── mocap_connector.py              # Mocap mode implementation (600+ lines)
│                                   # - MocapAPI SDK wrapper
│                                   # - Device connection management
│                                   # - Calibration workflow
│                                   # - Real-time data streaming
│
├── axis_studio_connector.py        # Secap mode implementation (330+ lines)
│                                   # - UDP broadcast receiver
│                                   # - Axis Studio BVH parser
│                                   # - Frame rate monitoring
│
├── recording_manager.py            # Recording and export (330+ lines)
│                                   # - Frame buffer management
│                                   # - BVH file generation
│                                   # - Quaternion to Euler conversion
│                                   # - Skeleton hierarchy export
│
├── mocap_api.py                    # MocapAPI SDK bindings (1300+ lines)
│                                   # - Low-level SDK wrapper
│                                   # - Event handling
│                                   # - Data structure definitions
│
├── README.md                       # This file - Project documentation
├── MODE_INTRODUCTION.md            # Detailed mode usage guide (7.8KB)
├── SECAP_QUICKSTART.md             # Secap mode quick start (6.3KB)
├── IMPLEMENTATION_SUMMARY.md       # Technical implementation details (13KB)
│
├── requirements.txt                # Python package dependencies
├── .gitignore                      # Git ignore rules
├── app_icon.ico                    # Application icon
├── tennis_analysis_history.json   # Tennis analysis session data
│
├── _internal/                      # PyInstaller bundled dependencies
│   ├── numpy/                      # Numerical computing library
│   ├── pygame/                     # Game engine and UI framework
│   ├── OpenGL/                     # 3D graphics library
│   └── ... (98 items total)
│
└── dist/                           # Build output directory (not in repo)
    └── BVH_Viewer.exe              # Standalone executable
```

## 📖 Detailed Mode Documentation

For comprehensive guides on each operation mode, see:

### [MODE_INTRODUCTION.md](MODE_INTRODUCTION.md) - Complete Mode Reference (7.8KB)
- **Offline Mode**: BVH file loading and analysis
  - Supported file formats and structure
  - Playback controls and timeline navigation
  - Kinematic analysis features
  - Data export options
  
- **Mocap Mode**: Direct device connection workflow
  - Device connection procedure (TCP/UDP)
  - 20-second stabilization phase requirements
  - Calibration poses (V-Pose, F-Pose, T-Pose, etc.)
  - Real-time streaming at 60 FPS
  - Recording and BVH export
  - Network configuration details
  
- **Secap Mode**: Axis Studio integration
  - UDP broadcast setup (port 7012)
  - Axis Studio configuration steps
  - Real-time data reception
  - Robot control use cases (e.g., Unitree G1)
  
### [SECAP_QUICKSTART.md](SECAP_QUICKSTART.md) - 5-Minute Secap Setup (6.3KB)
- Step-by-step Axis Studio configuration
- Network troubleshooting guide
- Common issues and solutions
- Port forwarding and firewall settings

### [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical Details (13KB)
- Architecture overview
- Module interaction diagrams
- Calibration workflow internals
- BVH data format specifications
- Performance optimization notes

## ⚙️ Configuration Guide

### Mocap Mode Network Settings

Edit network parameters in `mocap_connector.py` (lines 64-67):

```python
class MocapConnector:
    def __init__(self):
        # Network configuration
        self.local_ip = '10.42.0.101'      # Your computer's IP address
        self.local_port = 8002             # Local listening port
        self.device_ip = '10.42.0.202'     # Motion capture device IP
        self.device_port = 8080            # Device communication port
```

**Common Scenarios:**
- **Same computer**: Both IPs set to `127.0.0.1`
- **LAN connection**: Use actual IP addresses (check with `ipconfig`)
- **Different subnets**: Ensure routing is configured correctly

### Secap Mode UDP Configuration

Edit UDP port in `axis_studio_connector.py` (line 58):

```python
class AxisStudioConnector:
    def __init__(self):
        self.udp_port = 7012  # Axis Studio BVH broadcast port
```

**Axis Studio Settings:**
1. Open Axis Studio → Settings → BVH Data Broadcast
2. Enable "UDP Broadcast"
3. Set port to `7012` (must match BVH Viewer setting)
4. Set target IP:
   - Same computer: `127.0.0.1`
   - Different computer: BVH Viewer machine's IP address

### User Preferences Configuration

The application automatically saves your UI preferences to ensure a consistent experience across sessions.

**Configuration File Location**:
- Windows: `C:\Users\<YourName>\AppData\Roaming\BVH_Viewer\bvh_viewer_config.json`

**Saved Preferences Include**:
```json
{
    "show_position_panel": false,      // Position data panel visibility
    "show_velocity_panel": false,      // Velocity data panel visibility
    "default_mode": "offline",         // Startup mode (offline/mocap/secap)
    "last_file_path": "C:/path/...",  // Last opened BVH file
    "window_width": 1200,              // Window dimensions
    "window_height": 800
}
```

**Manual Editing** (Advanced Users):
You can directly edit the JSON file to customize default settings. Changes take effect on next application launch.

### UI Configuration (Developer Customization)

UI parameters are centralized in `UIConfig` class (bvh_visualizer_improved.py, lines 45-86):

```python
class UIConfig:
    # Window settings
    WINDOW_SCALE_FACTOR = 0.75    # Window size relative to screen
    DEFAULT_TARGET_FPS = 60        # Target frame rate
    
    # Camera settings
    CAMERA_FOV = 45                # Field of view (degrees)
    CAMERA_INIT_Y = -100.0         # Initial Y position
    CAMERA_INIT_Z = -300.0         # Initial Z position
    
    # Mouse sensitivity
    MOUSE_PAN_SENSITIVITY = 0.2
    MOUSE_ROTATE_SENSITIVITY = 0.15
    MOUSE_ZOOM_STEP = 10.0
    
    # UI Colors (RGB 0-1)
    COLOR_MODE_MOCAP = (0.4, 0.8, 0.4)   # Green
    COLOR_MODE_SECAP = (0.4, 0.7, 0.9)   # Blue
    COLOR_RECORDING = (0.9, 0.3, 0.3)    # Red
```

## 🎯 Use Cases and Workflows

### 1. Motion Capture Recording (Mocap Mode)

**Scenario**: Direct recording from Noitom motion capture suit

**Workflow**:
1. **Setup** (5 minutes)
   - Connect motion capture device to computer via network
   - Verify IP configuration matches device settings
   - Launch BVH Viewer

2. **Connect** (1 minute)
   - Press `M` to switch to Mocap mode (green indicator)
   - Press `C` to connect to device
   - Wait for "Connected" status

3. **Stabilize** (20 seconds)
   - **Critical**: Remain completely still
   - UI shows countdown: "采集稳定化中 - 请保持静止 (X秒)"
   - Stabilization ensures sensor accuracy

4. **Calibrate** (1-2 minutes)
   - Press `K` or click "Calibrate" button
   - Follow on-screen pose instructions
   - Hold pose during countdown (3-5 seconds)
   - Wait for "✅ 校准完成" confirmation

5. **Record** (variable duration)
   - Press `R` to start recording
   - Perform desired motion (60 FPS capture)
   - Press `R` again to stop
   - Red "Recording" indicator shows active status

6. **Export** (few seconds)
   - Press `E` to export BVH file
   - Choose save location and filename
   - File ready for use in 3D software (Blender, Maya, etc.)

**Best For**:
- Professional motion capture sessions
- High-quality animation data acquisition
- Research and biomechanical analysis

---

### 2. Real-time Robot Control (Secap Mode)

**Scenario**: Drive humanoid robot (e.g., Unitree G1) with human motion

**Workflow**:
1. **Axis Studio Setup** (2 minutes)
   - Open Axis Studio software
   - Connect and calibrate motion capture suit
   - Settings → BVH Data Broadcast → Enable UDP
   - Set port to `7012`, target IP to robot controller's IP

2. **BVH Viewer Setup** (30 seconds)
   - Launch BVH Viewer
   - Press `M` three times to Secap mode (blue indicator)
   - Press `C` to start listening on UDP port 7012

3. **Verify Connection** (immediate)
   - Status changes to "Receiving (60 FPS)"
   - Real-time skeleton appears in 3D view
   - Mimics performer's movements instantly

4. **Robot Control** (continuous)
   - BVH Viewer acts as data relay/visualizer
   - External retargeting script maps human skeleton to robot joints
   - Example: Unitree G1 SDK reads BVH stream via UDP

5. **Record Session** (optional)
   - Press `R` to record motion data
   - Useful for debugging and replay
   - Export to BVH for offline analysis

**Best For**:
- Humanoid robot teleoperation
- Real-time performance capture
- Motion retargeting applications
- VR/AR character control

---

### 3. Motion Analysis (Offline Mode)

**Scenario**: Analyze pre-recorded BVH animation data

**Workflow**:
1. **Load BVH File** (5 seconds)
   - Click "Load" button or drag-drop `.bvh` file
   - File parses and displays skeleton in T-pose
   - Timeline shows total frames and duration

2. **Playback Control**
   - Press `Space` to play/pause
   - `←` / `→` arrow keys for frame stepping
   - Click timeline to jump to specific frame
   - Adjust playback speed with UI controls

3. **Kinematic Analysis**
   - View real-time joint positions (left panel)
   - Monitor velocities and accelerations
   - Export kinematic data to CSV:
     - Click "Export" button
     - Data includes position, velocity, acceleration per frame

4. **Trajectory Visualization**
   - Click "Trajectory" button
   - Select joints to track (e.g., hands, feet, head)
   - Customize colors for each trajectory
   - Visual path shows movement over time

5. **Data Export**
   - **CSV Export**: All kinematic parameters
   - **BVH Re-export**: Modified/filtered animation

**Best For**:
- Post-production animation cleanup
- Biomechanical research
- Motion quality assessment
- Educational demonstrations

---

### 4. Tennis Serve Analysis (Offline Mode)

**Scenario**: Biomechanical analysis of tennis serve technique

**Workflow**:
1. **Load Tennis Serve BVH** (5 seconds)
   - Must contain full-body motion capture of serve
   - Recommended: 120+ FPS for accuracy

2. **Run Analysis** (click "Tennis Analysis")
   - **Automatic Phase Detection**:
     - Preparation (stance and ball toss)
     - Backswing (racket goes back)
     - Forward Swing (acceleration phase)
     - Contact (ball impact)
     - Follow-through (deceleration)
   
   - **Biomechanical Metrics Calculated**:
     - Racket speed at contact (km/h)
     - Ball contact point (3D coordinates)
     - Shoulder rotation angles
     - Hip rotation angles
     - Knee flexion angles
     - Spine lateral tilt
     - Energy transfer efficiency

3. **Visualization**
   - Phase markers on timeline
   - Angle graphs (shoulder, hip, knee)
   - Speed curve overlay
   - 3D contact point indicator

4. **Export Analysis Results**
   - JSON report with all metrics
   - PNG graphs of angle changes
   - CSV data for statistical analysis
   - History saved in `tennis_analysis_history.json`

**Best For**:
- Sports coaching and technique improvement
- Injury prevention analysis
- Performance comparison (before/after training)
- Research in sports biomechanics

## 🎮 Complete Controls Reference

### Mouse Controls

| Action | Control | Description |
|--------|---------|-------------|
| **Pan Camera** | Left Mouse Drag | Move camera horizontally and vertically |
| **Rotate View** | Right Mouse Drag | Rotate camera around skeleton (horizontal only) |
| **Reset View** | Middle Mouse Click | Return to default camera position |
| **Zoom In** | Scroll Wheel Up | Move camera closer to skeleton |
| **Zoom Out** | Scroll Wheel Down | Move camera away from skeleton |
| **Timeline Seek** | Left Click + Drag on Timeline | Scrub through animation frames |
| **Button Click** | Left Click | Activate UI buttons |

### Keyboard Shortcuts

#### Mode and Connection
| Key | Function | Description |
|-----|----------|-------------|
| `M` | **Switch Mode** | Cycle through Offline → Mocap → Secap → Offline |
| `Ctrl+1` | **Switch to Offline** | Directly switch to Offline mode with gray toast notification |
| `Ctrl+2` | **Switch to Mocap** | Directly switch to Mocap mode with green toast notification |
| `Ctrl+3` | **Switch to Secap** | Directly switch to Secap mode with blue toast notification |
| `C` | **Toggle Connection** | Connect/Disconnect (Mocap) or Listen/Stop (Secap) |
| `K` | **Calibrate** | Start calibration sequence (Mocap mode only) |

#### Recording and Export
| Key | Function | Description |
|-----|----------|-------------|
| `R` | **Toggle Recording** | Start/stop motion data recording |
| `E` | **Export BVH** | Save recorded data to BVH file |

#### Playback (Offline Mode)
| Key | Function | Description |
|-----|----------|-------------|
| `Space` | **Play/Pause** | Toggle animation playback |
| `←` | **Previous Frame** | Step backward one frame |
| `→` | **Next Frame** | Step forward one frame |

#### View Controls
| Key | Function | Description |
|-----|----------|-------------|
| `F` | **Reset View** | Return camera to default position and angle |

### UI Buttons

#### Mode Switching Panel (Left Bottom)
| Button | Color | Function |
|--------|-------|----------|
| **Mode** | Gray/Green/Blue | Current mode indicator with dropdown menu |
|  | • Gray = Offline | Click to open dropdown menu |
|  | • Green = Mocap | Select mode from list: Offline, Mocap, Secap |
|  | • Blue = Secap | Each option shows color indicator and text label |

**Dropdown Menu Features**:
- **Visual Indicators**: Color dots matching mode (gray/green/blue)
- **Text Labels**: Clear mode names (Offline, Mocap, Secap)
- **Selection Marker**: Blue dot indicates currently active mode
- **Hover Feedback**: Light blue highlight on hover
- **Click to Select**: Choose any mode instantly
- **Auto-close**: Menu closes after selection or when clicking outside

#### Connection Panel (Real-time Modes)
| Button | Availability | Function |
|--------|--------------|----------|
| **Connect** | Mocap mode | Establish connection to motion capture device |
| **Disconnect** | Mocap mode | Close device connection |
| **Listen** | Secap mode | Start listening for UDP broadcast |
| **Stop** | Secap mode | Stop listening |

#### Recording Panel
| Button | Color When Active | Function |
|--------|-------------------|----------|
| **Record** | Red | Start recording motion data |
| **Stop** | Gray | Stop recording (shows frame count) |
| **Export BVH** | N/A | Save recorded data to file |

#### Calibration Panel (Mocap Mode Only)
| Button | Color | Function |
|--------|-------|----------|
| **Calibrate** | Blue (ready) | Start calibration process |
|  | Orange (in progress) | Calibration active |
|  | Green (complete) | Calibration successful |
|  | Red (failed) | Calibration error - retry |

#### File Operations (Offline Mode)
| Button | Function |
|--------|----------|
| **Load** | Open BVH file dialog |
| **Export** | Export kinematic data to CSV |

#### Analysis Tools
| Button | Function |
|--------|----------|
| **Trajectory** | Configure joint trajectory visualization |
| **Tennis Analysis** | Run tennis serve biomechanical analysis |

### Status Indicators

#### Offline Mode
- **Frame Counter**: Current frame / Total frames
- **FPS Display**: Animation playback frame rate
- **Timeline Bar**: Visual progress indicator

#### Mocap Mode
- **Connection Status**: Disconnected / Connecting / Connected / Capturing
- **Stabilization Timer**: Countdown during 20-second stabilization
- **Calibration Progress**: Pose name, countdown, percentage
- **Capture FPS**: Real-time frame rate from device

#### Secap Mode  
- **Listening Status**: Not Listening / Waiting for Data / Receiving
- **UDP Port**: Port number being monitored (default: 7012)
- **Receive FPS**: Incoming data frame rate
- **Warning**: "⚠️ Please start BVH broadcast in Axis Studio" (if no data)

#### Recording Status (All Modes)
- **Recording**: Frame count and duration
- **Recorded**: Total frames captured when stopped

### Toast Notification System

**Visual Feedback for All Operations**:

The application uses a sophisticated toast notification system to provide immediate, non-intrusive feedback:

| Notification Type | Color | Use Case | Auto-Dismiss |
|------------------|-------|----------|-------------|
| **Success** | Green (#34C759) | Successful operations (Mocap mode switch, connection established) | 3 seconds |
| **Info** | Blue (#007AFF) | Informational messages (Secap mode switch) | 3 seconds |
| **Neutral** | Gray (#8E8E93) | Neutral state changes (Offline mode switch) | 3 seconds |
| **Warning** | Orange (#FF9500) | Caution messages (calibration needed) | 4 seconds |
| **Error** | Red (#FF3B30) | Operation failures (connection failed, SDK unavailable) | 5 seconds |

**Toast Features**:
- **Position**: Top-right corner, non-blocking
- **Animation**: Smooth slide-in from right, fade-out on dismiss
- **Stacking**: Up to 5 toasts can display simultaneously
- **Icon**: Each type has a distinct icon (✓, ℹ, ●, ⚠, ✗)
- **Auto-clear**: Older toasts automatically removed when new ones arrive

---

## 🔧 Troubleshooting Guide

### Common Issues and Solutions

#### 1. Application Won't Start

**Symptom**: Double-clicking exe shows error or nothing happens

**Solutions**:
- **Missing Visual C++ Redistributable**:
  ```
  Download and install:
  Microsoft Visual C++ Redistributable (latest version)
  https://aka.ms/vs/17/release/vc_redist.x64.exe
  ```

- **Antivirus Blocking**:
  - Add `BVH_Viewer.exe` to antivirus exceptions
  - Windows Defender: Settings → Virus & Threat Protection → Exclusions

- **Missing OpenGL Support**:
  - Update graphics drivers (NVIDIA/AMD/Intel)
  - Verify OpenGL version: Run `dxdiag` → Display tab

#### 2. Mocap Mode Connection Failed

**Symptom**: "Connection failed" or "Device not found" message

**Checklist**:
- [ ] Device is powered on and LED indicators show active
- [ ] Network cable connected (or WiFi configured)
- [ ] Computer and device on same subnet
  ```powershell
  # Check your IP: Open PowerShell
  ipconfig
  # Look for IPv4 Address (e.g., 10.42.0.101)
  ```
- [ ] IP addresses match in `mocap_connector.py`
- [ ] Firewall allows Python/exe on ports 8002 and 8080
- [ ] No other software using same ports

**Advanced Troubleshooting**:
```powershell
# Test network connectivity
ping 10.42.0.202

# Check port availability
netstat -an | findstr :8002
netstat -an | findstr :8080
```

#### 3. Calibration Timeout or Fails

**Symptom**: Calibration never completes or shows "Failed"

**Solutions**:
- **Stabilization not complete**: Wait full 20 seconds without moving
- **Incorrect pose**: 
  - F-Pose: Stand straight, arms at sides, palms forward
  - T-Pose: Stand straight, arms horizontal, palms down
  - Follow exact pose shown in Axis Studio documentation
- **Sensor interference**: 
  - Remove metal objects nearby
  - Avoid magnetic fields (speakers, monitors)
- **Firmware outdated**: Update device firmware via Axis Studio
- **Retry**: Click "Calibrate" again (state resets automatically)

#### 4. Secap Mode Not Receiving Data

**Symptom**: "Waiting for Data..." never changes to "Receiving"

**Step-by-Step Fix**:

1. **Verify Axis Studio Broadcast**:
   - Axis Studio → Settings → BVH Data Broadcast
   - Check "Enable UDP Broadcast" is ticked
   - Port shows `7012`
   - Target IP matches BVH Viewer computer

2. **Check Network Configuration**:
   ```powershell
   # Same computer (most common):
   Target IP in Axis Studio: 127.0.0.1
   
   # Different computers:
   # On BVH Viewer computer, run:
   ipconfig
   # Note IPv4 Address (e.g., 192.168.1.50)
   # Set this as Target IP in Axis Studio
   ```

3. **Firewall Rules**:
   - Windows Firewall → Advanced Settings → Inbound Rules
   - Create new rule: Allow UDP port 7012
   - Apply to both Private and Public networks

4. **Test UDP Reception**:
   ```powershell
   # Verify port is listening (after clicking "Listen" in BVH Viewer)
   netstat -an | findstr :7012
   # Should show: UDP 0.0.0.0:7012 *:*
   ```

5. **Port Conflict**:
   - Change to different port (e.g., 7013) in both:
     - `axis_studio_connector.py` line 58
     - Axis Studio broadcast settings

#### 5. Poor Frame Rate / Lag

**Symptom**: Animation stutters, low FPS displayed

**Optimizations**:
- **Disable trajectory visualization**: Click "Trajectory" → Unselect all joints
- **Close other applications**: Free up CPU/GPU resources
- **Reduce window size**: Smaller rendering area = better performance
- **Update graphics drivers**: Latest NVIDIA/AMD drivers
- **Lower quality settings** (for developers):
  ```python
  # In bvh_visualizer_improved.py, modify:
  UIConfig.DEFAULT_TARGET_FPS = 30  # Reduce from 60
  ```

#### 6. BVH Export Fails

**Symptom**: "Export failed" message or corrupted BVH file

**Solutions**:
- **Insufficient disk space**: Check free space (need ~10-50 MB per minute)
- **File path too long**: Save to shorter path (e.g., `C:\Exports\`)
- **No recording data**: Record at least 1 frame before exporting
- **Permissions issue**: Run as administrator or save to user folder

#### 7. Tennis Analysis Returns No Results

**Symptom**: "No serve detected" or empty analysis window

**Requirements**:
- BVH file must contain:
  - Full body skeleton (minimum: arms, shoulders, spine, hips)
  - At least 120 frames (2 seconds at 60 FPS)
  - Clear serve motion (preparation → contact → follow-through)

**Troubleshooting**:
- **Frame rate too low**: Re-record at 60+ FPS
- **Incomplete skeleton**: Verify all required joints present
- **Motion too fast**: Analysis needs smooth motion, not teleporting

#### 8. "Module not found" Errors (Developers)

**Symptom**: `ImportError: No module named 'pygame'` or similar

**Solution**:
```bash
# Reinstall all dependencies
pip install --force-reinstall -r requirements.txt

# If specific module missing:
pip install pygame PyOpenGL PyOpenGL-accelerate numpy matplotlib
```

### Getting Help

If issues persist:

1. **Check documentation**:
   - [MODE_INTRODUCTION.md](MODE_INTRODUCTION.md) - Mode-specific guides
   - [SECAP_QUICKSTART.md](SECAP_QUICKSTART.md) - Secap setup details

2. **Enable console output** (for developers):
   - Run from command line: `BVH_Viewer.exe`
   - Or modify build spec: `console=True`
   - Check error messages in console window

3. **Report bugs**:
   - Include: OS version, Python version (if running from source)
   - Attach: Error messages, screenshots
   - Describe: Steps to reproduce the issue

---

## 👨‍💻 Developer Information

### Code Structure and Architecture

#### Module Overview

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `bvh_visualizer_improved.py` | 3700+ | Main application loop, UI rendering, OpenGL graphics, mode management |
| `ui/components.py` | 900+ | Apple-style UI components (buttons, toasts, dropdowns, panels) |
| `ui/renderer.py` | 920+ | OpenGL 2D/3D rendering functions, drawing utilities |
| `ui/colors.py` | 200+ | Color definitions, gradients, glass effects |
| `ui/metrics.py` | 150+ | UI metrics, spacing, animation parameters |
| `mocap_connector.py` | 600+ | Mocap device communication, calibration, data streaming |
| `axis_studio_connector.py` | 330+ | UDP broadcast receiver, Axis Studio integration |
| `recording_manager.py` | 330+ | Frame buffering, BVH export, quaternion math |
| `mocap_api.py` | 1300+ | Low-level MocapAPI SDK bindings |

#### Key Classes

```python
# Application state management
class AppMode:
    OFFLINE = "offline"  # BVH file playback
    MOCAP = "mocap"      # Direct device connection  
    SECAP = "secap"      # Axis Studio broadcast

class AppState:
    mode: str                              # Current mode
    mocap_connector: MocapConnector        # Mocap mode handler
    axis_studio_connector: AxisStudioConnector  # Secap mode handler
    recording_manager: RecordingManager    # Shared recorder

# Skeleton representation
class Joint:
    name: str                    # Joint identifier
    parent: Joint                # Hierarchical parent
    children: List[Joint]        # Child joints
    offset: np.ndarray           # Local position offset
    matrix: np.ndarray           # 4x4 transformation matrix
    channels: List[str]          # Animation channels

# UI configuration
class UIConfig:
    WINDOW_SCALE_FACTOR = 0.75   # Window size ratio
    CAMERA_FOV = 45              # Field of view
    MOUSE_PAN_SENSITIVITY = 0.2  # Pan speed
    # ... 30+ configuration parameters
```

#### Data Flow

```
Offline Mode:
BVH File → parse_bvh() → Joint hierarchy → update_joint_matrices() → OpenGL rendering

Mocap Mode:
Device → MocapConnector.poll_and_update() → Frame data → update_realtime_joints() → Rendering
                                              └→ RecordingManager → BVH export

Secap Mode:  
Axis Studio → UDP:7012 → AxisStudioConnector.poll_and_update() → Frame data → Rendering
                                                                   └→ RecordingManager
```

### Development Setup

#### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git (for version control)
- Visual Studio Code or PyCharm (recommended IDEs)

#### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/BVH_Viewer.git
cd BVH_Viewer

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python bvh_visualizer_improved.py
```

#### Code Style Guidelines

- **PEP 8 compliance**: 4-space indentation, max 79 chars per line
- **Type hints**: Use for function signatures where practical
- **Docstrings**: Google style for all public functions/classes
- **Comments**: Explain "why", not "what" (code is self-documenting)

#### Testing

```bash
# Run application with different modes
python bvh_visualizer_improved.py  # Start in Offline mode

# Test BVH parsing
# Load sample BVH files from test_data/ folder

# Test Mocap mode (requires hardware)
# Configure IP in mocap_connector.py first

# Test Secap mode
# Start Axis Studio, enable UDP broadcast
# Switch to Secap mode, verify reception
```

### Contributing Guidelines

#### Pull Request Process

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature-name`
3. **Make changes**: Follow code style guidelines
4. **Test thoroughly**: All three modes, all features
5. **Commit**: `git commit -m "Feature: Add XYZ functionality"`
6. **Push**: `git push origin feature/your-feature-name`
7. **Open Pull Request**: Describe changes, reference issues

#### Feature Requests

- Use GitHub Issues with "enhancement" label
- Describe use case and expected behavior
- Include mockups/diagrams if applicable

#### Bug Reports

Include:
- OS version and Python version
- Steps to reproduce
- Expected vs actual behavior  
- Error messages / stack traces
- Screenshots (if UI-related)

### Extending the Application

#### Adding a New Analysis Module

```python
# Example: Adding basketball shot analysis

class BasketballAnalyzer:
    """Analyze basketball shooting form"""
    
    def __init__(self, joints_data, fps):
        self.joints = joints_data
        self.fps = fps
    
    def detect_shot_phases(self):
        """Detect: stance, gather, shot, release, follow-through"""
        # Implementation here
        pass
    
    def calculate_shot_angle(self):
        """Calculate release angle and arc"""
        # Implementation here
        pass

# Register in main UI:
# Add button in draw_analysis_panel()
# Hook up to analyzer on click
```

#### Adding a New Export Format

```python
# In recording_manager.py

def export_to_fbx(self, file_path: str) -> bool:
    """Export recorded data to FBX format"""
    # Convert BVH hierarchy to FBX
    # Write binary FBX file
    pass
```

---

## 📜 Version History

### Version 1.1 (Current - December 2024)
- ✅ **UI/UX Overhaul**: Complete redesign with Apple-style interface
  - Glass morphism effects with translucent panels
  - Smooth animations at 60 FPS
  - Modern color scheme and visual hierarchy
- ✅ **Enhanced Mode Switching**: 
  - Dropdown menu with visual indicators
  - Keyboard shortcuts (Ctrl+1/2/3)
  - Toast notifications for feedback
- ✅ **Smart Notifications System**:
  - Color-coded toast messages (Gray/Green/Blue)
  - Auto-dismiss with fade animations
  - Support for 5 notification types
- ✅ **User Preferences**: 
  - Automatic saving of UI states
  - Persistent panel visibility settings
  - Configuration file in AppData
- ✅ **Improved Components**:
  - Apple-style buttons with hover effects
  - Animated dropdown menus
  - Enhanced status indicators

### Version 1.0 (Initial Release)
- ✅ Three operation modes (Offline/Mocap/Secap)
- ✅ Real-time motion capture at 60 FPS
- ✅ BVH file import/export
- ✅ Kinematic analysis (position, velocity, acceleration)
- ✅ Trajectory visualization
- ✅ Tennis serve analysis
- ✅ Network configuration (TCP/UDP)
- ✅ Comprehensive documentation

### Planned Features (Future Versions)
- ⏳ Multi-skeleton support (multiple actors)
- ⏳ FBX/GLTF export formats
- ⏳ Video overlay (sync motion with video)
- ⏳ More sports analysis modules (basketball, golf, etc.)
- ⏳ Cloud storage integration
- ⏳ Collaborative viewing (multi-user)

---

## 📝 License and Credits

### License

This project is developed for motion capture data visualization and analysis.

### Third-Party Libraries

- **Pygame**: LGPL License - https://www.pygame.org/
- **PyOpenGL**: BSD License - http://pyopengl.sourceforge.net/
- **NumPy**: BSD License - https://numpy.org/
- **Matplotlib**: PSF License - https://matplotlib.org/
- **MocapAPI SDK**: Noitom Ltd. - https://www.noitom.com/

### Acknowledgments

- Noitom Technology for MocapAPI SDK and technical support
- Axis Studio for BVH broadcast protocol documentation
- Unitree Robotics for robot control use case inspiration

### Contact

For questions, bug reports, or collaboration inquiries:
- **Email**: yang.liu@noitom.com
---

**⭐ If you find this project useful, please consider giving it a star on GitHub!**

**Built with ❤️ for the motion capture and animation community**
