from PIL import Image
from typing import List, Dict
import uuid

class MaskAnalyzer:
    """Analyzes projection masks to detect zones - simplified version without OpenCV"""
    
    def __init__(self):
        self.min_area_threshold = 100  # Minimum pixels for a valid zone
        self.width = 0
        self.height = 0
    
    def analyze_mask(self, filepath: str) -> List[Dict]:
        """
        Analyze a PNG mask and return detected zones
        White pixels (255, 255, 255) are projection areas
        Black pixels (0, 0, 0) are masked areas
        """
        # Load image
        img = Image.open(filepath).convert('RGB')
        self.width, self.height = img.size
        pixels = img.load()
        
        # For now, return a simple zone detection
        # In production, you'd want to use OpenCV for proper connected component analysis
        zones = []
        
        # Simple scanning to find white regions (this is a placeholder)
        # Real implementation would use flood fill or connected components
        visited = set()
        
        for y in range(0, self.height, 50):  # Sample every 50 pixels
            for x in range(0, self.width, 50):
                if (x, y) in visited:
                    continue
                    
                # Check if this pixel is white
                r, g, b = pixels[x, y]
                if r == 255 and g == 255 and b == 255:
                    # Found a white pixel, create a zone around it
                    zone_bounds = self._find_zone_bounds(img, x, y, visited)
                    
                    if zone_bounds:
                        zone = {
                            "id": str(uuid.uuid4()),
                            "bounds": zone_bounds,
                            "center": {
                                "x": zone_bounds["x"] + zone_bounds["width"] // 2,
                                "y": zone_bounds["y"] + zone_bounds["height"] // 2
                            },
                            "area": zone_bounds["width"] * zone_bounds["height"],
                            "aspectRatio": round(zone_bounds["width"] / zone_bounds["height"], 2) if zone_bounds["height"] > 0 else 1
                        }
                        zones.append(zone)
        
        # Sort zones by area (largest first)
        zones.sort(key=lambda z: z["area"], reverse=True)
        
        # For demo purposes, if no zones found, create one large zone
        if not zones:
            zones.append({
                "id": str(uuid.uuid4()),
                "bounds": {
                    "x": 100,
                    "y": 100,
                    "width": self.width - 200,
                    "height": self.height - 200
                },
                "center": {
                    "x": self.width // 2,
                    "y": self.height // 2
                },
                "area": (self.width - 200) * (self.height - 200),
                "aspectRatio": round((self.width - 200) / (self.height - 200), 2)
            })
        
        return zones
    
    def _find_zone_bounds(self, img, start_x, start_y, visited):
        """Simple bounding box finder around a white region"""
        pixels = img.load()
        
        # Find bounds by scanning outward
        min_x, max_x = start_x, start_x
        min_y, max_y = start_y, start_y
        
        # Scan in expanding rectangles
        for radius in range(10, min(self.width, self.height) // 2, 10):
            found_white = False
            
            # Top and bottom edges
            for x in range(max(0, start_x - radius), min(self.width, start_x + radius)):
                if start_y - radius >= 0:
                    r, g, b = pixels[x, start_y - radius]
                    if r == 255 and g == 255 and b == 255:
                        min_y = start_y - radius
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        found_white = True
                
                if start_y + radius < self.height:
                    r, g, b = pixels[x, start_y + radius]
                    if r == 255 and g == 255 and b == 255:
                        max_y = start_y + radius
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        found_white = True
            
            # Left and right edges
            for y in range(max(0, start_y - radius), min(self.height, start_y + radius)):
                if start_x - radius >= 0:
                    r, g, b = pixels[start_x - radius, y]
                    if r == 255 and g == 255 and b == 255:
                        min_x = start_x - radius
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                        found_white = True
                
                if start_x + radius < self.width:
                    r, g, b = pixels[start_x + radius, y]
                    if r == 255 and g == 255 and b == 255:
                        max_x = start_x + radius
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                        found_white = True
            
            if not found_white:
                break
        
        # Mark region as visited
        for y in range(min_y, max_y + 1, 10):
            for x in range(min_x, max_x + 1, 10):
                visited.add((x, y))
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width * height < self.min_area_threshold:
            return None
        
        return {
            "x": min_x,
            "y": min_y,
            "width": width,
            "height": height
        }
    
    def classify_zone_size(self, area: int) -> str:
        """
        Classify zone size based on area
        """
        total_area = self.width * self.height
        if total_area == 0:
            return "unknown"
        
        percentage = (area / total_area) * 100
        
        if percentage > 20:
            return "large"
        elif percentage > 5:
            return "medium"
        else:
            return "small"