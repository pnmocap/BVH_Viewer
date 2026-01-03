# -*- coding: utf-8 -*-
"""
UI Renderer
===========

OpenGL-based rendering functions for Apple-style UI components.
Provides drawing functions for rounded rectangles, buttons, shadows, etc.
"""

import math
from typing import Tuple, Optional, List
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame

from .colors import AppleUIColors
from .metrics import AppleUIMetrics, ShadowParams
from .components import (
    AppleButton, ButtonState, ButtonGroup, Panel,
    StatusIndicator, ModeIndicator, Timeline,
    Toast, ToastManager, ToastType,
    DropdownMenu, DropdownOption
)


def draw_rounded_rect(x: float, y: float, width: float, height: float,
                      radius: float, color: Tuple,
                      border_color: Optional[Tuple] = None,
                      border_width: float = 1.0,
                      segments: int = 8) -> None:
    """
    Draw a rounded rectangle using OpenGL.
    
    Args:
        x, y: Bottom-left corner (OpenGL coordinates)
        width, height: Rectangle dimensions
        radius: Corner radius
        color: Fill color (RGB or RGBA tuple, values 0-1)
        border_color: Optional border color
        border_width: Border line width
        segments: Number of segments per corner arc
    """
    # Clamp radius to valid range
    radius = min(radius, width / 2, height / 2)
    
    if radius <= 0:
        # Fall back to regular rectangle
        draw_rect(x, y, width, height, color, border_color, border_width)
        return
    
    # Set fill color
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    # Draw filled rounded rectangle using triangle fan
    glBegin(GL_TRIANGLE_FAN)
    
    # Center point
    cx, cy = x + width / 2, y + height / 2
    glVertex2f(cx, cy)
    
    # Define corner centers and their angle ranges
    corners = [
        (x + radius, y + radius, 180, 270),                    # Bottom-left
        (x + width - radius, y + radius, 270, 360),            # Bottom-right
        (x + width - radius, y + height - radius, 0, 90),      # Top-right
        (x + radius, y + height - radius, 90, 180),            # Top-left
    ]
    
    # Draw each corner arc
    for corner_x, corner_y, start_angle, end_angle in corners:
        for i in range(segments + 1):
            angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
            px = corner_x + radius * math.cos(angle)
            py = corner_y + radius * math.sin(angle)
            glVertex2f(px, py)
    
    # Close the shape by connecting back to first point
    first_angle = math.radians(180)
    glVertex2f(x + radius + radius * math.cos(first_angle),
               y + radius + radius * math.sin(first_angle))
    
    glEnd()
    
    # Draw border if specified
    if border_color is not None:
        if len(border_color) == 4:
            glColor4f(*border_color)
        else:
            glColor3f(*border_color)
        glLineWidth(border_width)
        
        glBegin(GL_LINE_LOOP)
        for corner_x, corner_y, start_angle, end_angle in corners:
            for i in range(segments + 1):
                angle = math.radians(start_angle + (end_angle - start_angle) * i / segments)
                px = corner_x + radius * math.cos(angle)
                py = corner_y + radius * math.sin(angle)
                glVertex2f(px, py)
        glEnd()


def draw_rect(x: float, y: float, width: float, height: float,
              color: Tuple, border_color: Optional[Tuple] = None,
              border_width: float = 1.0) -> None:
    """
    Draw a simple rectangle (no rounded corners).
    
    Args:
        x, y: Bottom-left corner (OpenGL coordinates)
        width, height: Rectangle dimensions
        color: Fill color
        border_color: Optional border color
        border_width: Border line width
    """
    # Set fill color
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    # Draw filled rectangle
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    
    # Draw border if specified
    if border_color is not None:
        if len(border_color) == 4:
            glColor4f(*border_color)
        else:
            glColor3f(*border_color)
        glLineWidth(border_width)
        
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y)
        glVertex2f(x + width, y)
        glVertex2f(x + width, y + height)
        glVertex2f(x, y + height)
        glEnd()


