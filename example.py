from lcushidrelay import RelayBoard, Relay

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