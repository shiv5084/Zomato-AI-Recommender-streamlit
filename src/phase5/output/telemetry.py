import json
import sys
import time

class TelemetryTracker:
    """Lightweight observability for the recommendation pipeline."""
    
    def __init__(self):
        self.metrics = {
            "latency_ms": {},
            "counts": {}
        }
        self.starts = {}
        
    def start_timer(self, step_name: str):
        self.starts[step_name] = time.time()
        
    def stop_timer(self, step_name: str):
        if step_name in self.starts:
            duration_ms = (time.time() - self.starts[step_name]) * 1000
            self.metrics["latency_ms"][step_name] = round(duration_ms, 2)
            
    def record_count(self, key: str, value: int):
        self.metrics["counts"][key] = value
        
    def flush(self):
        """Print telemetry JSON to stderr."""
        print(json.dumps({"telemetry": self.metrics}), file=sys.stderr)
