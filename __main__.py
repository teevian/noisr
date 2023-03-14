#!/usr/bin/env python

import sys
from PyQt5.QtWidgets import QApplication
from gui import NoiserGUI

def main():
    """
        Runs the Noisr singleton instance
    """

    App = QApplication(sys.argv)
    Noisr = NoiserGUI()
    Noisr.show()

    sys.exit(App.exec_())

if  __name__ == '__main__':
    main()