def draw_shadow(x: float, y: float, width: float, height: float,
                radius: float, shadow_params: ShadowParams) -> None:
    """
    Draw a soft shadow effect using multiple semi-transparent layers.
    
    Args:
        x, y: Bottom-left corner of the object casting shadow
        width, height: Object dimensions
        radius: Corner radius of the object
        shadow_params: Shadow configuration (offset, blur, opacity)
    """
    if shadow_params.opacity <= 0:
        return
    
    offset_x = shadow_params.offset_x
    offset_y = shadow_params.offset_y
    blur = shadow_params.blur
    base_opacity = shadow_params.opacity
    
    # Number of layers for blur simulation
    layers = 5
    
    # Enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    for i in range(layers):
        # Calculate layer parameters
        layer_factor = (layers - i) / layers
        layer_opacity = base_opacity * layer_factor * 0.4
        layer_expand = blur * (i + 1) / layers
        
        # Shadow position (offset down and slightly expanded)
        shadow_x = x + offset_x - layer_expand / 2
        shadow_y = y - offset_y - layer_expand / 2  # Negative Y for downward shadow
        shadow_width = width + layer_expand
        shadow_height = height + layer_expand
        shadow_radius = radius + layer_expand / 2
        
        # Draw shadow layer
        draw_rounded_rect(
            shadow_x, shadow_y, shadow_width, shadow_height,
            shadow_radius,
            (0.0, 0.0, 0.0, layer_opacity)
        )


def draw_circle(cx: float, cy: float, radius: float, color: Tuple,
                segments: int = 32, filled: bool = True) -> None:
    """
    Draw a circle.
    
    Args:
        cx, cy: Center position
        radius: Circle radius
        color: Color tuple
        segments: Number of segments
        filled: Whether to fill the circle
    """
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
    else:
        glBegin(GL_LINE_LOOP)
    
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        px = cx + radius * math.cos(angle)
        py = cy + radius * math.sin(angle)
        glVertex2f(px, py)
    
    glEnd()


def draw_pill(x: float, y: float, width: float, height: float,
              color: Tuple, border_color: Optional[Tuple] = None) -> None:
    """
    Draw a pill-shaped element (fully rounded ends).
    
    Args:
        x, y: Bottom-left corner
        width, height: Dimensions
        color: Fill color
        border_color: Optional border color
    """
    radius = height / 2
    draw_rounded_rect(x, y, width, height, radius, color, border_color)


# ==================== Component Rendering Functions ====================

def draw_apple_button(button: AppleButton, display_height: int,
                      font_renderer=None) -> None:
    """
    Render an Apple-style button.
    
    Args:
        button: AppleButton instance to render
        display_height: Screen height (for coordinate conversion)
        font_renderer: Optional font rendering function
    """
    if not button.visible:
        return
    
    # Convert pygame coordinates to OpenGL coordinates
    # Pygame: (0,0) at top-left, Y increases downward
    # OpenGL: (0,0) at bottom-left, Y increases upward
    gl_x = button.x
    gl_y = display_height - button.y - button.height
    
    # Get current colors
    bg_color = button.get_current_background()
    text_color = button.get_colors().text
    border_color = button.get_colors().border
    
    # Apply scale transformation for press effect
    scale = button._press_scale
    if scale != 1.0:
        # Calculate scaled dimensions
        scaled_width = button.width * scale
        scaled_height = button.height * scale
        
        # Offset to keep centered
        offset_x = (button.width - scaled_width) / 2
        offset_y = (button.height - scaled_height) / 2
        
        gl_x += offset_x
        gl_y += offset_y
        
        actual_width = scaled_width
        actual_height = scaled_height
    else:
        actual_width = button.width
        actual_height = button.height
    
    # Enable blending for transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw shadow on hover
    if button._hover_progress > 0.1 and button.enabled:
        shadow_params = ShadowParams(
            offset_x=0,
            offset_y=2 * button._hover_progress,
            blur=6 * button._hover_progress,
            opacity=0.12 * button._hover_progress
        )
        draw_shadow(gl_x, gl_y, actual_width, actual_height,
                   button.corner_radius, shadow_params)
    
    # Draw button background
    draw_rounded_rect(
        gl_x, gl_y, actual_width, actual_height,
        button.corner_radius * scale,
        bg_color,
        border_color
    )
    
    # Draw text (centered)
    if font_renderer and button.text:
        text_x = gl_x + actual_width / 2
        text_y = gl_y + actual_height / 2
        # Note: Actual text rendering depends on font_renderer implementation
        # This is a placeholder for integration with OverlayManager


