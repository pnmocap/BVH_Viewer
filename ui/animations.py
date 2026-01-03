# -*- coding: utf-8 -*-
"""
Animation System
================

Smooth animation utilities for UI transitions and effects.
Provides easing functions, animation managers, and state interpolation.
"""

import math
import time
from typing import Dict, Tuple, Callable, Optional, Any
from dataclasses import dataclass, field


class EasingFunctions:
    """
    Collection of easing functions for smooth animations.
    
    All functions take a value t in range [0, 1] and return
    an eased value, also in range [0, 1].
    
    Reference: https://easings.net/
    """
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)."""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in: slow start."""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out: slow end."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out: slow start and end."""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in: slower start."""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out: slower end."""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out: slower start and end."""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """Quartic ease-out: very slow end."""
        return 1 - pow(1 - t, 4)
    
    @staticmethod
    def ease_out_quint(t: float) -> float:
        """Quintic ease-out: extremely slow end."""
        return 1 - pow(1 - t, 5)
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        """Exponential ease-in."""
        return 0 if t == 0 else pow(2, 10 * t - 10)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """Exponential ease-out."""
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """Exponential ease-in-out."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        if t < 0.5:
            return pow(2, 20 * t - 10) / 2
        else:
            return (2 - pow(2, -20 * t + 10)) / 2
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """Ease-out with overshoot (bouncy feel)."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease-out (spring-like)."""
        if t == 0:
            return 0
        if t == 1:
            return 1
        c4 = (2 * math.pi) / 3
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bounce ease-out."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    @staticmethod
    def spring(t: float, tension: float = 0.5) -> float:
        """
        Spring-like animation with configurable tension.
        
        Args:
            t: Progress (0-1)
            tension: Spring tension (0.1 = loose, 1.0 = tight)
        """
        decay = 1 - tension * 0.5
        frequency = 4 + tension * 4
        return 1 - math.exp(-decay * t * 10) * math.cos(frequency * t * math.pi)


@dataclass
class Animation:
    """
    Represents a single animation instance.
    
    Attributes:
        start_value: Initial value
        end_value: Target value
        duration: Animation duration in seconds
        easing: Easing function to use
        start_time: When the animation started
        on_complete: Callback when animation finishes
    """
    start_value: float
    end_value: float
    duration: float
    easing: Callable[[float], float] = field(default_factory=lambda: EasingFunctions.ease_out_cubic)
    start_time: float = field(default_factory=time.time)
    on_complete: Optional[Callable[[], None]] = None
    _completed: bool = False
    
    def get_value(self, current_time: Optional[float] = None) -> float:
        """
        Get the current interpolated value.
        
        Args:
            current_time: Current time (uses time.time() if None)
        
        Returns:
            Current animated value
        """
        if current_time is None:
            current_time = time.time()
        
        elapsed = current_time - self.start_time
        
        if elapsed >= self.duration:
            if not self._completed and self.on_complete:
                self.on_complete()
                self._completed = True
            return self.end_value
        
        # Calculate progress (0 to 1)
        progress = elapsed / self.duration
        
        # Apply easing
        eased_progress = self.easing(progress)
        
        # Interpolate value
        return self.start_value + (self.end_value - self.start_value) * eased_progress
    
    def is_complete(self, current_time: Optional[float] = None) -> bool:
        """Check if animation has completed."""
        if current_time is None:
            current_time = time.time()
        return (current_time - self.start_time) >= self.duration


