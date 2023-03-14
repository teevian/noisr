#!/usr/bin/env python

from msgid import egg
import os, time
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

def getPorts(system):
    """
        Returns ports whose connection is made with Arduino - MacOS and Linux only; Windows is for humanities majors
    """
    ports = []
    if system.lower() == 'linux':       # Linux
        matching_files = [f for f in os.scandir('/dev') if f.name.startswith('ttyACM')]

        # create list of full file paths
        for file in matching_files:
            full_path = os.path.join('/dev', file.name)
            ports.append(full_path)
    elif system.lower() == 'darwin':    # MacOS
        ports = [   
            port.device
            for port in serial.tools.list_ports.comports()
            if 'Arduino' in port.description and 'usbmodem' in port.device
        ]
    if not ports:
        raise PortError('Board not connected')
    return ports


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