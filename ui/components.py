# -*- coding: utf-8 -*-
"""
UI Components
=============

Reusable UI components with Apple-style design.
Includes buttons, panels, and interactive elements.
"""

import pygame
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from .colors import AppleUIColors
from .metrics import AppleUIMetrics
from .animations import LerpAnimator, get_lerp_animator


class ButtonState(Enum):
    """Button interaction states."""
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"


class ButtonStyle(Enum):
    """Button visual styles."""
    SECONDARY = "secondary"    # Gray background, dark text
    PRIMARY = "primary"        # Blue background, white text
    SUCCESS = "success"        # Green background, white text
    DANGER = "danger"          # Red background, white text
    WARNING = "warning"        # Orange background, white text
    GHOST = "ghost"            # Transparent, only border


@dataclass
class ButtonColors:
    """Color set for a button style."""
    background: Tuple[float, float, float, float]
    background_hover: Tuple[float, float, float, float]
    background_pressed: Tuple[float, float, float, float]
    text: Tuple[float, float, float, float]
    border: Optional[Tuple[float, float, float, float]] = None


# Pre-defined button color schemes
BUTTON_STYLE_COLORS: Dict[ButtonStyle, ButtonColors] = {
    ButtonStyle.SECONDARY: ButtonColors(
        background=AppleUIColors.BUTTON_DEFAULT,
        background_hover=AppleUIColors.BUTTON_HOVER,
        background_pressed=AppleUIColors.BUTTON_PRESSED,
        text=AppleUIColors.TEXT_PRIMARY,
        border=AppleUIColors.BORDER_LIGHT
    ),
    ButtonStyle.PRIMARY: ButtonColors(
        background=AppleUIColors.ACCENT_BLUE,
        background_hover=AppleUIColors.ACCENT_BLUE_DARK,
        background_pressed=(0.0, 0.35, 0.75, 1.0),
        text=AppleUIColors.TEXT_ON_ACCENT,
        border=None
    ),
    ButtonStyle.SUCCESS: ButtonColors(
        background=AppleUIColors.ACCENT_GREEN,
        background_hover=AppleUIColors.ACCENT_GREEN_DARK,
        background_pressed=(0.12, 0.55, 0.22, 1.0),
        text=AppleUIColors.TEXT_ON_ACCENT,
        border=None
    ),
    ButtonStyle.DANGER: ButtonColors(
        background=AppleUIColors.ACCENT_RED,
        background_hover=AppleUIColors.ACCENT_RED_DARK,
        background_pressed=(0.75, 0.15, 0.12, 1.0),
        text=AppleUIColors.TEXT_ON_ACCENT,
        border=None
    ),
    ButtonStyle.WARNING: ButtonColors(
        background=AppleUIColors.ACCENT_ORANGE,
        background_hover=AppleUIColors.ACCENT_ORANGE_DARK,
        background_pressed=(0.75, 0.42, 0.0, 1.0),
        text=AppleUIColors.TEXT_ON_ACCENT,
        border=None
    ),
    ButtonStyle.GHOST: ButtonColors(
        background=(0.0, 0.0, 0.0, 0.0),
        background_hover=(0.0, 0.0, 0.0, 0.05),
        background_pressed=(0.0, 0.0, 0.0, 0.1),
        text=AppleUIColors.ACCENT_BLUE,
        border=AppleUIColors.BORDER_MEDIUM
    ),
}


