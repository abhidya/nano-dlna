"""Video factory for creating test video instances."""

import factory
from factory import fuzzy
from datetime import timedelta
import random
import os
import tempfile
from types import SimpleNamespace
from typing import List, Optional

from tests.test_utils import create_test_video_file


class VideoFactory(factory.Factory):
    """Factory for creating Video instances."""
    
    class Meta:
        model = SimpleNamespace
    
    id = factory.Sequence(lambda n: n + 1)
    
    @factory.lazy_attribute
    def name(self):
        themes = ["Nature", "City", "Abstract", "Time-lapse", "Demo"]
        adjectives = ["Beautiful", "Amazing", "Stunning", "Relaxing", "Dynamic"]
        return f"{random.choice(adjectives)}_{random.choice(themes)}_{random.randint(100, 999)}"
    
    @factory.lazy_attribute
    def path(self):
        base_dir = os.path.join(tempfile.gettempdir(), "nano_dlna_test_videos")
        os.makedirs(base_dir, exist_ok=True)
        path = os.path.join(base_dir, f"{self.name}.mp4")
        if not os.path.exists(path):
            with open(path, "wb") as video_file:
                video_file.write(b"fake video content")
        return path

    @factory.lazy_attribute
    def file_name(self):
        return os.path.basename(self.path)
    
    file_size = fuzzy.FuzzyInteger(1_000_000, 1_000_000_000)  # 1MB to 1GB
    
    @factory.lazy_attribute
    def duration(self):
        return float(random.randint(30, 7200))
    
    @factory.lazy_attribute
    def resolution(self):
        resolutions = ["1920x1080", "1280x720", "3840x2160", "2560x1440"]
        return random.choice(resolutions)
    
    format = "mp4"
    has_subtitle = False
    subtitle_path = None


class VideoFileFactory:
    """Factory for creating actual video files for testing."""
    
    @staticmethod
    def create_test_file(
        name: Optional[str] = None,
        duration: int = 10,
        resolution: str = "640x480",
        with_audio: bool = True,
        output_dir: str = "/tmp/test_videos"
    ) -> str:
        """Create an actual video file for testing."""
        if not name:
            name = f"test_video_{random.randint(1000, 9999)}"
        
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, f"{name}.mp4")
        
        # Use the existing test utility
        create_test_video_file(
            file_path,
            duration=duration,
            width=int(resolution.split('x')[0]),
            height=int(resolution.split('x')[1])
        )
        
        return file_path
    
    @staticmethod
    def create_video_library(num_videos: int = 5) -> List[SimpleNamespace]:
        """Create a library of test videos with files."""
        videos = []
        
        categories = {
            "demo": {"duration": 30, "resolution": "1920x1080"},
            "test": {"duration": 10, "resolution": "1280x720"},
            "loop": {"duration": 60, "resolution": "1920x1080"},
            "short": {"duration": 5, "resolution": "640x480"}
        }
        
        for i in range(num_videos):
            category = random.choice(list(categories.keys()))
            settings = categories[category]
            
            # Create the actual file
            file_path = VideoFileFactory.create_test_file(
                name=f"{category}_video_{i}",
                duration=settings["duration"],
                resolution=settings["resolution"]
            )
            
            # Create the video model
            video = VideoFactory.create(
                path=file_path,
                duration=float(settings["duration"]),
                resolution=settings["resolution"],
                file_size=os.path.getsize(file_path),
                format="mp4",
            )
            
            videos.append(video)
        
        return videos


class PlaylistFactory(factory.Factory):
    """Factory for creating video playlists."""
    
    class Meta:
        model = dict
    
    name = factory.LazyFunction(
        lambda: f"Playlist_{random.choice(['Demos', 'Nature', 'Tests', 'Mixed'])}_{random.randint(100, 999)}"
    )
    
    @factory.lazy_attribute
    def videos(self):
        num_videos = random.randint(3, 10)
        return VideoFactory.create_batch(num_videos)
    
    shuffle = fuzzy.FuzzyChoice([True, False])
    repeat = True
    
    @factory.lazy_attribute
    def total_duration(self):
        total_seconds = sum(float(v.duration) for v in self.videos)
        return str(timedelta(seconds=total_seconds))


def create_test_video_scenarios():
    """Create various video test scenarios."""
    scenarios = {
        "standard": {
            "videos": [
                VideoFactory.create(
                    name="Standard_HD_Video",
                    resolution="1920x1080",
                    format="mp4",
                    duration=600.0
                )
            ]
        },
        "4k": {
            "videos": [
                VideoFactory.create(
                    name="4K_UHD_Video",
                    resolution="3840x2160",
                    format="mp4",
                    duration=300.0,
                )
            ]
        },
        "long_duration": {
            "videos": [
                VideoFactory.create(
                    name="Long_Movie",
                    resolution="1920x1080",
                    duration=9000.0,
                    file_size=5_000_000_000
                )
            ]
        },
        "playlist": {
            "playlist": PlaylistFactory.create(
                name="Test_Playlist",
                videos=VideoFactory.create_batch(5)
            )
        },
        "various_codecs": {
            "videos": [
                VideoFactory.create(name=f"{codec}_test", format=codec)
                for codec in ["h264", "h265", "vp9", "av1"]
            ]
        }
    }
    
    return scenarios