def draw_button_group(group: ButtonGroup, buttons: List[AppleButton],
                      display_height: int) -> None:
    """
    Render a button group with container.
    
    Args:
        group: ButtonGroup configuration
        buttons: List of AppleButton instances in this group
        display_height: Screen height for coordinate conversion
    """
    if not group.show_background:
        return
    
    # Calculate group size
    width, height = group.width, group.height
    if width == 0 or height == 0:
        # Auto-calculate
        visible_buttons = [b for b in buttons if b.visible]
        if not visible_buttons:
            return
        
        if group.orientation == "horizontal":
            width = (sum(b.width for b in visible_buttons) + 
                    group.spacing * (len(visible_buttons) - 1) + 
                    2 * group.padding)
            height = max(b.height for b in visible_buttons) + 2 * group.padding
        else:
            width = max(b.width for b in visible_buttons) + 2 * group.padding
            height = (sum(b.height for b in visible_buttons) + 
                     group.spacing * (len(visible_buttons) - 1) + 
                     2 * group.padding)
        
        if group.title:
            height += AppleUIMetrics.GROUP_TITLE_FONT_SIZE + AppleUIMetrics.GROUP_TITLE_MARGIN_BOTTOM
    
    # Convert to OpenGL coordinates
    gl_x = group.x
    gl_y = display_height - group.y - height
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw group background
    draw_rounded_rect(
        gl_x, gl_y, width, height,
        group.corner_radius,
        AppleUIColors.BACKGROUND_SECONDARY,
        AppleUIColors.BORDER_LIGHT
    )


def draw_panel(panel: Panel, display_height: int) -> None:
    """
    Render a panel container.
    
    Args:
        panel: Panel instance
        display_height: Screen height for coordinate conversion
    """
    # Convert to OpenGL coordinates
    gl_x = panel.x
    gl_y = display_height - panel.y - panel.height
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw shadow if enabled
    if panel.show_shadow:
        draw_shadow(gl_x, gl_y, panel.width, panel.height,
                   panel.corner_radius, AppleUIMetrics.SHADOW_MEDIUM)
    
    # Draw panel background
    draw_rounded_rect(
        gl_x, gl_y, panel.width, panel.height,
        panel.corner_radius,
        panel.background,
        panel.border_color
    )


def draw_status_indicator(indicator: StatusIndicator, display_height: int) -> None:
    """
    Render a status indicator (colored dot with label).
    
    Args:
        indicator: StatusIndicator instance
        display_height: Screen height for coordinate conversion
    """
    # Get indicator color
    color = indicator.get_color()
    
    # Apply pulse effect if enabled
    if indicator.show_pulse:
        alpha = indicator.get_pulse_alpha()
        color = (color[0], color[1], color[2], alpha)
    
    # Convert to OpenGL coordinates
    dot_radius = AppleUIMetrics.STATUS_INDICATOR_SIZE / 2
    gl_x = indicator.x + dot_radius
    gl_y = display_height - indicator.y - dot_radius
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw glow effect for active status
    if indicator.status in ["active", "recording", "connected"]:
        glow_color = (color[0], color[1], color[2], 0.3)
        draw_circle(gl_x, gl_y, dot_radius * 1.5, glow_color)
    
    # Draw indicator dot
    draw_circle(gl_x, gl_y, dot_radius, color)


