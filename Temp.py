from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
import sys

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.labels = [QLabel("0", self) for _ in range(2)]
        for label in self.labels:
            self.layout.addWidget(label)
        self.setLayout(self.layout)

        self.timers = [QTimer(self), QTimer(self)]
        for i, timer in enumerate(self.timers):
            increment = 1 if i == 0 else 2
            update_func = self.createUpdateFunction(self.labels[i], increment)
            timer.timeout.connect(update_func)
            timer.start(1000)  # 1초마다 타이머를 시작합니다.

    def createUpdateFunction(self, label, increment):
        def updateLabel():
            current_number = int(label.text())
            label.setText(str(current_number + increment))
        return updateLabel

app = QApplication(sys.argv)
widget = MyWidget()
widget.show()
sys.exit(app.exec_())
