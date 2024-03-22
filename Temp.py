# -*- coding: utf-8 -*-
"""
@author: Deep.I Inc. @Jongwon Kim
Revision date: 2020-12-30
See here for more information :
    https://deep-eye.tistory.com
    https://deep-i.net
"""

import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow,QApplication
from PyQt5.QtCore import QTimer
from PyQt5 import QtCore

FROM_CLASS = uic.loadUiType("ui.ui")[0]

class Windows(QMainWindow,FROM_CLASS):

    def __init__(self):
        super().__init__()

        # setup user interface
        self.setupUi(self) 
        # Widget Setup
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.show()
        # Timer Application
        self.time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.Timer)
        self.timer.start(1000)

    # Timer
    def Timer(self):
        self.time += 1
        self.lcdNumber.display(self.time)
    # Drag Event Method
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.offset = event.pos()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == QtCore.Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.offset = None
        super().mouseReleaseEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ShowApp = Windows()
    sys.exit(app.exec_())
