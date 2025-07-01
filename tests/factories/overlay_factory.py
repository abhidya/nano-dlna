"""Overlay configuration factory for creating test overlay instances."""

import factory
from factory import fuzzy
from datetime import datetime, timezone
import random
import json
from typing import Dict, List, Any

from web.backend.models.overlay import OverlayConfig, OverlayType


class OverlayConfigFactory(factory.Factory):
    """Factory for creating OverlayConfig instances."""
    
    class Meta:
        model = OverlayConfig
    
    id = factory.Sequence(lambda n: n)
    video_id = fuzzy.FuzzyInteger(1, 100)
    
    @factory.lazy_attribute
    def type(self):
        return random.choice([t.value for t in OverlayType])
    
    @factory.lazy_attribute
    def config(self):
        if self.type == OverlayType.IMAGE.value:
            return self._generate_image_config()
        elif self.type == OverlayType.TEXT.value:
            return self._generate_text_config()
        elif self.type == OverlayType.VIDEO.value:
            return self._generate_video_config()
        elif self.type == OverlayType.SHAPE.value:
            return self._generate_shape_config()
        elif self.type == OverlayType.EFFECT.value:
            return self._generate_effect_config()
        else:
            return {}
    
    enabled = fuzzy.FuzzyChoice([True, False], weights=[0.8, 0.2])
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    def _generate_image_config(self) -> Dict[str, Any]:
        """Generate configuration for image overlay."""
        return {
            "url": f"https://example.com/overlay_{random.randint(1, 100)}.png",
            "position": {
                "x": random.randint(0, 80),
                "y": random.randint(0, 80)
            },
            "size": {
                "width": random.randint(10, 50),
                "height": random.randint(10, 50)
            },
            "opacity": round(random.uniform(0.3, 1.0), 2),
            "animation": random.choice([
                None,
                {"type": "fade", "duration": 1000},
                {"type": "slide", "direction": "right", "duration": 2000}
            ])
        }
    
    def _generate_text_config(self) -> Dict[str, Any]:
        """Generate configuration for text overlay."""
        messages = [
            "Sample Text Overlay",
            "Live Stream",
            "Recording in Progress",
            "Welcome to the Show"
        ]
        
        return {
            "text": random.choice(messages),
            "font": random.choice(["Arial", "Helvetica", "Times New Roman", "Courier"]),
            "size": random.randint(16, 72),
            "color": f"#{random.randint(0, 0xFFFFFF):06x}",
            "background": random.choice([
                None,
                {"color": f"#{random.randint(0, 0xFFFFFF):06x}", "opacity": 0.7}
            ]),
            "position": {
                "x": random.randint(0, 80),
                "y": random.randint(0, 80)
            },
            "animation": random.choice([
                None,
                {"type": "typewriter", "speed": 50},
                {"type": "scroll", "direction": "left", "speed": 2}
            ])
        }
    
    def _generate_video_config(self) -> Dict[str, Any]:
        """Generate configuration for video overlay."""
        return {
            "url": f"https://example.com/overlay_video_{random.randint(1, 50)}.mp4",
            "position": {
                "x": random.randint(0, 70),
                "y": random.randint(0, 70)
            },
            "size": {
                "width": random.randint(20, 40),
                "height": random.randint(20, 40)
            },
            "loop": True,
            "muted": True,
            "opacity": round(random.uniform(0.7, 1.0), 2)
        }
    
    def _generate_shape_config(self) -> Dict[str, Any]:
        """Generate configuration for shape overlay."""
        shapes = ["rectangle", "circle", "triangle", "polygon"]
        shape_type = random.choice(shapes)
        
        config = {
            "shape": shape_type,
            "fill": f"#{random.randint(0, 0xFFFFFF):06x}",
            "stroke": f"#{random.randint(0, 0xFFFFFF):06x}",
            "strokeWidth": random.randint(1, 5),
            "opacity": round(random.uniform(0.3, 0.8), 2)
        }
        
        if shape_type == "rectangle":
            config.update({
                "x": random.randint(0, 80),
                "y": random.randint(0, 80),
                "width": random.randint(10, 30),
                "height": random.randint(10, 30)
            })
        elif shape_type == "circle":
            config.update({
                "cx": random.randint(10, 90),
                "cy": random.randint(10, 90),
                "radius": random.randint(5, 20)
            })
        
        return config
    
    def _generate_effect_config(self) -> Dict[str, Any]:
        """Generate configuration for effect overlay."""
        effects = ["blur", "brightness", "contrast", "grayscale", "sepia"]
        
        return {
            "effect": random.choice(effects),
            "intensity": round(random.uniform(0.1, 1.0), 2),
            "region": random.choice([
                None,  # Full screen
                {
                    "x": random.randint(0, 50),
                    "y": random.randint(0, 50),
                    "width": random.randint(30, 50),
                    "height": random.randint(30, 50)
                }
            ])
        }