def draw_mode_indicator(indicator: ModeIndicator, display_height: int) -> None:
    """
    Render a mode indicator pill.
    
    Args:
        indicator: ModeIndicator instance
        display_height: Screen height for coordinate conversion
    """
    # Get colors for current mode
    accent_color, bg_color = indicator.get_colors()
    
    # Convert to OpenGL coordinates
    gl_x = indicator.x
    gl_y = display_height - indicator.y - indicator.height
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw background pill
    draw_pill(gl_x, gl_y, indicator.width, indicator.height, bg_color)
    
    # Draw accent dot
    dot_x = gl_x + 10
    dot_y = gl_y + indicator.height / 2
    draw_circle(dot_x, dot_y, 4, accent_color)


def draw_timeline(timeline: Timeline, display_height: int) -> None:
    """
    Render a playback timeline with scrubber.
    
    Args:
        timeline: Timeline instance
        display_height: Screen height for coordinate conversion
    """
    # Convert to OpenGL coordinates
    gl_x = timeline.x
    gl_y = display_height - timeline.y - timeline.height
    
    # Calculate hover expansion
    height = timeline.height
    if timeline._hover_progress > 0:
        expansion = (AppleUIMetrics.TIMELINE_HEIGHT_EXPANDED - AppleUIMetrics.TIMELINE_HEIGHT)
        height += expansion * timeline._hover_progress
        gl_y -= expansion * timeline._hover_progress / 2
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw track background
    draw_rounded_rect(
        gl_x, gl_y, timeline.width, height,
        height / 2,  # Fully rounded
        timeline.track_color
    )
    
    # Draw progress
    if timeline.total_frames > 1:
        progress_width = timeline.progress * timeline.width
        if progress_width > 0:
            draw_rounded_rect(
                gl_x, gl_y, progress_width, height,
                height / 2,
                timeline.progress_color
            )
    
    # Draw handle
    handle_x = gl_x + timeline.progress * timeline.width
    handle_y = gl_y + height / 2
    handle_radius = AppleUIMetrics.TIMELINE_HANDLE_WIDTH / 2
    
    # Handle shadow
    draw_circle(handle_x, handle_y - 1, handle_radius + 1, (0, 0, 0, 0.2))
    
    # Handle circle
    draw_circle(handle_x, handle_y, handle_radius, AppleUIColors.BACKGROUND_TERTIARY)
    draw_circle(handle_x, handle_y, handle_radius - 1, timeline.handle_color)


# ==================== Text Rendering Functions ====================

# Global font cache for text rendering
_font_cache = {}

def _get_font(size: int = 13):
    """
    Get or create a pygame font of the specified size.
    
    Args:
        size: Font size in pixels
    
    Returns:
        pygame.font.Font instance
    """
    if size not in _font_cache:
        try:
            _font_cache[size] = pygame.font.SysFont("Arial", size)
        except:
            _font_cache[size] = pygame.font.Font(None, size)
    return _font_cache[size]


def draw_text_on_surface(surface: pygame.Surface, text: str, x: int, y: int,
                        color: Tuple[int, int, int], size: int = 13) -> None:
    """
    Draw text on a pygame surface at the specified position.
    
    Args:
        surface: Pygame surface to draw on
        text: Text to render
        x, y: Position (pygame coordinates, y=0 is top)
        color: Text color as RGB tuple (0-255)
        size: Font size
    """
    if not surface:
        return
    
    font = _get_font(size)
    # Convert color from 0-1 range to 0-255 if needed
    if isinstance(color[0], float) and color[0] <= 1.0:
        color = tuple(int(c * 255) for c in color[:3])
    
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))


# ==================== UI Setup Functions ====================

