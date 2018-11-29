import PySide2.QtWidgets as QtW
from PySide2.QtCore import Signal


class QMaxRollup(QtW.QGroupBox):
    collapsed = Signal()
    expanded = Signal()

    def __init__(self, *args):
        super(QMaxRollup, self).__init__(*args)
        self._expanded = True

        self.clicked.connect(self.toggle)

    # noinspection PyPep8Naming
    def setExpanded(self, state):
        self._expanded = state
        self.setChecked(state)

        for child in self.children():
            if not child.inherits("QLayout"):
                child.setVisible(state)

        if state:
            self.expanded.emit()
        else:
            self.collapsed.emit()

    # noinspection PyPep8Naming
    def isExpanded(self):
        return self._expanded

    def toggle(self):
        self.setExpanded(not self._expanded)