class OverlayEventFactory(factory.Factory):
    """Factory for creating overlay events."""
    
    class Meta:
        model = dict
    
    overlay_id = fuzzy.FuzzyInteger(1, 100)
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    
    @factory.lazy_attribute
    def event_type(self):
        return random.choice([
            "show", "hide", "update", "animate", "error"
        ])
    
    @factory.lazy_attribute
    def data(self):
        if self.event_type == "show":
            return {"duration": random.randint(1000, 5000)}
        elif self.event_type == "hide":
            return {"fade_out": random.choice([True, False])}
        elif self.event_type == "update":
            return {
                "property": random.choice(["position", "size", "opacity"]),
                "value": random.randint(0, 100)
            }
        elif self.event_type == "animate":
            return {
                "animation": random.choice(["bounce", "rotate", "pulse"]),
                "duration": random.randint(500, 2000)
            }
        elif self.event_type == "error":
            return {
                "error": random.choice([
                    "Failed to load resource",
                    "Invalid configuration",
                    "Network timeout"
                ])
            }


def create_overlay_scenarios() -> Dict[str, List[OverlayConfig]]:
    """Create various overlay test scenarios."""
    scenarios = {
        "simple_text": [
            OverlayConfigFactory.create(
                type=OverlayType.TEXT.value,
                config={
                    "text": "Simple Overlay",
                    "position": {"x": 10, "y": 10},
                    "size": 24,
                    "color": "#FFFFFF"
                }
            )
        ],
        "multi_overlay": [
            OverlayConfigFactory.create(type=OverlayType.IMAGE.value),
            OverlayConfigFactory.create(type=OverlayType.TEXT.value),
            OverlayConfigFactory.create(type=OverlayType.SHAPE.value)
        ],
        "animated": [
            OverlayConfigFactory.create(
                type=OverlayType.TEXT.value,
                config={
                    "text": "Scrolling Text",
                    "animation": {
                        "type": "scroll",
                        "direction": "left",
                        "speed": 3
                    }
                }
            )
        ],
        "picture_in_picture": [
            OverlayConfigFactory.create(
                type=OverlayType.VIDEO.value,
                config={
                    "url": "https://example.com/pip_video.mp4",
                    "position": {"x": 60, "y": 60},
                    "size": {"width": 30, "height": 30}
                }
            )
        ],
        "watermark": [
            OverlayConfigFactory.create(
                type=OverlayType.IMAGE.value,
                config={
                    "url": "https://example.com/logo.png",
                    "position": {"x": 85, "y": 85},
                    "size": {"width": 10, "height": 10},
                    "opacity": 0.5
                }
            )
        ],
        "complex": [
            OverlayConfigFactory.create(type=overlay_type.value)
            for overlay_type in OverlayType
        ]
    }
    
    return scenarios


class OverlayTemplateFactory(factory.Factory):
    """Factory for creating reusable overlay templates."""
    
    class Meta:
        model = dict
    
    name = factory.LazyFunction(
        lambda: f"Template_{random.choice(['Logo', 'Banner', 'Credits', 'Watermark'])}_{random.randint(100, 999)}"
    )
    
    @factory.lazy_attribute
    def overlays(self):
        template_type = self.name.split('_')[1]
        
        if template_type == "Logo":
            return [OverlayConfigFactory.build(
                type=OverlayType.IMAGE.value,
                config={
                    "url": "https://example.com/logo.png",
                    "position": {"x": 10, "y": 10},
                    "size": {"width": 15, "height": 15}
                }
            )]
        elif template_type == "Banner":
            return [
                OverlayConfigFactory.build(
                    type=OverlayType.SHAPE.value,
                    config={
                        "shape": "rectangle",
                        "x": 0, "y": 80,
                        "width": 100, "height": 20,
                        "fill": "#000000",
                        "opacity": 0.7
                    }
                ),
                OverlayConfigFactory.build(
                    type=OverlayType.TEXT.value,
                    config={
                        "text": "Important Announcement",
                        "position": {"x": 50, "y": 90},
                        "size": 32,
                        "color": "#FFFFFF"
                    }
                )
            ]
        else:
            return [OverlayConfigFactory.build()]
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "author": "Test User",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tags": ["test", "template"],
            "usage_count": random.randint(0, 100)
        }