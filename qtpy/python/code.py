import time
import board
from mouse_abs import Mouse
import usb_hid
import busio
import adafruit_vl53l0x
import analogio
import digitalio
import neopixel
import rotaryio

def scale_distance_to_mouse(dist, scaling_coefficient=0.5, inverted=False):
    max_mouse = 32767
    min_dist = 50.0
    max_dist = 1000.0*scaling_coefficient
    percentage = (max_dist - dist)/(max_dist - min_dist)
    # print('Distance percentage: {0}'.format(percentage))
    if inverted:
        return (max_mouse - int(percentage * max_mouse))
    else:
        return int(percentage * max_mouse)

def scale_distance_to_color(dist, scaling_coefficient=0.5):
    max_color = 255
    min_dist = 50.0
    max_dist = 1000.0*scaling_coefficient
    if dist >= max_dist:
        return max_color
    elif dist <= min_dist:
        return 0
    else:
        percentage = (max_dist - dist)/(max_dist - min_dist)
        return int(percentage * max_color)

i2c = busio.I2C(board.SCL1, board.SDA1)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)
vl53.measurement_timing_budget = 30000
vl53.start_continuous()

# set up toot trigger
toot = digitalio.DigitalInOut(board.A3)
toot.direction = digitalio.Direction.INPUT
toot.pull = digitalio.Pull.UP

# set up mouse active/invert switch
mouse = Mouse(usb_hid.devices)

mouse_active = digitalio.DigitalInOut(board.A2)
mouse_active.direction = digitalio.Direction.INPUT
mouse_active.pull = digitalio.Pull.UP

mouse_inverted = digitalio.DigitalInOut(board.SDA)
mouse_inverted.direction = digitalio.Direction.INPUT
mouse_inverted.pull = digitalio.Pull.UP

# set up neopixel (to indicate measurement precision)
# Use the active/invert switch to select timing budget on boot
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)

def blink(count):
    for i in range(0, count):
        pixel.fill((255, 0, 0))
        time.sleep(0.2)
        pixel.fill((0, 0, 0))
        time.sleep(0.2)
        
if mouse_active.value and mouse_inverted.value:
    vl53.measurement_timing_budget = 30000
    blink(3)
elif mouse_active.value:
    vl53.measurement_timing_budget = 20000
    blink(2)
else:
    vl53.measurement_timing_budget = 40000
    blink(4)

# done with neopixel
del pixel

# set up scale
scale_reference_voltage = digitalio.DigitalInOut(board.A1)
scale_reference_voltage.direction = digitalio.Direction.OUTPUT
scale_reference_voltage.value = True

scale = analogio.AnalogIn(board.A0)


tooting = False

smoothed_position = 0
# last_mouse_position = 0
# last_last_mouse_position = 0

# set up scroll wheel
encoder = rotaryio.IncrementalEncoder(board.RX, board.SCK)
last_wheel_position = 0
hat = digitalio.DigitalInOut(board.MISO)
hat.direction = digitalio.Direction.INPUT
hat.pull = digitalio.Pull.UP

# TODO: if hat is clicked, send "enter" keystroke instead of mouse button

# verbose = True

while True:
    # if verbose:
    #     time.sleep(1)

    if toot.value:
    #     if verbose:
    #         print('toot')
        if not tooting:
            mouse.press(Mouse.LEFT_BUTTON)
            tooting  = True
    elif tooting:
        mouse.release(Mouse.LEFT_BUTTON)
        tooting = False

    # if verbose:
    #     print(mouse_active.value, mouse_inverted.value)

    if mouse_active.value and mouse_inverted.value:
    #     if verbose:
    #         print('mouse disabled')

        # check mouse wheel only
        position = encoder.position
    #     if verbose:
    #         print('{0} -> {1}'.format(last_wheel_position, position))

        if position < last_wheel_position:
    #         if verbose:
    #             print('Move up')
            mouse.move(wheel=1)
        #     mouse.move(wheel=0)
        elif position > last_wheel_position:
            mouse.move(wheel=-1)
        #     mouse.move(wheel=0)
    #         if verbose:
    #             print('Move down')
    #     else:
    #         if verbose:
    #             print('hold still')
        mouse.release_all()
        last_wheel_position = position

        if hat.value == True:
        #     if verbose:
        #         print('click')
            # kbd.press(Keycode.ENTER)
            mouse.press(Mouse.RIGHT_BUTTON)
            while hat.value:
                # keep pressing until button released
                pass
            # kbd.release_all()
            mouse.release_all()
        continue
    # elif mouse_active.value:
    #     if verbose:
    #         print('mouse active')
    #     invert_mouse = False
    # elif mouse_inverted.value:
    #     if verbose:
    #         print('mouse inverted')
    #     invert_mouse = True

    # if verbose:
    #     print("\n")
    #     print("Range: {0}mm".format(vl53.range))
    #     print('Scale factor: {0}'.format(scale.value/65536))
    scale_factor = scale.value/65536
    mouse_position = scale_distance_to_mouse(vl53.range, scaling_coefficient=scale_factor, inverted=mouse_inverted.value)

    # Smooth the position so it doesn't wobble too much
    if -2000 > (smoothed_position - mouse_position) > 2000:
        # There was a big jump, skip smooothing this time
        smoothed_position = mouse_position
        # last_last_mouse_position = mouse_position
        # last_mouse_position = mouse_position
    else:
        # Simple Average
        smoothed_position = (smoothed_position + mouse_position)//2

        # kalman
        # first_term = mouse_position + 0.5*(last_mouse_position - mouse_position)
        # smoothed_position = int(first_term + 0.3333*(last_last_mouse_position - first_term))
    # if verbose:
    #     print(mouse_position, smoothed_position)
    mouse.move(x=14000, y=smoothed_position, wheel=0)
    # last_last_mouse_position = last_mouse_position
    # last_mouse_position = smoothed_position
    #break
