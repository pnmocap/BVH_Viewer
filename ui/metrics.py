# -*- coding: utf-8 -*-
"""
Apple-style UI Metrics
======================

Spacing, sizing, and dimension constants following Apple Human Interface Guidelines.
All measurements are in pixels unless otherwise noted.

Reference: https://developer.apple.com/design/human-interface-guidelines/layout
"""

from typing import Tuple, NamedTuple
from dataclasses import dataclass


class ShadowParams(NamedTuple):
    """Shadow parameters for UI elements."""
    offset_x: float
    offset_y: float
    blur: float
    opacity: float


@dataclass
class ButtonSize:
    """Button size configuration."""
    width: int
    height: int
    padding_h: int
    padding_v: int
    font_size: int
    corner_radius: int


class AppleUIMetrics:
    """
    Apple Design Language dimension constants.
    
    This class provides standardized measurements for creating
    consistent, well-proportioned UI layouts.
    
    Categories:
        - Corner radius (for rounded rectangles)
        - Button sizes (small, medium, large)
        - Spacing (xs, sm, md, lg, xl, xxl)
        - Shadow parameters
        - Font sizes
        - Animation timing
        - Panel dimensions
    
    Usage:
        from ui.metrics import AppleUIMetrics
        
        # Get corner radius
        radius = AppleUIMetrics.CORNER_RADIUS_MEDIUM
        
        # Get spacing
        margin = AppleUIMetrics.SPACING_LG
    """
    
    # ==================== Corner Radius ====================
    # Standard corner radius values for rounded rectangles
    
    CORNER_RADIUS_NONE: int = 0
    CORNER_RADIUS_XS: int = 4         # Very small elements, tags
    CORNER_RADIUS_SMALL: int = 6      # Small buttons, labels
    CORNER_RADIUS_MEDIUM: int = 10    # Standard buttons
    CORNER_RADIUS_LARGE: int = 14     # Cards, panels
    CORNER_RADIUS_XLARGE: int = 20    # Large panels, modals
    CORNER_RADIUS_FULL: int = 9999    # Fully rounded (pills)
    
    # ==================== Button Dimensions ====================
    # Standard button sizes following Apple's sizing guidelines
    
    # Small button (for compact areas, toolbars)
    BUTTON_HEIGHT_SMALL: int = 28
    BUTTON_MIN_WIDTH_SMALL: int = 48
    BUTTON_PADDING_H_SMALL: int = 10
    BUTTON_PADDING_V_SMALL: int = 4
    BUTTON_FONT_SIZE_SMALL: int = 12
    BUTTON_CORNER_SMALL: int = CORNER_RADIUS_SMALL
    
    # Medium button (default size)
    BUTTON_HEIGHT_MEDIUM: int = 36
    BUTTON_MIN_WIDTH_MEDIUM: int = 64
    BUTTON_PADDING_H_MEDIUM: int = 16
    BUTTON_PADDING_V_MEDIUM: int = 8
    BUTTON_FONT_SIZE_MEDIUM: int = 14
    BUTTON_CORNER_MEDIUM: int = CORNER_RADIUS_MEDIUM
    
    # Large button (primary actions, CTAs)
    BUTTON_HEIGHT_LARGE: int = 44
    BUTTON_MIN_WIDTH_LARGE: int = 80
    BUTTON_PADDING_H_LARGE: int = 20
    BUTTON_PADDING_V_LARGE: int = 10
    BUTTON_FONT_SIZE_LARGE: int = 16
    BUTTON_CORNER_LARGE: int = CORNER_RADIUS_MEDIUM
    
    # Extra large button (full-width actions)
    BUTTON_HEIGHT_XLARGE: int = 50
    BUTTON_MIN_WIDTH_XLARGE: int = 120
    BUTTON_PADDING_H_XLARGE: int = 24
    BUTTON_PADDING_V_XLARGE: int = 12
    BUTTON_FONT_SIZE_XLARGE: int = 17
    BUTTON_CORNER_XLARGE: int = CORNER_RADIUS_LARGE
    
    # Pre-configured button sizes
    BUTTON_SMALL = ButtonSize(
        width=BUTTON_MIN_WIDTH_SMALL,
        height=BUTTON_HEIGHT_SMALL,
        padding_h=BUTTON_PADDING_H_SMALL,
        padding_v=BUTTON_PADDING_V_SMALL,
        font_size=BUTTON_FONT_SIZE_SMALL,
        corner_radius=BUTTON_CORNER_SMALL
    )
    
    BUTTON_MEDIUM = ButtonSize(
        width=BUTTON_MIN_WIDTH_MEDIUM,
        height=BUTTON_HEIGHT_MEDIUM,
        padding_h=BUTTON_PADDING_H_MEDIUM,
        padding_v=BUTTON_PADDING_V_MEDIUM,
        font_size=BUTTON_FONT_SIZE_MEDIUM,
        corner_radius=BUTTON_CORNER_MEDIUM
    )
    
    BUTTON_LARGE = ButtonSize(
        width=BUTTON_MIN_WIDTH_LARGE,
        height=BUTTON_HEIGHT_LARGE,
        padding_h=BUTTON_PADDING_H_LARGE,
        padding_v=BUTTON_PADDING_V_LARGE,
        font_size=BUTTON_FONT_SIZE_LARGE,
        corner_radius=BUTTON_CORNER_LARGE
    )
    
    # ==================== Spacing System ====================
    # Consistent spacing values for margins and padding
    
    SPACING_NONE: int = 0
    SPACING_XXS: int = 2              # Minimal spacing
    SPACING_XS: int = 4               # Extra small
    SPACING_SM: int = 8               # Small
    SPACING_MD: int = 12              # Medium (default)
    SPACING_LG: int = 16              # Large
    SPACING_XL: int = 24              # Extra large
    SPACING_XXL: int = 32             # Double extra large
    SPACING_XXXL: int = 48            # Triple extra large
    
    # Common margin values
    MARGIN_WINDOW: int = 20           # Window edge margin
    MARGIN_PANEL: int = 16            # Panel internal margin
    MARGIN_BUTTON_GROUP: int = 8      # Between buttons in a group
    MARGIN_SECTION: int = 24          # Between UI sections
    
    # ==================== Shadow Parameters ====================
    # Shadow configurations for different elevation levels
    
    SHADOW_NONE = ShadowParams(0, 0, 0, 0)
    
    # Subtle shadow (buttons, small cards)
    SHADOW_SMALL = ShadowParams(
        offset_x=0,
        offset_y=1,
        blur=3,
        opacity=0.1
    )
    
    # Medium shadow (panels, dropdowns)
    SHADOW_MEDIUM = ShadowParams(
        offset_x=0,
        offset_y=2,
        blur=8,
        opacity=0.15
    )
    
    # Large shadow (modals, popovers)
    SHADOW_LARGE = ShadowParams(
        offset_x=0,
        offset_y=4,
        blur=16,
        opacity=0.2
    )
    
    # Extra large shadow (floating elements)
    SHADOW_XLARGE = ShadowParams(
        offset_x=0,
        offset_y=8,
        blur=32,
        opacity=0.25
    )
    
    # Button hover shadow
    SHADOW_BUTTON_HOVER = ShadowParams(
        offset_x=0,
        offset_y=2,
        blur=6,
        opacity=0.12
    )
    
    # ==================== Font Sizes ====================
    # Typography scale following Apple's type system
    
    FONT_SIZE_CAPTION2: int = 11      # Smallest readable text
    FONT_SIZE_CAPTION1: int = 12      # Captions, labels
    FONT_SIZE_FOOTNOTE: int = 13      # Footnotes
    FONT_SIZE_BODY: int = 14          # Body text (default)
    FONT_SIZE_CALLOUT: int = 15       # Callouts
    FONT_SIZE_HEADLINE: int = 16      # Headlines
    FONT_SIZE_TITLE3: int = 18        # Small titles
    FONT_SIZE_TITLE2: int = 20        # Medium titles
    FONT_SIZE_TITLE1: int = 24        # Large titles
    FONT_SIZE_LARGE_TITLE: int = 28   # Display text
    
    # Font weights (for reference, actual font loading needed)
    FONT_WEIGHT_REGULAR: str = "Regular"
    FONT_WEIGHT_MEDIUM: str = "Medium"
    FONT_WEIGHT_SEMIBOLD: str = "Semibold"
    FONT_WEIGHT_BOLD: str = "Bold"
    
    # Preferred fonts (in order of preference)
    FONT_FAMILIES: Tuple[str, ...] = (
        "SF Pro Display",      # macOS San Francisco
        "Segoe UI",            # Windows
        "Helvetica Neue",      # Fallback
        "Arial",               # Universal fallback
    )
    
    # ==================== Animation Timing ====================
    # Duration and easing for smooth animations
    
    # Durations in seconds
    ANIMATION_DURATION_INSTANT: float = 0.0
    ANIMATION_DURATION_FAST: float = 0.1      # Quick feedback
    ANIMATION_DURATION_NORMAL: float = 0.2    # Standard transitions
    ANIMATION_DURATION_SLOW: float = 0.35     # Complex animations
    ANIMATION_DURATION_SLOWER: float = 0.5    # Major transitions
    
    # Animation speeds (used for lerp-based animations)
    ANIMATION_SPEED_FAST: float = 0.25        # Quick response
    ANIMATION_SPEED_NORMAL: float = 0.15      # Standard
    ANIMATION_SPEED_SLOW: float = 0.08        # Smooth, deliberate
    
    # Button press scale factor
    BUTTON_PRESS_SCALE: float = 0.96          # Slightly shrink on press
    BUTTON_HOVER_LIFT: float = 1.0            # No scale on hover
    
    # ==================== Panel Dimensions ====================
    # Sizes for various UI panels
    
    # Position/velocity panels
    PANEL_WIDTH_SMALL: int = 200
    PANEL_WIDTH_MEDIUM: int = 280
    PANEL_WIDTH_LARGE: int = 360
    
    PANEL_ROW_HEIGHT: int = 24                # Height of each data row
    PANEL_HEADER_HEIGHT: int = 32             # Panel header/title height
    PANEL_CORNER_RADIUS: int = CORNER_RADIUS_LARGE
    
    # ==================== Timeline Dimensions ====================
    # Playback timeline component
    
    TIMELINE_HEIGHT: int = 8                  # Track height
    TIMELINE_HEIGHT_EXPANDED: int = 12        # Expanded on hover
    TIMELINE_HANDLE_WIDTH: int = 12           # Scrubber handle width
    TIMELINE_HANDLE_HEIGHT: int = 20          # Scrubber handle height
    TIMELINE_MARGIN_H: int = 60               # Horizontal margin
    TIMELINE_MARGIN_V: int = 40               # Distance from bottom
    
    # ==================== Status Bar ====================
    # Bottom status bar dimensions
    
    STATUS_BAR_HEIGHT: int = 28
    STATUS_INDICATOR_SIZE: int = 8            # Status dot size
    STATUS_PADDING: int = 12
    
    # ==================== Button Groups ====================
    # Layout configuration for button groups
    
    BUTTON_GROUP_SPACING: int = 8             # Space between buttons
    BUTTON_GROUP_PADDING: int = 12            # Padding inside group container
    BUTTON_GROUP_CORNER: int = CORNER_RADIUS_LARGE
    
    # Group title
    GROUP_TITLE_FONT_SIZE: int = 11
    GROUP_TITLE_MARGIN_BOTTOM: int = 8
    
    # ==================== Icon Sizes ====================
    # Standard icon dimensions
    
    ICON_SIZE_SMALL: int = 16
    ICON_SIZE_MEDIUM: int = 20
    ICON_SIZE_LARGE: int = 24
    ICON_SIZE_XLARGE: int = 32
    
    # ==================== Window Configuration ====================
    # Window and display settings
    
    WINDOW_MIN_WIDTH: int = 800
    WINDOW_MIN_HEIGHT: int = 600
    WINDOW_DEFAULT_SCALE: float = 0.75        # Default window size vs screen
    
    # UI area reservations
    UI_TOP_AREA_HEIGHT: int = 50              # Reserved for top toolbar
    UI_BOTTOM_AREA_HEIGHT: int = 120          # Reserved for bottom controls
    UI_SIDE_PANEL_WIDTH: int = 300            # Side panel width
    
    # ==================== Utility Methods ====================
    
    @staticmethod
    def get_button_size(size: str = "medium") -> ButtonSize:
        """
        Get button size configuration by name.
        
        Args:
            size: "small", "medium", or "large"
        
        Returns:
            ButtonSize configuration
        """
        sizes = {
            "small": AppleUIMetrics.BUTTON_SMALL,
            "medium": AppleUIMetrics.BUTTON_MEDIUM,
            "large": AppleUIMetrics.BUTTON_LARGE,
        }
        return sizes.get(size.lower(), AppleUIMetrics.BUTTON_MEDIUM)
    
    @staticmethod
    def get_shadow(elevation: str = "medium") -> ShadowParams:
        """
        Get shadow parameters by elevation level.
        
        Args:
            elevation: "none", "small", "medium", "large", "xlarge"
        
        Returns:
            ShadowParams configuration
        """
        shadows = {
            "none": AppleUIMetrics.SHADOW_NONE,
            "small": AppleUIMetrics.SHADOW_SMALL,
            "medium": AppleUIMetrics.SHADOW_MEDIUM,
            "large": AppleUIMetrics.SHADOW_LARGE,
            "xlarge": AppleUIMetrics.SHADOW_XLARGE,
        }
        return shadows.get(elevation.lower(), AppleUIMetrics.SHADOW_MEDIUM)
    
    @staticmethod
    def scale_for_dpi(value: int, dpi_scale: float = 1.0) -> int:
        """
        Scale a dimension value for high-DPI displays.
        
        Args:
            value: Original pixel value
            dpi_scale: DPI scaling factor (1.0 = 100%, 2.0 = 200%)
        
        Returns:
            Scaled pixel value
        """
        return int(value * dpi_scale)


