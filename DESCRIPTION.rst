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
    dev.get_description()
    devs = MettlerToledoDevices()  # Automatically finds all available devices
    dev = devs[0]