def setup_2d_rendering(display_width: int, display_height: int) -> None:
    """
    Set up OpenGL for 2D UI rendering.
    
    Call this before drawing any UI elements.
    
    Args:
        display_width: Screen width
        display_height: Screen height
    """
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, display_width, 0, display_height, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


def cleanup_2d_rendering() -> None:
    """
    Restore OpenGL state after 2D UI rendering.
    
    Call this after drawing all UI elements.
    """
    glEnable(GL_DEPTH_TEST)
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


# ==================== High-Level Rendering Functions ====================

def render_all_buttons(buttons: List[AppleButton], display_height: int,
                       font_renderer=None) -> None:
    """
    Render all buttons in a list.
    
    Args:
        buttons: List of AppleButton instances
        display_height: Screen height
        font_renderer: Optional font rendering function
    """
    for button in buttons:
        draw_apple_button(button, display_height, font_renderer)


def render_status_bar(x: int, y: int, width: int, height: int,
                      items: List[Tuple[str, str]],
                      display_height: int) -> None:
    """
    Render a status bar with multiple items.
    
    Args:
        x, y: Status bar position (pygame coordinates)
        width, height: Status bar dimensions
        items: List of (label, value) tuples
        display_height: Screen height
    """
    # Convert to OpenGL coordinates
    gl_x = x
    gl_y = display_height - y - height
    
    # Enable blending
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Draw background
    draw_rounded_rect(
        gl_x, gl_y, width, height,
        AppleUIMetrics.CORNER_RADIUS_SMALL,
        AppleUIColors.BACKGROUND_SECONDARY,
        AppleUIColors.BORDER_LIGHT
    )


# ==================== Utility Drawing Functions ====================

def draw_icon_play(x: float, y: float, size: float, color: Tuple) -> None:
    """Draw a play icon (triangle)."""
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    glBegin(GL_TRIANGLES)
    glVertex2f(x, y)
    glVertex2f(x, y + size)
    glVertex2f(x + size * 0.866, y + size / 2)  # sqrt(3)/2 for equilateral
    glEnd()


def draw_icon_pause(x: float, y: float, size: float, color: Tuple) -> None:
    """Draw a pause icon (two bars)."""
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    bar_width = size * 0.3
    gap = size * 0.2
    
    # Left bar
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + bar_width, y)
    glVertex2f(x + bar_width, y + size)
    glVertex2f(x, y + size)
    glEnd()
    
    # Right bar
    glBegin(GL_QUADS)
    glVertex2f(x + bar_width + gap, y)
    glVertex2f(x + bar_width * 2 + gap, y)
    glVertex2f(x + bar_width * 2 + gap, y + size)
    glVertex2f(x + bar_width + gap, y + size)
    glEnd()


def draw_icon_record(x: float, y: float, size: float, color: Tuple) -> None:
    """Draw a record icon (filled circle)."""
    draw_circle(x + size / 2, y + size / 2, size / 2, color)


def draw_icon_stop(x: float, y: float, size: float, color: Tuple) -> None:
    """Draw a stop icon (square)."""
    if len(color) == 4:
        glColor4f(*color)
    else:
        glColor3f(*color)
    
    padding = size * 0.15
    
    glBegin(GL_QUADS)
    glVertex2f(x + padding, y + padding)
    glVertex2f(x + size - padding, y + padding)
    glVertex2f(x + size - padding, y + size - padding)
    glVertex2f(x + padding, y + size - padding)
    glEnd()


# ==================== Toast Notification Rendering ====================

