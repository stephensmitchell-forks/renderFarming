# General Built-ins
# import sys
import logging
import cStringIO
import os

# Other Render Farming files
import renderFarmingConfig as rFCfg
import renderFarmingSpinach as rFS
import renderFarmingKale as rFK
import renderFarmingTools as rFT
import renderFarmingSATSDialogUI as rFSATS

# 3DS Max Specific
import MaxPlus

# PySide 2
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QStandardItemModel, QStandardItem
import PySide2.QtWidgets as QtW
from PySide2.QtCore import QFile, QTimer


class RenderFarmingUI(QtW.QDialog):

    def __init__(self, ui_path, runtime, parent=MaxPlus.GetQMaxMainWindow()):
        """
        The Initialization of the main UI class
        :param ui_path: The path to the .UI file from QDesigner
        :param runtime: The pymxs runtime from max
        :param parent: The main Max Window
        """
        super(RenderFarmingUI, self).__init__(parent)

        # ---------------------------------------------------
        #                    Variables
        # ---------------------------------------------------

        self._ui_path = ui_path
        self._rt = runtime
        self._parent = parent

        self._cfg = rFCfg.Configuration()
        self._cfg.set_max_system_directories(self._rt)

        # ---------------------------------------------------
        #                      Logging
        # ---------------------------------------------------

        # Creates Log Stream

        self._clg = logging.getLogger("renderFarming")
        self._clg.setLevel(self._cfg.get_log_level())

        # Log file Handling

        log_file = self._cfg.get_log_file()
        fh = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        self._clg.addHandler(fh)

        self._clg.info("Render Farming: Starting")

        # ---------------------------------------------------
        #                     Main Init
        # ---------------------------------------------------

        # Log display handler
        self._log_stream = cStringIO.StringIO()

        self._log_to_stream()

        self._clg.debug("Reading UI definition from {}".format(self._ui_path))

        # UI Loader

        ui_file = QFile(os.path.join(self._ui_path, "renderFarmingMainWidget.ui"))
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self._tabbed_widget = loader.load(ui_file)

        ui_file.close()

        # Attaches loaded UI to the dialog box

        main_layout = QtW.QVBoxLayout()
        main_layout.addWidget(self._tabbed_widget)

        self.setLayout(main_layout)

        # Titling

        self._window_title = self._generate_title()
        self.setWindowTitle(self._window_title)

        # General Attributes

        self._saved = True

        self._camera = self._rt.getActiveCamera()

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._tabbed_widget.currentChanged.connect(self._tab_change_handler)

        vpc_code = MaxPlus.NotificationCodes.ViewportChange
        self._viewport_change_handler = MaxPlus.NotificationManager.Register(vpc_code, self.cam_change_handler)

        # ---------------------------------------------------
        #               Final Initializing
        # ---------------------------------------------------

        self._spinach_tbdg = SpinachTBDG(self, self._rt, self._cfg)
        self._kale_tbdg = KaleTBDG(self, self._rt, self._cfg)
        self._config_tbdg = ConfigTBDG(self, self._rt, self._cfg)
        self._log_tbdg = LogTBDG(self, self._rt, self._cfg)

        self._spinach_tbdg.set_spinach_status(self._spinach_tbdg.get_status_message())

        self.config_setup_all()

    # ---------------------------------------------------
    #                   Setup Functions
    # ---------------------------------------------------

    def _generate_title(self):
        return "{1} - RenderFarming{0}".format(self._cfg.get_version(), self._cfg.get_project_code())

    def config_setup_all(self):
        self._config_tbdg.config_page_setup()
        self._spinach_tbdg.spinach_page_setup()

    def config_apply_all(self, save_file=True):
        flg = logging.getLogger("renderFarming.UI._config_apply")
        flg.debug("Current Configuration:\n{0}\n{1}\n{0}".format('*'*20, self._cfg))

        if not self._saved:
            self._config_tbdg.config_apply_config_page()
            self._spinach_tbdg.config_apply_spinach_page()

            if save_file:
                flg.info("Saving Configuration file")
                self._cfg.save_config()
                self._saved = True
                self._window_title = self._generate_title()
                self.setWindowTitle(self._window_title)
            else:
                flg.debug("Applying without saving")
        else:
            flg.info("Nothing to Save")

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    def _tab_change_handler(self):
        if self._tabbed_widget.currentIndex() is 3:
            return self._refresh_log()

    def _refresh_log(self):
        log_value = self._log_stream.getvalue()
        self._log_tbdg.append_log_text(log_value)
        self._log_stream = cStringIO.StringIO()
        self._log_to_stream()
        return

    def _log_to_stream(self):
        printable_log = logging.StreamHandler(self._log_stream)
        printable_log.setFormatter(logging.Formatter(logging.BASIC_FORMAT))

        logging.getLogger().addHandler(printable_log)

    def cam_change_handler(self, code):
        if self._camera is not None:
            stored_cam = self._camera
        else:
            stored_cam = "None"

        if self._rt.getActiveCamera() is not None:
            cur_cam = (self._rt.getActiveCamera())
        else:
            cur_cam = "None"

        if stored_cam != cur_cam:
            self._clg.debug("Camera change detected (Code: {})".format(code))
            if self._spinach_tbdg.get_ready_status():
                wrn = rFT.html_color_text("Warning:", "Orange")
                self._spinach_tbdg.set_spinach_status("{} Camera has changed".format(wrn))
            self._camera = self._rt.getActiveCamera()

    # ---------------------------------------------------
    #                    Getters
    # ---------------------------------------------------

    def get_window_title(self):
        return self._window_title

    def get_saved_status(self):
        return self._saved

    def set_saved_status(self, saved):
        self._saved = saved

    # ---------------------------------------------------
    #                    Dialogs
    # ---------------------------------------------------

    def sats_dialog_opener(self):
        self._clg.debug("Opening the \"Set Active Time Segment\" dialog")
        dialog = rFSATS.RenderFarmingSATSDialogUI(self._ui_path, self._rt, self._parent)
        if not dialog.exec_():
            self._spinach_tbdg.set_spinach_status(dialog.get_status_message())
            self._spinach_tbdg.set_nth_frame(dialog.get_nth_frame())
            dialog.destroy()
            return False
        else:
            dialog.destroy()
            return True

    # ---------------------------------------------------
    #                Layout Functions
    # ---------------------------------------------------

    def hide_qwidget(self, widget):
        """
        Hides a QWidget and then shrinks the QDialog to make up for the missing space
        :param widget: A QWidget somewhere underneath self
        :return:
        """
        if widget.isVisible():
            widget.setVisible(False)

            # Calculates the height without the widget
            new_height = self.height() - widget.height()

            # Waits on the minimumSizeHint to re-calculate before shrinking the QDialog
            if new_height < self.minimumSizeHint().height():
                _timer = QTimer()
                _timer.singleShot(30, self._resize_height)
            else:
                self.resize(self.width(), new_height)
        else:
            # Un hides the widget and adds it's height to the
            widget.setVisible(True)

    def _resize_height(self):
        """
        Shrinks the dialog height to the minimum size hint
        :return:
        """
        self.resize(self.width(), self.minimumSizeHint().height())

    # ---------------------------------------------------
    #                    Wrappers
    # ---------------------------------------------------

    # ---------------------------------------------------
    #                    Overrides
    # ---------------------------------------------------

    def closeEvent(self, event):
        MaxPlus.NotificationManager.Unregister(self._viewport_change_handler)

        self._config_tbdg.config_reset()
        self._saved = False
        self.config_apply_all(True)

        logging.shutdown()

        event.accept()


