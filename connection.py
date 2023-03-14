#!/usr/bin/env python

from msgid import egg
import os, time, platform
from msgid import _
import serial
import serial.tools.list_ports  # should pip install esptool (?)

from PyQt5.QtCore import QThread, pyqtSignal

######################################################################
# IAD protocol
######################################################################
# Created this protocol based on control characters in the likes of
# old system protocols for data transmission
######################################################################

IAD_PROTOCOL = {            # https://theasciicode.com.ar
    'START'     : b'\x01',  # SOH: start header control character  
    'PAUSE'     : b'\x03',  # ETX: indicates that it is the end of the message (interrupt)
    'STOP'      : b'\x04',  # EOT: indicates the end of transmission
    'ENQUIRE'   : b'\x05',  # ENQ: requests a response from arduino to confirm it is ready (Equiry)
    'OK'        : b'\x06',  # ACK: acknowledgement
    'SYNC'      : b'\x16',  # DLE: synchronous Idle (used for transmission)
    'ERROR'     : b'\x21'   # NAK: exclaim(error) special character
}


######################################################################
# Classes, Exceptions and Threads
######################################################################

class ReaderThread(QThread):
    """
        Opens the serial to read asynchronosusly
    """
    data_ready = pyqtSignal(float)
    def __init__(self, _ser, _rate, parent=None):
        super().__init__(parent)
        self.ser = _ser
        self.rate = _rate

    def run(self):
        while True:
            if self.ser.readable():
                analog_value = self.ser.readline().decode().strip()
                self.data_ready.emit(float(analog_value))
            QThread.msleep(1000 // self.rate)   # changes reading rate in real-time!


class PortError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class ConnectionError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class ConnectionTimeout(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

######################################################################
# Functions and utils
######################################################################

def osIndependent(implementations : dict):
    """
        A decorator that returns a function that selects the correct implementation based on the operating system.
        
        Args:
            implementations (dict): A dictionary mapping operating system names to their corresponding implementations.
            
        Returns:
            function: A function that selects the correct implementation based on the operating system.
            
        Raises:
            OSError: If the operating system is not supported by the provided implementations.
    """
    def wrapper(func):
        def implementationSelector():
            system = platform.system().lower()
            if system in implementations:
                return implementations[system]()
            raise OSError('Unsupported operating system')
        return implementationSelector
    return wrapper


def getPortsOnLinux():
    """
        Returns a list of all the available serial ports on a Linux system.
        
        Returns:
            list: A list of all the available serial ports on a Linux system.
        """
    return [os.path.join('/dev', file_name) for file_name in os.listdir('/dev') if file_name.startswith('ttyACM')]


def getPortsOnMac():
    """
        Returns a list of all the available serial ports on a Mac system.
        
        Returns:
            list: A list of all the available serial ports on a Mac system.
        """
    return [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description and 'usbmodem' in port.device]


def getPortsOnWindows():
    """
        Returns a list of all the available serial ports on a Windows system.
        
        Returns:
            list: A list of all the available serial ports on a Windows system.
    """
    return [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description]


@osIndependent({
    'linux': getPortsOnLinux,
    'darwin': getPortsOnMac,
    'windows': getPortsOnWindows
    })
def getPorts():
    """
        Returns a list of all the available serial ports on the current system, regardless of the operating system.
        
        Returns:
            list: A list of all the available serial ports on the current system.
        """
    pass


def handshake(connection):
    """
        Handshake with Arduino. Retuns a string
    """
    connection.reset_input_buffer()
    connection.write(IAD_PROTOCOL['ENQUIRE'])

    time.sleep(0.1)
    if connection.readable():
        # readable is cool because it doesn't block I/O, as is_waiting does :)
        random_number = int(connection.readline().decode().strip())
        return egg(int(random_number))
    else:
        return "Arduino is down"


# TODO this should raise an exception
def startReadingPin(self, connection, pin):
    """
        Starts reading input
    """
    connection.write(IAD_PROTOCOL['START'])

    # Wait for acknowledgement from Arduino TODO create timeout here
    while True:
        response = connection.read()
        if response == IAD_PROTOCOL['OK']:
            print(response)
            break

    # pin to read from
    pin = 1
    connection.write(pin.to_bytes(1, byteorder='little', signed=False))

    #
    self.btPlayPause.setText("Stop")
    self.is_reading = True
    self.serial_thread.start() # Start the serial reader thread

def stopReadingPin(self, connection, port):
    """
        Stops reading input
    """
    # Send command to Arduino to stop sending analog values
    connection.write(IAD_PROTOCOL['STOP'])

    self.btPlayPause.setText("Start")
    self.is_reading = False
    self.serial_thread.terminate() # Stop the serial reader thread

def openConnection(port):
    """
        Opens the connection with arduino through @arduinoPort
    """
    if bool(port):
        try:
            # https://pyserial.readthedocs.io/en/stable/pyserial_api.html
            return serial.Serial(port, 9600, timeout=1)
        except serial.SerialException:
            raise Exception('Serial monitor not found!')


def info(connection):
    """
        Receives a @connection string and returns a representative dict
    """
    pairsList = str(connection).split("(")[1].split(")")[0].split(",")      # remove special characters
    pairsList = [pair.strip() for pair in pairsList]                        # removes white spaces

    parsedConnection = {}
    for pair in pairsList:                                                  # splits into key-value pairs
        key, value = pair.split("=")
        parsedConnection[key.strip()] = value.strip()

    return parsedConnection