def draw_toast(toast: Toast, x: float, y: float, width: float, height: float,
               display_height: int) -> None:
    """
    Draw a single toast notification.
    
    Args:
        toast: Toast object to render
        x, y: Position (OpenGL coordinates, y from bottom)
        width, height: Toast dimensions
        display_height: Screen height for coordinate conversion
    """
    if toast._opacity <= 0:
        return
    
    # Apply opacity to colors
    bg_color = (0.15, 0.15, 0.15, 0.95 * toast._opacity)  # Dark background
    accent_color = toast.color[:3] + (toast._opacity,)
    text_color = (1.0, 1.0, 1.0, toast._opacity)
    
    # Apply slide animation offset
    y_with_offset = y - toast._y_offset
    
    radius = 12
    
    # Draw shadow (only if mostly visible)
    if toast._opacity > 0.5:
        shadow_color = (0.0, 0.0, 0.0, 0.3 * toast._opacity)
        draw_rounded_rect(x + 2, y_with_offset - 4, width, height, radius, shadow_color)
    
    # Draw background
    draw_rounded_rect(x, y_with_offset, width, height, radius, bg_color)
    
    # Draw accent bar on left
    bar_width = 4
    draw_rounded_rect(x + 4, y_with_offset + 8, bar_width, height - 16, 2, accent_color)
    
    # Draw icon circle
    icon_size = 20
    icon_x = x + 16
    icon_y = y_with_offset + (height - icon_size) / 2
    draw_circle(icon_x + icon_size/2, icon_y + icon_size/2, icon_size/2, accent_color)


def draw_toast_manager(toast_manager: ToastManager, display: Tuple[int, int]) -> None:
    """
    Draw all active toasts from a ToastManager.
    
    Args:
        toast_manager: ToastManager instance
        display: (width, height) of display
    """
    toasts = toast_manager.get_toasts()
    if not toasts:
        return
    
    width = toast_manager.TOAST_WIDTH
    height = toast_manager.TOAST_HEIGHT
    margin = toast_manager.TOAST_MARGIN
    
    # Position toasts in top-right corner
    start_x = display[0] - width - 20
    start_y = display[1] - 60  # Below top bar
    
    for i, toast in enumerate(toasts):
        # Stack toasts vertically
        y = start_y - i * (height + margin)
        draw_toast(toast, start_x, y, width, height, display[1])


# ==================== Dropdown Menu Rendering ====================

def draw_dropdown_menu(dropdown: DropdownMenu, display: Tuple[int, int], overlay_manager=None) -> None:
    """
    Draw a dropdown menu options (not the trigger button, which is handled separately).
    
    Args:
        dropdown: DropdownMenu instance
        display: (width, height) of display
        overlay_manager: Optional overlay manager for text rendering (e.g., overlay_manager from main)
    """
    if not dropdown.is_open:
        return  # Only render when menu is open
    
    # Convert pygame coords to OpenGL coords
    gl_y = display[1] - dropdown.y - dropdown.height
    radius = 8
    
    # Draw menu options if open
    if dropdown._open_progress > 0:
        menu_bg = (1.0, 1.0, 1.0, 0.98 * dropdown._open_progress)
        menu_y = gl_y - 4 - dropdown.menu_height * dropdown._open_progress
        menu_height = dropdown.menu_height * dropdown._open_progress
        
        # Menu shadow
        shadow_color = (0.0, 0.0, 0.0, 0.15 * dropdown._open_progress)
        draw_rounded_rect(dropdown.x + 2, menu_y - 4, dropdown.width, menu_height, radius, shadow_color)
        
        # Menu background
        draw_rounded_rect(dropdown.x, menu_y, dropdown.width, menu_height, radius, menu_bg,
                          border_color=AppleUIColors.BORDER_LIGHT, border_width=1)
        
        # Draw options
        for i, opt in enumerate(dropdown.options):
            opt_y = gl_y - 4 - (i + 1) * dropdown.height * dropdown._open_progress
            
            # Hover highlight
            if i == dropdown._hover_index and opt.enabled:
                highlight_color = (0.0, 0.478, 1.0, 0.1 * dropdown._open_progress)
                draw_rounded_rect(dropdown.x + 4, opt_y + 2, dropdown.width - 8, 
                                  dropdown.height - 4, 6, highlight_color)
            
            # Option indicator dot (if selected)
            if opt.id == dropdown.selected_id:
                dot_color = AppleUIColors.ACCENT_BLUE[:3] + (dropdown._open_progress,)
                draw_circle(dropdown.x + 16, opt_y + dropdown.height / 2, 4, dot_color)
            
            # Option color indicator
            if opt.color:
                color_with_alpha = opt.color[:3] + (dropdown._open_progress,)
                draw_circle(dropdown.x + 32, opt_y + dropdown.height / 2, 6, color_with_alpha)
            
            # Option text (draw label)
            if opt.label and overlay_manager:
                # Use overlay manager for text rendering
                text_color = (0, 0, 0, 255)  # Black text
                if not opt.enabled:
                    text_color = (200, 200, 200, 255)  # Gray for disabled
                
                # Text position in OpenGL coordinates (y=0 at bottom)
                # Same as color indicator, align text vertically with circles
                text_x = int(dropdown.x + 45)
                text_y = int(opt_y + dropdown.height / 2 - 6)  # Slightly below center for baseline
                overlay_manager.draw_text(text_x, text_y, opt.label, text_color, size=13)