@dataclass
class AppleButton:
    """
    Apple-style button component with hover and click effects.
    
    Attributes:
        x, y: Position (top-left corner in pygame coordinates)
        width, height: Button dimensions
        text: Button label
        style: Visual style (primary, secondary, etc.)
        enabled: Whether button is interactive
        visible: Whether button is rendered
        on_click: Callback function when clicked
        icon: Optional icon name (for future use)
        tooltip: Optional tooltip text
    """
    x: int
    y: int
    width: int
    height: int
    text: str
    style: ButtonStyle = ButtonStyle.SECONDARY
    enabled: bool = True
    visible: bool = True
    on_click: Optional[Callable[[], None]] = None
    icon: Optional[str] = None
    tooltip: Optional[str] = None
    corner_radius: int = AppleUIMetrics.CORNER_RADIUS_MEDIUM
    font_size: int = AppleUIMetrics.FONT_SIZE_BODY
    
    # Animation state (managed by ButtonManager)
    _state: ButtonState = field(default=ButtonState.NORMAL, init=False)
    _hover_progress: float = field(default=0.0, init=False)
    _press_scale: float = field(default=1.0, init=False)
    _id: str = field(default="", init=False)
    
    @property
    def rect(self) -> pygame.Rect:
        """Get pygame Rect for collision detection."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def state(self) -> ButtonState:
        """Get current button state."""
        if not self.enabled:
            return ButtonState.DISABLED
        return self._state
    
    def get_colors(self) -> ButtonColors:
        """Get the color scheme for current style."""
        return BUTTON_STYLE_COLORS.get(self.style, BUTTON_STYLE_COLORS[ButtonStyle.SECONDARY])
    
    def get_current_background(self) -> Tuple[float, float, float, float]:
        """
        Get the current background color based on state and animation.
        
        Returns:
            Interpolated background color
        """
        colors = self.get_colors()
        
        if not self.enabled:
            return AppleUIColors.BUTTON_DISABLED
        
        # Blend between states based on hover progress
        if self._state == ButtonState.PRESSED:
            return colors.background_pressed
        elif self._hover_progress > 0:
            # Interpolate between normal and hover
            return AppleUIColors.blend(
                colors.background,
                colors.background_hover,
                self._hover_progress
            )
        else:
            return colors.background
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside the button."""
        return self.rect.collidepoint(x, y)
    
    def set_position(self, x: int, y: int) -> None:
        """Update button position."""
        self.x = x
        self.y = y
    
    def set_size(self, width: int, height: int) -> None:
        """Update button size."""
        self.width = width
        self.height = height