# ==================== Layout Helpers ====================

class LayoutHelper:
    """
    Helper functions for calculating UI layouts.
    """
    
    @staticmethod
    def center_in_rect(item_width: int, item_height: int,
                       container_x: int, container_y: int,
                       container_width: int, container_height: int) -> Tuple[int, int]:
        """
        Calculate position to center an item within a container.
        
        Returns:
            (x, y) position for centered item
        """
        x = container_x + (container_width - item_width) // 2
        y = container_y + (container_height - item_height) // 2
        return (x, y)
    
    @staticmethod
    def distribute_horizontally(items: int, container_width: int,
                                item_width: int, padding: int = 0) -> list:
        """
        Calculate x positions to distribute items evenly.
        
        Returns:
            List of x positions for each item
        """
        if items <= 0:
            return []
        
        available_width = container_width - (2 * padding)
        total_items_width = items * item_width
        
        if items == 1:
            return [padding + (available_width - item_width) // 2]
        
        spacing = (available_width - total_items_width) / (items - 1)
        
        positions = []
        for i in range(items):
            x = padding + i * (item_width + spacing)
            positions.append(int(x))
        
        return positions
    
    @staticmethod
    def stack_vertically(items: list, start_y: int, spacing: int) -> list:
        """
        Calculate y positions for vertically stacked items.
        
        Args:
            items: List of item heights
            start_y: Starting y position
            spacing: Space between items
        
        Returns:
            List of y positions for each item
        """
        positions = []
        current_y = start_y
        
        for height in items:
            positions.append(current_y)
            current_y += height + spacing
        
        return positions
