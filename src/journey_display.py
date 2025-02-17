import logging
from src.lib.waveshare_epd import epd7in5_V2
from src.skanetrafiken import JourneyPlanner
import time

from src.display_config import DisplayManager
from src.config import AppConfig

class JourneyDisplay:
    def __init__(self, config: AppConfig):
        self.config = config
        self.epd = self._initialize_epd()
        self.display_manager = DisplayManager(self.epd, config.display)
        self.journey_planners = self._initialize_journey_planners()

    def _initialize_epd(self):
        epd = epd7in5_V2.EPD()
        epd.init()
        epd.Clear()
        return epd

    def _initialize_journey_planners(self):
        return {
            config.display_name: JourneyPlanner(config.from_point_id, config.to_point_id)
            for config in self.config.journeys
        }

    def update_display(self):
        """Update the display with current journey information."""
        try:
            self.epd.init_fast()
            image = self.display_manager.create_base_image()
            
            # Calculate section width based on number of journey planners
            section_width = self.config.display.width // len(self.journey_planners)
            
            # Draw journey sections
            for i, (name, planner) in enumerate(self.journey_planners.items()):
                try:
                    journey_times = planner.get_journey_times()
                    start_x = i * section_width
                    self.display_manager.draw_journey_section(
                        image=image,
                        journeys=journey_times,
                        title=name,
                        start_x=start_x,
                        section_width=section_width
                    )
                except Exception as e:
                    logging.error(f"Error fetching journey times for {name}: {e}")
            
            self.display_manager.update_display(image)
            
        except Exception as e:
            logging.error(f"Error updating display: {e}")
            raise

    def cleanup(self):
        """Clean up resources and put display to sleep."""
        try:
            self.epd.init()
            self.epd.Clear()
            self.epd.sleep()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")