class ButtonManager:
    """
    Manages multiple buttons with shared animation state.
    
    Handles:
    - Mouse hover detection
    - Click detection and callbacks
    - Animation updates (hover, press)
    - Rendering coordination
    
    Usage:
        manager = ButtonManager()
        
        # Create buttons
        manager.add_button("mode", AppleButton(10, 10, 80, 36, "Mode"))
        manager.add_button("connect", AppleButton(100, 10, 80, 36, "Connect"))
        
        # In game loop:
        manager.update(mouse_pos, mouse_buttons)
        
        # Get button for rendering
        btn = manager.get_button("mode")
    """
    
    def __init__(self):
        self.buttons: Dict[str, AppleButton] = {}
        self.animator = LerpAnimator()
        self._last_pressed: Optional[str] = None
        self._clicked_this_frame: Optional[str] = None
    
    def add_button(self, button_id: str, button: AppleButton) -> None:
        """
        Register a button with the manager.
        
        Args:
            button_id: Unique identifier for the button
            button: AppleButton instance
        """
        button._id = button_id
        self.buttons[button_id] = button
        
        # Initialize animation values
        self.animator.set_immediate(f"{button_id}_hover", 0.0)
        self.animator.set_immediate(f"{button_id}_scale", 1.0)
    
    def remove_button(self, button_id: str) -> None:
        """Remove a button from the manager."""
        if button_id in self.buttons:
            del self.buttons[button_id]
    
    def get_button(self, button_id: str) -> Optional[AppleButton]:
        """Get a button by ID."""
        return self.buttons.get(button_id)
    
    def update(self, mouse_pos: Tuple[int, int], mouse_buttons: Tuple[bool, bool, bool]) -> Optional[str]:
        """
        Update all button states based on mouse input.
        
        Args:
            mouse_pos: Current mouse position (x, y)
            mouse_buttons: Mouse button states (left, middle, right)
        
        Returns:
            ID of clicked button, or None
        """
        self._clicked_this_frame = None
        left_pressed = mouse_buttons[0]
        
        for button_id, button in self.buttons.items():
            if not button.visible or not button.enabled:
                button._state = ButtonState.DISABLED
                self.animator.set_target(f"{button_id}_hover", 0.0)
                self.animator.set_target(f"{button_id}_scale", 1.0)
                continue
            
            is_hovering = button.contains_point(*mouse_pos)
            
            # Determine state
            if is_hovering and left_pressed:
                button._state = ButtonState.PRESSED
                self.animator.set_target(f"{button_id}_hover", 1.0)
                self.animator.set_target(f"{button_id}_scale", AppleUIMetrics.BUTTON_PRESS_SCALE)
                self._last_pressed = button_id
            elif is_hovering:
                button._state = ButtonState.HOVER
                self.animator.set_target(f"{button_id}_hover", 1.0)
                self.animator.set_target(f"{button_id}_scale", 1.0)
                
                # Check for click (button was pressed and now released)
                if self._last_pressed == button_id and not left_pressed:
                    self._clicked_this_frame = button_id
                    if button.on_click:
                        button.on_click()
            else:
                button._state = ButtonState.NORMAL
                self.animator.set_target(f"{button_id}_hover", 0.0)
                self.animator.set_target(f"{button_id}_scale", 1.0)
        
        # Clear last pressed if mouse released
        if not left_pressed:
            self._last_pressed = None
        
        # Update animations
        self.animator.update_all(speed=AppleUIMetrics.ANIMATION_SPEED_NORMAL)
        
        # Apply animation values to buttons
        for button_id, button in self.buttons.items():
            button._hover_progress = self.animator.get_value(f"{button_id}_hover", 0.0)
            button._press_scale = self.animator.get_value(f"{button_id}_scale", 1.0)
        
        return self._clicked_this_frame
    
    def was_clicked(self, button_id: str) -> bool:
        """Check if a specific button was clicked this frame."""
        return self._clicked_this_frame == button_id
    
    def get_all_buttons(self) -> List[AppleButton]:
        """Get all registered buttons."""
        return list(self.buttons.values())
    
    def set_button_enabled(self, button_id: str, enabled: bool) -> None:
        """Enable or disable a button."""
        if button_id in self.buttons:
            self.buttons[button_id].enabled = enabled
    
    def set_button_visible(self, button_id: str, visible: bool) -> None:
        """Show or hide a button."""
        if button_id in self.buttons:
            self.buttons[button_id].visible = visible
    
    def set_button_style(self, button_id: str, style: ButtonStyle) -> None:
        """Change a button's visual style."""
        if button_id in self.buttons:
            self.buttons[button_id].style = style
    
    def set_button_text(self, button_id: str, text: str) -> None:
        """Change a button's text label."""
        if button_id in self.buttons:
            self.buttons[button_id].text = text


@dataclass
class ButtonGroup:
    """
    A group of related buttons with a shared container.
    
    Attributes:
        title: Group title (displayed above buttons)
        buttons: List of button IDs in this group
        x, y: Group container position
        width: Container width (auto-calculated if 0)
        orientation: "horizontal" or "vertical"
        spacing: Space between buttons
    """
    title: str
    button_ids: List[str]
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    orientation: str = "vertical"
    spacing: int = AppleUIMetrics.BUTTON_GROUP_SPACING
    padding: int = AppleUIMetrics.BUTTON_GROUP_PADDING
    show_background: bool = True
    corner_radius: int = AppleUIMetrics.BUTTON_GROUP_CORNER
    
    def calculate_size(self, manager: ButtonManager) -> Tuple[int, int]:
        """
        Calculate the size needed for this group.
        
        Args:
            manager: ButtonManager containing the buttons
        
        Returns:
            (width, height) tuple
        """
        buttons = [manager.get_button(bid) for bid in self.button_ids]
        buttons = [b for b in buttons if b is not None and b.visible]
        
        if not buttons:
            return (0, 0)
        
        if self.orientation == "horizontal":
            width = sum(b.width for b in buttons) + self.spacing * (len(buttons) - 1) + 2 * self.padding
            height = max(b.height for b in buttons) + 2 * self.padding
            if self.title:
                height += AppleUIMetrics.GROUP_TITLE_FONT_SIZE + AppleUIMetrics.GROUP_TITLE_MARGIN_BOTTOM
        else:  # vertical
            width = max(b.width for b in buttons) + 2 * self.padding
            height = sum(b.height for b in buttons) + self.spacing * (len(buttons) - 1) + 2 * self.padding
            if self.title:
                height += AppleUIMetrics.GROUP_TITLE_FONT_SIZE + AppleUIMetrics.GROUP_TITLE_MARGIN_BOTTOM
        
        return (width, height)
    
    def layout_buttons(self, manager: ButtonManager) -> None:
        """
        Position buttons within this group.
        
        Args:
            manager: ButtonManager containing the buttons
        """
        buttons = [manager.get_button(bid) for bid in self.button_ids]
        buttons = [b for b in buttons if b is not None and b.visible]
        
        if not buttons:
            return
        
        # Calculate starting position
        start_x = self.x + self.padding
        start_y = self.y + self.padding
        
        if self.title:
            start_y += AppleUIMetrics.GROUP_TITLE_FONT_SIZE + AppleUIMetrics.GROUP_TITLE_MARGIN_BOTTOM
        
        if self.orientation == "horizontal":
            current_x = start_x
            for button in buttons:
                button.set_position(current_x, start_y)
                current_x += button.width + self.spacing
        else:  # vertical
            current_y = start_y
            for button in buttons:
                button.set_position(start_x, current_y)
                current_y += button.height + self.spacing


