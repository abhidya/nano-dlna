"""Video factory for creating test video instances."""

import factory
from factory import fuzzy
from datetime import datetime, timezone, timedelta
import random
import os
from typing import List, Optional

from web.backend.models.video import Video
from tests.test_utils import create_test_video_file


class VideoFactory(factory.Factory):
    """Factory for creating Video instances."""
    
    class Meta:
        model = Video
    
    id = factory.Sequence(lambda n: n)
    
    @factory.lazy_attribute
    def name(self):
        themes = ["Nature", "City", "Abstract", "Time-lapse", "Demo"]
        adjectives = ["Beautiful", "Amazing", "Stunning", "Relaxing", "Dynamic"]
        return f"{random.choice(adjectives)}_{random.choice(themes)}_{random.randint(100, 999)}"
    
    @factory.lazy_attribute
    def file_path(self):
        base_dir = "/tmp/test_videos"
        return os.path.join(base_dir, f"{self.name}.mp4")
    
    file_size = fuzzy.FuzzyInteger(1_000_000, 1_000_000_000)  # 1MB to 1GB
    
    @factory.lazy_attribute
    def duration(self):
        # Duration in seconds (30s to 2 hours)
        seconds = random.randint(30, 7200)
        return str(timedelta(seconds=seconds))
    
    @factory.lazy_attribute
    def resolution(self):
        resolutions = ["1920x1080", "1280x720", "3840x2160", "2560x1440"]
        return random.choice(resolutions)
    
    @factory.lazy_attribute
    def codec(self):
        codecs = ["h264", "h265", "vp9", "av1"]
        return random.choice(codecs)
    
    @factory.lazy_attribute
    def bitrate(self):
        # Bitrate in kbps
        return random.randint(1000, 10000)
    
    @factory.lazy_attribute
    def metadata(self):
        return {
            "fps": random.choice([24, 25, 30, 60]),
            "audio_codec": random.choice(["aac", "mp3", "opus"]),
            "audio_bitrate": random.randint(128, 320),
            "container": "mp4",
            "has_audio": True,
            "creation_date": datetime.now(timezone.utc).isoformat()
        }
    
    uploaded_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    last_played = None
    play_count = 0
    
    @factory.lazy_attribute
    def tags(self):
        all_tags = ["demo", "loop", "nature", "urban", "abstract", "4k", "hd", "test"]
        num_tags = random.randint(1, 4)
        return random.sample(all_tags, num_tags)


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
    def create_video_library(num_videos: int = 5) -> List[Video]:
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
                file_path=file_path,
                duration=str(timedelta(seconds=settings["duration"])),
                resolution=settings["resolution"],
                file_size=os.path.getsize(file_path),
                tags=[category]
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
        total_seconds = sum(
            int(v.duration.split(':')[0]) * 3600 +
            int(v.duration.split(':')[1]) * 60 +
            int(v.duration.split(':')[2])
            for v in self.videos
        )
        return str(timedelta(seconds=total_seconds))


def create_test_video_scenarios():
    """Create various video test scenarios."""
    scenarios = {
        "standard": {
            "videos": [
                VideoFactory.create(
                    name="Standard_HD_Video",
                    resolution="1920x1080",
                    codec="h264",
                    duration="0:10:00"
                )
            ]
        },
        "4k": {
            "videos": [
                VideoFactory.create(
                    name="4K_UHD_Video",
                    resolution="3840x2160",
                    codec="h265",
                    duration="0:05:00",
                    bitrate=20000
                )
            ]
        },
        "long_duration": {
            "videos": [
                VideoFactory.create(
                    name="Long_Movie",
                    resolution="1920x1080",
                    duration="2:30:00",
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
                VideoFactory.create(name=f"{codec}_test", codec=codec)
                for codec in ["h264", "h265", "vp9", "av1"]
            ]
        }
    }
    
    return scenarios