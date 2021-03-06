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
from renderFarmingQWidgets import QTimeSegDialog
from renderFarmingQWidgets.QMaxRollout import QMaxRollout
import renderFarmingColors as rCL

# 3DS Max Specific
import MaxPlus

# PySide 2
from PySide2.QtUiTools import QUiLoader
import PySide2.QtGui as QtG
import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC

import pymxs

Signal = QtC.Signal
Slot = QtC.Slot

rt = pymxs.runtime


class RenderFarmingUI(QtW.QDialog):

    def __init__(self, ui_path, parent=MaxPlus.GetQMaxMainWindow()):
        """
        The Initialization of the main UI class
        :param ui_path: The path to the .UI file from QDesigner
        :param parent: The main Max Window
        """
        super(RenderFarmingUI, self).__init__(parent)

        # ---------------------------------------------------
        #                    Variables
        # ---------------------------------------------------

        self._ui_path = ui_path
        self._parent = parent

        self._cfg = rFCfg.Configuration()
        self._cfg.set_max_system_directories(rt)

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

        ui_file = QtC.QFile(os.path.join(self._ui_path, "renderFarmingMainWidget.ui"))
        ui_file.open(QtC.QFile.ReadOnly)

        loader = QUiLoader()
        loader.registerCustomWidget(QMaxRollout)
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

        self._camera = rt.getActiveCamera()

        # ---------------------------------------------------
        #               Tab Initializing
        # ---------------------------------------------------

        self._spinach_tbdg = SpinachTBDG(
            self._tabbed_widget.findChild(QtW.QWidget, "spinach_tbdg"), self._cfg)
        self._kale_tbdg = KaleTBDG(
            self._tabbed_widget.findChild(QtW.QWidget, "kale_tbdg"), self._cfg)
        self._config_tbdg = ConfigTBDG(
            self._tabbed_widget.findChild(QtW.QWidget, "config_tbdg"), self._cfg)
        self._log_tbdg = LogTBDG(
            self._tabbed_widget.findChild(QtW.QWidget, "log_tbdg"), self._cfg)

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._tabbed_widget.currentChanged.connect(self._tab_change_handler)

        self._config_tbdg.saved.connect(self.config_apply_all)
        self._config_tbdg.edit.connect(self._config_edit_handler)
        self._config_tbdg.reset.connect(self._config_reset_handler)
        self._config_tbdg.set_log_level.connect(self._set_log_level_handler)

        self._spinach_tbdg.run_kale.connect(self._spinach_run_kale_handler)
        self._kale_tbdg.back.connect(self._kl_tbdg_back_btn_handler)

        vpc_code = MaxPlus.NotificationCodes.ViewportChange
        self._viewport_change_handler = MaxPlus.NotificationManager.Register(vpc_code, self.cam_change_handler)

        # ---------------------------------------------------
        #               Final Initializing
        # ---------------------------------------------------

        self.config_setup_all()

    # ---------------------------------------------------
    #                   Setup Functions
    # ---------------------------------------------------

    def _generate_title(self):
        return "{1} - RenderFarming{0}".format(self._cfg.get_version(), self._cfg.get_project_code())

    def config_setup_all(self):
        self._config_tbdg.config_page_setup()
        self._config_tbdg.config_page_ui_setup()
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

    def _config_edit_handler(self):
        if self.get_saved_status():
            self.setWindowTitle("{} *".format(self.get_window_title()))
            self.set_saved_status(False)

    def _config_reset_handler(self):
        self.set_saved_status(True)
        self.setWindowTitle(self.get_window_title())

    @Slot(str)
    def _set_log_level_handler(self, level):
        self._clg.setLevel(level)
        self._refresh_log()

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    def _tab_change_handler(self):
        if self._tabbed_widget.currentIndex() == 3:
            return self._refresh_log()
        self._kale_tbdg.reset_back_btn()

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

        if rt.getActiveCamera() is not None:
            cur_cam = (rt.getActiveCamera())
        else:
            cur_cam = "None"

        if stored_cam != cur_cam:
            self._clg.debug("Camera change detected (Code: {})".format(code))
            if self._spinach_tbdg.get_ready_status():
                wrn = rFT.html_color_text("Warning:", "Orange")
                self._spinach_tbdg.set_spinach_status("{} Camera has changed".format(wrn))
            self._camera = rt.getActiveCamera()

    def _spinach_run_kale_handler(self):
        index = self._tabbed_widget.currentIndex()
        self._tabbed_widget.setCurrentWidget(self._kale_tbdg.tab())
        self._kale_tbdg.external_run(index)

    @Slot(int)
    def _kl_tbdg_back_btn_handler(self, index):
        self._tabbed_widget.setCurrentIndex(index)

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
                _timer = QtC.QTimer()
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
        try:
            MaxPlus.NotificationManager.Unregister(self._viewport_change_handler)
        except ValueError as e:
            self._clg.debug("Notification handler missing: {}".format(e))

        self._config_tbdg.config_reset()
        self._saved = False
        self.config_apply_all(True)

        logging.shutdown()

        event.accept()