class KaleTBDG:
    def __init__(self, parent, rt, cfg):
        """
        Class for the Kale page of the RenderFarming Dialog
        :param parent: the renderFarming Dialog
        :param rt: pymxs.runtime
        :param cfg: renderFarming Configuration
        """
        self._parent = parent

        # Variables

        self._cfg = cfg
        self._rt = rt

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.KaleTBDG")

        # Kale Job

        self._kale = None

        # Table

        self._table = KaleTableView(self._parent, self._kale)

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._kl_run_btn = self._parent.findChild(QtW.QPushButton, 'kl_run_btn')

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._kl_run_btn.clicked.connect(self._kl_run_handler)

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    def _kl_run_handler(self):
        self._kale = rFK.Kale(self._rt, self._cfg)
        self._table.update_model(self._kale)
        return

    # ---------------------------------------------------
    #                  Wrapper Function
    # ---------------------------------------------------


class KaleTableView:
    def __init__(self, parent, kale):
        self._parent = parent
        self._kale = kale

        self._kl_results_text_tbvw = self._parent.findChild(QtW.QTableView, "kl_results_text_tbvw")

        self._ktm = None

        if self._kale is None:
            self._ktm = DummyKaleTableModel()
            self._kl_results_text_tbvw.setModel(self._ktm.get_model())
        else:
            self._model_to_table()

    def _model_to_table(self):
        self._ktm = KaleTableModel(self._kale)
        self._kl_results_text_tbvw.setModel(self._ktm.get_model())

        self._kl_results_text_tbvw.resizeRowsToContents()

    def update_model(self, kale):
        self._kale = kale
        self._model_to_table()