@dataclass
class StatusIndicator:
    """
    Status indicator component (colored dot with label).
    
    Used for showing connection status, recording status, etc.
    """
    x: int
    y: int
    label: str
    status: str = "inactive"  # "active", "inactive", "warning", "error"
    show_pulse: bool = False  # Pulsing animation for active state
    
    _pulse_phase: float = field(default=0.0, init=False)
    
    def get_color(self) -> Tuple[float, float, float, float]:
        """Get the indicator color based on status."""
        status_colors = {
            "active": AppleUIColors.ACCENT_GREEN,
            "inactive": AppleUIColors.ACCENT_GRAY,
            "warning": AppleUIColors.ACCENT_ORANGE,
            "error": AppleUIColors.ACCENT_RED,
            "recording": AppleUIColors.ACCENT_RED,
            "connecting": AppleUIColors.ACCENT_ORANGE,
            "connected": AppleUIColors.ACCENT_GREEN,
            "disconnected": AppleUIColors.ACCENT_GRAY,
        }
        return status_colors.get(self.status, AppleUIColors.ACCENT_GRAY)
    
    def update(self, dt: float) -> None:
        """Update pulse animation."""
        if self.show_pulse:
            self._pulse_phase += dt * 3.0  # 3 Hz pulse
            if self._pulse_phase > 6.28:  # 2 * pi
                self._pulse_phase -= 6.28
    
    def get_pulse_alpha(self) -> float:
        """Get current pulse alpha (0.5 - 1.0)."""
        import math
        return 0.75 + 0.25 * math.sin(self._pulse_phase)


@dataclass
class Panel:
    """
    Container panel with rounded corners and optional shadow.
    
    Used for grouping UI elements visually.
    """
    x: int
    y: int
    width: int
    height: int
    title: Optional[str] = None
    background: Tuple[float, float, float, float] = field(
        default_factory=lambda: AppleUIColors.PANEL_BACKGROUND
    )
    corner_radius: int = AppleUIMetrics.PANEL_CORNER_RADIUS
    show_shadow: bool = True
    border_color: Optional[Tuple[float, float, float, float]] = None
    
    @property
    def rect(self) -> pygame.Rect:
        """Get pygame Rect."""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def content_rect(self) -> pygame.Rect:
        """Get content area rect (inside padding)."""
        padding = AppleUIMetrics.MARGIN_PANEL
        return pygame.Rect(
            self.x + padding,
            self.y + padding,
            self.width - 2 * padding,
            self.height - 2 * padding
        )


# ==================== Mode Indicator Component ====================

