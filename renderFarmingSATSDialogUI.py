import MaxPlus
import logging
import os

from PySide2.QtUiTools import QUiLoader
import PySide2.QtWidgets as QtW
from PySide2.QtCore import QFile

import renderFarmingTools as rFT


class RenderFarmingSATSDialogUI(QtW.QDialog):

    def __init__(self, ui_path, runtime, parent=MaxPlus.GetQMaxMainWindow()):
        super(RenderFarmingSATSDialogUI, self).__init__(parent)

        self._clg = logging.getLogger("renderFarming.UI.SATSDialog")

        ui_file = QFile(os.path.join(ui_path, "renderFarmingSATSDialog.ui"))

        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self._dialog_box = loader.load(ui_file)
        ui_file.close()

        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self._dialog_box)

        self.setLayout(main_layout)

        self._rt = runtime

        self._start_frame = 0
        self._end_frame = 0

        self._status_message = str()

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._sats_btnbx = self.findChild(QtW.QDialogButtonBox, 'sats_btnbx')

        self._sats_end_sb = self.findChild(QtW.QSpinBox, 'sats_end_sb')
        self._sats_start_sb = self.findChild(QtW.QSpinBox, 'sats_start_sb')

        self._sats_end_sb.setValue(int(self._rt.animationRange.end))
        self._sats_start_sb.setValue(int(self._rt.animationRange.start))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._sats_btnbx.accepted.connect(self._sats_accept_handler)
        self._sats_btnbx.rejected.connect(self._sats_reject_handler)

        # ---------------------------------------------------
        #                  Handler Function
        # ---------------------------------------------------

    def _sats_accept_handler(self):
        self._start_frame = self._sats_start_sb.value()
        self._end_frame = self._sats_end_sb.value()

        if self._end_frame < self._start_frame:
            er = rFT.html_color_text("ERROR:", "#ff3232")
            self._status_message = ("{} Start Frame is greater than End Frame".format(er))
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
        self._rt.animationRange = self._rt.interval(self._start_frame, self._end_frame)

    def get_status_message(self):
        return self._status_message
