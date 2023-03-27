#!/usr/bin/env python

from msgid import egg
import os
import time
import platform
from msgid import _
from threading import Lock
import serial
import serial.tools.list_ports  # should pip install esptool (?)

from PyQt5.QtCore import QThread, pyqtSignal

######################################################################
# NOISR protocol
######################################################################

CONTROLS = {            # https://theasciicode.com.ar
    'START': b'\x01',   # SOH: start header control character
    'PAUSE': b'\x03',   # ETX: indicates that it is the end of the message (interrupt)
    'STOP': b'\x04',    # EOT: indicates the end of transmission
    'ENQUIRE': b'\x05', # ENQ: requests a response from arduino to confirm it is ready (Equiry)
    'OK': b'\x06',      # ACK: acknowledgement
    'SYNC': b'\x16',    # DLE: synchronous Idle (used for transmission)
    'ERROR': b'\x21'    # NAK: exclaim(error) special character
}


######################################################################
# Classes, Exceptions and Threads
######################################################################

class NOISRProtocol(serial.Serial):
    """
        Class that interfaces with Arduino through Serial enclosed by a communication protocol
    """
    def __init__(self, port: str, baudrate: int, timeout: int=1):
        super().__init__(port, baudrate, timeout=timeout)
        self.serial_thread = None
    
    def handshake(self, pin: int) -> int:
        return NOISRProtocol.handshake(self.port, self.baudrate, pin, self.timeout)

    @staticmethod
    def handshake(port: str, baudrate: int, pin: int, timeout: int=1) -> int:
        """
            Hanshakes Arduino

            Returns:
                A random number
        """
        try:
            with serial.Serial(port, baudrate, timeout=timeout) as connection:
                connection.reset_input_buffer()
                connection.write(CONTROLS['ENQUIRE'])

                # waits for Arduino's acknowledgment for 3 seconds
                timeout = time.time() + 3
                while connection.read(1) != CONTROLS['OK']:
                    if time.time() > timeout:
                        connection.write(CONTROLS['STOP'])
                        raise ConnectionTimeout(_('CON_ERR_TIMEOUT'))

                connection.write(pin.to_bytes(1, byteorder='big', signed=False))

                # Wait for Arduino to respond
                timeout = time.time() + 3
                while not connection.readable():
                    if time.time() > timeout:
                        connection.write(CONTROLS['STOP'])
                        raise ConnectionTimeout(_('CON_ERR_TIMEOUT'))
                    pass

                return int.from_bytes(connection.read(1), byteorder='big')
        except (serial.serialutil.SerialException, TimeoutError):
            raise

    def startReading(self, pin: int, read_rate: int, data_ready, timeout: int=5):
        try:
            self.serial_thread = NOISRProtocol.PinReaderThread(self, read_rate)
            self.serial_thread.data_ready.connect(data_ready)

            self.write(CONTROLS['START'])

            # wait for acknowledgement from Arduino for 5 seconds (timeout)
            timer = time.time() + timeout
            read = None
            while read != CONTROLS['OK']:
                read = self.read()
                if time.time() > timer:
                    raise ConnectionTimeout(_('CON_ERR_TIMEOUT'))

            print(read)
            print(pin)
            self.write(pin.to_bytes(1, byteorder='little', signed=False))

            print("pin was given")
            self.serial_thread.start()
        except (ReadFromSerialError, serial.SerialException):
            raise
    
    def stopReading(self):
        self.serial_thread.stop()
        self.serial_thread.wait()

    class PinReaderThread(QThread):
        """
            Opens the serial to read asynchronosusly
        """
        data_ready = pyqtSignal(float)

        def __init__(self, serial_connection, rate: int, parent=None):
            super().__init__(parent)
            self.serial_connection = serial_connection
            self.rate = rate
            self._should_run = True
            self._lock = Lock()

        def stop(self):
            with self._lock:
                self._should_run = False

        def run(self):
            try:
                while self._should_run:
                    with self._lock:
                        if self.serial_connection.readable():
                            analog_value = self.serial_connection.readline().decode().strip()
                            self.data_ready.emit(float(analog_value))
                    self.msleep(1000 // self.rate)
            except Exception as e:
                raise e
            finally:
                self.serial_connection.write(CONTROLS['STOP'])
                self.serial_connection.close()


class NoPortError(Exception):
    def __init__(self, message='Port error'):
        self.message = message
        super().__init__(self.message)


class ReadFromSerialError(Exception):
    def __init__(self, message='Connection error'):
        self.message = message
        super().__init__(self.message)


class InvalidPinError(Exception):
    def __init__(self, message='Invalid Pin Error'):
        self.message = message
        super().__init__(self.message)


class ConnectionTimeout(Exception):
    """
        Exception raised when a connection times out.
    """
    DEFAULT_MESSAGE = "Connection timed out"

    def __init__(self, port_name=None, timeout_duration=None):
        """
            Initializes a ConnectionTimeout instance.

            Args:
                port_name (str, optional): The name of the port that timed out. Defaults to None.
                timeout_duration (int, optional): The duration of the timeout in seconds. Defaults to None.
        """
        self.port_name = port_name
        self.timeout_duration = timeout_duration
        if port_name and timeout_duration:
            self.message = f'Timed out connecting to port {port_name} after {timeout_duration} seconds'
        elif port_name:
            self.message = f'Timed out connecting to port {port_name}'
        elif timeout_duration:
            self.message = f'Timed out after {timeout_duration} seconds'
        else:
            self.message = self.DEFAULT_MESSAGE
        super().__init__(self.message)


######################################################################
# Functions and utils
######################################################################

def cross_platform(implementations: dict):
    """
        This decorator returns a function that selects the correct implementation based on the operating system

        Args:
            implementations (dict): a map of operating system (key) and corresponding implementation (value)

        Returns:
            function: the correct implementation based on the operating system

        Raises:
            OSError: if the operating system is not supported
    """
    def wrapper(func):
        def implementationSelector():
            try:
                system = platform.system().lower()
                if system in implementations:
                    return implementations[system]()
                raise OSError('Unsupported operating system')
            except Exception as implementation_error:
                raise implementation_error
        return implementationSelector
    return wrapper


def getArduinoPortsOnLinux():
    """
        Returns:
            list: all the available serial ports on a Linux system
    """
    return [os.path.join('/dev', file_name) for file_name in os.listdir('/dev') if file_name.startswith('ttyACM')]


def getArduinoPortsOnMac():
    """
        Returns:
            list: all the available serial ports on a Mac system
    """
    return [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description and 'usbmodem' in port.device]


def getArduinoPortsOnWindows():
    """
        Returns:
            list: all the available serial ports on a Windows system
    """
    return [port.device for port in serial.tools.list_ports.comports() if 'Arduino' in port.description]


@cross_platform({
    'linux': getArduinoPortsOnLinux,
    'darwin': getArduinoPortsOnMac,
    'windows': getArduinoPortsOnWindows
})
def getPorts():
    """
        Returns:
            list: all the available serial ports on the current system
    """
    pass


# https://pyserial.readthedocs.io/en/stable/pyserial_api.html

def info(connection):
    """
        Receives a @connection string and returns a representative dict
    """
    pairsList = str(connection).split("(")[1].split(")")[
        0].split(",")      # remove special characters
    pairsList = [pair.strip() for pair in pairsList]

    parsedConnection = {}
    for pair in pairsList:  # splits into key-value pairs
        key, value = pair.split("=")
        parsedConnection[key.strip()] = value.strip()

    return parsedConnection