class ModeIndicator:
    """
    Mode indicator showing current application mode (Offline/Mocap/Secap).
    
    Displays as a pill-shaped badge with mode-specific color.
    """
    
    MODE_COLORS = {
        "offline": (AppleUIColors.MODE_OFFLINE, AppleUIColors.MODE_OFFLINE_BG),
        "mocap": (AppleUIColors.MODE_MOCAP, AppleUIColors.MODE_MOCAP_BG),
        "secap": (AppleUIColors.MODE_SECAP, AppleUIColors.MODE_SECAP_BG),
    }
    
    MODE_LABELS = {
        "offline": "Offline",
        "mocap": "Mocap",
        "secap": "Secap",
    }
    
    def __init__(self, x: int, y: int, mode: str = "offline"):
        self.x = x
        self.y = y
        self.mode = mode
        self.width = 80
        self.height = 28
        self.corner_radius = AppleUIMetrics.CORNER_RADIUS_FULL
        
        # Animation
        self._target_colors = self.MODE_COLORS.get(mode, self.MODE_COLORS["offline"])
        self._current_bg = self._target_colors[1]
    
    def set_mode(self, mode: str) -> None:
        """Change the displayed mode."""
        self.mode = mode
        self._target_colors = self.MODE_COLORS.get(mode, self.MODE_COLORS["offline"])
    
    def get_colors(self) -> Tuple[Tuple, Tuple]:
        """Get (accent_color, background_color) for current mode."""
        return self.MODE_COLORS.get(self.mode, self.MODE_COLORS["offline"])
    
    def get_label(self) -> str:
        """Get display label for current mode."""
        return self.MODE_LABELS.get(self.mode, "Unknown")


# ==================== Timeline Component ====================

