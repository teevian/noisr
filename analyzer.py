import pyqtgraph as pg

from PyQt5.QtWidgets import (
        QTableWidget, QTableWidgetItem
        )

class Plotter(pg.PlotWidget):
    def __init__(self):
        super(Plotter, self).__init__(useOpenGL=True)

        self.setLabel('left', 'Voltage', units='V', size='18pt')
        self.setLabel('bottom', 'Time', units='s', size='18pt')
        self.showGrid(x=True, y=True, alpha=0.7)
        self.setLimits(xMin = 0, yMin = -12, yMax = 12)
        self.setMouseEnabled(x = True, y = False) 

        vb = self.getViewBox()
        vb.setAspectLocked(lock = False)
        vb.setAutoVisible(y = 1.0)
        vb.enableAutoRange(axis = 'y', enable = True)

class Table(QTableWidget):
    def __init__(self, rows, columns):
        super(Table, self).__init__(rows, columns)

        self.setStyleSheet('background-color: rgb(0, 0, 0);')
        self.horizontalHeader().setStretchLastSection(True)
        self.setHorizontalHeaderLabels(['Time', 'Voltage', 'Moving Average', 'Comment'])
        self.verticalHeader().setVisible(False)