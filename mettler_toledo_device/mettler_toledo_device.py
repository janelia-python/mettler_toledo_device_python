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

class BioshakeError(Exception):
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
    _DEFAULT_SPEED_TARGET = 1000
    _SHAKE_STATE_DESCRIPTIONS = {
        0: 'Shaking is active',
        1: 'Shaker has a stop command detect',
        2: 'Shaker in the braking mode',
        3: 'Arrived in the home position',
        4: 'Manual mode',
        5: 'Acceleration',
        6: 'Deceleration',
        7: 'Deceleration with stopping',
        90: 'ECO mode',
        99: 'Boot process running',
        -1: '',
    }
    _ELM_STATE_DESCRIPTIONS = {
        1: 'Microplate is locked',
        3: 'Microplate is unlocked',
        9: 'Error',
        -1: '',
    }

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
        request = request + '\r';
        return request

    def _send_request(self,*args):

        '''Sends request to bioshake device over serial port and
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
            raise BioshakeError(request)
        return response

    def close(self):
        '''
        Close the device serial port.
        '''
        self._serial_device.close()

    def get_port(self):
        return self._serial_device.port

    def info(self):
        '''
        Listing of general information.
        '''
        return self._send_request_get_response('info')

    def get_version(self):
        '''
        Send back the current version number.
        '''
        return self._send_request_get_response('getVersion')

    def get_description(self):
        '''
        Send back the current model information.
        '''
        return self._send_request_get_response('getDescription')

    def reset_device(self):
        '''
        Restart the controller.
        '''
        return self._send_request_get_response('resetDevice')

    def get_error_list(self):
        '''
        Return a semicolon separated list with warnings and errors that
        occurred.
        '''
        return self._send_request_get_response('getErrorList')

    def set_eco_mode(self):
        '''
        Switch the shaker into economical mode. It will reduce electricity
        consumption by switching off the solenoid for the home
        position and the deactivation of the ELM function. Warning:
        No home position!!! ELM is in locked position!!!
        '''
        return self._send_request_get_response('setEcoMode')

    def leave_eco_mode(self):
        '''
        Leave the economical mode and change in the normal operating state
        with finding the home position.
        '''
        return self._send_request_get_response('leaveEcoMode')

    def shake_on(self,speed_target=_DEFAULT_SPEED_TARGET):
        '''
        Start the shaking at the target speed (rpm) or with the default
        speed if no speed_target provided.
        '''
        response = self._set_shake_speed_target(speed_target)
        if response is not None:
            return self._send_request_get_response('shakeOn')

    def shake_on_with_runtime(self,runtime,speed_target=_DEFAULT_SPEED_TARGET):
        '''
        Shake for runtime duration (s) at the speed_target (rpm) or with
        the default speed_target if none provided. Allowable runtime
        range: 0 – 99999 seconds.
        '''
        response = self._set_shake_speed_target(speed_target)
        if response is not None:
            return self._send_request_get_response('shakeOnWithRuntime'+str(int(runtime)))

    def get_shake_remaining_time(self):
        '''
        Return the remaining time in seconds.
        '''
        return int(float(self._send_request_get_response('getShakeRemainingTime')))

    def shake_off(self):
        '''
        Stop the shaking and return to the home position.
        '''
        return self._send_request_get_response('shakeOff')

    def shake_emergency_off(self):
        '''
        High-Speed stop for the shaking. Warning: No defined home
        position !!!
        '''
        return self._send_request_get_response('shakeEmergencyOff')

    def shake_go_home(self):
        '''
        Shaker goes to the home position and lock in.
        '''
        return self._send_request_get_response('shakeGoHome')

    def get_shake_state(self):
        '''
        Return the state of shaking.
        '''
        shake_state_value = self._send_request_get_response('getShakeState')
        if len(shake_state_value) > 0:
            shake_state_value = int(shake_state_value)
        else:
            shake_state_value = -1
        return {'value': shake_state_value,
                'description': self._SHAKE_STATE_DESCRIPTIONS[shake_state_value]}

    def get_shake_speed_target(self):
        '''
        Return the target mixing speed. (rpm)
        '''
        return int(float(self._send_request_get_response('getShakeTargetSpeed')))

    def _set_shake_speed_target(self,speed_target=_DEFAULT_SPEED_TARGET):
        '''
        Set the target mixing speed. Allowable range: 200 – 3000 rpm
        '''
        if (speed_target >= 200) and (speed_target <= 3000):
            return self._send_request_get_response('setShakeTargetSpeed'+str(int(speed_target)))
        else:
            print(self._set_shake_speed_target.__doc__)

    def get_default_shake_speed_target(self):
        '''
        Get the default mixing speed. (rpm)
        '''
        return self._DEFAULT_SPEED_TARGET

    def get_shake_speed_actual(self):
        '''
        Return the current mixing speed. (rpm)
        '''
        return int(float(self._send_request_get_response('getShakeActualSpeed')))

    def get_shake_speed_min(self):
        '''
        Return the least shake_speed set point.
        '''
        return int(float(self._send_request_get_response('getShakeMinRpm')))

    def get_shake_speed_max(self):
        '''
        Return the biggest shake_speed set point.
        '''
        return int(float(self._send_request_get_response('getShakeMaxRpm')))

    def get_shake_acceleration(self):
        '''
        Return the acceleration/deceleration value. (seconds)
        '''
        return int(float(self._send_request_get_response('getShakeAcceleration')))

    def set_shake_acceleration(self,acceleration):
        '''
        Set the acceleration/deceleration value in seconds. Allowable
        range: 0 - 10 seconds
        '''
        if (acceleration >= 0) and (acceleration <= 10):
            return self._send_request_get_response('setShakeAcceleration'+str(acceleration))
        else:
            print(self.set_shake_acceleration.__doc__)

    def temp_on(self,temp_target):
        '''
        Activate the temperature control. temp_target allowed range: 0 – 99.0 (°C)
        '''
        response = self._set_temp_target(temp_target)
        if response is not None:
            return self._send_request_get_response('tempOn')

    def temp_off(self):
        '''
        Deactivate the temperature control.
        '''
        return self._send_request_get_response('tempOff')

    def get_temp_target(self):
        '''
        Return the target temperature. (°C)
        '''
        return float(self._send_request_get_response('getTempTarget'))

    def _set_temp_target(self,temp_target):
        '''
        Set the target temperature in °C allowed range: 0 – 99.0 in °C
        '''
        if (temp_target >= 0) and (temp_target <= 99):
            return self._send_request_get_response('setTempTarget'+str(int(round(temp_target*10))))
        else:
            print(self.set_temp_target.__doc__)

    def get_temp_actual(self):
        '''
        Return the actual temperature. (°C)
        '''
        return float(self._send_request_get_response('getTempActual'))

    def get_temp_min(self):
        '''
        Return the least set point of temperature. (°C)
        '''
        return float(self._send_request_get_response('getTempMin'))

    def get_temp_max(self):
        '''
        Return the biggest set point of temperature. (°C)
        '''
        return float(self._send_request_get_response('getTempMax'))

    def set_elm_lock_pos(self):
        '''
        Close the Edge Locking Mechanism (ELM).
        The microplate is locked.
        '''
        return self._send_request_get_response('setElmLockPos')

    def set_elm_unlock_pos(self):
        '''
        Opens the Edge Locking Mechanism (ELM) for gripping of microplates.
        The microplate is not locked.
        '''
        return self._send_request_get_response('setElmUnlockPos')

    def get_elm_state(self):
        '''
        Return the state of Edge Locking Mechanism (ELM).
        '''
        elm_state_value = self._send_request_get_response('getElmState')
        if len(elm_state_value) > 0:
            elm_state_value = int(elm_state_value)
        else:
            elm_state_value = -1
        return {'value': elm_state_value,
                'description': self._ELM_STATE_DESCRIPTIONS[elm_state_value]}


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
            description = dev.get_description()
            if 'BIOSHAKE' in description:
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
        err_string = 'Could not find any Bioshake devices. Check connections and permissions.\n'
        err_string += 'Tried ports: ' + str(serial_device_ports)
        raise RuntimeError(err_string)
    else:
        err_string = 'Found more than one Bioshake device. Specify port or model_number and/or serial_number.\n'
        err_string += 'Matching ports: ' + str(mettler_toledo_device_ports)
        raise RuntimeError(err_string)


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    debug = False
    dev = MettlerToledoDevice(debug=debug)