@dataclass
class Timeline:
    """
    Playback timeline component with scrubber.
    
    Displays progress and allows seeking through animation.
    """
    x: int
    y: int
    width: int
    height: int = AppleUIMetrics.TIMELINE_HEIGHT
    
    current_frame: int = 0
    total_frames: int = 1
    is_playing: bool = False
    
    # Visual settings
    track_color: Tuple = field(default_factory=lambda: AppleUIColors.TIMELINE_BACKGROUND)
    progress_color: Tuple = field(default_factory=lambda: AppleUIColors.TIMELINE_PROGRESS)
    handle_color: Tuple = field(default_factory=lambda: AppleUIColors.TIMELINE_HANDLE)
    
    # Interaction state
    _is_dragging: bool = field(default=False, init=False)
    _hover_progress: float = field(default=0.0, init=False)
    
    @property
    def progress(self) -> float:
        """Get current progress (0.0 - 1.0)."""
        if self.total_frames <= 1:
            return 0.0
        return self.current_frame / (self.total_frames - 1)
    
    @property
    def handle_x(self) -> int:
        """Get the x position of the scrubber handle."""
        return int(self.x + self.progress * self.width)
    
    def set_frame_from_x(self, x: int) -> int:
        """
        Set frame based on x position.
        
        Args:
            x: Mouse x position
        
        Returns:
            New frame number
        """
        relative_x = max(0, min(x - self.x, self.width))
        progress = relative_x / self.width if self.width > 0 else 0
        self.current_frame = int(progress * (self.total_frames - 1))
        return self.current_frame
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within timeline area (with padding for handle)."""
        padding = AppleUIMetrics.TIMELINE_HANDLE_HEIGHT // 2
        return (self.x - padding <= x <= self.x + self.width + padding and
                self.y - padding <= y <= self.y + self.height + padding)


# ==================== Toast Notification System ====================

class ToastType(Enum):
    """Toast notification types with corresponding colors."""
    SUCCESS = "success"    # Green - operation succeeded
    WARNING = "warning"    # Orange - caution needed
    ERROR = "error"        # Red - operation failed
    INFO = "info"          # Blue - informational
    NEUTRAL = "neutral"    # Gray - neutral/offline state


TOAST_COLORS = {
    ToastType.SUCCESS: AppleUIColors.ACCENT_GREEN,
    ToastType.WARNING: AppleUIColors.ACCENT_ORANGE,
    ToastType.ERROR: AppleUIColors.ACCENT_RED,
    ToastType.INFO: AppleUIColors.ACCENT_BLUE,
    ToastType.NEUTRAL: AppleUIColors.ACCENT_GRAY,
}

TOAST_ICONS = {
    ToastType.SUCCESS: "✓",
    ToastType.WARNING: "⚠",
    ToastType.ERROR: "✗",
    ToastType.INFO: "ℹ",
    ToastType.NEUTRAL: "●",  # Filled circle for neutral
}


@dataclass
class Toast:
    """
    A single toast notification message.
    
    Attributes:
        message: Text to display
        toast_type: Type determines color (success/warning/error/info)
        duration: How long to show in seconds
        created_at: Timestamp when created
    """
    message: str
    toast_type: ToastType = ToastType.INFO
    duration: float = 3.0  # seconds
    created_at: float = field(default_factory=lambda: 0.0)
    
    # Animation state
    _opacity: float = field(default=0.0, init=False)
    _y_offset: float = field(default=20.0, init=False)  # Slide in animation
    _is_dismissed: bool = field(default=False, init=False)
    
    @property
    def color(self) -> Tuple[float, float, float, float]:
        """Get the color for this toast type."""
        return TOAST_COLORS.get(self.toast_type, AppleUIColors.ACCENT_BLUE)
    
    @property
    def icon(self) -> str:
        """Get the icon character for this toast type."""
        return TOAST_ICONS.get(self.toast_type, "ℹ")


class ToastManager:
    """
    Manages toast notifications with stacking and animations.
    
    Features:
    - Auto-dismiss after duration
    - Smooth fade in/out animations
    - Stacking multiple toasts
    - Maximum toast limit
    
    Usage:
        toast_mgr = ToastManager()
        toast_mgr.show("File loaded successfully!", ToastType.SUCCESS)
        toast_mgr.show("Connection failed", ToastType.ERROR)
        
        # In render loop:
        toast_mgr.update(delta_time)
        toast_mgr.render(display, overlay_manager)
    """
    
    MAX_TOASTS = 5
    TOAST_WIDTH = 320
    TOAST_HEIGHT = 48
    TOAST_MARGIN = 8
    TOAST_PADDING = 16
    ANIMATION_SPEED = 8.0
    
    def __init__(self):
        self._toasts: List[Toast] = []
        self._time = 0.0
    
    def show(self, message: str, toast_type: ToastType = ToastType.INFO, duration: float = 3.0):
        """
        Show a new toast notification.
        
        Args:
            message: Text to display
            toast_type: Type (success/warning/error/info)
            duration: How long to show in seconds
        """
        # Remove oldest if at max
        while len(self._toasts) >= self.MAX_TOASTS:
            self._toasts.pop(0)
        
        toast = Toast(
            message=message,
            toast_type=toast_type,
            duration=duration,
            created_at=self._time
        )
        self._toasts.append(toast)
        print(f"[Toast] {toast_type.value.upper()}: {message}")
    
    def success(self, message: str, duration: float = 3.0):
        """Show a success toast."""
        self.show(message, ToastType.SUCCESS, duration)
    
    def warning(self, message: str, duration: float = 4.0):
        """Show a warning toast."""
        self.show(message, ToastType.WARNING, duration)
    
    def error(self, message: str, duration: float = 5.0):
        """Show an error toast."""
        self.show(message, ToastType.ERROR, duration)
    
    def info(self, message: str, duration: float = 3.0):
        """Show an info toast."""
        self.show(message, ToastType.INFO, duration)
    
    def update(self, delta_time: float):
        """
        Update toast animations and remove expired toasts.
        
        Args:
            delta_time: Time since last update in seconds
        """
        self._time += delta_time
        
        toasts_to_remove = []
        
        for toast in self._toasts:
            age = self._time - toast.created_at
            
            # Fade in phase (first 0.2 seconds)
            if age < 0.2:
                toast._opacity = min(1.0, toast._opacity + delta_time * self.ANIMATION_SPEED)
                toast._y_offset = max(0.0, toast._y_offset - delta_time * 100)
            # Visible phase
            elif age < toast.duration - 0.3:
                toast._opacity = 1.0
                toast._y_offset = 0.0
            # Fade out phase (last 0.3 seconds)
            elif age < toast.duration:
                toast._opacity = max(0.0, toast._opacity - delta_time * self.ANIMATION_SPEED)
            # Expired
            else:
                toasts_to_remove.append(toast)
        
        for toast in toasts_to_remove:
            self._toasts.remove(toast)
    
    def get_toasts(self) -> List[Toast]:
        """Get all active toasts for rendering."""
        return self._toasts
    
    def clear_all(self):
        """Remove all toasts immediately."""
        self._toasts.clear()


# ==================== Dropdown Menu Component ====================

@dataclass
class DropdownOption:
    """A single option in a dropdown menu."""
    id: str
    label: str
    icon: Optional[str] = None
    color: Optional[Tuple[float, float, float, float]] = None
    enabled: bool = True


@dataclass
class DropdownMenu:
    """
    Apple-style dropdown menu component.
    
    Attributes:
        x, y: Position of the trigger button
        width: Width of the menu
        options: List of selectable options
        selected_id: Currently selected option ID
    """
    x: int
    y: int
    width: int
    height: int = 36
    
    options: List[DropdownOption] = field(default_factory=list)
    selected_id: str = ""
    
    # State
    is_open: bool = False
    enabled: bool = True
    
    # Animation
    _hover_index: int = field(default=-1, init=False)
    _open_progress: float = field(default=0.0, init=False)
    
    # Callbacks
    on_change: Optional[Callable[[str], None]] = None
    
    @property
    def selected_option(self) -> Optional[DropdownOption]:
        """Get the currently selected option."""
        for opt in self.options:
            if opt.id == self.selected_id:
                return opt
        return self.options[0] if self.options else None
    
    @property
    def menu_height(self) -> int:
        """Calculate total menu height when open."""
        return len(self.options) * self.height + 8  # padding
    
    def get_option_rect(self, index: int) -> pygame.Rect:
        """Get rect for a specific option."""
        option_y = self.y + self.height + 4 + index * self.height
        return pygame.Rect(self.x, option_y, self.width, self.height)
    
    def toggle(self):
        """Toggle dropdown open/close."""
        self.is_open = not self.is_open
    
    def select(self, option_id: str):
        """Select an option by ID."""
        old_id = self.selected_id
        self.selected_id = option_id
        self.is_open = False
        
        if old_id != option_id and self.on_change:
            self.on_change(option_id)
    
    def handle_click(self, x: int, y: int) -> bool:
        """
        Handle mouse click on dropdown menu options (not trigger button).
        
        Note: Trigger button click is handled separately by the mode button.
        This method only handles menu option selection and closing.
        
        Returns:
            True if click was handled
        """
        # Check menu option clicks when open
        if self.is_open:
            for i, opt in enumerate(self.options):
                if opt.enabled:
                    opt_rect = self.get_option_rect(i)
                    if opt_rect.collidepoint(x, y):
                        self.select(opt.id)
                        return True
            
            # Check if click is on trigger area (don't toggle, just keep open)
            trigger_rect = pygame.Rect(self.x, self.y, self.width, self.height)
            if trigger_rect.collidepoint(x, y):
                return False  # Let mode button handle it
            
            # Click outside menu closes it
            self.is_open = False
            return True
        
        return False
    
    def handle_hover(self, x: int, y: int):
        """Update hover state based on mouse position."""
        self._hover_index = -1
        if self.is_open:
            for i, opt in enumerate(self.options):
                opt_rect = self.get_option_rect(i)
                if opt_rect.collidepoint(x, y) and opt.enabled:
                    self._hover_index = i
                    break
    
    def update(self, delta_time: float):
        """Update animation state."""
        target = 1.0 if self.is_open else 0.0
        speed = 12.0
        if self._open_progress < target:
            self._open_progress = min(target, self._open_progress + delta_time * speed)
        elif self._open_progress > target:
            self._open_progress = max(target, self._open_progress - delta_time * speed)
    
    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within dropdown area (including open menu)."""
        trigger_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        if trigger_rect.collidepoint(x, y):
            return True
        if self.is_open:
            menu_rect = pygame.Rect(self.x, self.y + self.height, self.width, self.menu_height)
            return menu_rect.collidepoint(x, y)
        return False
