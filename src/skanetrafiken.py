import requests
import re
from datetime import datetime, timedelta
from src.time_manager import TimeManager

class JourneyPlanner:
    def __init__(self, from_point_id, to_point_id):
        self.url = "https://www.skanetrafiken.se/gw-tps/api/v2/Journey"
        self.from_point_id = from_point_id
        self.to_point_id = to_point_id
        self.time_manager = TimeManager()
        self.params = {
            "fromPointId": self.from_point_id,
            "fromPointType": "STOP_AREA",
            "toPointId": self.to_point_id,
            "toPointType": "STOP_AREA",
            "arrival": "false",
            "priority": "SHORTEST_TIME",
            "journeysAfter": "6",
            "walkSpeed": "NORMAL",
            "maxWalkDistance": "2000",
            "allowWalkToOtherStop": "true"
        }
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "sv-SE",
            "search-engine-environment": "TjP",
        }

    def extract_time(self, timestamp):
            """Extracts hours and minutes from a timestamp and converts to Sweden time."""
            pattern = r"(\d{2}):(\d{2})"
            match = re.search(pattern, timestamp)
            if match:
                time_str = match.group(1) + ":" + match.group(2)
                return self.time_manager.convert_to_sweden_time(time_str)
            return timestamp


    def get_route_status(self, route_info):
        """Returns the formatted time with status (e.g., 'Cancelled' if applicable)."""
        time_departure = self.extract_time(route_info["routeLinks"][0]["from"]["time"])
        time_arrival = self.extract_time(route_info["routeLinks"][0]["to"]["time"])
        try:
            delay_time = route_info["routeLinks"][0]["from"]["deviation"]
        except KeyError:
            delay_time = None
        if "deviationTag" in route_info and route_info["deviationTag"]["text"] == "INSTÄLLD":
            return {"departure": time_departure, "arrival": "Cancelled", "track": "Cancelled"}
        else:
            track = route_info["routeLinks"][0]["from"]["pos"]
            return {"departure": time_departure, "arrival": time_arrival, "track": track, "delay": delay_time}

    def filter_upcoming_journeys(self, journey_times):
        """Filters out journeys that have already departed or depart in the next 5 minutes."""
        upcoming_journeys = []
        
        for journey in journey_times:
            departure_str = journey["departure"]
            if departure_str == "Cancelled":
                continue
                
            if self.time_manager.is_future_time(departure_str, min_minutes_ahead=5):
                upcoming_journeys.append(journey)
                
        return sorted(upcoming_journeys, key=lambda x: x["departure"])
    
    def get_journey_times(self):
        """Fetches and returns the journey times as a dictionary."""
        response = requests.get(self.url, params=self.params, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            journeys = data.get("journeys", [])
            journey_times = [self.get_route_status(route) for route in journeys]
            journey_times = self.filter_upcoming_journeys(journey_times)
            return journey_times
        else:
            raise Exception(f"Request failed with status code {response.status_code}")

if __name__ == "__main__":
    journey_planner_lund = JourneyPlanner("9021012080040000", "9021012081216000")
    try:
        journey_times = journey_planner_lund.get_journey_times()
        print(journey_times)
    except Exception as e:
        print(e)