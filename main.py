# main.py
import logging
import signal
import sys
import time
from datetime import datetime, timedelta, time as dt_time
import os
import random
from pathlib import Path

from src.config import AppConfig
from src.journey_display import JourneyDisplay
from PIL import Image,ImageDraw
from src.time_manager import TimeManager

class DisplayController:
    def __init__(self):
        self.config = AppConfig()
        self.journey_display = JourneyDisplay(self.config)
        self.is_running = True
        self.last_art_update = None
        self.img_folder = Path('./img')
        self.current_art = None
        self.base_image = None  # Store the base image for partial updates
        self.last_full_refresh = None
        self.next_full_refresh_time = None
        self.time_manger = TimeManager()

    def cleanup(self):
        """Cleanup resources before shutdown."""
        logging.info("Cleaning up...")
        self.journey_display.cleanup()

    def get_current_mode(self) -> str:
        """Determine the current display mode based on time of day."""
        current_time = datetime.now().time()
        
        # Journey display time: 06:00 - 10:00
        journey_start = dt_time(6, 0)
        journey_end = dt_time(10, 0)
        
        # Art display time: 10:00 - 22:00
        art_start = dt_time(10, 0)
        art_end = dt_time(22, 0)
        
        # Sleep time: 23:00 - 07:00
        # Special case: 1 AM shutdown
        if current_time.hour == 1 and current_time.minute == 0:
            return "shutdown"
        
        if journey_start <= current_time < journey_end:
            return "journey"
        elif art_start <= current_time < art_end:
            return "art"
        else:
            return "sleep"
    
    def initialize_journey_display(self):
        """Initialize the display with full content for the first time."""
        try:
            self.journey_display.epd.init_fast()
            self.base_image = self.journey_display.display_manager.create_base_image()
            # Draw initial journey information
            section_width = self.config.display.width // len(self.journey_display.journey_planners)
            for i, (name, planner) in enumerate(self.journey_display.journey_planners.items()):
                journey_times = planner.get_journey_times()
                start_x = i * section_width
                self.journey_display.display_manager.draw_journey_section(
                    image=self.base_image,
                    journeys=journey_times,
                    title=name,
                    start_x=start_x,
                    section_width=section_width
                )
            # Display the full image
            self.journey_display.epd.display(self.journey_display.epd.getbuffer(self.base_image))
            time.sleep(2)  # Wait for the display to settle
            # Initialize partial mode
            self.journey_display.epd.init_part()
        except Exception as e:
            logging.error(f"Error initializing journey display: {e}")
            raise

    def update_time_display(self):
        """Update only the time portion of the display."""
        try:
            if self.base_image is None:
                self.initialize_journey_display()
                return

            # Create ImageDraw object for the existing base image
            draw = ImageDraw.Draw(self.base_image)
            
            # Clear the time area with white rectangle
            time_x, time_y = 10, 10
            time_width, time_height = 200, 60
            draw.rectangle((time_x, time_y, time_x + time_width, time_y + time_height), fill=255)
            
            # Draw new time
            current_time = self.journey_display.display_manager.time_manager.get_current_time()
            draw.text((time_x, time_y), current_time, 
                     font=self.journey_display.display_manager.fonts['large'], fill=0)
            
            # Perform partial update
            self.journey_display.epd.display_Partial(
                self.journey_display.epd.getbuffer(self.base_image),
                0, 0, self.journey_display.epd.width, self.journey_display.epd.height
            )
        except Exception as e:
            logging.error(f"Error updating time display: {e}")
            raise


    def display_journey(self):
        """Update journey information on display."""
        current_time = datetime.now()
        
        # Check if we need a full refresh
        needs_full_refresh = (
            self.base_image is None or
            (self.last_full_refresh and 
             (current_time - self.last_full_refresh).total_seconds() >= 300)  # 5 minutes
        )

        if needs_full_refresh:
            # Perform full refresh
            self.initialize_journey_display()
            self.last_full_refresh = current_time
        else:
            # Only update the time
            self.update_time_display()


    def get_random_image(self) -> Path:
        """Select a random image from the img folder."""
        # List all files with common image extensions
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp'}
        image_files = [
            f for f in self.img_folder.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            raise FileNotFoundError("No image files found in the img folder")
        
        # Select a random image, different from the current one if possible
        available_images = [img for img in image_files if img != self.current_art]
        if not available_images and image_files:
            available_images = image_files
            
        selected_image = random.choice(available_images)
        self.current_art = selected_image
        return selected_image

    def prepare_art_image(self, img: Image.Image) -> Image.Image:
        """Prepare an image for display by resizing and converting it appropriately."""

        display_width = self.config.display.width
        display_height = self.config.display.height
        
        img_ratio = img.width / img.height
        display_ratio = display_width / display_height
        
        if img_ratio > display_ratio:
            # Image is wider than display
            new_width = display_width
            new_height = int(display_width / img_ratio)
        else:
            # Image is taller than display
            new_height = display_height
            new_width = int(display_height * img_ratio)
        
        background = Image.new('1', (display_width, display_height), 255)
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        resized_img = resized_img.convert('L')  # Convert to grayscale first
        resized_img = resized_img.point(lambda x: 0 if x < 128 else 255, '1')  # Convert to binary
        
        x = (display_width - new_width) // 2
        y = (display_height - new_height) // 2
        
        background.paste(resized_img, (x, y))
        
        return background
    
    def display_art(self):
        """Display random art and go to sleep."""
        if self.last_art_update is None:
            try:
                self.journey_display.epd.init()
                image_path = self.get_random_image()
                with Image.open(image_path) as img:
                    background = self.prepare_art_image(img)
                    self.journey_display.epd.display(self.journey_display.epd.getbuffer(background))
                    self.last_art_update = datetime.now()
                    time.sleep(3)  # Wait for the display to settle
                    self.journey_display.epd.sleep()
            except Exception as e:
                logging.error(f"Error displaying art: {e}")
                raise
    
    def display_shutdown(self):
        """Turn off the display at 1 AM."""
        try:
            self.journey_display.epd.init()
            self.journey_display.epd.Clear()
            self.journey_display.epd.sleep()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
            raise

    def update_display(self):
        """Update display based on current mode."""
        current_mode = self.get_current_mode()
        logging.info(f"Current display mode: {current_mode}")
        
        if current_mode == "shutdown":
            self.display_shutdown()
        elif current_mode == "journey":
            self.display_journey()
        elif current_mode == "art":
            self.display_art()
        elif current_mode == "sleep":
            self.journey_display.cleanup()

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("debug.log")
        ]
    )
    
    controller = DisplayController()
    
    def signal_handler(signum, frame):
        logging.info("Shutting down...")
        controller.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        last_mode = None
        while controller.is_running:
            current_mode = controller.get_current_mode()
            
            if current_mode == "journey":
                controller.update_display()
                time.sleep(30)
            elif current_mode == "art":
                if last_mode != "art":
                    controller.update_display()
                time.sleep(300)
            elif current_mode == "shutdown":
                controller.update_display()
                time.sleep(3600)
            else:  # sleep mode
                if last_mode != "sleep":
                    controller.update_display()
                time.sleep(300)
                
            last_mode = current_mode
                
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        controller.cleanup()
        sys.exit(1)
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()
