# PyPortal controlled LED ring for photography with retroreflective chromakey background
# 2021-04-01 Paul Williamson paul@mustbeart.com
# derived (extensively) from https://learn.adafruit.com/pyportal-neopixel-color-oicker

import time
import board
import displayio
from adafruit_pyportal import PyPortal
from adafruit_button import Button
from adafruit_display_shapes.triangle import Triangle
import neopixel

BPP = 3  # for RGB
# BPP = 4     # for RGBW

# Set the background color to ~match the background image
BACKGROUND_COLOR = 0x604470

# Calibration Table: f/stops below full to brightness in [0.0,1.0]
brightnesses = (1.0, 0.50, 0.25, 0.125, 0.0625)  # values probably wrong

# Set the NeoPixel default brightness
BRIGHTNESS_DEFAULT = 2  # as f/stops below full brightness
brightness = BRIGHTNESS_DEFAULT

lightring = neopixel.NeoPixel(
    board.D4, 60, bpp=BPP, brightness=brightnesses[brightness]
)

# Turn off NeoPixels to start
lightring.fill(0)

# Setup PyPortal without networking for now
pyportal = PyPortal(default_bg=BACKGROUND_COLOR)

# Button colors
# Encoded as hex because it auto-translates to 3-tuples for RGB or 4-tuples for RGBW
RED = 0xFF0000
GREEN = 0x00FF00
BLUE = 0x0000FF
WHITE = 0xFFFFFF
OFF = 0x000000

ptr_color = None

# Button types
SPOT = 0
LEVEL = 1

# Spot Color buttons
spots = [
    {"label": "r", "pos": (10, 10), "size": (60, 60), "color": RED},
    {"label": "g", "pos": (90, 10), "size": (60, 60), "color": GREEN},
    {"label": "b", "pos": (170, 10), "size": (60, 60), "color": BLUE},
    {"label": "w", "pos": (250, 10), "size": (60, 60), "color": WHITE},
    {"label": "k", "pos": (250, 170), "size": (60, 60), "color": OFF},
]

# Light level selector buttons
levels = [
    {"label": 4, "pos": (10, 90), "size": (60, 60)},
    {"label": 3, "pos": (70, 90), "size": (60, 60)},
    {"label": 2, "pos": (130, 90), "size": (60, 60)},
    {"label": 1, "pos": (190, 90), "size": (60, 60)},
    {"label": 0, "pos": (250, 90), "size": (60, 60)},
]

# Button feedback sound files
sounds = {
    "r": "/sounds/red.wav",
    "g": "/sounds/green.wav",
    "b": "/sounds/blue.wav",
    "w": "/sounds/white.wav",
    "k": "/sounds/off.wav",
    0: "/sounds/full.wav",
    1: "/sounds/one.wav",
    2: "/sounds/two.wav",
    3: "/sounds/three.wav",
    4: "/sounds/four.wav",
}

# Button processing functions
functions = {
    "r": SPOT,
    "g": SPOT,
    "b": SPOT,
    "w": SPOT,
    "k": SPOT,
    0: LEVEL,
    1: LEVEL,
    2: LEVEL,
    3: LEVEL,
    4: LEVEL,
}


# Updates the pointer on the brightness scale
def update_ptr(brightness, color):
    ptr_group.x = 30 + 60 * (4 - brightness)

    while ptr_group:
        ptr_group.pop()
    ptr = Triangle(10, 0, 20, 15, 0, 15, fill=color, outline=0x000000)
    ptr_group.append(ptr)


# The screen background and the brightness scale are in this image
scale_image_file = open("/images/scale_bg.bmp", "rb")
scale = displayio.OnDiskBitmap(scale_image_file)
scale_sprite = displayio.TileGrid(scale, pixel_shader=displayio.ColorConverter())
pyportal.splash.append(scale_sprite)

# Initialize a pointer to the brightness scale
ptr_group = displayio.Group()
ptr_group.y = 135
update_ptr(brightness, None)
pyportal.splash.append(ptr_group)

# Initialize all the on-screen buttons
buttons = []
for spot in spots:
    button = Button(
        x=spot["pos"][0],
        y=spot["pos"][1],
        width=spot["size"][0],
        height=spot["size"][1],
        style=Button.SHADOWROUNDRECT,
        fill_color=spot["color"],
        outline_color=0x222222,
        name=spot["label"],
    )
    pyportal.splash.append(button)
    buttons.append(button)
for level in levels:
    button = Button(
        x=level["pos"][0],
        y=level["pos"][1],
        width=level["size"][0],
        height=level["size"][1],
        style=Button.RECT,
        fill_color=None,
        outline_color=None,
        name=level["label"],
    )
    pyportal.splash.append(button)
    buttons.append(button)

# Process touch input, updating screen and LED ring
while True:
    touch = pyportal.touchscreen.touch_point
    if touch:
        for button in buttons:
            if button.contains(touch):
                print("Touched", button.name)
                function = functions[button.name]
                if function == SPOT:
                    lightring.fill(button.fill_color)
                    ptr_color = button.fill_color
                    update_ptr(brightness, ptr_color)
                elif function == LEVEL:
                    brightness = button.name
                    lightring.brightness = brightnesses[brightness]
                    update_ptr(brightness, ptr_color)
                    pyportal.play_file(sounds[button.name])
                break
        while pyportal.touchscreen.touch_point:
            pass

    time.sleep(0.05)
