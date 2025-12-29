"""
Heartbeat Manager
Sends periodic heartbeat to server
"""
import threading
import time
from typing import Callable, Optional


class HeartbeatManager:
    def __init__(self, heartbeat_callback: Callable[[], bool], interval: int = 120):
        """
        Initialize heartbeat manager
        
        Args:
            heartbeat_callback: Function to call for sending heartbeat
            interval: Interval in seconds between heartbeats (default: 2 minutes)
        """
        self.heartbeat_callback = heartbeat_callback
        self.interval = interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def _worker(self):
        """Worker thread for periodic heartbeat"""
        while self.running:
            try:
                success = self.heartbeat_callback()
                if success:
                    print(f"Heartbeat sent successfully")
                else:
                    print(f"Heartbeat failed")
            except Exception as e:
                print(f"Heartbeat worker error: {e}")
            
            # Wait for next interval
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def start(self):
        """Start periodic heartbeat"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        print(f"Heartbeat started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop periodic heartbeat"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("Heartbeat stopped")
    
    def set_interval(self, interval: int):
        """Update heartbeat interval"""
        self.interval = max(30, interval)  # Minimum 30 seconds
        print(f"Heartbeat interval updated to {self.interval}s")


if __name__ == "__main__":
    # Test heartbeat
    def test_callback() -> bool:
        print("Sending heartbeat...")
        return True
    
    manager = HeartbeatManager(test_callback, interval=10)
    manager.start()
    
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