class KaleTableModel:
    def __init__(self, kale):
        self._kale = kale

        self._model = QStandardItemModel()

        self._populate_columns()
        self._create_headers()

    def _create_headers(self):
        label_list = "Title", "Text", "Category", "Priority"
        self._model.setHorizontalHeaderLabels(label_list)

    def _populate_columns(self):
        kale_list = self._kale.get_list()
        for row, kl in enumerate(kale_list):
            self._populate_row(row, kl)

    def _populate_row(self, row, kale_item):
        title = QStandardItem(rFT.clean_title(kale_item.get_title()))
        text = QStandardItem(kale_item.get_text())
        category = QStandardItem(kale_item.get_category())
        priority = QStandardItem(self._priority_to_text(kale_item.get_priority()))

        self._model.setItem(row, 0, title)
        self._model.setItem(row, 1, text)
        self._model.setItem(row, 2, category)
        self._model.setItem(row, 3, priority)

    def get_model(self):
        return self._model

    def _priority_to_text(self, priority_integer):
        return self._kale.get_priorities().get(priority_integer, "Invalid Key")


class DummyKaleTableModel:
    def __init__(self):
        self._model = QStandardItemModel()

        self._populate_columns()
        self._create_headers()

    def _create_headers(self):
        label_list = "Title", "Text", "Category", "Priority"
        self._model.setHorizontalHeaderLabels(label_list)

    def _populate_columns(self):
        for row in range(10):
            self._populate_row(row)

    def _populate_row(self, row):
        title = QStandardItem(" ")
        text = QStandardItem(" ")
        category = QStandardItem(" ")
        priority = QStandardItem(" ")

        self._model.setItem(row, 0, title)
        self._model.setItem(row, 1, text)
        self._model.setItem(row, 2, category)
        self._model.setItem(row, 3, priority)

    def get_model(self):
        return self._model


