# SPDX-FileCopyrightText: 2017 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_hid.mouse.Mouse`
====================================================
* Author(s): Dan Halbert, Bitboy
https://gist.github.com/bitboy85/cdcd0e7e04082db414b5f1d23ab09005
"""
from time import sleep

# https://github.com/adafruit/circuitpython/issues/5461
def find_device(devices, *, usage_page, usage):
    """Search through the provided list of devices to find the one with the matching usage_page and
    usage."""
    if hasattr(devices, "send_report"):
        devices = [devices]
    for device in devices:
        if (
            device.usage_page == usage_page
            and device.usage == usage
            and hasattr(device, "send_report")
        ):
            return device
    raise ValueError("Could not find matching HID device.")
	
	
class Mouse:
    """Send USB HID mouse reports."""

    LEFT_BUTTON = 1
    """Left mouse button."""

    def __init__(self, devices):
        self._mouse_device = find_device(devices, usage_page=0x1, usage=0x02)
        self.report = bytearray(6)

        # Do a no-op to test if HID device is ready.
        # If not, wait a bit and try once more.
        try:
            self._send_no_move()
        except OSError:
            sleep(1)
            self._send_no_move()

    def press(self, buttons):
        self.report[0] |= buttons
        self._send_no_move()

    def release(self, buttons):
        self.report[0] &= ~buttons
        self._send_no_move()

    def release_all(self):
        """Release all the mouse buttons."""
        self.report[0] = 0
        self._send_no_move()

    def click(self, buttons):
        self.press(buttons)
        self.release(buttons)

    def move(self, x=0, y=0, wheel=0):
        # Coordinates
        x = self._limit_coord(x)
        y = self._limit_coord(y)
        # HID reports use little endian
        x1, x2 = (x & 0xFFFFFFF).to_bytes(2, 'little')
        y1, y2 = (y & 0xFFFFFFF).to_bytes(2, 'little')
        # print(f'Moving to {y}')
        self.report[1] = x1
        self.report[2] = x2
        self.report[3] = y1
        self.report[4] = y2
        self._mouse_device.send_report(self.report)

    def _send_no_move(self):
        """Send a button-only report."""
        self.report[1] = 0
        self.report[2] = 0
        self.report[3] = 0
        self.report[4] = 0
        self._mouse_device.send_report(self.report)

    @staticmethod
    def _limit(dist):
        return min(127, max(-127, dist))

    @staticmethod
    def _limit_coord(coord):
        return min(32767, max(0, coord))