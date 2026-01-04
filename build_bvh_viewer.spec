# -*- mode: python ; coding: utf-8 -*-
"""
BVH Viewer - PyInstaller Build Specification
=============================================

This spec file configures PyInstaller to create a standalone executable
for the BVH Viewer application with all dependencies included.

Build command: pyinstaller build_bvh_viewer.spec
Output: dist/BVH_Viewer.exe
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all UI module files
ui_module_hiddenimports = [
    'ui',
    'ui.components',
    'ui.renderer',
    'ui.colors',
    'ui.metrics',
]

# Collect all necessary hidden imports
hidden_imports = [
    # Core dependencies
    'pygame',
    'pygame.locals',
    'pygame.font',
    'pygame.mixer',
    'OpenGL',
    'OpenGL.GL',
    'OpenGL.GLU',
    'OpenGL.GLUT',
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_agg',
    
    # Standard library modules that might be missed
    'json',
    'ctypes',
    'struct',
    'socket',
    'threading',
    'queue',
    'enum',
    'dataclasses',
    'typing',
    
    # Application modules
    'mocap_api',
    'mocap_connector',
    'axis_studio_connector',
    'recording_manager',
] + ui_module_hiddenimports

# Data files to include
datas = [
    # Include the entire ui module directory
    ('ui', 'ui'),
]

# Binaries - PyInstaller will automatically find most DLLs
binaries = []

a = Analysis(
    ['bvh_visualizer_improved.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'test',
        'unittest',
        'pydoc',
        'doctest',
        'xmlrpc',
        'pdb',
        'setuptools',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed application (no console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico',  # Application icon
)
