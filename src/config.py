from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

@dataclass
class DisplayConfig:
    width: int
    height: int
    font_path: str
    font_sizes: Dict[str, int] = None

    def __post_init__(self):
        if self.font_sizes is None:
            self.font_sizes = {
                "small": 16,
                "medium": 32,
                "medium_large": 36,
                "large": 42
            }

@dataclass
class JourneyConfig:
    from_point_id: str
    to_point_id: str
    display_name: str
    max_journeys: int = 5

class AppConfig:
    def __init__(self):
        self.display = DisplayConfig(
            width=800,
            height=480,
            font_path='/home/pi/project/src/font/inter.ttf'
        )
        
        self.journeys = [
            JourneyConfig("9021012080040000", "9021012081216000", "Hyllie → Lund"),
            JourneyConfig("9021012080040000", "9021012045011000", "Hyllie → Østerport")
        ]
