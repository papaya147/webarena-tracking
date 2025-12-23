import sys
import json
import time
from unittest.mock import MagicMock

mock_pylink = MagicMock()
sys.modules["pylink"] = mock_pylink


from pygaze import settings

settings.TRACKERTYPE = "opengaze"
settings.DISPTYPE = "pygame"
settings.DISPSIZE = (1920, 1080)
settings.FULLSCREEN = False

from pygaze.display import Display
from pygaze.eyetracker import EyeTracker

MAX_EVENTS = 100
events = 0


def record(GAZE_LOGS_FILE, stop_sig):
    gaze_file = open(GAZE_LOGS_FILE, "w")

    disp = Display()
    tracker = EyeTracker(disp)

    tracker.start_recording()

    try:
        while not stop_sig.is_set():
            gaze_pos = tracker.sample()

            if gaze_pos != (-1, -1):
                data = {
                    "x": gaze_pos[0],
                    "y": gaze_pos[1],
                    "timestamp": int(time.time() * 1000),
                }
                gaze_file.write(json.dumps(data) + "\n")
                events += 1
                if events >= MAX_EVENTS:
                    gaze_file.flush()
                    events = 0

            time.sleep(0.01)

    except Exception as e:
        print(e)

    finally:
        tracker.stop_recording()
        tracker.close()
        disp.close()
        gaze_file.close()
