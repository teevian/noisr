#!/usr/bin/env python


# oscilloscope picotech.com/ ; hantek

import analyzer
import json, time, serial, csv
import pyqtgraph as pg
import factory, connection
import utils

import numpy as np
from collections import deque
from platform import system
from msgid import _, egg
from PyQt5.QtCore import (
        QSize, Qt, QDateTime, QTimer
        )
from PyQt5.QtWidgets import (
        QMainWindow, QVBoxLayout, QWidget,
        QHBoxLayout, QTabWidget, QTextEdit,
        QTableWidget, QTextEdit, QTableWidgetItem,
        QFileDialog
        )
from PyQt5.QtGui import (
        QIcon, QIntValidator
        )


######################################################################
# PyQt window for a Noisr instance
######################################################################         

class NoiserGUI(QMainWindow):
    """
        Implements the main window for a Noisr instance
    """
    def __init__(self, parent=None):
        super(NoiserGUI, self).__init__(parent)
        self.initUI(self.loadConfigs())


    def initUI(self, configs):
        """
            Sets up the layout and user interface
        """
        ## window setup
        window  = configs['main_window']
        meta    = configs['meta']

        self.setupEnvironment()

        self.name       = meta['name']
        self.filename   = utils.getFunName(meta['extension'], '_')
        self.title_canonical = f"{self.name} {meta['version']} {meta['dev_phase']}"
        self.title      = f'{self.title_canonical} — {self.filename}'

        self.ICON_SIZE  = QSize(window['ic_size'], window['ic_size'])
        self.NO_BOARD   = _('NO_BOARD')
        self.is_reading = False
        self.is_saved   = False
        self.is_signal_stabilized = False
        self.serial_connection = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.onReadStopButtonClick)

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon(window['icon']))
        self.resize(QSize(window['width'], window['height']))

        ## create Noisr widgets
        self.log = NoiserGUI.Logger()
        self.log.i(_('ENV_CREATE'))

        factory.ToolBars(self, configs['env_paths']['toolbars'])
        factory.MenuBar(self, 'path to menu file')
        factory.StatusBar(self, self.filename)
        factory.Noter(self, configs['notes_colors'])

        self.createAnalyzer()
        factory.AnalogPinChoicer(self)
        factory.Scheduler(self)
        factory.Controllers(self)

        self._createMainLayout()

        self.log.i(_('ENV_OK'))
        self.onConnectButtonClick()

    ############################
    # Inner classes
    ############################
    class Logger(QTextEdit):
        """
            Class to handle communication w/ user through the Logger
        """
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setReadOnly(True)

            self.formats = {
                'info': '{}',
                'error': '<span style="color:#c0392b;">{}</span>',
                'warning': '<span style="color:orange;">{}</span>',
                'valid': '<span style="color:green;">{}</span>'
            }

        def _log(self, message, level='info'):
            """
                Logs message of the given level
            """
            formatted_message = self.formats[level].format(message)
            log_message = QDateTime.currentDateTime().toString('[hh:mm:ss] ') + formatted_message
            self.append(log_message)

        def i(self, message):
            """
                Logs info messages
            """
            self._log(message)

        def v(self, message):
            """
                Logs validation and confirmation messages
            """
            self._log(message, 'valid')

        def e(self, message):
            """
                Logs error messages (no need to be exception)
            """
            self._log(message, 'error')

        def x(self, err, solution=''):
            """
                Logs Exceptions messages and preferably provides a solution
            """
            message = type(err).__name__ + ': ' + str(err)
            self._log(message, 'error')
            if solution:
                self.i(solution)
    

    ############################
    # Event handling methods
    ############################
    def onReadStopButtonClick(self) -> None:
        """
            Activates (odd clicks) and interrupts (even clicks) receiving the data from arduino
        """
        # stops the timer if it is running
        if self.timer.isActive():
            self.timer.stop()

        if not self.is_reading:
            current_port = self.ids['combobox_connected_ports'].currentText()
            if current_port != 'no board':
                try:
                    self.serial_connection = connection.NOISRProtocol(
                        current_port, baudrate=9600, timeout=1)

                    self.serial_connection.startReading(
                        self.selected_pin,
                        self.ids['spinbox_read_rate'].value(),
                        self.update_plot)

                    self.is_reading = True
                    self.__startReadingSetup()
                except (connection.ReadFromSerialError, serial.SerialException) as err:
                    self.log.x(err)
        else:
            self.serial_connection.stopReading()
            #self.serial_connection.close()

            self.is_reading = False
            self.__stopReadingSetup()


    def onConnectButtonClick(self, baudrate : int=9600) -> None:
        """
            Opens connection to ackwonledge Arduino
        """
        if self.is_reading:
            self.log.e(_('ERR_THREAD_RUNNING'))
            return

        port = self.ids.get('combobox_connected_ports', {}).currentText()
        if port == 'no board' or not port:
            self.log.e(_('CON_SOL_PORTS'))
            return

        try:
            self.log.i(f'{_("CON_HANDSHAKE_PORT")}{self.selected_pin}')
            response = connection.NOISRProtocol.handshake(port, baudrate, self.selected_pin, timeout=1)
            self.log.i(f'{_("CON_ARDUINO_SAYS")}{egg(response)}')
        except Exception as error:
            self.log.x(error)


    def __startReadingSetup(self):
        self.log.i(_('READ_START'))

        self.btPlayPause.setText("STOP")
        self.statusbar.setStyleSheet('background-color: rgb(118, 178, 87);')
        self.statusbar.showMessage(_('STATUSBAR_READ_START'), 1000)
        self.setWindowTitle(f'{self.title} (🟢 reading...)')


    def __stopReadingSetup(self):
        self.log.i(_('READ_STOP'))
        self.log.i(_('CON_CLOSED'))

        self.btPlayPause.setText('START')
        self.statusbar.setStyleSheet('background-color: rgb(0, 122, 204);')
        self.statusbar.showMessage(_('STATUSBAR_READ_STOP'), 1000)
        self.setWindowTitle(self.title)


    ## plot utils
    def setPlotterYRange(self):
        """
            Changes scale of the plotter according to max and min values
        """
        self.Yscale_min = self.ids['Yscale_min'].value()
        self.Yscale_max = self.ids['Yscale_max'].value()

        # prevents man-min from inverting order
        self.ids['Yscale_min'].setMaximum(self.Yscale_max - 1)
        self.ids['Yscale_max'].setMinimum(self.Yscale_min + 1)

        self.plotter.setYRange(self.Yscale_min, self.Yscale_max, padding=0)


    def setPlotterXRange(self):
        """
            Changes scale of the plotter according to the value
        """
        self.display_memory = self.ids['spinbox_display_memory'].value()


    def onAutoScaleClick(self):
        """
            Changes scale of the plotter according to max and min values
        """
        if self.data_queue:
            voltages_in_queue = self.data_voltages_queue
            min_val, max_val = min(voltages_in_queue), max(voltages_in_queue)

            min_val = max(int(min_val), -12)
            max_val = min(int(max_val + 1), 12)

            self.ids['Yscale_min'].setValue(min_val)
            self.ids['Yscale_max'].setValue(max_val)
        else:
            self.log.i(_('PLOT_ERR_AUTOSCALE'))

        self.setPlotterYRange()
        self.statusbar.showMessage(_('STATUSBAR_SCALE_CHANGED') + str([self.Yscale_min, self.Yscale_max]), 1000)


    def updateArduinoPorts(self):
        """
            Syncs the combobox for ports for new ports
        """
        self.ids['combobox_connected_ports'].clear()
        self.ids['combobox_connected_ports'].addItems(self.getArduinoPorts())


    def getArduinoPorts(self):
        """
            Sets up the combobox with ports connected with Arduino

            Returns:
                The list of ports connected to Arduino (or ['no board'] if it finds no connection)
        """
        try:
            self.log.i(_('CON_PORTS'))
            ports = connection.getPorts()
            self.log.v(f'{_("CON_OK_PORTS")}{ports}')
        except Exception as e:
            self.log.x(e)
            ports = []

        if not ports:
            self.log.e(_('CON_SOL_PORTS'))
            ports = [_('NO_BOARD')]

        return ports


    def closeEvent(self, event):
        """
            Disallow the window to be closed while Serial thread is running
        """
        #self.serial_reader.stop()
        #self.serial_reader.wait()
        if not self.is_reading:
            event.accept()
        else:
            self.log.e(_('ERR_THREAD_RUNNING'))
            event.ignore()


    def _createMainLayout(self):
        """
            Creates the layout for the application
        """
        ## left board - for data analysis
        containerLeft = QVBoxLayout()
        containerLeft.addStretch()
        containerLeft.addWidget(self.analyzer, alignment = Qt.AlignTop)
        containerLeft.addStretch()
        containerLeft.addWidget(self.log)

        ## right board - for data handling
        containerRight = QVBoxLayout()
        containerRight.addWidget(self.tabNoter)
        containerRight.addWidget(self.groupPinChoice)
        containerRight.addWidget(self.groupSchedule)
        containerRight.addLayout(self.layoutControllers)
        containerRight.addStretch()

        ## main container - disposes boards into two columns
        containerMain = QHBoxLayout()
        containerMain.addLayout(containerLeft)
        containerMain.addLayout(containerRight)

        ## render layout into QWidget
        NoisrWidget = QWidget()
        NoisrWidget.setLayout(containerMain)
        self.setCentralWidget(NoisrWidget)


    def onBoardInfoClick(self):
        factory.boardInfoDialog()
    

    def onBoardCodeClick(self):
        factory.boardCodeDialog('./noiserino/noiserino.ino')


    def thresholdValidator(self):
        validator = QIntValidator()
        validator.setRange(-25, 25)
        return validator


    def toggleThreshold(self, checked):
        if checked:
            self.threshold_line.show()
        else:
            self.threshold_line.hide()


    def toggleClampFunction(self, checked):
        if checked:
            self.clamp_function.show()
        else:
            self.clamp_function.hide()


    def onAnalogPinChanged(self):
        """
            Sets up environment when the user chooses another analog pin to read from
        """
        self.selected_pin = self.groupbox.checkedId()
        self.plotter.setTitle(f'Data from PIN A{self.selected_pin}')
        self.statusbar.showMessage(_('STATUSBAR_PIN_CHANGED') + str(self.selected_pin), 1000)


    def createAnalyzer(self):
        """
            Generates the display from which data can be analyzed
        """
        ## tab container and style
        self.analyzer = QTabWidget(movable=True, tabPosition=QTabWidget.South)
        self.analyzer.setStyleSheet("QTabWidget::pane { border: 0; }")

        ## plotter
        self.plotter = analyzer.Plotter()

        self.setPlotterYRange()
        self.setPlotterXRange()

        self.updateStabilizationDeviation()

        # TODO CONSIDERATIONS for 'essential mode
        #self.plotter.setDownsampling(auto=True)

        self.buffer_deque_len = 50  # TODO enable to change this in options
        self.data_queue = deque(maxlen=self.buffer_deque_len)

        self.data_voltages_queue_clamp = deque(maxlen=self.buffer_deque_len)
        #self.data_queue_moving_average = deque(maxlen=deque_len +2)
        self.data_voltages_queue = deque(maxlen=self.buffer_deque_len)   # optimizing for speed

        self.times = np.zeros(self.buffer_deque_len)
        self.voltages = np.zeros(self.buffer_deque_len)

        ## graphs and lines to show
        self.signal = self.plotter.plot(self.times, self.voltages, pen='g', width=5, name='Voltage')
        self.clamp_function = self.plotter.plot(self.times, self.voltages, pen='y', width=2, name='Clamp Function')
        #self.average_function = self.plotter.plot(self.times, self.voltages, pen='w', width=2, name='Moving Average')

        self.threshold_line = pg.InfiniteLine(
            angle = 0,
            movable = True,
            pen = pg.mkPen(color='r',
            width = 3,
            style = Qt.DashLine))
        self.threshold_line.sigDragged.connect(self.updateThresholdSpinBox)

        self.threshold_line.setPos(float(self.ids['spinbox_threshold'].value()))
        self.plotter.addItem(self.threshold_line)

        self.setThreshold()

        ## table
        self.table = analyzer.Table(0, 4)

        ## generates tabs compatible with analyzer board
        tabPlot = factory.AnalyzerTab(QHBoxLayout, self.plotter)
        tabTable = factory.AnalyzerTab(QHBoxLayout, self.table)
  
        self.analyzer.addTab(tabPlot, QIcon('./data/icons/ic_read.svg'), 'Oscilloscope')
        self.analyzer.addTab(tabTable, QIcon('./data/icons/ic_sum'), 'Spreadsheet')


    def update_plot(self, new_voltage):
        """
            Updates the plot with data
        """
        new_time = self.times[-1] + (1 / self.serial_connection.serial_thread.rate)

        if self.groupSchedule.isChecked() and not self.timer.isActive()\
            and (self.comboStartAt.currentText() == 'right away' or self.is_signal_stabilized):

            unit_factor = 1000 if self.comboTimeUnits.currentText() == 's' else 1
            time = int(self.spinboxTime.value()) * unit_factor
            self.log.i(_('TIMER_START'))
            self.timer.start(time)

        self.data_queue.append((new_time, new_voltage))
        self.data_voltages_queue_clamp.append(self.clampValue(new_voltage))
        self.data_voltages_queue.append(new_voltage)

        self.times, self.voltages = zip(*self.data_queue)

        if self.checkStabilization() != self.is_signal_stabilized:
            self.toggleStabilization()

        if len(self.times) < 2: # TODO optimize this
            return

        self.signal.setData(self.times, self.voltages)
        self.clamp_function.setData(self.times, self.data_voltages_queue_clamp)

        self.plotter.setYRange(self.Yscale_min, self.Yscale_max, padding=0)
        print(self.times[-min(self.display_memory, len(self.times))])
        print(self.times[-1])
        self.plotter.setXRange(self.times[-min(self.display_memory, len(self.times))], self.times[-1], padding=0)

        #self.label.setPos(self.x_data[-1], 1)
        #self.label.setText(f"Y = {self.y_data[-1]:.2f}")

        ## updates table
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(round(new_time, 2))))
        self.table.setItem(row, 1, QTableWidgetItem(str(new_voltage)))
        if self.is_signal_stabilized:
            self.table.setItem(row, 3, QTableWidgetItem(str('Signal is stabilized;')))
        self.table.scrollToBottom()


    def movingAverage(self, n=3):
        cumulative_sum = np.cumsum(np.insert(self.data_voltages_queue, 0, 0))
        return (cumulative_sum[n:] - cumulative_sum[:-n]) / float(n)


    def clampValue(self, value):
        return self.threshold_reference if value >= self.threshold_reference else 0


    ## threshold
    def setThreshold(self):
        """
            Changes the threshold
        """
        self.threshold_reference = self.ids['spinbox_threshold'].value()


    def updateThresholdSpinBox(self):
        """
            Updates the threshold value if the threshold is manually moved
        """
        new_threshold = self.threshold_line.value()
        self.ids['spinbox_threshold'].setValue(new_threshold)

    def updateThresholdLine(self, new_threshold):
        """
            Updates the threshold line in our friend plotter
        """
        self.threshold_line.setPos(new_threshold)
        self.threshold_reference = new_threshold


    ## stabilization
    def toggleStabilization(self):
        """
        Toggles the signal stabilization and updates the GUI and curve accordingly.
        """
        try:
            current_time = str(self.data_queue[0])
        except IndexError:
            raise IndexError("Data queue is empty.")
        
        if self.is_signal_stabilized:
            self.signal.setPen(pg.mkPen(color=(0, 122, 204), width=4))
            self.log.i('Signal not stabilized since ' + current_time)
        else:
            self.signal.setPen(pg.mkPen(color=(118, 178, 87), width=4))
            self.log.i('Signal stabilized since ' + current_time)

        self.is_signal_stabilized = not self.is_signal_stabilized


    def checkStabilization(self):
        """
            Checks if the signal is stabilized
        """
        voltages_std_dev = np.std(self.data_voltages_queue)
        return voltages_std_dev < self.spinbox_stabilization_stddev


    def updateStabilizationDeviation(self):
        """
            Updates the stabilization value
        """
        self.spinbox_stabilization_stddev = self.ids['spinbox_stabilization_stddev'].value()


    ## read rate
    def setReadRate(self, rate):
        """
            Changes the read rate from arduino
        """
        if self.is_reading:
            self.serial_connection.serial_thread.rate = rate


    def saveTXT(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save as TXT', self.filename, 'Text files (*.txt);;All Files (*)')
        if filename:
            with open(filename, 'w') as f:
                f.write('Time\tVoltage\n')
                for row in range(self.table.rowCount()):
                    time_item = self.table.item(row, 0)
                    voltage_item = self.table.item(row, 1)
                    f.write(f"{time_item.text()}\t{voltage_item.text()}\n")


    def saveCSV(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Save as CSV', self.filename, 'CSV files (*.csv);;All Files (*)')
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', 'Voltage'])
                for row in range(self.table.rowCount()):
                    time_item = self.table.item(row, 0)
                    voltage_item = self.table.item(row, 1)
                    writer.writerow([time_item.text(), voltage_item.text()])


    ############################
    # Utility Methods
    ############################
    def doNothing(self):
        """
            That's right: this function does nothing :)
        """
        pass


    def setupEnvironment(self, path='./configs/toolbars.json'):
        """
            Sets up global attributes for the window
        """
        self.system = system()
        self.ids = {}
        with open(path, 'r') as ids_file:
            env = json.load(ids_file)
        for key, value in env.items():
            for item in value.get('actions', []):
                item_id = item.get('@id')
                if item_id:
                    self.ids[item_id] = ''



    # TODO missing args from the caller
    def loadConfigs(self, configsPath='./configs/settings.json'):
        """
            Sets up the global environment according to the configs.json file
        """
        with open(configsPath, 'r') as configsDefault:
            return json.load(configsDefault)