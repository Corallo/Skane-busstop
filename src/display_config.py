from PIL import Image, ImageDraw, ImageFont, ImageOps
from typing import List, Dict
import logging
from src.time_manager import TimeManager
from src.config import DisplayConfig

class DisplayManager:
    def __init__(self, epd, config: DisplayConfig):
        self.epd = epd
        self.config = config
        self.fonts = self._initialize_fonts()
        self.time_manager = TimeManager()

    def create_time_image(self) -> Image.Image:
        """Create an image containing only the current time."""
        image = Image.new('1', (200, 60), 255)
        draw = ImageDraw.Draw(image)
        
        draw.text((10, 10), self.time_manager.get_current_time(), 
                 font=self.fonts['large'], fill=0)
        
        return image
        
    def _initialize_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        return {
            size_name: ImageFont.truetype(self.config.font_path, size) 
            for size_name, size in self.config.font_sizes.items()
        }
    
    def create_base_image(self) -> Image.Image:
        """Create a new base image with initial layout."""
        image = Image.new('1', (self.config.width, self.config.height), 255)
        draw = ImageDraw.Draw(image)
        
        # Draw vertical division line
        draw.line((self.config.width//2, 0, self.config.width//2, self.config.height), fill=0)
        
        # Draw header line
        draw.line((0, 60, self.config.width, 60), fill=0)
        
        # Draw current time in Sweden timezone
        draw.text((10, 10), self.time_manager.get_current_time(), font=self.fonts['large'], fill=0)
        
        return image

    def draw_journey_section(self, image: Image.Image, journeys: List[Dict], 
                           title: str, start_x: int, section_width: int,
                           spacing: int = 50) -> None:
        """Draw a section of journey information with columns."""
        draw = ImageDraw.Draw(image)
        
        title_y = 70+20
        headers_y = 150
        content_start_y = 180
        column_padding = 10
        
        symbol_width = 30
        content_start_x = start_x + column_padding + symbol_width
        remaining_width = section_width - (2 * column_padding) - symbol_width
        column_width = remaining_width // 3
        
        departure_x = content_start_x
        arrival_x = departure_x + column_width
        track_x = arrival_x + column_width
        
        title_x = start_x + (section_width - len(title)*18) // 2
        draw.text((title_x, title_y), title, font=self.fonts['medium_large'], fill=0)
        
        draw.text((departure_x, headers_y), "Departure", font=self.fonts['small'], fill=0)
        draw.text((arrival_x+10, headers_y), "Arrival", font=self.fonts['small'], fill=0)
        draw.text((track_x, headers_y), "Track", font=self.fonts['small'], fill=0)
        
        draw.line((start_x + 5, headers_y + 25, 
                  start_x + section_width - 5, headers_y + 25), fill=0)
        
        # Draw journey entries
        for i, entry in enumerate(journeys[:5]):
            y_pos = content_start_y + (spacing * i)
            
            symbol_x = start_x + column_padding
            if entry.get('cancelled'):
                draw.text((symbol_x, y_pos), "×", font=self.fonts['medium'], fill=0)
            elif entry.get('delay'):
                draw.text((symbol_x, y_pos), "!", font=self.fonts['medium'], fill=0)
            
            # Draw times using the same x positions as headers
            draw.text((departure_x, y_pos), entry['departure'], 
                     font=self.fonts['medium'], fill=0)
            draw.text((arrival_x, y_pos), entry['arrival'], 
                     font=self.fonts['medium'], fill=0)
            if entry['track'] != "Cancelled":
                draw.text((track_x, y_pos), entry['track'].split(" ")[-1], 
                         font=self.fonts['medium'], fill=0)
            if entry.get('delay'):
                draw.text((departure_x + 85, y_pos - 8), 
                         "+"+str(entry['delay']), font=self.fonts['small'], fill=0)

    def update_display(self, image: Image.Image) -> None:
        """Update the EPD display with the given image."""
        self.epd.display(self.epd.getbuffer(image))
    
    def flip_color(self, image: Image.Image) -> Image.Image:
        display_image = image.convert("L")
        display_image = ImageOps.invert(display_image)
        display_image = display_image.convert("1")
        return display_image