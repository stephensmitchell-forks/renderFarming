# import sys
import logging
import cStringIO

# import renderFarmingConfig as rFCfg
import renderFarmingSpinach as rFS
import renderFarmingTools as rFT

import MaxPlus
# import pymxs

from PySide2.QtUiTools import QUiLoader
# from PySide2.QtGui import QCloseEvent
import PySide2.QtWidgets as QtW
from PySide2.QtCore import QFile

# uif = 'renderFarmingUI.ui'
#
# cfg = rFCfg.Configuration()
# rt = pymxs.runtime
#
#
# lg = logging.getLogger("renderFarming")
# lg.setLevel(cfg.get_log_level())
#
# log_file = cfg.get_log_file()
# fh = logging.FileHandler(log_file)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# fh.setFormatter(formatter)
# lg.addHandler(fh)
# lg.info("Render Farming: Starting")


class RenderFarmingUI(QtW.QDialog):

    def __init__(self, ui_file, runtime, configuration, log, parent=MaxPlus.GetQMaxMainWindow()):
        super(RenderFarmingUI, self).__init__(parent)

        self._clg = logging.getLogger("renderFarming.UI")

        # Log display handler
        self._log_stream = cStringIO.StringIO()

        self._log_to_stream()

        self._clg.debug("Reading UI definition from {}".format(ui_file))

        ui_file = QFile(ui_file)

        ui_file.open(QFile.ReadOnly)

        self._rt = runtime
        self._cfg = configuration
        self._lg = log

        self._saved = True

        loader = QUiLoader()
        self._tabbed_widget = loader.load(ui_file)
        ui_file.close()

        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self._tabbed_widget)

        self.setLayout(main_layout)

        self._window_title = "Render Farming - v{}".format(self._cfg.get_version())

        self.setWindowTitle(self._window_title)

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        # Spinach
        self._sp_man_prepass_btn = self.findChild(QtW.QPushButton, 'sp_1f_man_prepass_btn')
        self._sp_man_beauty_btn = self.findChild(QtW.QPushButton, 'sp_1f_man_beauty_btn')
        self._sp_1f_auto_btn = self.findChild(QtW.QPushButton, 'sp_1f_auto_btn')

        # Config
        self._cfg_save_btn = self.findChild(QtW.QPushButton, 'config_save_btn')
        self._cfg_reset_btn = self.findChild(QtW.QPushButton, 'config_reset_btn')

        # Log
        self._lg_open_explorer_btn = self.findChild(QtW.QPushButton, 'lg_open_explorer_btn')

        # ---------------------------------------------------
        #               Label Definitions
        # ---------------------------------------------------

        self._spinach_status_lb = self.findChild(QtW.QLabel, 'label_spinach_status')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        # Config
        # - Projects
        self._cfg_prj_projectCode_le = self.findChild(QtW.QLineEdit, 'config_project_projectCode_le')
        self._cfg_prj_fullName_le = self.findChild(QtW.QLineEdit, 'config_project_fullName_le')

        # - Paths
        self._cfg_pth_projectsDirectory_le = self.findChild(QtW.QLineEdit, 'config_paths_projectsDirectory_le')
        self._cfg_pth_logDirectory_le = self.findChild(QtW.QLineEdit, 'config_paths_logDirectory_le')
        self._cfg_pth_framesDirectory_le = self.findChild(QtW.QLineEdit, 'config_paths_framesDirectory_le')
        self._cfg_pth_irradianceMapDirectory_le = self.findChild(QtW.QLineEdit,
                                                                 'config_paths_irradianceMapDirectory_le')
        self._cfg_pth_lightCacheDirectory_le = self.findChild(QtW.QLineEdit, 'config_paths_lightCacheDirectory_le')

        # - Backburner
        self._cfg_bb_manager_le = self.findChild(QtW.QLineEdit, 'config_backburner_manager_le')

        # ---------------------------------------------------
        #             Plain Text Edit Definitions
        # ---------------------------------------------------

        # Logs
        self._lg_text_pte = self.findChild(QtW.QPlainTextEdit, 'lg_text_pte')

        # ---------------------------------------------------
        #               Combo Box Connections
        # ---------------------------------------------------

        # Spinach
        self._sp_gi_mode_cmbx = GIModeComboBox(self.findChild(QtW.QComboBox, 'sp_gi_mode_cmbx'))

        # Config
        # - Logs
        self._cfg_lg_loggingLevel_cmbx = LogLevelComboBox(self.findChild(QtW.QComboBox,
                                                                         'config_logging_loggingLevel_cmbx'))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # Spinach
        self._sp_gi_mode_cmbx.cmbx.activated.connect(self._sp_gi_mode_cmbx_handler)
        self._sp_man_prepass_btn.clicked.connect(self._sp_man_prepass_btn_handler)
        self._sp_man_beauty_btn.clicked.connect(self._sp_man_beauty_btn_handler)
        # self._sp_1f_auto_btn.clicked.connect(self._single_frame_auto_handler)
        self._sp_1f_auto_btn.setEnabled(False)

        # config

        self._cfg_save_btn.clicked.connect(self._config_save_handler)
        self._cfg_reset_btn.clicked.connect(self._config_reset_handler)

        self._cfg_prj_projectCode_le.textEdited.connect(self._edit_handler)
        self._cfg_prj_fullName_le.textEdited.connect(self._edit_handler)

        self._cfg_pth_projectsDirectory_le.textEdited.connect(self._edit_handler)
        self._cfg_pth_logDirectory_le.textEdited.connect(self._edit_handler)
        self._cfg_pth_framesDirectory_le.textEdited.connect(self._edit_handler)
        self._cfg_pth_irradianceMapDirectory_le.textEdited.connect(self._edit_handler)
        self._cfg_pth_lightCacheDirectory_le.textEdited.connect(self._edit_handler)

        self._cfg_bb_manager_le.textEdited.connect(self._edit_handler)

        self._cfg_lg_loggingLevel_cmbx.cmbx.activated.connect(self._edit_handler)

        # Log
        self._lg_open_explorer_btn.clicked.connect(self._log_open_explorer_handler)

        # General
        self._tabbed_widget.currentChanged.connect(self._tab_change_handler)

        # ---------------------------------------------------
        #               Final Initializing
        # ---------------------------------------------------

        self._spinach = rFS.SpinachJob(self._rt, self._cfg)
        self._spinach_status(self._spinach.get_status_message())
        self._config_setup()

    # ---------------------------------------------------
    #                   Setup Functions
    # ---------------------------------------------------

    def _config_setup(self):
        self._cfg_prj_projectCode_le.setText(self._cfg.get_project_code())
        self._cfg_prj_fullName_le.setText(self._cfg.get_project_full_name())

        self._cfg_pth_projectsDirectory_le.setText(self._cfg.get_projects_path(True))
        self._cfg_pth_framesDirectory_le.setText(self._cfg.get_frames_path(True))
        self._cfg_pth_irradianceMapDirectory_le.setText(self._cfg.get_irradiance_cache_path(True))
        self._cfg_pth_lightCacheDirectory_le.setText(self._cfg.get_light_cache_path(True))
        self._cfg_pth_logDirectory_le.setText(self._cfg.get_log_path(True))

        self._cfg_bb_manager_le.setText(self._cfg.get_net_render_manager())

        self._cfg_lg_loggingLevel_cmbx.set_by_level(self._cfg.get_log_level())

        return

    def _config_apply(self, save_file=True):
        flg = logging.getLogger("renderFarming.UI._config_apply")
        flg.debug("Current Configuration:\n{0}\n{1}\n{0}".format('*'*20, self._cfg))
        if not self._saved:
            self._cfg.set_project_code(self._cfg_prj_projectCode_le.text())
            self._cfg.set_project_full_name(self._cfg_prj_fullName_le.text())

            self._cfg.set_projects_path(self._cfg_pth_projectsDirectory_le.text())
            self._cfg.set_frames_path(self._cfg_pth_framesDirectory_le.text())
            self._cfg.set_irradiance_cache_path(self._cfg_pth_irradianceMapDirectory_le.text())
            self._cfg.set_light_cache_path(self._cfg_pth_lightCacheDirectory_le.text())
            self._cfg.set_log_path(self._cfg_pth_logDirectory_le.text())

            self._cfg.set_net_render_manager(self._cfg_bb_manager_le.text())

            log_level = self._cfg_lg_loggingLevel_cmbx.get_level()
            self._cfg.set_log_level(log_level)
            self._lg.setLevel(log_level)

            if save_file:
                flg.info("Saving Configuration file")
                self._cfg.save_config()
                self._saved = True
                self.setWindowTitle(self._window_title)
            else:
                flg.debug("Applying without saving")
        else:
            flg.info("Nothing to Save")

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    # Spinach
    # ---------------------------------------------------

    def _sp_auto_btn_handler(self):
        self._clg.error("Automatic submission not implemented")

        er = rFT.html_color_text("ERROR:", "#ff3232")
        self._spinach_status("{} Automatic submission not implemented".format(er))
        return

        # self._spinach.check_camera()
        # self._spinach_status(self._spinach.get_status_message())
        # if not self._spinach.get_ready_status():
        #     self._spinach.prepare_job()
        #
        # if self._spinach.get_ready_status():
        #     self._spinach.single_frame_prepass()
        #     self._spinach.from_file()
        #     self._spinach_status(self._spinach.get_status_message())

    def _sp_man_prepass_btn_handler(self):
        self._spinach.check_camera()
        self._spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            self._spinach.prepare_prepass(self._sp_gi_mode_cmbx.get_prepass_mode())

        self._spinach_status(self._spinach.get_status_message())

    def _sp_man_beauty_btn_handler(self):
        self._spinach.check_camera()
        self._spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            self._spinach.prepare_beauty_pass(self._sp_gi_mode_cmbx.get_beauty_mode())

        self._spinach_status(self._spinach.get_status_message())

    def _sp_gi_mode_cmbx_handler(self):
        self._clg.debug("Gi mode changed, index is: {}".format(self._sp_gi_mode_cmbx))
        if self._sp_gi_mode_cmbx.get_prepass_mode() is -1:
            self._sp_man_prepass_btn.setEnabled(False)
        else:
            self._sp_man_prepass_btn.setEnabled(True)

    def _spinach_status(self, text):
        self._spinach_status_lb.setText("Status: {}".format(text))

    # Config
    # ---------------------------------------------------

    def _config_save_handler(self):
        flg = logging.getLogger("renderFarming.UI._config_save_handler")
        flg.debug("Applying User edits to configuration and saving changes to the configuration file")
        self._config_apply()
        return

    def _config_reset_handler(self):
        flg = logging.getLogger("renderFarming.UI._config_reset_handler")
        flg.debug("Resetting Configuration to Stored")
        self._config_setup()

        self._saved = True
        self.setWindowTitle(self._window_title)
        return

    def _edit_handler(self):
        if self._saved:
            self.setWindowTitle("{} *".format(self._window_title))
            self._saved = False

    # Log
    # ---------------------------------------------------

    def _log_open_explorer_handler(self):
        self._rt.ShellLaunch("explorer.exe", self._cfg.get_log_path())
        return

    def _refresh_log(self):
        log_value = self._log_stream.getvalue()
        self._lg_text_pte.appendPlainText(log_value)
        self._log_stream = cStringIO.StringIO()
        self._log_to_stream()
        return

    def _log_to_stream(self):
        printable_log = logging.StreamHandler(self._log_stream)
        printable_log.setFormatter(logging.Formatter(logging.BASIC_FORMAT))

        logging.getLogger().addHandler(printable_log)

    # General
    # ---------------------------------------------------

    def _tab_change_handler(self):
        if self._tabbed_widget.currentIndex() is 2:
            return self._refresh_log()


