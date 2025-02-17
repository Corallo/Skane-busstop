from datetime import datetime, timedelta
import pytz

class TimeManager:
    def __init__(self):
        self.sweden_tz = pytz.timezone('Europe/Stockholm')
    
    def get_current_time(self) -> str:
        """Get current time in Sweden in HH:MM format."""
        return datetime.now(self.sweden_tz).strftime('%H:%M')
    
    def convert_to_sweden_time(self, time_str: str) -> str:
        """Converts a time string from UTC to Swedish time."""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            utc_time = pytz.UTC.localize(datetime.combine(datetime.utcnow().date(), time_obj.time()))
            sweden_time = utc_time.astimezone(self.sweden_tz)
            return sweden_time.strftime("%H:%M")
        except ValueError:
            return time_str

    
    def is_future_time(self, time_str: str, min_minutes_ahead: int = 5) -> bool:
        """Check if a time (already in Swedish time) is at least `min_minutes_ahead` minutes in the future."""
        try:

            current_time = datetime.now(self.sweden_tz)
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            check_time = self.sweden_tz.localize(
                datetime.combine(current_time.date(), time_obj)
            )
            if check_time < current_time - timedelta(hours=1):
                check_time += timedelta(days=1)
            return check_time > current_time + timedelta(minutes=min_minutes_ahead)

        except ValueError:
            return False

    
    def convert_to_sweden_datetime(self, time_str: str) -> datetime:
        """Converts a time string (HH:MM in UTC) to a full Sweden-localized datetime object."""
        time_obj = datetime.strptime(time_str, "%H:%M")  # Parse time as HH:MM
        utc_time = pytz.UTC.localize(datetime.combine(datetime.utcnow().date(), time_obj.time()))  
        return utc_time.astimezone(self.sweden_tz)  # Convert to Sweden time

