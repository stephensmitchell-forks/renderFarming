import MaxPlus
import logging

import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

import pymxs
rt = pymxs.runtime


class QTimeSegDialogUI(QtW.QDialog):

    def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
        super(QTimeSegDialogUI, self).__init__(parent)

        self._clg = logging.getLogger("renderFarming.UI.SATSDialog")

        self._dialog_box = QTimeSegDialogDefinition()

        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self._dialog_box)

        self.setLayout(main_layout)

        self._start_frame = 0
        self._end_frame = 0
        self._nth_frame = 1

        self._status_message = str()

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._sats_btnbx = self._dialog_box.sats_btnbx

        self._sats_end_sb = self._dialog_box.sats_end_sb
        self._sats_start_sb = self._dialog_box.sats_start_sb
        self._sats_evr_nth_frm_sb = self._dialog_box.sats_evr_nth_frm_sb

        self._sats_end_sb.setValue(int(rt.animationRange.end))
        self._sats_start_sb.setValue(int(rt.animationRange.start))
        self._sats_evr_nth_frm_sb.setValue(int(rt.rendNThFrame))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # noinspection PyUnresolvedReferences
        self._sats_btnbx.accepted.connect(self._sats_accept_handler)
        # noinspection PyUnresolvedReferences
        self._sats_btnbx.rejected.connect(self._sats_reject_handler)

        # ---------------------------------------------------
        #                  Handler Function
        # ---------------------------------------------------

    def _sats_accept_handler(self):
        self._start_frame = self._sats_start_sb.value()
        self._end_frame = self._sats_end_sb.value()
        self._nth_frame = self._sats_evr_nth_frm_sb.value()

        if self._end_frame < self._start_frame:
            self._status_message = "ERROR: Start Frame is greater than End Frame"
            self.reject()

        self._set_time_segment()

        self._status_message = "OK"
        self.accept()
        return

    def _sats_reject_handler(self):
        self._status_message = "Cancelled by User"
        self.reject()
        return

    def _set_time_segment(self):
        rt.animationRange = rt.interval(self._start_frame, self._end_frame)
        rt.rendNThFrame = self._nth_frame
        # print("S: {}, E: {}, Nth: {}".format(self._start_frame, self._end_frame, self._nth_frame))

    def get_status_message(self):
        return self._status_message

    def get_nth_frame(self):
        return self._nth_frame


class QTimeSegDialogDefinition(QtW.QWidget):
    """
    Generated using pyside2-uic and then cleaned up
    """
    def __init__(self):
        super(QTimeSegDialogDefinition, self).__init__()

        self.verticalLayout = QtW.QVBoxLayout()

        self.label_sats_title = QtW.QLabel()
        font = QtG.QFont()
        font.setPointSize(12)

        self.label_sats_title.setFont(font)
        self.label_sats_title.setAlignment(QtC.Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_sats_title)
        spacer_item_1 = QtW.QSpacerItem(20, 40, QtW.QSizePolicy.Minimum, QtW.QSizePolicy.Expanding)

        self.verticalLayout.addItem(spacer_item_1)

        self.line = QtW.QFrame()
        self.line.setFrameShape(QtW.QFrame.HLine)
        self.line.setFrameShadow(QtW.QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)
        self.formLayout = QtW.QFormLayout()

        self.label_sats_start = QtW.QLabel()

        self.formLayout.setWidget(0, QtW.QFormLayout.LabelRole, self.label_sats_start)
        self.label_sats_end = QtW.QLabel()

        self.formLayout.setWidget(1, QtW.QFormLayout.LabelRole, self.label_sats_end)

        self.sats_start_sb = QtW.QSpinBox()
        self.sats_start_sb.setMinimum(-65535)
        self.sats_start_sb.setMaximum(65535)

        self.formLayout.setWidget(0, QtW.QFormLayout.FieldRole, self.sats_start_sb)

        self.sats_end_sb = QtW.QSpinBox()
        self.sats_end_sb.setSuffix("")
        self.sats_end_sb.setMinimum(-65535)
        self.sats_end_sb.setMaximum(65535)
        self.sats_end_sb.setProperty("value", 300)
        self.sats_end_sb.setDisplayIntegerBase(10)

        self.formLayout.setWidget(1, QtW.QFormLayout.FieldRole, self.sats_end_sb)
        self.label_evr_nth_frm = QtW.QLabel()

        self.formLayout.setWidget(2, QtW.QFormLayout.LabelRole, self.label_evr_nth_frm)

        self.sats_evr_nth_frm_sb = QtW.QSpinBox()
        self.sats_evr_nth_frm_sb.setEnabled(True)
        self.sats_evr_nth_frm_sb.setMinimum(1)
        self.sats_evr_nth_frm_sb.setMaximum(65535)
        self.sats_evr_nth_frm_sb.setSingleStep(5)
        self.sats_evr_nth_frm_sb.setProperty("value", 1)

        self.formLayout.setWidget(2, QtW.QFormLayout.FieldRole, self.sats_evr_nth_frm_sb)

        self.verticalLayout.addLayout(self.formLayout)

        self.line_2 = QtW.QFrame()
        self.line_2.setFrameShape(QtW.QFrame.HLine)
        self.line_2.setFrameShadow(QtW.QFrame.Sunken)

        self.verticalLayout.addWidget(self.line_2)

        spacer_item_2 = QtW.QSpacerItem(20, 40, QtW.QSizePolicy.Minimum, QtW.QSizePolicy.Expanding)

        self.verticalLayout.addItem(spacer_item_2)

        self.sats_btnbx = QtW.QDialogButtonBox()
        self.sats_btnbx.setOrientation(QtC.Qt.Horizontal)
        self.sats_btnbx.setStandardButtons(QtW.QDialogButtonBox.Cancel | QtW.QDialogButtonBox.Ok)
        self.sats_btnbx.setCenterButtons(True)

        self.verticalLayout.addWidget(self.sats_btnbx)

        self.setLayout(self.verticalLayout)

        self.setWindowTitle("Render Farming")
        self.label_sats_title.setText("Set Active Time Segment?")
        self.label_sats_start.setText("Start Time")
        self.label_sats_end.setText("End Time")
        self.label_evr_nth_frm.setText("Every Nth Frame")

        self.sats_start_sb.setToolTip(
            "<html><head/><body><p>The frame number of the beginning of the shot.</p></body></html>"
        )

        self.sats_end_sb.setToolTip(
            "<html><head/><body><p>The frame number of the end of the shot.</p></body></html>"
        )

        self.sats_evr_nth_frm_sb.setToolTip(
            "<html><head/><body><p>Max will only renders frames at this interval.</p></body></html>"
            )