class SpinachTBDG:
    def __init__(self, parent, rt, cfg):
        """
        Class for the Spinach page of the RenderFarming Dialog
        :param parent: the renderFarming Dialog
        :param rt: pymxs.runtime
        :param cfg: renderFarming Configuration
        """
        self._parent = parent

        # Variables

        self._cfg = cfg
        self._rt = rt

        self._settings_visible = True

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.SpinachTBDG")

        # Spinach Job

        self._spinach = rFS.SpinachJob(self._rt, self._cfg)

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._sp_man_prepass_btn = self._parent.findChild(QtW.QPushButton, 'sp_1f_man_prepass_btn')
        self._sp_man_beauty_btn = self._parent.findChild(QtW.QPushButton, 'sp_1f_man_beauty_btn')
        self._sp_backburner_submit_btn = self._parent.findChild(QtW.QPushButton, 'sp_backburner_submit_btn')
        self._sp_reset_btn = self._parent.findChild(QtW.QPushButton, 'sp_reset_btn')

        self._sp_settings_btn = self._parent.findChild(QtW.QPushButton, 'sp_settings_btn')

        # ---------------------------------------------------
        #               Spin Box Definitions
        # ---------------------------------------------------

        self._sp_multi_frame_increment_sb = self._parent.findChild(QtW.QSpinBox, 'sp_multi_frame_increment_sb')

        # ---------------------------------------------------
        #               Check Box Definitions
        # ---------------------------------------------------

        self._sp_pad_gi_range_ckbx = self._parent.findChild(QtW.QCheckBox, 'sp_pad_gi_range_ckbx')
        self._sp_sub_fold_name_gi_ckbx = self._parent.findChild(QtW.QCheckBox, 'sp_sub_fold_name_gi_ckbx')
        self._sp_run_kale_ckbx = self._parent.findChild(QtW.QCheckBox, 'sp_run_kale_ckbx')

        # ---------------------------------------------------
        #               Label Definitions
        # ---------------------------------------------------

        self._spinach_status_lb = self._parent.findChild(QtW.QLabel, 'label_spinach_status')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        self._sp_frm_subFolder_le = self._parent.findChild(QtW.QLineEdit, 'sp_frm_subFolder_le')

        # ---------------------------------------------------
        #             Layout Element Definitions
        # ---------------------------------------------------

        self._sp_settings_gb = self._parent.findChild(QtW.QGroupBox, 'sp_settings_gb')

        # ---------------------------------------------------
        #               Combo Box Connections
        # ---------------------------------------------------

        self._sp_gi_mode_cmbx = GIModeComboBox(self._parent.findChild(QtW.QComboBox, 'sp_gi_mode_cmbx'))

        self._sp_vfb_type_cmbx = IndexBasedComboBox(self._parent.findChild(QtW.QComboBox, 'sp_vfb_type_cmbx'))
        self._sp_img_filt_ovr_cmbx = IndexBasedComboBox(self._parent.findChild(QtW.QComboBox, 'sp_img_filt_ovr_cmbx'))
        self._sp_sats_prompt_cmbx = SATSPromptComboBox(self._parent.findChild(QtW.QComboBox, 'sp_sats_prompt_cmbx'))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._sp_settings_btn.clicked.connect(self._sp_settings_hide_handler)

        self._sp_gi_mode_cmbx.cmbx.activated.connect(self._sp_gi_mode_cmbx_handler)

        self._sp_man_prepass_btn.clicked.connect(self._sp_man_prepass_btn_handler)
        self._sp_man_beauty_btn.clicked.connect(self._sp_man_beauty_btn_handler)
        self._sp_backburner_submit_btn.clicked.connect(self._backburner_submit_handler)

        self._sp_vfb_type_cmbx.cmbx.activated.connect(self._sp_settings_change_handler)
        self._sp_img_filt_ovr_cmbx.cmbx.activated.connect(self._sp_settings_change_handler)
        self._sp_frm_subFolder_le.editingFinished.connect(self._sp_settings_change_handler)
        self._sp_multi_frame_increment_sb.valueChanged.connect(self._sp_settings_change_handler)

        self._sp_reset_btn.clicked.connect(self._spinach_reset_handler)

        self._sp_pad_gi_range_ckbx.stateChanged.connect(self._sp_settings_change_handler)
        self._sp_sub_fold_name_gi_ckbx.stateChanged.connect(self._sp_settings_change_handler)
        self._sp_run_kale_ckbx.stateChanged.connect(self._sp_settings_change_handler)

    # ---------------------------------------------------
    #                  Setup Function
    # ---------------------------------------------------

    def spinach_page_setup(self):
        cmbx_set_cur_ind(self._sp_gi_mode_cmbx.cmbx, (self._cfg.get_interface_setting("sp_gi_mode_cmbx_ind", 1)))
        self._sp_gi_mode_cmbx_handler()

        cmbx_set_cur_ind(self._sp_vfb_type_cmbx.cmbx, (self._cfg.get_interface_setting("sp_vfb_type_cmbx_ind", 1)))
        cmbx_set_cur_ind(self._sp_img_filt_ovr_cmbx.cmbx,
                         (self._cfg.get_interface_setting("sp_img_filt_ovr_cmbx_ind", 1)))
        cmbx_set_cur_ind(self._sp_sats_prompt_cmbx.cmbx,
                         (self._cfg.get_interface_setting("sp_sats_prompt_cmbx_ind", 1)))

        self._sp_frm_subFolder_le.setText(self._cfg.get_interface_setting("sp_frm_subFolder_le_str", 0))
        self._sp_multi_frame_increment_sb.setValue(self._cfg.get_interface_setting("sp_multi_frame_increment_int", 1))

        self._sp_pad_gi_range_ckbx.setChecked(self._cfg.get_interface_setting("sp_pad_gi_range_bool", 3))
        self._sp_run_kale_ckbx.setChecked(self._cfg.get_interface_setting("sp_run_kale_bool", 3))
        self._sp_sub_fold_name_gi_ckbx.setChecked(self._cfg.get_interface_setting("sp_sub_fold_name_gi_bool", 3))

        self._settings_visible = self._cfg.get_interface_setting("sp_settings_bool", 3)

        self._sp_settings_change_handler()
        self._sp_settings_hide_initializer()

    def config_apply_spinach_page(self):
        self._cfg.set_interface_setting("sp_gi_mode_cmbx_ind", self._sp_gi_mode_cmbx.cmbx.currentIndex())

        self._cfg.set_interface_setting("sp_vfb_type_cmbx_ind", self._sp_vfb_type_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_img_filt_ovr_cmbx_ind", self._sp_img_filt_ovr_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_sats_prompt_cmbx_ind", self._sp_sats_prompt_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_multi_frame_increment_int", self._sp_multi_frame_increment_sb.value())

        self._cfg.set_interface_setting("sp_pad_gi_range_bool", self._sp_pad_gi_range_ckbx.isChecked())
        self._cfg.set_interface_setting("sp_run_kale_bool", self._sp_run_kale_ckbx.isChecked())
        self._cfg.set_interface_setting("sp_sub_fold_name_gi_bool", self._sp_sub_fold_name_gi_ckbx.isChecked())

        self._cfg.set_interface_setting("sp_frm_subFolder_le_str", self._sp_frm_subFolder_le.text())

        self._cfg.set_interface_setting("sp_settings_bool", self._settings_visible)

    # ---------------------------------------------------
    #                  Handler Functions
    # ---------------------------------------------------

    def _sp_settings_hide_handler(self):
        """
        Hides settings section
        :return:
        """
        self._parent.hide_qwidget(self._sp_settings_gb)
        self._settings_visible = not self._settings_visible

    def _sp_settings_hide_initializer(self):
        if not self._settings_visible:
            self._sp_settings_btn.setChecked(False)
            self._sp_settings_gb.setVisible(False)

    def _backburner_submit_handler(self):
        """
        Handler for Backburner submission
        :return: none
        """
        self._spinach.submit()
        return

    def _sp_man_prepass_btn_handler(self):
        """
        Handler for prepass submission
        :return:
        """
        flg = logging.getLogger("renderFarming.UI._sp_man_prepass_btn_handler")
        flg.debug("Executing Prepass")
        if self._sp_sats_prompt_cmbx.prepass():
            flg.debug("SATS Dialog Requested")
            if not self._parent.sats_dialog_opener():
                flg.warning("SATS Dialog cancelled, interrupting prepass")
                return
        self._spinach.check_camera()
        self.set_spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            flg.debug("Spinach reports not ready, attempting to prepare the Job")
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            flg.debug("Spinach reports ready, preparing the pass")
            self._spinach.prepare_prepass(self._sp_gi_mode_cmbx.get_prepass_mode())

        self.set_spinach_status(self._spinach.get_status_message())
        self._match_prefix()

    def _sp_man_beauty_btn_handler(self):
        """
        Handler for beauty pass submission
        :return:
        """
        flg = logging.getLogger("renderFarming.UI._sp_man_beauty_btn_handler")
        flg.debug("Executing Beauty Pass")
        if self._sp_sats_prompt_cmbx.beauty():
            flg.debug("SATS Dialog Requested")
            if not self._parent.sats_dialog_opener():
                flg.warning("SATS Dialog cancelled, interrupting beauty pass")
                return
        self._spinach.check_camera()
        self.set_spinach_status(self._spinach.get_status_message())
        if not self._spinach.get_ready_status():
            flg.debug("Spinach reports not ready, attempting to prepare the Job")
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            flg.debug("Spinach reports ready, preparing the pass")
            self._spinach.prepare_beauty_pass(self._sp_gi_mode_cmbx.get_beauty_mode())

        self.set_spinach_status(self._spinach.get_status_message())
        self._match_prefix()

    def _sp_gi_mode_cmbx_handler(self):
        """
        Handler for changing the GI combo box
        :return:
        """
        self._clg.debug("Gi mode changed, index is: {}".format(self._sp_gi_mode_cmbx))
        if self._sp_gi_mode_cmbx.get_prepass_mode() is -1:
            self._sp_man_prepass_btn.setEnabled(False)
        else:
            self._sp_man_prepass_btn.setEnabled(True)

    def _spinach_reset_handler(self):
        """
        Handler for reset button
        :return:
        """
        self._spinach.reset_renderer()
        self.set_spinach_status(self._spinach.get_status_message())

    def _sp_settings_change_handler(self):
        """
        Handler for changes in spinach settings
        :return:
        """
        self._spinach.set_frame_buffer_type(self._sp_vfb_type_cmbx.get_index())
        self._spinach.set_image_filter_override(self._sp_img_filt_ovr_cmbx.get_index())
        self._spinach.set_frames_sub_folder(self._sp_frm_subFolder_le.text())

        self._spinach.set_multi_frame_increment(self._sp_multi_frame_increment_sb.value())
        self._spinach.set_pad_gi(self._sp_pad_gi_range_ckbx.isChecked())
        self._spinach.set_sub_folder_as_gi_name(self._sp_sub_fold_name_gi_ckbx.isChecked())

    # ---------------------------------------------------
    #                Checker Functions
    # ---------------------------------------------------

    def _match_prefix(self):
        """
        Wrapper for rFT.match_prefix()
        :return: None
        """
        chk = rFT.match_prefix(self._rt.maxFileName, self._cfg.get_project_code())
        if chk is not None:
            self.set_spinach_status(chk)

    # ---------------------------------------------------
    #                  Getter Functions
    # ---------------------------------------------------

    def get_status_message(self):
        """
        Gets the current status message
        :return:
        """
        self._spinach.get_status_message()

    def get_ready_status(self):
        return self._spinach.get_ready_status()

    # ---------------------------------------------------
    #                  Setter Functions
    # ---------------------------------------------------

    def set_spinach_status(self, text):
        self._spinach_status_lb.setText("Status: {}".format(text))

    def set_nth_frame(self, nth_frame):
        self._spinach.set_nth_frame(nth_frame)


class ConfigTBDG:
    def __init__(self, parent, rt, cfg):
        """
        Class for the Configuration page of the RenderFarming Dialog
        :param parent: the renderFarming Dialog
        :param rt: pymxs.runtime
        :param cfg: renderFarming Configuration
        """
        self._parent = parent

        # Variables

        self._cfg = cfg
        self._rt = rt

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.ConfigTBDG")

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._cfg_save_btn = self._parent.findChild(QtW.QPushButton, 'config_save_btn')
        self._cfg_reset_btn = self._parent.findChild(QtW.QPushButton, 'config_reset_btn')
        self._cfg_test_btn = self._parent.findChild(QtW.QPushButton, 'config_test_btn')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        # - Projects
        self._cfg_prj_projectCode_le = self._parent.findChild(QtW.QLineEdit, 'config_project_projectCode_le')
        self._cfg_prj_fullName_le = self._parent.findChild(QtW.QLineEdit, 'config_project_fullName_le')

        # - Paths
        self._cfg_pth_projectsDirectory_le = self._parent.findChild(QtW.QLineEdit, 'config_paths_projectsDirectory_le')
        self._cfg_pth_logDirectory_le = self._parent.findChild(QtW.QLineEdit, 'config_paths_logDirectory_le')
        self._cfg_pth_framesDirectory_le = self._parent.findChild(QtW.QLineEdit, 'config_paths_framesDirectory_le')
        self._cfg_pth_irradianceMapDirectory_le = self._parent.findChild(QtW.QLineEdit,
                                                                         'config_paths_irradianceMapDirectory_le')
        self._cfg_pth_lightCacheDirectory_le = self._parent.findChild(QtW.QLineEdit,
                                                                      'config_paths_lightCacheDirectory_le')

        # - Backburner
        self._cfg_bb_manager_le = self._parent.findChild(QtW.QLineEdit, 'config_backburner_manager_le')

        # ---------------------------------------------------
        #               Combo Box Connections
        # ---------------------------------------------------

        self._cfg_lg_loggingLevel_cmbx = LogLevelComboBox(self._parent.findChild(QtW.QComboBox,
                                                                                 'config_logging_loggingLevel_cmbx'))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._cfg_test_btn.pressed.connect(self._config_test_press_handler)
        self._cfg_test_btn.released.connect(self._config_test_release_handler)

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
    #                  Setup Function
    # ---------------------------------------------------

    def config_page_setup(self):
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

    def config_apply_config_page(self):
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
        self._clg.setLevel(log_level)

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    def _config_test_press_handler(self):
        self._config_test(True)

    def _config_test_release_handler(self):
        self._config_test(False)

    def _config_test(self, show):
        self._clg.debug("Showing Resolved Paths")
        raw = not show
        self._cfg_pth_projectsDirectory_le.setText(self._cfg.get_projects_path(raw))
        self._cfg_pth_framesDirectory_le.setText(self._cfg.get_frames_path(raw))
        self._cfg_pth_irradianceMapDirectory_le.setText(self._cfg.get_irradiance_cache_path(raw))
        self._cfg_pth_lightCacheDirectory_le.setText(self._cfg.get_light_cache_path(raw))
        self._cfg_pth_logDirectory_le.setText(self._cfg.get_log_path(raw))

    def _config_save_handler(self):
        flg = logging.getLogger("renderFarming.UI._config_save_handler")
        flg.debug("Applying User edits to configuration and saving changes to the configuration file")
        self._parent.config_apply_all()
        return

    def _config_reset_handler(self):
        flg = logging.getLogger("renderFarming.UI._config_reset_handler")
        flg.debug("Resetting Configuration to Stored")
        self.config_page_setup()

        self._parent.set_saved_status(True)
        self._parent.setWindowTitle(self._parent.get_window_title())
        return

    def _edit_handler(self):
        if self._parent.get_saved_status():
            self._parent.setWindowTitle("{} *".format(self._parent.get_window_title()))
            self._parent.set_saved_status(False)

    def config_reset(self):
        self._config_reset_handler()


class LogTBDG:
    def __init__(self, parent, rt, cfg):
        """
        Class for the Log page of the RenderFarming Dialog
        :param parent: the renderFarming Dialog
        :param rt: pymxs.runtime
        :param cfg: renderFarming Configuration
        """
        self._parent = parent

        # Variables

        self._cfg = cfg
        self._rt = rt

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.LogTBDG")

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._lg_open_explorer_btn = self._parent.findChild(QtW.QPushButton, 'lg_open_explorer_btn')

        # ---------------------------------------------------
        #             Plain Text Edit Definitions
        # ---------------------------------------------------

        self._lg_text_pte = self._parent.findChild(QtW.QPlainTextEdit, 'lg_text_pte')

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._lg_open_explorer_btn.clicked.connect(self._log_open_explorer_handler)

    # ---------------------------------------------------
    #                  Handler Functions
    # ---------------------------------------------------

    def _log_open_explorer_handler(self):
        self._rt.ShellLaunch("explorer.exe", self._cfg.get_log_path())
        return

    # ---------------------------------------------------
    #                  Setter Functions
    # ---------------------------------------------------

    def append_log_text(self, text):
        self._lg_text_pte.appendPlainText(text)


class LogLevelComboBox:
    def __init__(self, combo_box):
        """
        Switches the Log Level Combo Box
        :param combo_box: A QComboBox object
        """
        self.cmbx = combo_box

        self.level_dict = {
            0: "CRITICAL",
            1: "ERROR",
            2: "WARNING",
            3: "INFO",
            4: "DEBUG"
        }

    def set_by_level(self, debug_level):
        name_dict = dict(zip(self.level_dict.values(), self.level_dict.keys()))
        self.cmbx.setCurrentIndex(name_dict.get(debug_level, 4))

    def get_level(self):
        index = self.cmbx.currentIndex()
        return self.level_dict.get(index, "DEBUG")


class GIModeComboBox:
    def __init__(self, combo_box):
        """
        Switches between Gi Modes
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
        :param combo_box: A QComboBox object
        """
        self.cmbx = combo_box

        self._prepass_mode = {
            5: -1,
            4: -1,
            3: 6,
            2: 4,
            1: 2,
            0: 0
        }
        self._beauty_mode = {
            5: 9,
            4: 8,
            3: 7,
            2: 5,
            1: 3,
            0: 1
        }

    def get_prepass_mode(self):
        index = self.cmbx.currentIndex()
        return self._prepass_mode.get(index, 0)

    def get_beauty_mode(self):
        index = self.cmbx.currentIndex()
        return self._beauty_mode.get(index, 0)

    def __str__(self):
        return self.cmbx.currentText()

    def __repr__(self):
        return self.__str__()


class SATSPromptComboBox:
    def __init__(self, combo_box):
        """
        Switches the SATS dialog on and off
        :param combo_box: A QComboBox object
        """
        self.cmbx = combo_box

        self._prepass_bool = {
            3: True,
            2: False,
            1: True,
            0: False
        }
        self._beauty_bool = {
            3: True,
            2: True,
            1: False,
            0: False
        }

    def prepass(self):
        index = self.cmbx.currentIndex()
        return self._prepass_bool.get(index, 0)

    def beauty(self):
        index = self.cmbx.currentIndex()
        return self._beauty_bool.get(index, 0)

    def __str__(self):
        return self.cmbx.currentText()

    def __repr__(self):
        return self.__str__()


class IndexBasedComboBox:
    def __init__(self, combo_box):
        """
        Switches the SATS dialog on and off
        :param combo_box: A QComboBox object
        """
        self.cmbx = combo_box

    def get_index(self):
        index = self.cmbx.currentIndex()
        return index

    def __str__(self):
        return self.cmbx.currentText()

    def __repr__(self):
        return self.__str__()


def cmbx_set_cur_ind(cmbx, index):
    """
    Prevents a QComboBox from being assigned an index outside of it's range
    :param cmbx: the QComboBox to operate on
    :param index: The integer being assigned to the QComboBox
    :return: None
    """
    index = int(index)
    max_ind = cmbx.maxVisibleItems()
    if index > max_ind:
        cmbx.setCurrentIndex(max_ind)
    elif index >= 0:
        cmbx.setCurrentIndex(index)
    else:
        cmbx.setCurrentIndex(0)


# if __name__ == '__main__':
#     app = MaxPlus.GetQMaxMainWindow()
#     form = RenderFarmingUI(uif, rt, cfg)
#     sys.exit(app.exec_())

# app = QtW.QApplication(sys.argv)
# form = RenderFarmingUI(uif, rt, cfg, lg, app)
# sys.exit(app.exec_())
