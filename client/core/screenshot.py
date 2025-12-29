"""
Screenshot Capture and Upload Module
"""
import io
import threading
import time
from PIL import ImageGrab
from typing import Callable, Optional


class ScreenshotManager:
    def __init__(self, upload_callback: Callable[[bytes], bool], interval: int = 300):
        """
        Initialize screenshot manager
        
        Args:
            upload_callback: Function to call with screenshot bytes
            interval: Interval in seconds between screenshots (default: 5 minutes)
        """
        self.upload_callback = upload_callback
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def capture_screenshot(self) -> Optional[bytes]:
        """Capture screenshot and return as bytes"""
        try:
            # Capture screen
            screenshot = ImageGrab.grab()
            
            # Convert to bytes
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG', optimize=True, quality=85)
            buffer.seek(0)
            
            return buffer.read()
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return None
    
    def _worker(self):
        """Worker thread for periodic screenshot capture"""
        while self.running:
            try:
                screenshot_bytes = self.capture_screenshot()
                if screenshot_bytes:
                    success = self.upload_callback(screenshot_bytes)
                    if success:
                        print(f"Screenshot uploaded successfully")
                    else:
                        print(f"Screenshot upload failed")
            except Exception as e:
                print(f"Screenshot worker error: {e}")
            
            # Wait for next interval
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def start(self):
        """Start periodic screenshot capture"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print(f"Screenshot capture started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop periodic screenshot capture"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Screenshot capture stopped")
    
    def set_interval(self, interval: int):
        """Update screenshot interval"""
        self.interval = max(60, interval)  # Minimum 1 minute
        print(f"Screenshot interval updated to {self.interval}s")


if __name__ == "__main__":
    # Test screenshot capture
    def test_callback(data: bytes) -> bool:
        print(f"Captured {len(data)} bytes")
        return True
    
    manager = ScreenshotManager(test_callback, interval=10)
    manager.start()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
