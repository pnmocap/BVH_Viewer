# BVH 3D Viewer

A 3D motion capture data visualization tool for BVH (Biovision Hierarchy) files.

## Features

- **3D Skeleton Visualization**: Real-time 3D rendering of motion capture data using OpenGL
- **BVH File Parsing**: Support for standard BVH file format with hierarchical skeleton structure
- **Interactive Controls**: 
  - Mouse drag to rotate view
  - Mouse wheel to zoom
  - Space bar to play/pause animation
  - Arrow keys to navigate frames
- **Kinematic Analysis**: Real-time calculation of joint angles and motion parameters
- **Customizable Display**: Toggle skeleton display, trajectory visualization, and angle measurements

## Technical Stack

- **Python 3.x**
- **Pygame**: Window management and user input handling
- **PyOpenGL**: 3D graphics rendering
- **NumPy**: Mathematical computations and data processing
- **PyInstaller**: Executable packaging

## Quick Start

### For End Users

1. Download `bvh_visualizer_improved.exe` and the `_internal` folder
2. Run the executable file
3. Load a BVH file to start visualization

### For Developers

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python bvh_visualizer_improved.py
   ```

## Building Executable

To create a standalone executable:

```bash
pyinstaller --onefile --windowed --add-data "demodata.bvh;." bvh_visualizer_improved.py
```

## Project Structure

```
bvh demo 9.12.2/
├── bvh_visualizer_improved.py    # Main application source code
├── bvh_visualizer_improved.exe   # Compiled executable (Windows)
├── _internal/                    # PyInstaller dependencies
├── demodata.bvh                  # Sample BVH file
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## File Delivery Guide

### Minimum Delivery Package (End Users)
- `bvh_visualizer_improved.exe`
- `_internal/` folder

### Development Package (GitHub)
- `bvh_visualizer_improved.py`
- `requirements.txt`
- `.gitignore`
- `README.md`
- Sample BVH files (optional)

### Files to Exclude from GitHub
- `bvh_visualizer_improved.exe`
- `_internal/` folder
- `build/` and `dist/` directories
- `*.spec` files
- Python cache files (`__pycache__/`, `*.pyc`)
- Large BVH files

## BVH File Format

The application supports standard BVH files with:
- HIERARCHY section defining skeleton structure
- MOTION section containing frame data
- Joint rotation data in ZXY order

## Controls

- **Mouse Drag**: Rotate camera view
- **Mouse Wheel**: Zoom in/out
- **Space**: Play/pause animation
- **Left/Right Arrow**: Previous/next frame
- **Up/Down Arrow**: Speed up/slow down playback

## License

This project is developed for motion capture data visualization and analysis.
