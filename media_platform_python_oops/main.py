# media_streaming_platform.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
import random

# --- Abstract Base Classes ---

class MediaContent(ABC):
    def __init__(self, title: str, premium: bool = False):
        self.title = title
        self.premium = premium
        self.ratings = []

    @abstractmethod
    def play(self):
        pass

    @abstractmethod
    def get_duration(self) -> int:
        pass

    @abstractmethod
    def get_file_size(self) -> float:
        pass

    @abstractmethod
    def calculate_streaming_cost(self, subscription_tier: str) -> float:
        pass

    def add_rating(self, rating: int):
        if 1 <= rating <= 5:
            self.ratings.append(rating)

    def get_average_rating(self) -> float:
        return sum(self.ratings) / len(self.ratings) if self.ratings else 0.0

    def is_premium_content(self) -> bool:
        return self.premium

class StreamingDevice(ABC):
    def __init__(self, device_name: str):
        self.device_name = device_name

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def stream_content(self, content: MediaContent):
        pass

    @abstractmethod
    def adjust_quality(self, quality: str):
        pass

    def get_device_info(self) -> str:
        return f"Device: {self.device_name}"

    def check_compatibility(self, content: MediaContent) -> bool:
        # For simplicity, all devices are compatible with all content
        return True

# --- Concrete Media Content Types ---

class Movie(MediaContent):
    def __init__(self, title, duration, resolution, genre, director, premium=False):
        super().__init__(title, premium)
        self.duration = duration  # in minutes
        self.resolution = resolution
        self.genre = genre
        self.director = director

    def play(self):
        print(f"Playing movie: {self.title} ({self.resolution})")

    def get_duration(self):
        return self.duration

    def get_file_size(self):
        # Assume 1GB per hour at 1080p, 2GB per hour at 4K
        size_per_hour = 2 if self.resolution == "4K" else 1
        return (self.duration / 60) * size_per_hour

    def calculate_streaming_cost(self, subscription_tier):
        base_cost = 5.0 if self.premium else 2.0
        if subscription_tier == "Premium":
            return base_cost * 0.5
        elif subscription_tier == "Family":
            return base_cost * 0.7
        return base_cost

class TVShow(MediaContent):
    def __init__(self, title, episodes, seasons, current_episode, premium=False):
        super().__init__(title, premium)
        self.episodes = episodes
        self.seasons = seasons
        self.current_episode = current_episode

    def play(self):
        print(f"Playing TV Show: {self.title} - S{self.seasons}E{self.current_episode}")

    def get_duration(self):
        # Assume each episode is 45 minutes
        return 45

    def get_file_size(self):
        # Assume 500MB per episode
        return 0.5

    def calculate_streaming_cost(self, subscription_tier):
        base_cost = 1.0 if self.premium else 0.5
        if subscription_tier == "Premium":
            return base_cost * 0.5
        elif subscription_tier == "Family":
            return base_cost * 0.7
        return base_cost

class Podcast(MediaContent):
    def __init__(self, title, episode_number, transcript_available, duration, premium=False):
        super().__init__(title, premium)
        self.episode_number = episode_number
        self.transcript_available = transcript_available
        self.duration = duration

    def play(self):
        print(f"Playing Podcast: {self.title} - Episode {self.episode_number}")

    def get_duration(self):
        return self.duration

    def get_file_size(self):
        # Assume 50MB per 30 minutes
        return (self.duration / 30) * 0.05

    def calculate_streaming_cost(self, subscription_tier):
        base_cost = 0.5 if self.premium else 0.2
        if subscription_tier == "Premium":
            return base_cost * 0.5
        elif subscription_tier == "Family":
            return base_cost * 0.7
        return base_cost

class Music(MediaContent):
    def __init__(self, title, artist, album, lyrics_available, duration, premium=False):
        super().__init__(title, premium)
        self.artist = artist
        self.album = album
        self.lyrics_available = lyrics_available
        self.duration = duration

    def play(self):
        print(f"Playing Music: {self.title} by {self.artist}")

    def get_duration(self):
        return self.duration

    def get_file_size(self):
        # Assume 10MB per 5 minutes
        return (self.duration / 5) * 0.01

    def calculate_streaming_cost(self, subscription_tier):
        base_cost = 0.3 if self.premium else 0.1
        if subscription_tier == "Premium":
            return base_cost * 0.5
        elif subscription_tier == "Family":
            return base_cost * 0.7
        return base_cost

# --- Concrete Streaming Devices ---

class SmartTV(StreamingDevice):
    def __init__(self):
        super().__init__("SmartTV")
        self.screen_size = "Large"
        self.resolution = "4K"
        self.surround_sound = True

    def connect(self):
        print("SmartTV connected to WiFi.")

    def stream_content(self, content: MediaContent):
        print(f"Streaming '{content.title}' on SmartTV in {self.resolution} with surround sound.")

    def adjust_quality(self, quality: str):
        print(f"SmartTV quality set to {quality}.")

