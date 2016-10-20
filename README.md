#mettler_toledo_device_python

This Python package (mettler\_toledo\_device) creates a class named
MettlerToledoDevice, which contains an instance of
serial\_device2.SerialDevice and adds methods to it to interface to
Mettler Toledo balances and scales that use the Mettler Toledo
Standard Interface Command Set (MT-SICS).

Authors:

    Peter Polidoro <polidorop@janelia.hhmi.org>

Contributors:

    James Pells <https://github.com/jpells>
    Roger Zatkoff <https://github.com/rpzatkoff>

License:

    BSD

##Mettler Toledo RS232 Setup

| BAUDRATE | BIT/PARITY | STOP BITS | HANDSHAKE | END OF LINE  | CHAR SET | CONTINUOUS MODE |
| :-:      | :-:        | :-:       | :-:       | :-:          | :-:      | :-:             |
| 9600     | 8/NO       | 1         | NONE      | \<CR\>\<LF\> | ANSI/WIN | OFF             |

##Example Usage


```python
from mettler_toledo_device import MettlerToledoDevice
dev = MettlerToledoDevice() # Might automatically find device if one available
# if it is not found automatically, specify port directly
dev = MettlerToledoDevice(port='/dev/ttyUSB0') # Linux specific port
dev = MettlerToledoDevice(port='/dev/tty.usbmodem262471') # Mac OS X specific port
dev = MettlerToledoDevice(port='COM3') # Windows specific port
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
```

```python
devs = MettlerToledoDevices()  # Might automatically find all available devices
# if they are not found automatically, specify ports to use
devs = MettlerToledoDevices(use_ports=['/dev/ttyUSB0','/dev/ttyUSB1']) # Linux
devs = MettlerToledoDevices(use_ports=['/dev/tty.usbmodem262471','/dev/tty.usbmodem262472']) # Mac OS X
devs = MettlerToledoDevices(use_ports=['COM3','COM4']) # Windows
dev = devs[0]
```

##Installation

[Setup Python](https://github.com/janelia-pypi/python_setup)

###Linux and Mac OS X

```shell
mkdir -p ~/virtualenvs/mettler_toledo_device
virtualenv ~/virtualenvs/mettler_toledo_device
source ~/virtualenvs/mettler_toledo_device/bin/activate
pip install mettler_toledo_device
```

###Windows

```shell
virtualenv C:\virtualenvs\mettler_toledo_device
C:\virtualenvs\mettler_toledo_device\Scripts\activate
pip install mettler_toledo_device
```