class KaleTBDG(QtC.QObject):
    back = Signal(int)

    def __init__(self, tab, cfg):
        """
        Class for the Kale page of the RenderFarming Dialog
        :param tab: the renderFarming Dialog
        :param cfg: renderFarming Configuration
        """
        super(KaleTBDG, self).__init__()
        self._tab = tab

        # Variables

        self._cfg = cfg

        # External Run
        self._original_index = 0

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.KaleTBDG")

        # Kale Job

        self._kale = None

        # Table
        self._kl_results_text_tbvw = self._tab.findChild(QtW.QTableView, "kl_results_text_tbvw")

        self._table = KaleTableView(self._kl_results_text_tbvw, self._kale)

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._kl_run_btn = self._tab.findChild(QtW.QPushButton, 'kl_run_btn')
        self._kl_completion_pb = self._tab.findChild(QtW.QProgressBar, 'kl_completion_pb')
        self._kl_completion_pb.setVisible(False)

        self._kl_back_btn = self._tab.findChild(QtW.QPushButton, 'kl_back_btn')
        self._kl_back_hide_widget = self._tab.findChild(QtW.QWidget, 'kl_back_hide_widget')
        self.reset_back_btn()

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._kl_run_btn.clicked.connect(self._kl_run_handler)
        self._kl_back_btn.clicked.connect(self._kl_back_btn_handler)

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    def _kl_run_handler(self):
        self._kl_completion_pb.setVisible(True)

        self._kale = rFK.Kale(self._cfg)
        self._table.update_model(self._kale)

        self._kale.set_tasks.connect(self._pb_set_tasks_handler)
        self._kale.add_task.connect(self._pb_add_task_handler)

        self._kl_completion_pb.setVisible(False)
        return

    def _kl_back_btn_handler(self):
        self.back.emit(self._original_index)
        self.reset_back_btn()

    @Slot(int)
    def _pb_set_tasks_handler(self, task_number):
        if task_number > 0:
            self._kl_completion_pb.setTextVisible(True)
            self._kl_completion_pb.setRange(0, task_number)
        else:
            self._kl_completion_pb.setTextVisible(False)
            self._kl_completion_pb.setRange(0, 0)

    @Slot(int)
    def _pb_add_task_handler(self, num):
        self._kl_completion_pb.setValue(self._progress_bar.value() + num)

    def external_run(self, original_index):
        self._original_index = original_index
        self._kl_run_handler()
        self._kl_back_hide_widget.setVisible(True)

    def reset_back_btn(self):
        self._kl_back_hide_widget.setVisible(False)

    # ---------------------------------------------------
    #                  Getter Function
    # ---------------------------------------------------

    def tab(self):
        return self._tab


class KaleTableView:
    def __init__(self, table, kale):
        self._kale = kale

        self._table = table

        self._ktm = None

        if self._kale is None:
            self._ktm = KaleTableModel()
            self._table.setModel(self._ktm)
        else:
            self._model_to_table()

    def _model_to_table(self):
        self._ktm = KaleSortModel(self._kale)
        self._table.setModel(self._ktm)

        self._table.resizeRowsToContents()

    def update_model(self, kale):
        self._kale = kale
        self._model_to_table()