@dataclass
class ColorAnimation:
    """
    Animation for color transitions (RGBA).
    """
    start_color: Tuple[float, float, float, float]
    end_color: Tuple[float, float, float, float]
    duration: float
    easing: Callable[[float], float] = field(default_factory=lambda: EasingFunctions.ease_out_cubic)
    start_time: float = field(default_factory=time.time)
    
    def get_color(self, current_time: Optional[float] = None) -> Tuple[float, float, float, float]:
        """Get the current interpolated color."""
        if current_time is None:
            current_time = time.time()
        
        elapsed = current_time - self.start_time
        
        if elapsed >= self.duration:
            return self.end_color
        
        progress = self.easing(elapsed / self.duration)
        
        return (
            self.start_color[0] + (self.end_color[0] - self.start_color[0]) * progress,
            self.start_color[1] + (self.end_color[1] - self.start_color[1]) * progress,
            self.start_color[2] + (self.end_color[2] - self.start_color[2]) * progress,
            self.start_color[3] + (self.end_color[3] - self.start_color[3]) * progress,
        )
    
    def is_complete(self, current_time: Optional[float] = None) -> bool:
        """Check if animation has completed."""
        if current_time is None:
            current_time = time.time()
        return (current_time - self.start_time) >= self.duration


class AnimationManager:
    """
    Manages multiple animations and provides smooth value transitions.
    
    Usage:
        manager = AnimationManager()
        
        # Start an animation
        manager.animate("button_hover", 0.0, 1.0, duration=0.2)
        
        # Get current value (call every frame)
        hover_value = manager.get_value("button_hover")
    """
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.color_animations: Dict[str, ColorAnimation] = {}
        self._current_values: Dict[str, float] = {}
        self._current_colors: Dict[str, Tuple[float, float, float, float]] = {}
    
    def animate(self, key: str, start_value: float, end_value: float,
                duration: float = 0.2,
                easing: Callable[[float], float] = None,
                on_complete: Optional[Callable[[], None]] = None) -> None:
        """
        Start a new animation.
        
        Args:
            key: Unique identifier for this animation
            start_value: Starting value (or None to use current value)
            end_value: Target value
            duration: Animation duration in seconds
            easing: Easing function (default: ease_out_cubic)
            on_complete: Callback when animation completes
        """
        if easing is None:
            easing = EasingFunctions.ease_out_cubic
        
        # Use current value as start if animation is already running
        if key in self._current_values and start_value is None:
            start_value = self._current_values[key]
        elif start_value is None:
            start_value = 0.0
        
        self.animations[key] = Animation(
            start_value=start_value,
            end_value=end_value,
            duration=duration,
            easing=easing,
            start_time=time.time(),
            on_complete=on_complete
        )
    
    def animate_to(self, key: str, end_value: float,
                   duration: float = 0.2,
                   easing: Callable[[float], float] = None) -> None:
        """
        Animate from current value to target value.
        
        Args:
            key: Animation key
            end_value: Target value
            duration: Animation duration
            easing: Easing function
        """
        current = self.get_value(key)
        self.animate(key, current, end_value, duration, easing)
    
    def animate_color(self, key: str,
                      start_color: Tuple[float, float, float, float],
                      end_color: Tuple[float, float, float, float],
                      duration: float = 0.2,
                      easing: Callable[[float], float] = None) -> None:
        """
        Start a color animation.
        
        Args:
            key: Unique identifier
            start_color: Starting RGBA color
            end_color: Target RGBA color
            duration: Animation duration
            easing: Easing function
        """
        if easing is None:
            easing = EasingFunctions.ease_out_cubic
        
        self.color_animations[key] = ColorAnimation(
            start_color=start_color,
            end_color=end_color,
            duration=duration,
            easing=easing,
            start_time=time.time()
        )
    
    def get_value(self, key: str, default: float = 0.0) -> float:
        """
        Get the current value for an animation.
        
        Args:
            key: Animation key
            default: Default value if no animation exists
        
        Returns:
            Current animated value
        """
        if key not in self.animations:
            return self._current_values.get(key, default)
        
        value = self.animations[key].get_value()
        self._current_values[key] = value
        
        # Clean up completed animations
        if self.animations[key].is_complete():
            del self.animations[key]
        
        return value
    
    def get_color(self, key: str, 
                  default: Tuple[float, float, float, float] = (0, 0, 0, 1)) -> Tuple[float, float, float, float]:
        """
        Get the current color for a color animation.
        
        Args:
            key: Animation key
            default: Default color if no animation exists
        
        Returns:
            Current animated color
        """
        if key not in self.color_animations:
            return self._current_colors.get(key, default)
        
        color = self.color_animations[key].get_color()
        self._current_colors[key] = color
        
        # Clean up completed animations
        if self.color_animations[key].is_complete():
            del self.color_animations[key]
        
        return color
    
    def set_value(self, key: str, value: float) -> None:
        """
        Set a value immediately without animation.
        
        Args:
            key: Value key
            value: Value to set
        """
        self._current_values[key] = value
        # Cancel any running animation
        if key in self.animations:
            del self.animations[key]
    
    def is_animating(self, key: str) -> bool:
        """Check if a specific animation is currently running."""
        return key in self.animations or key in self.color_animations
    
    def cancel(self, key: str) -> None:
        """Cancel an animation."""
        if key in self.animations:
            del self.animations[key]
        if key in self.color_animations:
            del self.color_animations[key]
    
    def cancel_all(self) -> None:
        """Cancel all running animations."""
        self.animations.clear()
        self.color_animations.clear()
    
    def update(self) -> None:
        """
        Update all animations (call once per frame).
        This cleans up completed animations.
        """
        current_time = time.time()
        
        # Update value animations
        completed = []
        for key, anim in self.animations.items():
            self._current_values[key] = anim.get_value(current_time)
            if anim.is_complete(current_time):
                completed.append(key)
        
        for key in completed:
            del self.animations[key]
        
        # Update color animations
        completed = []
        for key, anim in self.color_animations.items():
            self._current_colors[key] = anim.get_color(current_time)
            if anim.is_complete(current_time):
                completed.append(key)
        
        for key in completed:
            del self.color_animations[key]


