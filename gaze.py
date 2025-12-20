import pygaze
import pygame
from pygaze.display import Display
from pygaze.eyetracker import EyeTracker
import pygaze.libtime as timer

SHOW_DOT = True
DOT_COLOR = (0, 255, 0)
BG_COLOR = (20, 20, 20)


class DisplaySettings:
    DISPTYPE = "pygame"
    FULLSCREEN = False
    TRACKERTYPE = "opengaze"
    DISPSIZE = (1280, 720)


pygaze.settings = DisplaySettings()

disp = Display(dispsize=(1280, 720), fgc=DOT_COLOR, bgc=BG_COLOR)
tracker = EyeTracker(display=disp)


tracker.start_recording()
print("Press 'ESC' to quit.")

t0 = timer.get_time()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    gaze_pos = tracker.sample()

    disp.fill()

    if SHOW_DOT and gaze_pos != (-1, -1):
        pygame.draw.circle(
            disp.screen,
            DOT_COLOR,
            (int(gaze_pos[0]), int(gaze_pos[1])),
            15,
        )

    disp.show()

tracker.stop_recording()
tracker.close()
disp.close()