class LogLevelComboBox:
    def __init__(self, combo_box):
        self.cmbx = combo_box

    def set_by_level(self, debug_level):
        if "CRITICAL" in debug_level:
            self.cmbx.setCurrentIndex(0)
        elif "ERROR" in debug_level:
            self.cmbx.setCurrentIndex(1)
        elif "WARNING" in debug_level:
            self.cmbx.setCurrentIndex(2)
        elif "INFO" in debug_level:
            self.cmbx.setCurrentIndex(3)
        elif "DEBUG" in debug_level:
            self.cmbx.setCurrentIndex(4)
        else:
            self.cmbx.setCurrentIndex(0)

    def get_level(self):
        index = self.cmbx.currentIndex()
        if index == 4:
            debug_level = "DEBUG"
        elif index == 3:
            debug_level = "INFO"
        elif index == 2:
            debug_level = "WARNING"
        elif index == 1:
            debug_level = "ERROR"
        else:
            debug_level = "CRITICAL"
        return debug_level


class GIModeComboBox:
    """
        Gi Modes
            -0:   Single Frame Irradiance Map, Light Cache: 0
            -1:   From File Single Frame Irradiance Map, Light Cache: 0
            -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache: 1
            -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1): 1
            -4:   Animation Prepass Irradiance Map, Light Cache: 2
            -5:   Animation Interpolated Irradiance Map, no secondary: 2
            -6:   Brute Force, Light Cache: 3
            -7:   Brute Force, From File Light Cache: 3
            -8:   Brute Force, Light Cache with a new Light Cache every frame: 4
            -9:   Brute Force, Brute Force: 5
    """
    def __init__(self, combo_box):
        self.cmbx = combo_box

    def get_prepass_mode(self):
        index = self.cmbx.currentIndex()
        if index == 5:
            prepass_mode = -1
        elif index == 4:
            prepass_mode = -1
        elif index == 3:
            prepass_mode = 6
        elif index == 2:
            prepass_mode = 4
        elif index == 1:
            prepass_mode = 2
        elif index == 0:
            prepass_mode = 0
        else:
            prepass_mode = 0
        return prepass_mode

    def get_beauty_mode(self):
        index = self.cmbx.currentIndex()
        if index == 5:
            beauty_mode = 9
        elif index == 4:
            beauty_mode = 8
        elif index == 3:
            beauty_mode = 7
        elif index == 2:
            beauty_mode = 5
        elif index == 1:
            beauty_mode = 3
        elif index == 0:
            beauty_mode = 1
        else:
            beauty_mode = 1
        return beauty_mode

    def __str__(self):
        return self.cmbx.currentText()

    def __repr__(self):
        return self.__str__()


# if __name__ == '__main__':
#     app = MaxPlus.GetQMaxMainWindow()
#     form = RenderFarmingUI(uif, rt, cfg)
#     sys.exit(app.exec_())

# app = QtW.QApplication(sys.argv)
# form = RenderFarmingUI(uif, rt, cfg, lg, app)
# sys.exit(app.exec_())
