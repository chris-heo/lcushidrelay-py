"""
Interface for LCUS HID relay cards
"""

import hid

class Relay:
    """
    Abstraction layer for LCUS HID relay card's relays
    Please note that the initial state is unknown and assumed to be false
    """
    def __init__(self, parent: "RelayBoard", index: int) -> None:
        self.parent = parent
        self.index = index
        self._value = False

    @property
    def value(self) -> bool:
        """
        Sets or gets the relay's value

        :return: state of the relay
        :rtype: state of the relay
        """
        return self._value

    @value.setter
    def value(self, new_value: bool):
        self.parent.set_relay(self.index, new_value)
        self._value = new_value

    def on(self):
        """
        Turn the relay on (energize)
        
        :param self: 
        """
        self.value = True

    def off(self):
        """
        Turn the relay off (de-energize)
        """
        self.value = False

    def toggle(self):
        """
        Toggle the relay
        """
        self.value = not self.value

class RelayBoard:
    """
    LCUS HID relay Card interface
    """
    USB_VID = 0x5131
    USB_PID = 0x2007

    def __init__(self, path: str | None = None, relay_count: int = 4) -> None:
        self.dev = hid.device()
        self.relay_count = relay_count
        self.ch = tuple(Relay(self, i) for i in range(relay_count))

        if path is None:
            # if no path is provided, take the first found device
            # sadly, there no serial number is baked into the firmware
            # this makes using multiple relay cards a bit more bothersome
            # check the readme for approaches to mitigate this
            devices = hid.enumerate(self.USB_VID, self.USB_PID)
            if len(devices) == 0:
                raise FileNotFoundError("No device with VID/PID pair could be found")
            path = devices[0]["path"]
        else:
            # if a path was provided, check if it's connected
            devices = hid.enumerate()
            found = False
            for device in devices:
                if device["path"] == path:
                    found = True
                    break

            if found is False:
                raise FileNotFoundError("Device could not be found")

        self.dev.open_path(path)

    def set_relay(self, index: int, value: bool):
        """
        Set the state of a relay
        
        :param index: index of the relay, against the protocol description, it starts at 0
        :type index: int
        :param value: State of the relay, True is energized
        :type value: bool
        """
        if not 0 <= index < self.relay_count:
            raise IndexError("index out of range")

        # | Byte | Description |
        # |-----:|-------------|
        # |    0 | is report id (which seemingly is ignored by the MCU)
        # |    1 | Start of frame, always 0xA0
        # |    2 | relay number, 1 ... 254
        # |    3 | command, 0: off, 1: on
        # |      | the rest is supposed to be 2: off w/ response, 3: on w/ resp., 4: toggle, 5: status
        # |      | except for 0/1, no other commands seem to work for the HID version.
        # |    4 | Checksum, which is basically the sum of all previous bytes of the message

        data = [0, 0xA0, index + 1, 1 if value is True else 0]
        data += [sum(data) & 0xFF]

        # don't forget to reflect the value in self.ch:
        self.ch[index]._value = value #pylint: disable=protected-access

        self.dev.write(data)
        self.dev.read(4)

    def set_multi(self, values: int, mask: int = 0xFF):
        """
        Set multiple relays at once (this is not simultaneously)

        :param value: Value of the relays
        :type value: int
        :param mask: Mask for setting the relay, 1 = set relay, 0 = ignore relay
        :type mask: int
        """
        for i in range(self.relay_count):
            ch_mask = 1 << i
            if mask & ch_mask != 0:
                self.ch[i].value = (values & ch_mask) != 0

    def set_multi_str(self, values: str):
        """
        Set multiple relays at once, as a string (this is not simultaneously)

        :param values: FPGA-style string to set, clear or toggle a relay
                       1/H/S (logic 1, high, set) will turn the relay at the given index on
                       0/L/R/C (logic 1, low, reset, clear) will turn the relay at the given index off
                       T/^ will toggle the relay at the given index
                       all inputs are case-insensitive, other characters will be ignored
        :type values: str
        """
        for i, value in enumerate(values[:self.relay_count].upper()):
            ch = self.ch[i]
            if value in "1HS":
                ch.on()
            elif value in "0LRC":
                ch.off()
            elif value == "T^":
                ch.toggle()

if __name__ == "__main__":
    # there are multiple ways to control the relays
    rb = RelayBoard()

    # 1: set_relay method on a RelayBoard object:
    rb.set_relay(0, True)

    # 2: indexed channel w/ object's value:
    rb.ch[1].value = True

    # readback is also possible - please note that the initial state is unknown
    print(rb.ch[1].value)

    # 3: indexed channel w/ method:
    rb.ch[2].on()
    # or just toggle the relay - please note that the initial state is unknown
    rb.ch[3].toggle()

    # 4: do some funny stuff with strings:
    rb.set_multi_str("HL1T")
    # HL1T will set:
    # relay 0 high, relay 1 low, relay 2 high, toggle relay 3

    # 5: bulk-set relays, optionally with mask
    rb.set_multi(0b0000, 0b0001)
