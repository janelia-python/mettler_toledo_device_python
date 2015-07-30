# -*- coding: utf-8 -*-
from __future__ import print_function, division
import serial
import time
import atexit
import platform
import os
from exceptions import Exception

from serial_device2 import SerialDevice, SerialDevices, find_serial_device_ports, WriteFrequencyError

try:
    from pkg_resources import get_distribution, DistributionNotFound
    _dist = get_distribution('mettler_toledo_device')
    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'mettler_toledo_device')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except (ImportError,DistributionNotFound):
    __version__ = None
else:
    __version__ = _dist.version


DEBUG = False
BAUDRATE = 9600

class MettlerToledoError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class MettlerToledoDevice(object):
    '''
    This Python package (mettler_toledo_device) creates a class named
    MettlerToledoDevice, which contains an instance of
    serial_device2.SerialDevice and adds methods to it to interface to
    Mettler Toledo balances and scales that use the Mettler Toledo
    Standard Interface Command Set (MT-SICS).

    Example Usage:

    dev = MettlerToledoDevice() # Automatically finds device if one available
    dev = MettlerToledoDevice('/dev/ttyUSB0') # Linux
    dev = MettlerToledoDevice('/dev/tty.usbmodem262471') # Mac OS X
    dev = MettlerToledoDevice('COM3') # Windows
    dev.get_description()
    '''
    _TIMEOUT = 0.05
    _WRITE_WRITE_DELAY = 0.05
    _RESET_DELAY = 2.0

    def __init__(self,*args,**kwargs):
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            kwargs.update({'debug': DEBUG})
            self.debug = DEBUG
        if 'try_ports' in kwargs:
            try_ports = kwargs.pop('try_ports')
        else:
            try_ports = None
        if 'baudrate' not in kwargs:
            kwargs.update({'baudrate': BAUDRATE})
        elif (kwargs['baudrate'] is None) or (str(kwargs['baudrate']).lower() == 'default'):
            kwargs.update({'baudrate': BAUDRATE})
        if 'timeout' not in kwargs:
            kwargs.update({'timeout': self._TIMEOUT})
        if 'write_write_delay' not in kwargs:
            kwargs.update({'write_write_delay': self._WRITE_WRITE_DELAY})
        if ('port' not in kwargs) or (kwargs['port'] is None):
            port =  find_mettler_toledo_device_port(baudrate=kwargs['baudrate'],
                                                    try_ports=try_ports,
                                                    debug=kwargs['debug'])
            kwargs.update({'port': port})

        t_start = time.time()
        self._serial_device = SerialDevice(*args,**kwargs)
        atexit.register(self._exit_mettler_toledo_device)
        time.sleep(self._RESET_DELAY)
        t_end = time.time()
        self._debug_print('Initialization time =', (t_end - t_start))

    def _debug_print(self, *args):
        if self.debug:
            print(*args)

    def _exit_mettler_toledo_device(self):
        pass

    def _args_to_request(self,*args):
        request = ''.join(map(str,args))
        request = request + '\r\n';
        return request

    def _send_request(self,*args):

        '''Sends request to device over serial port and
        returns number of bytes written'''

        request = self._args_to_request(*args)
        self._debug_print('request', request)
        bytes_written = self._serial_device.write_check_freq(request,delay_write=True)
        return bytes_written

    def _send_request_get_response(self,*args):

        '''Sends request to device over serial port and
        returns response'''

        request = self._args_to_request(*args)
        self._debug_print('request', request)
        response = self._serial_device.write_read(request,use_readline=True,check_write_freq=True)
        response = response.strip()
        if (response == 'e'):
            request = request.strip()
            raise MettlerToledoError(request)
        return response

    def close(self):
        '''
        Close the device serial port.
        '''
        self._serial_device.close()

    def get_port(self):
        return self._serial_device.port

    def get_commands(self):
        '''
        Inquiry of all implemented MT-SICS commands.
        '''
        return self._send_request_get_response('I0')

    def get_mtsics_level(self):
        '''
        Inquiry of MT-SICS level and MT-SICS versions.
        '''
        return self._send_request_get_response('I1')

    def get_serial_number(self):
        '''
        Inquiry of serial number.
        '''
        return self._send_request_get_response('I4')


class MettlerToledoDevices(list):
    '''
    MettlerToledoDevices inherits from list and automatically populates it with
    MettlerToledoDevices on all available serial ports.

    Example Usage:

    devs = MettlerToledoDevices()  # Automatically finds all available devices
    dev = devs[0]
    '''
    def __init__(self,*args,**kwargs):
        if ('use_ports' not in kwargs) or (kwargs['use_ports'] is None):
            mettler_toledo_device_ports = find_mettler_toledo_device_ports(*args,**kwargs)
        else:
            mettler_toledo_device_ports = use_ports

        for port in mettler_toledo_device_ports:
            dev = MettlerToledoDevice(*args,**kwargs)
            self.append(dev)


def find_mettler_toledo_device_ports(baudrate=None, try_ports=None, debug=DEBUG):
    serial_device_ports = find_serial_device_ports(try_ports=try_ports, debug=debug)
    os_type = platform.system()
    if os_type == 'Darwin':
        serial_device_ports = [x for x in serial_device_ports if 'tty.usbmodem' in x or 'tty.usbserial' in x]

    mettler_toledo_device_ports = []
    for port in serial_device_ports:
        try:
            dev = MettlerToledoDevice(port=port,baudrate=baudrate,debug=debug)
            serial_number = dev.get_serial_number()
            if 'I4 ' in description:
                mettler_toledo_device_ports.append(port)
            dev.close()
        except (serial.SerialException, IOError):
            pass
    return mettler_toledo_device_ports

def find_mettler_toledo_device_port(baudrate=None, model_number=None, serial_number=None, try_ports=None, debug=DEBUG):
    mettler_toledo_device_ports = find_mettler_toledo_device_ports(baudrate=baudrate,
                                                                   try_ports=try_ports,
                                                                   debug=debug)
    if len(mettler_toledo_device_ports) == 1:
        return mettler_toledo_device_ports[0]
    elif len(mettler_toledo_device_ports) == 0:
        serial_device_ports = find_serial_device_ports(try_ports)
        err_string = 'Could not find any MettlerToledo devices. Check connections and permissions.\n'
        err_string += 'Tried ports: ' + str(serial_device_ports)
        raise RuntimeError(err_string)
    else:
        err_string = 'Found more than one MettlerToledo device. Specify port or model_number and/or serial_number.\n'
        err_string += 'Matching ports: ' + str(mettler_toledo_device_ports)
        raise RuntimeError(err_string)


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    debug = False
    dev = MettlerToledoDevice(debug=debug)
