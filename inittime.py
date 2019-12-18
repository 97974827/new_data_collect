import device

dv = device.Device()

dv.TIME_USE = False
try:
    dv.set_time()
finally:
    pass
