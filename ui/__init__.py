# -*- coding: utf-8 -*-
"""
BVH Viewer UI Module
====================

Apple-style UI components for BVH Viewer application.

This module provides:
- AppleUIColors: Color palette following Apple Human Interface Guidelines
- AppleUIMetrics: Spacing, sizing, and dimension constants
- UI Components: Buttons, panels, status bars with hover/click effects
- Animations: Smooth transitions and state changes

Usage:
    from ui import AppleUIColors, AppleUIMetrics, ButtonManager
    from ui.renderer import draw_apple_button, draw_rounded_rect
"""

from .colors import AppleUIColors, EnhancedVisuals
from .metrics import AppleUIMetrics
from .components import (
    ButtonState, ButtonStyle, AppleButton, ButtonManager, ButtonGroup,
    ToastType, Toast, ToastManager,
    DropdownOption, DropdownMenu
)
from .animations import AnimationManager, EasingFunctions

__all__ = [
    'AppleUIColors',
    'AppleUIMetrics',
    'ButtonState',
    'ButtonStyle',
    'AppleButton',
    'ButtonManager',
    'ButtonGroup',
    'AnimationManager',
    'EasingFunctions',
    # New components
    'ToastType',
    'Toast',
    'ToastManager',
    'DropdownOption',
    'DropdownMenu',
]

__version__ = '1.0.0'