class KaleSortModel(QtC.QSortFilterProxyModel):
    def __init__(self, kale):
        super(KaleSortModel, self).__init__()
        self._kale = kale
        self._priorities_dict = self._kale.get_priorities()
        self._priorities_inverted_dict = dict(zip(self._priorities_dict.values(), self._priorities_dict.keys()))

        self._model = KaleTableModel()
        self._model.refresh()

        self.setSourceModel(self._model)

        self._populate_columns()

    def _populate_columns(self):
        kale_list = self._kale.get_list()
        for row, kl in enumerate(kale_list):
            self._populate_row(row, kl)

    def _populate_row(self, row, kale_item):
        priority = kale_item.get_priority()
        row_list = [
            kale_item.get_title(),
            kale_item.get_text(),
            kale_item.get_category(),
            self._priority_to_text(priority)
        ]

        for col, item in enumerate(row_list):
            qt_item = QtG.QStandardItem(item)
            qt_item.setBackground(self._priority_to_color(priority))
            self._model.setItem(row, col, qt_item)

    def _priority_to_text(self, priority_integer):
        return self._priorities_dict.get(priority_integer, "Invalid Key")

    # noinspection PyMethodMayBeStatic
    def _priority_to_color(self, priority_integer):
        color_dict = {
            0: rCL.kale_low,
            1: rCL.kale_medium,
            2: rCL.kale_high,
            3: rCL.kale_critical
        }
        return color_dict.get(priority_integer, rCL.kale_default)

    def lessThan(self, source_left, source_right):
        left_data = source_left.data()
        right_data = source_right.data()
        if source_left.column() != 3:
            return left_data < right_data
        else:
            int_left = self._priorities_inverted_dict.get(left_data, 0)
            int_right = self._priorities_inverted_dict.get(right_data, 0)
            return int_left < int_right


class KaleTableModel(QtG.QStandardItemModel):
    def __init__(self):
        super(KaleTableModel, self).__init__()

        self._init_populate_columns()
        self._create_headers()

    def _create_headers(self):
        label_list = rFK.label_list
        self.setHorizontalHeaderLabels(label_list)

    def refresh(self):
        self.clear()
        self._create_headers()

    # ---------------------------------------------------
    #        Initial Population Function
    # ---------------------------------------------------

    def _init_populate_columns(self):
        for row in range(10):
            self._init_populate_row(row)

    def _init_populate_row(self, row):
        title = QtG.QStandardItem(" ")
        text = QtG.QStandardItem(" ")
        category = QtG.QStandardItem(" ")
        priority = QtG.QStandardItem(" ")

        self.setItem(row, 0, title)
        self.setItem(row, 1, text)
        self.setItem(row, 2, category)
        self.setItem(row, 3, priority)


