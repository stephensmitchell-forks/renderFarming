import PySide2.QtWidgets as QtW
from PySide2.QtCore import Signal


class QMaxRollup(QtW.QWidget):
    collapsed = Signal()
    expanded = Signal()

    def __init__(self):
        super(QMaxRollup).__init__()
