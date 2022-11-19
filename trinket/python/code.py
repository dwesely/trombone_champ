from adafruit_vl53l0x import VL53L0X
from adafruit_debouncer import Debouncer
from time import sleep
import board
from busio import I2C
from usb_hid import devices
from digitalio import DigitalInOut, Direction, Pull
from mouse_abs import Mouse

i2c = I2C(board.SCL, board.SDA)
vl53 = VL53L0X(i2c)
vl53.measurement_timing_budget = 30000


vl53.start_continuous()

def scale_distance_to_mouse(dist, scaling_coefficient=0.5, inverted=False):
    max_mouse = 32767
    min_dist = 50.0
    max_dist = 1000.0*scaling_coefficient
    percentage = (max_dist - dist)/(max_dist - min_dist)
    if inverted:
        return (max_mouse - int(percentage * max_mouse))
    else:
        return int(percentage * max_mouse)

# set up toot trigger
toot = DigitalInOut(board.D1)
toot.direction = Direction.INPUT
toot.pull = Pull.UP
switch = Debouncer(toot)

# set up mouse active/invert switch
mouse = Mouse(devices)

mouse_active = DigitalInOut(board.D3)
mouse_active.direction = Direction.INPUT
mouse_active.pull = Pull.UP

mouse_inverted = DigitalInOut(board.D4)
mouse_inverted.direction = Direction.INPUT
mouse_inverted.pull = Pull.UP

scale_factor = 0.5

tooting = False

smoothed_position = 0

while True:
    # sleep(1)

    switch.update()
    if switch.fell:
        mouse.press(Mouse.LEFT_BUTTON)
    if switch.rose:
        mouse.release(Mouse.LEFT_BUTTON)

    if mouse_active.value and mouse_inverted.value:
        sleep(0.5)
        continue

    mouse_position = scale_distance_to_mouse(vl53.range, scaling_coefficient=scale_factor, inverted=mouse_inverted.value)

    if -2000 > (smoothed_position - mouse_position) > 2000:
        # There was a big jump, skip smooothing this time
        smoothed_position = mouse_position
    else:
        # Simple Average
        smoothed_position = (smoothed_position + mouse_position)//2


    # print("Range: {0}mm, smoothed: {1}".format(vl53.range, smoothed_position))
    mouse.move(x=14000, y=smoothed_position, wheel=0)