class LerpAnimator:
    """
    Simple lerp-based animator for smooth value transitions.
    
    This is a simpler alternative to AnimationManager that uses
    linear interpolation each frame, similar to the original
    hover_progress implementation.
    
    Usage:
        animator = LerpAnimator()
        animator.set_target("hover", 1.0)
        current = animator.update("hover", speed=0.15)
    """
    
    def __init__(self):
        self._values: Dict[str, float] = {}
        self._targets: Dict[str, float] = {}
    
    def set_target(self, key: str, target: float) -> None:
        """Set target value for lerping."""
        self._targets[key] = target
        if key not in self._values:
            self._values[key] = 0.0
    
    def get_value(self, key: str, default: float = 0.0) -> float:
        """Get current value."""
        return self._values.get(key, default)
    
    def update(self, key: str, speed: float = 0.15) -> float:
        """
        Update value towards target using lerp.
        
        Args:
            key: Value key
            speed: Lerp speed (0-1, higher = faster)
        
        Returns:
            Updated value
        """
        if key not in self._values:
            self._values[key] = 0.0
        if key not in self._targets:
            self._targets[key] = 0.0
        
        current = self._values[key]
        target = self._targets[key]
        
        # Lerp towards target
        new_value = current + (target - current) * speed
        
        # Snap to target if very close
        if abs(new_value - target) < 0.001:
            new_value = target
        
        self._values[key] = new_value
        return new_value
    
    def update_all(self, speed: float = 0.15) -> Dict[str, float]:
        """
        Update all values towards their targets.
        
        Returns:
            Dictionary of all current values
        """
        for key in self._targets:
            self.update(key, speed)
        return self._values.copy()
    
    def set_immediate(self, key: str, value: float) -> None:
        """Set value immediately (no animation)."""
        self._values[key] = value
        self._targets[key] = value


# Global animation manager instance
_global_animation_manager: Optional[AnimationManager] = None
_global_lerp_animator: Optional[LerpAnimator] = None


def get_animation_manager() -> AnimationManager:
    """Get the global animation manager instance."""
    global _global_animation_manager
    if _global_animation_manager is None:
        _global_animation_manager = AnimationManager()
    return _global_animation_manager


def get_lerp_animator() -> LerpAnimator:
    """Get the global lerp animator instance."""
    global _global_lerp_animator
    if _global_lerp_animator is None:
        _global_lerp_animator = LerpAnimator()
    return _global_lerp_animator