# ==================== Mode Selector Rendering ====================

def draw_mode_selector(x: float, y: float, width: float, height: float,
                       options: list, selected_index: int,
                       display_height: int, hover_index: int = -1) -> None:
    """
    Draw a segmented control style mode selector.
    
    Args:
        x, y: Position (pygame coordinates)
        width, height: Overall dimensions
        options: List of (id, label, color) tuples
        selected_index: Currently selected index
        display_height: Screen height for coordinate conversion
        hover_index: Index being hovered (-1 for none)
    """
    # Convert to OpenGL coords
    gl_y = display_height - y - height
    
    segment_width = width / len(options) if options else width
    radius = 10
    
    # Draw background pill
    bg_color = AppleUIColors.BACKGROUND_SECONDARY
    draw_pill(x, gl_y, width, height, bg_color, border_color=AppleUIColors.BORDER_LIGHT)
    
    # Draw segments
    for i, (opt_id, label, color) in enumerate(options):
        seg_x = x + i * segment_width
        
        if i == selected_index:
            # Selected segment - filled background
            seg_color = color[:3] + (0.9,) if color else AppleUIColors.ACCENT_BLUE
            inner_radius = radius - 2
            draw_rounded_rect(seg_x + 2, gl_y + 2, segment_width - 4, height - 4,
                              inner_radius, seg_color)
        elif i == hover_index:
            # Hover highlight
            hover_color = (0.0, 0.0, 0.0, 0.05)
            draw_rounded_rect(seg_x + 2, gl_y + 2, segment_width - 4, height - 4,
                              radius - 2, hover_color)


# ==================== Enhanced Panel Rendering ====================

def draw_glass_panel(x: float, y: float, width: float, height: float,
                     radius: float = 12, blur_amount: float = 0.8) -> None:
    """
    Draw a frosted glass effect panel (simplified version).
    
    Args:
        x, y: Position (OpenGL coordinates)
        width, height: Panel dimensions
        radius: Corner radius
        blur_amount: Blur intensity (0-1)
    """
    # Frosted glass background
    glass_color = (1.0, 1.0, 1.0, 0.85)
    
    # Subtle shadow
    shadow_color = (0.0, 0.0, 0.0, 0.08)
    draw_rounded_rect(x + 1, y - 2, width, height, radius, shadow_color)
    
    # Main glass background
    draw_rounded_rect(x, y, width, height, radius, glass_color,
                      border_color=(1.0, 1.0, 1.0, 0.5), border_width=1)
    
    # Top highlight for depth
    highlight_color = (1.0, 1.0, 1.0, 0.3)
    draw_rounded_rect(x + 2, y + height - radius - 2, width - 4, 2, 1, highlight_color)
