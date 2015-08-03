mettler_toledo_device_python
======================

This Python package (mettler\_toledo\_device) creates a class named
MettlerToledoDevice, which contains an instance of
serial\_device2.SerialDevice and adds methods to it to interface to
Mettler Toledo balances and scales that use the Mettler Toledo
Standard Interface Command Set (MT-SICS).

Authors::

    Peter Polidoro <polidorop@janelia.hhmi.org>

License::

    BSD

Example Usage::

    from mettler_toledo_device import MettlerToledoDevice
    dev = MettlerToledoDevice() # Automatically finds device if one available
    dev = MettlerToledoDevice('/dev/ttyUSB0') # Linux
    dev = MettlerToledoDevice('/dev/tty.usbmodem262471') # Mac OS X
    dev = MettlerToledoDevice('COM3') # Windows
    dev.get_serial_number()
    1126493049
    dev.get_balance_data()
    ['XS204', 'Excellence', '220.0090', 'g']
    dev.get_weight_stable()
    [-0.0082, 'g'] #if weight is stable
    None  #if weight is dynamic
    dev.get_weight()
    [-0.6800, 'g', 'S'] #if weight is stable
    [-0.6800, 'g', 'D'] #if weight is dynamic
    dev.zero_stable()
    True  #zeros if weight is stable
    False  #does not zero if weight is not stable
    dev.zero()
    'S'   #zeros if weight is stable
    'D'   #zeros if weight is dynamic
    devs = MettlerToledoDevices()  # Automatically finds all available devices
    dev = devs[0]

