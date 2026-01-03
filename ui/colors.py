# -*- coding: utf-8 -*-
"""
Apple-style Color Palette
=========================

Color definitions following Apple Human Interface Guidelines.
All colors are in RGB(A) format with values from 0.0 to 1.0.

Reference: https://developer.apple.com/design/human-interface-guidelines/color
"""

from typing import Tuple

# Type alias for color tuples
Color3 = Tuple[float, float, float]
Color4 = Tuple[float, float, float, float]


class AppleUIColors:
    """
    Apple Design Language color palette - Light Mode
    
    This class provides a comprehensive set of colors that follow
    Apple's Human Interface Guidelines for creating modern, clean UIs.
    
    Color Categories:
        - Background colors (primary, secondary, tertiary)
        - Accent colors (blue, green, red, orange, etc.)
        - Text colors (primary, secondary, tertiary)
        - UI element colors (borders, separators, shadows)
        - Button state colors (default, hover, pressed, disabled)
        - Mode indicator colors (offline, mocap, secap)
    
    Usage:
        from ui.colors import AppleUIColors
        
        # Get background color
        bg = AppleUIColors.BACKGROUND_PRIMARY
        
        # Get accent color for buttons
        btn_color = AppleUIColors.ACCENT_BLUE
    """
    
    # ==================== Background Colors ====================
    # Used for main window, panels, and cards
    
    BACKGROUND_PRIMARY: Color4 = (0.98, 0.98, 0.98, 1.0)      # #FAFAFA - Main background
    BACKGROUND_SECONDARY: Color4 = (0.95, 0.95, 0.97, 1.0)    # #F2F2F7 - Card/panel background
    BACKGROUND_TERTIARY: Color4 = (1.0, 1.0, 1.0, 1.0)        # #FFFFFF - Pure white
    BACKGROUND_ELEVATED: Color4 = (1.0, 1.0, 1.0, 1.0)        # Elevated surfaces
    
    # 3D viewport background - slightly warm white
    VIEWPORT_BACKGROUND: Color4 = (0.96, 0.96, 0.96, 1.0)     # #F5F5F5
    
    # ==================== Accent Colors ====================
    # Primary action colors following Apple's color system
    
    # Apple Blue - Primary accent for interactive elements
    ACCENT_BLUE: Color4 = (0.0, 0.478, 1.0, 1.0)              # #007AFF
    ACCENT_BLUE_LIGHT: Color4 = (0.25, 0.61, 1.0, 1.0)        # #40A0FF - Lighter variant
    ACCENT_BLUE_DARK: Color4 = (0.0, 0.40, 0.85, 1.0)         # #0066D9 - Darker variant
    
    # Apple Green - Success, positive actions, Mocap mode
    ACCENT_GREEN: Color4 = (0.20, 0.78, 0.35, 1.0)            # #34C759
    ACCENT_GREEN_LIGHT: Color4 = (0.35, 0.85, 0.50, 1.0)      # #5AD97F
    ACCENT_GREEN_DARK: Color4 = (0.15, 0.65, 0.28, 1.0)       # #26A647
    
    # Apple Red - Destructive actions, warnings, recording
    ACCENT_RED: Color4 = (1.0, 0.23, 0.19, 1.0)               # #FF3B30
    ACCENT_RED_LIGHT: Color4 = (1.0, 0.45, 0.42, 1.0)         # #FF736B
    ACCENT_RED_DARK: Color4 = (0.85, 0.18, 0.15, 1.0)         # #D92E26
    
    # Apple Orange - Warnings, calibration in progress
    ACCENT_ORANGE: Color4 = (1.0, 0.58, 0.0, 1.0)             # #FF9500
    ACCENT_ORANGE_LIGHT: Color4 = (1.0, 0.70, 0.30, 1.0)      # #FFB34D
    ACCENT_ORANGE_DARK: Color4 = (0.85, 0.48, 0.0, 1.0)       # #D97A00
    
    # Apple Yellow - Caution, stabilizing
    ACCENT_YELLOW: Color4 = (1.0, 0.80, 0.0, 1.0)             # #FFCC00
    
    # Apple Teal - Alternative accent
    ACCENT_TEAL: Color4 = (0.35, 0.78, 0.80, 1.0)             # #59C7CC
    
    # Apple Purple - Special features
    ACCENT_PURPLE: Color4 = (0.69, 0.32, 0.87, 1.0)           # #AF52DE
    
    # Apple Pink - Tennis analysis / Sports
    ACCENT_PINK: Color4 = (1.0, 0.18, 0.33, 1.0)              # #FF2D55
    
    # Neutral Gray - Offline mode, disabled states
    ACCENT_GRAY: Color4 = (0.56, 0.56, 0.58, 1.0)             # #8E8E93
    ACCENT_GRAY_LIGHT: Color4 = (0.68, 0.68, 0.70, 1.0)       # #AEAEB2
    ACCENT_GRAY_DARK: Color4 = (0.44, 0.44, 0.46, 1.0)        # #707075
    
    # ==================== Text Colors ====================
    # Typography colors for different hierarchy levels
    
    TEXT_PRIMARY: Color4 = (0.0, 0.0, 0.0, 1.0)               # Primary text - Black
    TEXT_SECONDARY: Color4 = (0.24, 0.24, 0.26, 0.6)          # Secondary text - 60% opacity
    TEXT_TERTIARY: Color4 = (0.24, 0.24, 0.26, 0.3)           # Placeholder/disabled - 30%
    TEXT_QUATERNARY: Color4 = (0.24, 0.24, 0.26, 0.18)        # Very subtle text
    
    # Text on colored backgrounds
    TEXT_ON_ACCENT: Color4 = (1.0, 1.0, 1.0, 1.0)             # White text on accent colors
    TEXT_ON_DARK: Color4 = (1.0, 1.0, 1.0, 0.85)              # White text on dark bg
    
    # ==================== UI Element Colors ====================
    # Borders, separators, and structural elements
    
    SEPARATOR: Color4 = (0.24, 0.24, 0.26, 0.29)              # Separator lines
    SEPARATOR_OPAQUE: Color3 = (0.82, 0.82, 0.84)             # Opaque separator
    
    BORDER_LIGHT: Color4 = (0.0, 0.0, 0.0, 0.1)               # Light border
    BORDER_MEDIUM: Color4 = (0.0, 0.0, 0.0, 0.15)             # Medium border
    BORDER_DARK: Color4 = (0.0, 0.0, 0.0, 0.25)               # Dark border
    
    # Shadow color (used with varying opacity)
    SHADOW: Color4 = (0.0, 0.0, 0.0, 0.15)                    # Default shadow
    
    # ==================== Button State Colors ====================
    # Colors for interactive button states
    
    BUTTON_DEFAULT: Color4 = (0.95, 0.95, 0.97, 1.0)          # Default state - #F2F2F7
    BUTTON_HOVER: Color4 = (0.90, 0.90, 0.92, 1.0)            # Hover state - slightly darker
    BUTTON_PRESSED: Color4 = (0.85, 0.85, 0.87, 1.0)          # Pressed state - even darker
    BUTTON_DISABLED: Color4 = (0.95, 0.95, 0.97, 0.5)         # Disabled - 50% opacity
    
    # Primary button (filled with accent color)
    BUTTON_PRIMARY: Color4 = ACCENT_BLUE
    BUTTON_PRIMARY_HOVER: Color4 = ACCENT_BLUE_DARK
    BUTTON_PRIMARY_PRESSED: Color4 = (0.0, 0.35, 0.75, 1.0)   # Darker blue
    
    # Destructive button
    BUTTON_DESTRUCTIVE: Color4 = ACCENT_RED
    BUTTON_DESTRUCTIVE_HOVER: Color4 = ACCENT_RED_DARK
    
    # ==================== Mode Indicator Colors ====================
    # Colors for the three application modes
    
    MODE_OFFLINE: Color4 = ACCENT_GRAY                         # Gray for offline
    MODE_OFFLINE_BG: Color4 = (0.56, 0.56, 0.58, 0.15)        # Light gray background
    
    MODE_MOCAP: Color4 = ACCENT_GREEN                          # Green for Mocap
    MODE_MOCAP_BG: Color4 = (0.20, 0.78, 0.35, 0.15)          # Light green background
    
    MODE_SECAP: Color4 = ACCENT_BLUE                           # Blue for Secap
    MODE_SECAP_BG: Color4 = (0.0, 0.478, 1.0, 0.15)           # Light blue background
    
    # ==================== Status Colors ====================
    # Colors for various states and statuses
    
    STATUS_CONNECTED: Color4 = ACCENT_GREEN
    STATUS_DISCONNECTED: Color4 = ACCENT_GRAY
    STATUS_CONNECTING: Color4 = ACCENT_ORANGE
    STATUS_ERROR: Color4 = ACCENT_RED
    
    STATUS_RECORDING: Color4 = ACCENT_RED
    STATUS_RECORDING_PULSE: Color4 = (1.0, 0.4, 0.35, 1.0)    # Pulsing red
    
    STATUS_CALIBRATING: Color4 = ACCENT_ORANGE
    STATUS_CALIBRATED: Color4 = ACCENT_GREEN
    STATUS_CALIBRATION_READY: Color4 = ACCENT_BLUE
    
    STATUS_STABILIZING: Color4 = ACCENT_YELLOW
    STATUS_RECEIVING: Color4 = ACCENT_GREEN
    STATUS_WAITING: Color4 = ACCENT_ORANGE
    
    # ==================== Skeleton Rendering Colors ====================
    # Colors for 3D skeleton visualization
    
    SKELETON_BONE: Color3 = (0.3, 0.3, 0.3)                   # Bone color
    SKELETON_JOINT: Color3 = (0.2, 0.6, 0.9)                  # Joint sphere color
    SKELETON_SELECTED: Color3 = (1.0, 0.6, 0.0)               # Selected joint
    SKELETON_ROOT: Color3 = (0.9, 0.2, 0.2)                   # Root joint (Hips)
    
    # Grid and axis colors
    GRID_LINE: Color4 = (0.7, 0.7, 0.7, 0.5)                  # Grid lines
    GRID_MAJOR: Color4 = (0.5, 0.5, 0.5, 0.6)                 # Major grid lines
    AXIS_X: Color3 = (0.9, 0.2, 0.2)                          # X axis - Red
    AXIS_Y: Color3 = (0.2, 0.9, 0.2)                          # Y axis - Green
    AXIS_Z: Color3 = (0.2, 0.2, 0.9)                          # Z axis - Blue
    
    # ==================== Timeline Colors ====================
    # Colors for playback timeline
    
    TIMELINE_BACKGROUND: Color4 = (0.85, 0.85, 0.87, 1.0)     # Track background
    TIMELINE_PROGRESS: Color4 = ACCENT_BLUE                    # Progress bar
    TIMELINE_HANDLE: Color4 = (0.3, 0.3, 0.3, 1.0)            # Scrubber handle
    TIMELINE_FRAME_MARKER: Color4 = (0.4, 0.4, 0.4, 0.5)      # Frame markers
    
    # ==================== Panel Colors ====================
    # Colors for UI panels (position/velocity displays)
    
    PANEL_BACKGROUND: Color4 = (1.0, 1.0, 1.0, 0.95)          # Panel background
    PANEL_HEADER: Color4 = (0.95, 0.95, 0.97, 1.0)            # Panel header
    PANEL_BORDER: Color4 = (0.0, 0.0, 0.0, 0.1)               # Panel border
    
    # ==================== Utility Methods ====================
    
    @staticmethod
    def with_alpha(color: Color4, alpha: float) -> Color4:
        """
        Return a color with modified alpha value.
        
        Args:
            color: Original color tuple (r, g, b, a)
            alpha: New alpha value (0.0 - 1.0)
        
        Returns:
            New color tuple with modified alpha
        """
        return (color[0], color[1], color[2], alpha)
    
    @staticmethod
    def blend(color1: Color4, color2: Color4, factor: float) -> Color4:
        """
        Blend two colors together.
        
        Args:
            color1: First color
            color2: Second color
            factor: Blend factor (0.0 = color1, 1.0 = color2)
        
        Returns:
            Blended color
        """
        factor = max(0.0, min(1.0, factor))
        return (
            color1[0] + (color2[0] - color1[0]) * factor,
            color1[1] + (color2[1] - color1[1]) * factor,
            color1[2] + (color2[2] - color1[2]) * factor,
            color1[3] + (color2[3] - color1[3]) * factor if len(color1) > 3 and len(color2) > 3 else 1.0
        )
    
    @staticmethod
    def darken(color: Color4, amount: float = 0.1) -> Color4:
        """
        Darken a color by a given amount.
        
        Args:
            color: Original color
            amount: Amount to darken (0.0 - 1.0)
        
        Returns:
            Darkened color
        """
        return (
            max(0.0, color[0] - amount),
            max(0.0, color[1] - amount),
            max(0.0, color[2] - amount),
            color[3] if len(color) > 3 else 1.0
        )
    
    @staticmethod
    def lighten(color: Color4, amount: float = 0.1) -> Color4:
        """
        Lighten a color by a given amount.
        
        Args:
            color: Original color
            amount: Amount to lighten (0.0 - 1.0)
        
        Returns:
            Lightened color
        """
        return (
            min(1.0, color[0] + amount),
            min(1.0, color[1] + amount),
            min(1.0, color[2] + amount),
            color[3] if len(color) > 3 else 1.0
        )
    
    @staticmethod
    def to_pygame(color: Color4) -> Tuple[int, int, int, int]:
        """
        Convert normalized color (0-1) to Pygame format (0-255).
        
        Args:
            color: Color in 0-1 range
        
        Returns:
            Color in 0-255 range for Pygame
        """
        return (
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            int(color[3] * 255) if len(color) > 3 else 255
        )
    
    @staticmethod
    def from_hex(hex_color: str) -> Color4:
        """
        Convert hex color string to normalized RGBA tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#FF3B30" or "FF3B30")
        
        Returns:
            Color tuple (r, g, b, a) with values 0.0 - 1.0
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
            return (r, g, b, 1.0)
        elif len(hex_color) == 8:
            r, g, b, a = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4, 6))
            return (r, g, b, a)
        else:
            raise ValueError(f"Invalid hex color: {hex_color}")


# ==================== Color Presets for Quick Access ====================

class ColorPresets:
    """
    Pre-defined color combinations for common UI elements.
    """
    
    # Button color sets: (default, hover, pressed, text)
    BUTTON_SECONDARY = (
        AppleUIColors.BUTTON_DEFAULT,
        AppleUIColors.BUTTON_HOVER,
        AppleUIColors.BUTTON_PRESSED,
        AppleUIColors.TEXT_PRIMARY
    )
    
    BUTTON_PRIMARY = (
        AppleUIColors.ACCENT_BLUE,
        AppleUIColors.ACCENT_BLUE_DARK,
        AppleUIColors.BUTTON_PRIMARY_PRESSED,
        AppleUIColors.TEXT_ON_ACCENT
    )
    
    BUTTON_SUCCESS = (
        AppleUIColors.ACCENT_GREEN,
        AppleUIColors.ACCENT_GREEN_DARK,
        (0.12, 0.55, 0.22, 1.0),
        AppleUIColors.TEXT_ON_ACCENT
    )
    
    BUTTON_DANGER = (
        AppleUIColors.ACCENT_RED,
        AppleUIColors.ACCENT_RED_DARK,
        (0.75, 0.15, 0.12, 1.0),
        AppleUIColors.TEXT_ON_ACCENT
    )
    
    BUTTON_WARNING = (
        AppleUIColors.ACCENT_ORANGE,
        AppleUIColors.ACCENT_ORANGE_DARK,
        (0.75, 0.42, 0.0, 1.0),
        AppleUIColors.TEXT_ON_ACCENT
    )


# ==================== Enhanced Visual Effects ====================

class EnhancedVisuals:
    """
    Additional visual enhancement colors for modern UI effects.
    """
    
    # Gradient colors for buttons
    GRADIENT_BLUE_START: tuple = (0.0, 0.52, 1.0, 1.0)
    GRADIENT_BLUE_END: tuple = (0.0, 0.40, 0.85, 1.0)
    
    GRADIENT_GREEN_START: tuple = (0.25, 0.85, 0.40, 1.0)
    GRADIENT_GREEN_END: tuple = (0.15, 0.65, 0.28, 1.0)
    
    # Glass effect colors
    GLASS_BACKGROUND: tuple = (1.0, 1.0, 1.0, 0.75)
    GLASS_BORDER: tuple = (1.0, 1.0, 1.0, 0.5)
    GLASS_HIGHLIGHT: tuple = (1.0, 1.0, 1.0, 0.3)
    
    # Toast notification colors
    TOAST_SUCCESS_BG: tuple = (0.15, 0.15, 0.15, 0.95)
    TOAST_ERROR_BG: tuple = (0.18, 0.12, 0.12, 0.95)
    TOAST_WARNING_BG: tuple = (0.18, 0.15, 0.10, 0.95)
    TOAST_INFO_BG: tuple = (0.12, 0.14, 0.18, 0.95)
    
    # Dropdown menu colors
    DROPDOWN_BG: tuple = (1.0, 1.0, 1.0, 0.98)
    DROPDOWN_HOVER: tuple = (0.0, 0.478, 1.0, 0.08)
    DROPDOWN_SELECTED: tuple = (0.0, 0.478, 1.0, 0.12)
    
    # Enhanced shadows
    SHADOW_SOFT: tuple = (0.0, 0.0, 0.0, 0.06)
    SHADOW_MEDIUM: tuple = (0.0, 0.0, 0.0, 0.12)
    SHADOW_STRONG: tuple = (0.0, 0.0, 0.0, 0.20)
    
    # Skeleton enhanced colors
    SKELETON_GRADIENT_START: tuple = (0.35, 0.75, 0.95, 1.0)
    SKELETON_GRADIENT_END: tuple = (0.20, 0.50, 0.85, 1.0)
    
    SKELETON_FINGER_COLOR: tuple = (0.75, 0.55, 0.35, 1.0)
    SKELETON_SPINE_COLOR: tuple = (0.55, 0.75, 0.55, 1.0)
    
    # Status indicator glow
    GLOW_GREEN: tuple = (0.20, 0.78, 0.35, 0.3)
    GLOW_RED: tuple = (1.0, 0.23, 0.19, 0.3)
    GLOW_BLUE: tuple = (0.0, 0.478, 1.0, 0.3)
    GLOW_ORANGE: tuple = (1.0, 0.58, 0.0, 0.3)