class SpinachTBDG(QtC.QObject):
    run_kale = Signal()

    def __init__(self, tab, cfg):
        """
        Class for the Spinach page of the RenderFarming Dialog
        :param tab: the renderFarming Dialog
        :param cfg: renderFarming Configuration
        """
        self._tab = tab
        super(SpinachTBDG, self).__init__()

        # Variables

        self._cfg = cfg

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.SpinachTBDG")

        # Spinach Job

        self._spinach = rFS.SpinachJob(self._cfg)

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._sp_man_prepass_btn = self._tab.findChild(QtW.QPushButton, 'sp_1f_man_prepass_btn')
        self._sp_man_beauty_btn = self._tab.findChild(QtW.QPushButton, 'sp_1f_man_beauty_btn')
        self._sp_backburner_submit_btn = self._tab.findChild(QtW.QPushButton, 'sp_backburner_submit_btn')
        self._sp_reset_btn = self._tab.findChild(QtW.QPushButton, 'sp_reset_btn')

        # ---------------------------------------------------
        #               Spin Box Definitions
        # ---------------------------------------------------

        self._sp_multi_frame_increment_sb = self._tab.findChild(QtW.QSpinBox, 'sp_multi_frame_increment_sb')
        self._sp_autosave_interval_dsb = self._tab.findChild(QtW.QDoubleSpinBox, 'sp_autosave_interval_dsb')

        # ---------------------------------------------------
        #               Check Box Definitions
        # ---------------------------------------------------

        self._sp_pad_gi_range_ckbx = self._tab.findChild(QtW.QCheckBox, 'sp_pad_gi_range_ckbx')
        self._sp_sub_fold_name_gi_ckbx = self._tab.findChild(QtW.QCheckBox, 'sp_sub_fold_name_gi_ckbx')
        self._sp_run_kale_ckbx = self._tab.findChild(QtW.QCheckBox, 'sp_run_kale_ckbx')
        self._sp_resumable_rendering_ckbx = self._tab.findChild(QtW.QCheckBox, 'sp_resumable_rendering_ckbx')

        # ---------------------------------------------------
        #               Label Definitions
        # ---------------------------------------------------

        self._spinach_status_lb = self._tab.findChild(QtW.QLabel, 'label_spinach_status')
        self._label_autosave_interval = self._tab.findChild(QtW.QLabel, 'label_autosave_interval')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        self._sp_frm_subFolder_le = self._tab.findChild(QtW.QLineEdit, 'sp_frm_subFolder_le')

        # ---------------------------------------------------
        #             Layout Element Definitions
        # ---------------------------------------------------

        self._sp_gi_settings_mro = self._tab.findChild(QMaxRollout, 'sp_gi_settings_mro')
        self._sp_frame_buffer_mro = self._tab.findChild(QMaxRollout, 'sp_frame_buffer_mro')

        # ---------------------------------------------------
        #               Combo Box Connections
        # ---------------------------------------------------

        self._sp_gi_mode_cmbx = GIModeComboBox(self._tab.findChild(QtW.QComboBox, 'sp_gi_mode_cmbx'))

        self._sp_vfb_type_cmbx = IndexBasedComboBox(self._tab.findChild(QtW.QComboBox, 'sp_vfb_type_cmbx'))
        self._sp_img_filt_ovr_cmbx = IndexBasedComboBox(self._tab.findChild(QtW.QComboBox, 'sp_img_filt_ovr_cmbx'))
        self._sp_sats_prompt_cmbx = SATSPromptComboBox(self._tab.findChild(QtW.QComboBox, 'sp_sats_prompt_cmbx'))

        self._sp_file_format_cmbx = IndexBasedComboBox(self._tab.findChild(QtW.QComboBox, 'sp_file_format_cmbx'))

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._sp_gi_mode_cmbx.cmbx.activated.connect(self._sp_gi_mode_cmbx_handler)

        self._sp_man_prepass_btn.clicked.connect(self._sp_man_prepass_btn_handler)
        self._sp_man_beauty_btn.clicked.connect(self._sp_man_beauty_btn_handler)
        self._sp_backburner_submit_btn.clicked.connect(self._backburner_submit_handler)

        self._sp_vfb_type_cmbx.cmbx.activated.connect(self._sp_vfb_type_cmbx_handler)
        self._sp_file_format_cmbx.cmbx.activated.connect(self._sp_file_format_cmbx_handler)

        self._sp_img_filt_ovr_cmbx.cmbx.activated.connect(
            lambda: self._spinach.set_image_filter_override(self._sp_img_filt_ovr_cmbx.get_index())
        )
        self._sp_frm_subFolder_le.editingFinished.connect(
            lambda: self._spinach.set_frames_sub_folder(self._sp_frm_subFolder_le.text())
        )
        self._sp_multi_frame_increment_sb.valueChanged.connect(
            lambda: self._spinach.set_multi_frame_increment(self._sp_multi_frame_increment_sb.value())
        )
        self._sp_autosave_interval_dsb.valueChanged.connect(
            lambda: self._spinach.set_autosave_interval(self._sp_autosave_interval_dsb.value())
        )
        self._sp_pad_gi_range_ckbx.stateChanged.connect(
            lambda: self._spinach.set_pad_gi(self._sp_pad_gi_range_ckbx.isChecked())
        )
        self._sp_sub_fold_name_gi_ckbx.stateChanged.connect(
            lambda: self._spinach.set_sub_folder_as_gi_name(self._sp_sub_fold_name_gi_ckbx.isChecked())
        )
        self._sp_resumable_rendering_ckbx.stateChanged.connect(
            lambda: self._spinach.set_resumable_rendering(self._sp_resumable_rendering_ckbx.isChecked())
        )

        self._sp_reset_btn.clicked.connect(self._sp_reset_handler)

        # self._sp_run_kale_ckbx.stateChanged.connect(self._sp_settings_change_handler)

        self._spinach.status_update.connect(self._spinach_status_handler)
        self._spinach.not_ready.connect(self._spinach_not_ready_handler)

        # ---------------------------------------------------
        #                       Setup
        # ---------------------------------------------------
        self.spinach_page_setup()

    # ---------------------------------------------------
    #                 Config Functions
    # ---------------------------------------------------

    def spinach_page_setup(self):
        cmbx_set_cur_ind(self._sp_gi_mode_cmbx.cmbx, (self._cfg.get_interface_setting("sp_gi_mode_cmbx_ind", 1)))
        self._sp_gi_mode_cmbx_handler()

        cmbx_set_cur_ind(self._sp_vfb_type_cmbx.cmbx, (self._cfg.get_interface_setting("sp_vfb_type_cmbx_ind", 1)))
        cmbx_set_cur_ind(self._sp_file_format_cmbx.cmbx, (self._cfg.get_interface_setting("sp_file_format_ind", 1)))
        cmbx_set_cur_ind(self._sp_img_filt_ovr_cmbx.cmbx,
                         (self._cfg.get_interface_setting("sp_img_filt_ovr_cmbx_ind", 1)))
        cmbx_set_cur_ind(self._sp_sats_prompt_cmbx.cmbx,
                         (self._cfg.get_interface_setting("sp_sats_prompt_cmbx_ind", 1)))

        self._sp_frm_subFolder_le.setText(self._cfg.get_interface_setting("sp_frm_subFolder_le_str", 0))
        self._sp_multi_frame_increment_sb.setValue(self._cfg.get_interface_setting("sp_multi_frame_increment_int", 1))
        self._sp_autosave_interval_dsb.setValue(self._cfg.get_interface_setting("sp_autosave_interval_flt", 2))

        self._sp_pad_gi_range_ckbx.setChecked(self._cfg.get_interface_setting("sp_pad_gi_range_bool", 3))
        self._sp_run_kale_ckbx.setChecked(self._cfg.get_interface_setting("sp_run_kale_bool", 3))
        self._sp_sub_fold_name_gi_ckbx.setChecked(self._cfg.get_interface_setting("sp_sub_fold_name_gi_bool", 3))
        self._sp_resumable_rendering_ckbx.setChecked(self._cfg.get_interface_setting("sp_resumable_render_bool", 3))

        self._mro_set_delay(self._sp_gi_settings_mro, self._cfg.get_interface_setting("sp_gi_settings_bool", 3))
        self._mro_set_delay(self._sp_frame_buffer_mro, self._cfg.get_interface_setting("sp_fb_settings_bool", 3))

        self._sp_apply_initial_settings()

    def config_apply_spinach_page(self):
        self._cfg.set_interface_setting("sp_gi_mode_cmbx_ind", self._sp_gi_mode_cmbx.cmbx.currentIndex())

        self._cfg.set_interface_setting("sp_vfb_type_cmbx_ind", self._sp_vfb_type_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_file_format_ind", self._sp_file_format_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_img_filt_ovr_cmbx_ind", self._sp_img_filt_ovr_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_sats_prompt_cmbx_ind", self._sp_sats_prompt_cmbx.cmbx.currentIndex())
        self._cfg.set_interface_setting("sp_multi_frame_increment_int", self._sp_multi_frame_increment_sb.value())
        self._cfg.set_interface_setting("sp_autosave_interval_flt", self._sp_autosave_interval_dsb.value())

        self._cfg.set_interface_setting("sp_pad_gi_range_bool", self._sp_pad_gi_range_ckbx.isChecked())
        self._cfg.set_interface_setting("sp_run_kale_bool", self._sp_run_kale_ckbx.isChecked())
        self._cfg.set_interface_setting("sp_sub_fold_name_gi_bool", self._sp_sub_fold_name_gi_ckbx.isChecked())
        self._cfg.set_interface_setting("sp_resumable_render_bool", self._sp_resumable_rendering_ckbx.isChecked())

        self._cfg.set_interface_setting("sp_frm_subFolder_le_str", self._sp_frm_subFolder_le.text())

        self._cfg.set_interface_setting("sp_gi_settings_bool", self._sp_gi_settings_mro.isExpanded())
        self._cfg.set_interface_setting("sp_fb_settings_bool", self._sp_frame_buffer_mro.isExpanded())

    # ---------------------------------------------------
    #                  Handler Functions
    # ---------------------------------------------------

    # noinspection PyMethodMayBeStatic
    def _mro_set_delay(self, widget, state):
        widget.setExpandedDelay(state)

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
            if not self.sats_dialog_opener():
                flg.warning("SATS Dialog cancelled, interrupting prepass")
                return
        self._spinach.check_camera()
        if not self._spinach.get_ready_status():
            flg.debug("Spinach reports not ready, attempting to prepare the Job")
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            flg.debug("Spinach reports ready, preparing the pass")
            self._spinach.prepare_prepass(self._sp_gi_mode_cmbx.get_prepass_mode())

        self._match_prefix()
        self._run_kale()

    def _sp_man_beauty_btn_handler(self):
        """
        Handler for beauty pass submission
        :return:
        """
        flg = logging.getLogger("renderFarming.UI._sp_man_beauty_btn_handler")
        flg.debug("Executing Beauty Pass")
        if self._sp_sats_prompt_cmbx.beauty():
            flg.debug("SATS Dialog Requested")
            if not self._tab.sats_dialog_opener():
                flg.warning("SATS Dialog cancelled, interrupting beauty pass")
                return
        self._spinach.check_camera()
        if not self._spinach.get_ready_status():
            flg.debug("Spinach reports not ready, attempting to prepare the Job")
            self._spinach.prepare_job()

        if self._spinach.get_ready_status():
            flg.debug("Spinach reports ready, preparing the pass")
            self._spinach.prepare_beauty_pass(self._sp_gi_mode_cmbx.get_beauty_mode())

        self._match_prefix()
        self._run_kale()

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

    def _sp_file_format_cmbx_handler(self):
        self._spinach.set_file_format(self._sp_file_format_cmbx.get_index())

    def _sp_vfb_type_cmbx_handler(self):
        index = self._sp_vfb_type_cmbx.get_index()
        self._spinach.set_frame_buffer_type(index)

        # Disables Save Formats that are not compatible with the Max Frame Buffer
        if index == 0:
            cmbx_set_cur_ind(self._sp_file_format_cmbx.cmbx, 0)
            self._sp_resumable_rendering_ckbx.setChecked(False)

            self._sp_file_format_cmbx_handler()
            self._spinach.set_resumable_rendering(False)

            self._sp_file_format_cmbx.cmbx.setEnabled(False)
            self._sp_autosave_interval_dsb.setEnabled(False)
            self._sp_resumable_rendering_ckbx.setEnabled(False)
            self._label_autosave_interval.setEnabled(False)
        else:
            self._sp_file_format_cmbx.cmbx.setEnabled(True)
            self._sp_autosave_interval_dsb.setEnabled(True)
            self._sp_resumable_rendering_ckbx.setEnabled(True)
            self._label_autosave_interval.setEnabled(True)

    def _sp_reset_handler(self):
        """
        Handler for reset button
        :return:
        """
        self._spinach.reset_renderer()

    def _sp_apply_initial_settings(self):
        """
        Handler for altering the spinach object based on the initial ui state
        :return:
        """
        self._sp_vfb_type_cmbx_handler()
        self._spinach.set_file_format(self._sp_file_format_cmbx.get_index())
        self._spinach.set_image_filter_override(self._sp_img_filt_ovr_cmbx.get_index())
        self._spinach.set_frames_sub_folder(self._sp_frm_subFolder_le.text())
        self._spinach.set_autosave_interval(self._sp_autosave_interval_dsb.value())

        self._spinach.set_multi_frame_increment(self._sp_multi_frame_increment_sb.value())
        self._spinach.set_pad_gi(self._sp_pad_gi_range_ckbx.isChecked())
        self._spinach.set_sub_folder_as_gi_name(self._sp_sub_fold_name_gi_ckbx.isChecked())
        self._spinach.set_resumable_rendering(self._sp_resumable_rendering_ckbx.isChecked())

    # ---------------------------------------------------
    #                Checker Functions
    # ---------------------------------------------------

    def _match_prefix(self):
        """
        Wrapper for rFT.match_prefix()
        :return: None
        """
        chk = rFT.match_prefix(rt.maxFileName, self._cfg.get_project_code())
        if chk is not None:
            self.set_spinach_status(chk)

    def _run_kale(self):
        if self._sp_run_kale_ckbx.isChecked():
            self.run_kale.emit()

    # ---------------------------------------------------
    #                  Getter Functions
    # ---------------------------------------------------

    def get_status_message(self):
        """
        Gets the current status message
        :return:
        """
        self._spinach_status_lb.text()

    def get_ready_status(self):
        return self._spinach.get_ready_status()

    # ---------------------------------------------------
    #                  Setter Functions
    # ---------------------------------------------------

    def set_spinach_status(self, text):
        self._spinach_status_lb.setText("Status: {}".format(text))

    @Slot(rFS.SpinachMessage)
    def _spinach_status_handler(self, message):
        self._clg.debug("Spinach status set to {}".format(message.raw_message()))
        self.set_spinach_status(message.styled_message())

    def _spinach_not_ready_handler(self):
        nr = rFT.html_color_text("Not Ready:", "Orange")
        self.set_spinach_status("{} {}".format(nr, self._spinach_status_lb.text()))

    def set_nth_frame(self, nth_frame):
        self._spinach.set_nth_frame(nth_frame)

    # ---------------------------------------------------
    #                    Dialogs
    # ---------------------------------------------------

    def sats_dialog_opener(self):
        self._clg.debug("Opening the \"Set Active Time Segment\" dialog")
        dialog = QTimeSegDialog.QTimeSegDialogUI()
        if not dialog.exec_():
            self.set_spinach_status(dialog.get_status_message())
            self.set_nth_frame(dialog.get_nth_frame())
            dialog.destroy()
            return False
        else:
            dialog.destroy()
            return True


class ConfigTBDG(QtC.QObject):
    saved = Signal()
    reset = Signal()
    edit = Signal()
    set_log_level = Signal(str)

    def __init__(self, tab, cfg):
        """
        Class for the Configuration page of the RenderFarming Dialog
        :param tab: the renderFarming Dialog
        :param cfg: renderFarming Configuration
        """
        super(ConfigTBDG, self).__init__()
        self._tab = tab

        # Variables

        self._cfg = cfg

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.ConfigTBDG")

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._cfg_save_btn = self._tab.findChild(QtW.QPushButton, 'config_save_btn')
        self._cfg_reset_btn = self._tab.findChild(QtW.QPushButton, 'config_reset_btn')
        self._cfg_test_btn = self._tab.findChild(QtW.QPushButton, 'config_test_btn')

        # ---------------------------------------------------
        #               Line Edit Definitions
        # ---------------------------------------------------

        # - Projects
        self._cfg_prj_projectCode_le = self._tab.findChild(QtW.QLineEdit, 'config_project_projectCode_le')
        self._cfg_prj_fullName_le = self._tab.findChild(QtW.QLineEdit, 'config_project_fullName_le')

        # - Paths
        self._cfg_pth_projectsDirectory_le = self._tab.findChild(QtW.QLineEdit, 'config_paths_projectsDirectory_le')
        self._cfg_pth_logDirectory_le = self._tab.findChild(QtW.QLineEdit, 'config_paths_logDirectory_le')
        self._cfg_pth_framesDirectory_le = self._tab.findChild(QtW.QLineEdit, 'config_paths_framesDirectory_le')
        self._cfg_pth_irradianceMapDirectory_le = self._tab.findChild(QtW.QLineEdit,
                                                                      'config_paths_irradianceMapDirectory_le')
        self._cfg_pth_lightCacheDirectory_le = self._tab.findChild(QtW.QLineEdit,
                                                                   'config_paths_lightCacheDirectory_le')

        # - Backburner
        self._cfg_bb_manager_le = self._tab.findChild(QtW.QLineEdit, 'config_backburner_manager_le')

        # ---------------------------------------------------
        #               Combo Box Definitions
        # ---------------------------------------------------

        self._cfg_lg_loggingLevel_cmbx = LogLevelComboBox(self._tab.findChild(QtW.QComboBox,
                                                                              'config_logging_loggingLevel_cmbx'))

        # ---------------------------------------------------
        #               Layout Definitions
        # ---------------------------------------------------

        self._config_project_mro = self._tab.findChild(QMaxRollout, 'config_project_mro')
        self._config_paths_mro = self._tab.findChild(QMaxRollout, 'config_paths_mro')
        self._config_backburner_mro = self._tab.findChild(QMaxRollout, 'config_backburner_mro')
        self._config_logging_mro = self._tab.findChild(QMaxRollout, 'config_logging_mro')

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
        # Config

        self._cfg_prj_projectCode_le.setText(self._cfg.get_project_code())
        self._cfg_prj_fullName_le.setText(self._cfg.get_project_full_name())

        self._cfg_pth_projectsDirectory_le.setText(self._cfg.get_projects_path(True))
        self._cfg_pth_framesDirectory_le.setText(self._cfg.get_frames_path(True))
        self._cfg_pth_irradianceMapDirectory_le.setText(self._cfg.get_irradiance_cache_path(True))
        self._cfg_pth_lightCacheDirectory_le.setText(self._cfg.get_light_cache_path(True))
        self._cfg_pth_logDirectory_le.setText(self._cfg.get_log_path(True))

        self._cfg_bb_manager_le.setText(self._cfg.get_net_render_manager())

        self._cfg_lg_loggingLevel_cmbx.set_by_level(self._cfg.get_log_level())

    def config_page_ui_setup(self):
        self._config_project_mro.setExpandedDelay(self._cfg.get_interface_setting("cg_project_mro_bool", 3))
        self._config_paths_mro.setExpandedDelay(self._cfg.get_interface_setting("cg_paths_mro_bool", 3))
        self._config_backburner_mro.setExpandedDelay(self._cfg.get_interface_setting("cg_backburner_mro_bool", 3))
        self._config_logging_mro.setExpandedDelay(self._cfg.get_interface_setting("cg_logging_mro_bool", 3))

    def config_apply_config_page(self):
        # Config

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
        self.set_log_level.emit(log_level)

        # UI only

        self._cfg.set_interface_setting("cg_project_mro_bool", self._config_project_mro.isExpanded())
        self._cfg.set_interface_setting("cg_paths_mro_bool", self._config_paths_mro.isExpanded())
        self._cfg.set_interface_setting("cg_backburner_mro_bool", self._config_backburner_mro.isExpanded())
        self._cfg.set_interface_setting("cg_logging_mro_bool", self._config_logging_mro.isExpanded())

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
        self._clg.debug("Applying User edits to configuration and saving changes to the configuration file")
        self.saved.emit()

    def _config_reset_handler(self):
        self._clg.debug("Resetting Configuration to Stored")
        self.config_page_setup()
        self.reset.emit()

    def _edit_handler(self):
        self.edit.emit()

    def config_reset(self):
        self._config_reset_handler()


class LogTBDG(QtC.QObject):
    def __init__(self, tab, cfg):
        """
        Class for the Log page of the RenderFarming Dialog
        :param tab: the renderFarming Dialog
        :param cfg: renderFarming Configuration
        """
        super(LogTBDG, self).__init__()
        self._tab = tab

        # Variables

        self._cfg = cfg

        # Logger

        self._clg = logging.getLogger("renderFarming.UI.LogTBDG")

        # ---------------------------------------------------
        #                 Button Definitions
        # ---------------------------------------------------

        self._lg_open_explorer_btn = self._tab.findChild(QtW.QPushButton, 'lg_open_explorer_btn')

        # ---------------------------------------------------
        #             Plain Text Edit Definitions
        # ---------------------------------------------------

        self._lg_text_pte = self._tab.findChild(QtW.QPlainTextEdit, 'lg_text_pte')
        LogSyntaxHighlighter(self._lg_text_pte.document())

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._lg_open_explorer_btn.clicked.connect(self._log_open_explorer_handler)

    # ---------------------------------------------------
    #                  Handler Functions
    # ---------------------------------------------------

    def _log_open_explorer_handler(self):
        rt.ShellLaunch("explorer.exe", self._cfg.get_log_path())
        return

    # ---------------------------------------------------
    #                  Setter Functions
    # ---------------------------------------------------

    def append_log_text(self, text):
        old = self._lg_text_pte.toPlainText()
        self._lg_text_pte.setPlainText(self._filter_empty_lines(old))
        self._lg_text_pte.appendPlainText(text)

    # noinspection PyMethodMayBeStatic
    def _filter_empty_lines(self, text):
        """
        Filters out empty lines from the log text
        From: https://stackoverflow.com/a/24172715
        :param text: The string to be filtered
        :return:
        """
        return "".join([s for s in text.strip().splitlines(True) if s.strip("\r\n").strip()])


class LogSyntaxHighlighter(QtG.QSyntaxHighlighter):
    def __init__(self, parent):
        super(LogSyntaxHighlighter, self).__init__(parent)
        # noinspection SpellCheckingInspection
        self.rules = (
            HighlightRule("\\bDEBUG:\\b", rCL.log_debug, "bold", "underline"),
            HighlightRule("\\bINFO:\\b", rCL.log_info, "bold", "underline"),
            HighlightRule("\\bWARNING:\\b", rCL.log_warning, "bold", "underline"),
            HighlightRule("\\bERROR:\\b", rCL.log_error, "bold", "underline"),
            HighlightRule("\\bCRITICAL:\\b", rCL.log_critical, "bold", "underline"),
            HighlightRule("renderFarming|RenderFarming", rCL.log_renderFarming, "italic"),
            HighlightRule("Kale|kale|\\bConfig\\b|\\bconfig\\b|Spinach|spinach", rCL.log_module, "italic")
        )

    def highlightBlock(self, text):
        for rule in self.rules:

            expression = QtC.QRegExp(rule.pattern)

            index = expression.indexIn(text, 0)

            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, rule.style)
                index = expression.indexIn(text, index + length)


class HighlightRule(object):
    """
    From: https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
    Constructs a QTextCharFormat and a QRegExp and keeps them together for later use
    """
    def __init__(self, pattern, color, *args):
        self.pattern = QtC.QRegExp(pattern)
        self.style = QtG.QTextCharFormat()

        if color is not None:
            if type(color) is QtG.QColor:
                self.style.setForeground(color)
            else:
                _color = QtG.QColor()
                _color.setNamedColor(color)
                self.style.setForeground(_color)

        if 'bold' in args:
            self.style.setFontWeight(QtG.QFont.Bold)
        if 'italic' in args:
            self.style.setFontItalic(True)
        if 'underline' in args:
            self.style.setFontUnderline(True)


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