class Laptop(StreamingDevice):
    def __init__(self):
        super().__init__("Laptop")
        self.screen_size = "Medium"
        self.headphone_support = True

    def connect(self):
        print("Laptop connected to WiFi.")

    def stream_content(self, content: MediaContent):
        print(f"Streaming '{content.title}' on Laptop with headphones.")

    def adjust_quality(self, quality: str):
        print(f"Laptop quality set to {quality}.")

class Mobile(StreamingDevice):
    def __init__(self):
        super().__init__("Mobile")
        self.screen_size = "Small"
        self.battery_optimization = True

    def connect(self):
        print("Mobile connected to cellular network.")

    def stream_content(self, content: MediaContent):
        print(f"Streaming '{content.title}' on Mobile with battery optimization.")

    def adjust_quality(self, quality: str):
        print(f"Mobile quality set to {quality}.")

class SmartSpeaker(StreamingDevice):
    def __init__(self):
        super().__init__("SmartSpeaker")
        self.audio_only = True
        self.voice_control = True

    def connect(self):
        print("SmartSpeaker connected to WiFi.")

    def stream_content(self, content: MediaContent):
        print(f"Streaming '{content.title}' on SmartSpeaker (audio only).")

    def adjust_quality(self, quality: str):
        print(f"SmartSpeaker audio quality set to {quality}.")

# --- User and Platform Classes ---

class User:
    def __init__(self, username: str, subscription_tier: str = "Free", parental_control: bool = False):
        self.username = username
        self.subscription_tier = subscription_tier  # Free, Premium, Family
        self.watch_history: List[MediaContent] = []
        self.preferences: Dict[str, Any] = {}
        self.parental_control = parental_control
        self.analytics: Dict[str, int] = {}  # title -> watch time in minutes

    def watch(self, content: MediaContent, device: StreamingDevice):
        if self.parental_control and getattr(content, "genre", "") == "Adult":
            print("Parental control enabled. Cannot play this content.")
            return
        device.connect()
        device.stream_content(content)
        content.play()
        self.watch_history.append(content)
        self.analytics[content.title] = self.analytics.get(content.title, 0) + content.get_duration()

    def set_preference(self, key: str, value: Any):
        self.preferences[key] = value

    def get_recommendations(self, all_content: List[MediaContent]) -> List[MediaContent]:
        # Simple recommendation: match genre or artist/album
        recs = []
        pref_genre = self.preferences.get("genre")
        pref_artist = self.preferences.get("artist")
        for c in all_content:
            if pref_genre and hasattr(c, "genre") and c.genre == pref_genre:
                recs.append(c)
            elif pref_artist and hasattr(c, "artist") and c.artist == pref_artist:
                recs.append(c)
        # Fallback: random
        if not recs:
            recs = random.sample(all_content, min(3, len(all_content)))
        return recs

    def get_analytics(self):
        return self.analytics

class StreamingPlatform:
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.content: List[MediaContent] = []
        self.devices: List[StreamingDevice] = []

    def add_user(self, user: User):
        self.users[user.username] = user

    def add_content(self, content: MediaContent):
        self.content.append(content)

    def add_device(self, device: StreamingDevice):
        self.devices.append(device)

    def recommend_content(self, username: str) -> List[MediaContent]:
        user = self.users.get(username)
        if user:
            return user.get_recommendations(self.content)
        return []

    def report_watch_time(self, username: str):
        user = self.users.get(username)
        if user:
            return user.get_analytics()
        return {}

    def filter_content(self, parental_control: bool) -> List[MediaContent]:
        if parental_control:
            return [c for c in self.content if getattr(c, "genre", "") != "Adult"]
        return self.content

# --- Example Usage ---

if __name__ == "__main__":
    # Create platform
    platform = StreamingPlatform()

    # Add content
    m1 = Movie("Inception", 148, "4K", "Sci-Fi", "Christopher Nolan", premium=True)
    m2 = Movie("Toy Story", 81, "1080p", "Animation", "John Lasseter")
    tv1 = TVShow("Breaking Bad", 62, 5, 1, premium=True)
    p1 = Podcast("TechTalk", 10, True, 60)
    mu1 = Music("Imagine", "John Lennon", "Imagine", True, 4)

    platform.add_content(m1)
    platform.add_content(m2)
    platform.add_content(tv1)
    platform.add_content(p1)
    platform.add_content(mu1)

    # Add devices
    tv = SmartTV()
    laptop = Laptop()
    mobile = Mobile()
    speaker = SmartSpeaker()

    platform.add_device(tv)
    platform.add_device(laptop)
    platform.add_device(mobile)
    platform.add_device(speaker)

    # Add user
    user1 = User("alice", "Premium")
    user1.set_preference("genre", "Sci-Fi")
    platform.add_user(user1)

    # User watches content
    user1.watch(m1, tv)
    user1.watch(mu1, mobile)

    # Recommendations
    recs = platform.recommend_content("alice")
    print("Recommended for alice:")
    for r in recs:
        print(f"- {r.title}")

    # Analytics
    print("Watch time analytics:", platform.report_watch_time("alice"))

    # Parental control filtering
    print("Content with parental control:")
    for c in platform.filter_content(parental_control=True):
        print(f"- {c.title}")
