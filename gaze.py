import sys
from unittest.mock import MagicMock

# 1. TRICK PYGAZE: Create a fake pylink module before anything else imports it
mock_pylink = MagicMock()
sys.modules["pylink"] = mock_pylink

# 2. SETUP SETTINGS
from pygaze import settings

settings.TRACKERTYPE = "opengaze"
settings.DISPTYPE = "pygame"  # Use pygame since 'dummy' failed
settings.DISPSIZE = (1920, 1080)
settings.FULLSCREEN = False

# 3. NOW IMPORT THE REST
import time
from pygaze.display import Display
from pygaze.eyetracker import EyeTracker

# 4. INITIALIZE
# This might open a black window, but you can just minimize it.
disp = Display()
tracker = EyeTracker(disp)

print("Starting Gazepoint data stream...")
print("Coordinates will appear below. Press Ctrl+C to quit.")

tracker.start_recording()

try:
    while True:
        # Get the latest gaze position
        gaze_pos = tracker.sample()
        
        if gaze_pos != (-1, -1):
            # Print x, y coordinates to the terminal
            print(f"X: {gaze_pos[0]:<8.2f} Y: {gaze_pos[1]:<8.2f}")
        
        # We don't call disp.show() or disp.fill(), 
        # so the window stays idle/black.
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    tracker.stop_recording()
    tracker.close()
    disp.close()