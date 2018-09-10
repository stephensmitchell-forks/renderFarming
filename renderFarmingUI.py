# import sys
import logging

# import renderFarmingConfig as rFCfg
import renderFarmingSpinach as rFS

# import MaxPlus
# import pymxs

from PySide2.QtUiTools import QUiLoader
# from PySide2.QtGui import QCloseEvent
import PySide2.QtWidgets as QtW
from PySide2.QtCore import QFile, QObject

uif = 'renderFarmingUI.ui'

# cfg = rFCfg.config
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


class RenderFarmingUI(QObject):

    def __init__(self, ui_file, runtime, configuration, lg, parent=None):
        super(RenderFarmingUI, self).__init__(parent)

        clg = logging.getLogger("renderFarming.UI")

        clg.debug("Reading UI definition from {}".format(ui_file))

        ui_file = QFile(ui_file)

        ui_file.open(QFile.ReadOnly)

        self._rt = runtime
        self._cfg = configuration
        self._lg = lg

        self._saved = True

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        self._window_title = self.window.window().windowTitle()

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        # Spinach
        self._single_frame_prepass_btn = self.window.findChild(QtW.QPushButton, 'single_frame_prepass_btn')
        self._single_frame_beauty_pass_handler_btn = self.window.findChild(QtW.QPushButton,
                                                                           'single_frame_beauty_pass_handler_btn')
        self._single_frame_auto_btn = self.window.findChild(QtW.QPushButton, 'single_frame_auto_btn')

        # Config
        self._cfg_save_btn = self.window.findChild(QtW.QPushButton, 'config_save_btn')
        self._cfg_reset_btn = self.window.findChild(QtW.QPushButton, 'config_reset_btn')

        # ---------------------------------------------------
        #               Label Definitions
        # ---------------------------------------------------

        self._spinach_status_lb = self.window.findChild(QtW.QLabel, 'label_spinach_status')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        # Config
        # Projects
        self._cfg_prj_projectCode_le = self.window.findChild(QtW.QLineEdit, 'config_project_projectCode_le')
        self._cfg_prj_fullName_le = self.window.findChild(QtW.QLineEdit, 'config_project_fullName_le')

        # Paths
        self._cfg_pth_projectsDirectory_le = self.window.findChild(QtW.QLineEdit, 'config_paths_projectsDirectory_le')
        self._cfg_pth_logDirectory_le = self.window.findChild(QtW.QLineEdit, 'config_paths_logDirectory_le')
        self._cfg_pth_framesDirectory_le = self.window.findChild(QtW.QLineEdit, 'config_paths_framesDirectory_le')
        self._cfg_pth_irradianceMapDirectory_le = self.window.findChild(QtW.QLineEdit,
                                                                        'config_paths_irradianceMapDirectory_le')
        self._cfg_pth_lightCacheDirectory_le = self.window.findChild(QtW.QLineEdit,
                                                                     'config_paths_lightCacheDirectory_le')

        # Backburner
        self._cfg_bb_manager_le = self.window.findChild(QtW.QLineEdit, 'config_backburner_manager_le')

        # ---------------------------------------------------
        #               Combo Box Connections
        # ---------------------------------------------------

        # Config
        # Logs
        self._cfg_lg_loggingLevel_cmbx = LogLevelComboBox(self.window.findChild(QtW.QComboBox,
                                                                                'config_logging_loggingLevel_cmbx'))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # Spinach
        self._single_frame_prepass_btn.clicked.connect(self._single_frame_prepass_handler)
        self._single_frame_beauty_pass_handler_btn.clicked.connect(self._single_frame_beauty_pass_handler)
        self._single_frame_auto_btn.clicked.connect(self._single_frame_auto_handler)

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

    def _config_apply(self):
        flg = logging.getLogger("renderFarming.UI._config_apply")
        flg.debug("Current Configuration:\n{}".format(self._cfg))
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

            flg.info("Saving Configuration file")
            self._cfg.save_config()
            self._saved = True
            self.window.window().setWindowTitle(self._window_title)
        else:
            flg.debug("Nothing to Save")

    # ---------------------------------------------------
    #                  Handler Function
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
        self.window.window().setWindowTitle(self._window_title)
        return

    def _single_frame_auto_handler(self):
        flg = logging.getLogger("renderFarming.UI._spinach_execute_handler")
        flg.debug("Executing Spinach")
        self._spinach_status(self._spinach.get_status_message())

        self._spinach.check_camera()
        self._spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            self._spinach.single_frame_prepass()
            self._spinach.from_file()
            self._spinach_status(self._spinach.get_status_message())

    def _single_frame_prepass_handler(self):
        self._spinach.check_camera()
        self._spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            self._spinach.single_frame_prepass()
            self._spinach_status(self._spinach.get_status_message())

    def _single_frame_beauty_pass_handler(self):
        self._spinach.check_camera()
        self._spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            self._spinach.from_file()
            self._spinach_status(self._spinach.get_status_message())

    def _edit_handler(self):
        if self._saved:
            self.window.window().setWindowTitle("{} *".format(self._window_title))
            self._saved = False

    def _spinach_status(self, text):
        self._spinach_status_lb.setText("Status: {}".format(text))


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


# if __name__ == '__main__':
#     app = MaxPlus.GetQMaxMainWindow()
#     form = RenderFarmingUI(uif, rt, cfg)
#     sys.exit(app.exec_())

# app = MaxPlus.GetQMaxMainWindow()
# form = RenderFarmingUI(uif, rt, cfg)
# sys.exit(app.exec_())
