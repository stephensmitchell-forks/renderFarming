import ctypes
import sys
import os
import shutil

import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC
from PySide2.QtGui import QPixmap
from tempfile import gettempdir


def is_admin():
    if "dev" in sys.argv:
        return True
    else:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as error:
            print("Unable to retrieve UAC Elevation level: %s" % error)
            return False


def main():
    if is_admin():
        app = QtW.QApplication(sys.argv)
        w = RenderFarmingInstallerMainWindow()
        w.show()
        app.exec_()

    else:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__), None, 1)


class DirectoryLocator:
    def __init__(self):
        self._appdata_dir = os.getenv('LOCALAPPDATA')
        self._temp = os.path.join(gettempdir(), '.{}'.format(hash(os.times())))

        self._max_dir = self._find_max_dir()

        self._enu_dir = self._find_enu_dir()

        self._user_macros = self._find_user_macros_dir()
        self._user_scripts = self._find_user_scripts_dir()

        self._install_dir = os.path.join(self._user_scripts, "BDF", "renderFarming")
        self._light_icons, self._dark_icons = self._find_icons()

    def _find_max_dir(self):
        return "C:\\Program Files\\Autodesk\\3ds Max 2018\\"

    def _find_enu_dir(self):
        return os.path.realpath(os.path.join(self._appdata_dir, 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU'))

    def _find_user_macros_dir(self):
        return os.path.realpath(os.path.join(self._enu_dir, 'usermacros'))

    def _find_user_scripts_dir(self):
        return os.path.realpath(os.path.join(self._enu_dir, 'scripts'))

    def _find_icons(self):
        icons_light_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Light", "RenderFarming")
        icons_dark_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Dark", "RenderFarming")
        return icons_light_dir, icons_dark_dir

    def get_temp(self):
        return self._temp

    def get_appdata(self):
        return self._appdata_dir

    def get_max_install(self):
        return self._max_dir

    def get_enu(self):
        return self._enu_dir

    def get_user_macros(self):
        return self._user_macros

    def get_user_scripts(self):
        return self._user_scripts

    def get_render_farming_install(self):
        return self._install_dir


class RenderFarmingInstaller:

    def __init__(self, items, ui):
        self._ui = ui
        self._items = items

    def run_installation(self):
        self._ui.progress_bar.set_tasks(len(self._items) * 2)
        try:
            self._create_directories()
            self._copy_files()
        except (IOError, OSError) as e:
            self._ui.install_error(e)

    def run_un_installation(self):
        self._ui.progress_bar.set_tasks(len(self._items) * 2)
        try:
            self._delete_files()
        except (IOError, OSError) as e:
            self._ui.install_error(e)

    def _create_directories(self):
        for item in self._items:
            directory = item.get_destination_dir()
            if not os.path.isdir(directory):
                os.makedirs(directory)
            self._ui.progress_bar.add()

    def _copy_files(self):
        for item in self._items:
            src = os.path.join(item.get_source())
            dst = os.path.join(item.get_destination())
            shutil.copy2(src, dst)
            self._ui.progress_bar.add()

    def _delete_files(self):
        for item in self._items:
            file_name = item.get_source()
            if os.path.exists(file_name):
                os.remove(file_name)
                self._ui.progress_bar.add()


class InstallerItem:

    def __init__(self, source, destination):
        self._src = source
        self._dst = destination

    def get_source(self):
        return os.path.normpath(self._src)

    def get_destination(self):
        return os.path.normpath(self._dst)

    def get_destination_dir(self):
        return os.path.normpath(os.path.basename(self._dst))

    def get_source_dir(self):
        return os.path.normpath(os.path.basename(self._src))


class RenderFarmingInstallerMainWindow(QtW.QDialog):

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)

        self._main_layout = QtW.QVBoxLayout()

        self._intro_page = InstallerIntroPage()
        # noinspection PyUnresolvedReferences
        self._intro_page.install.connect(self.install)
        # noinspection PyUnresolvedReferences
        self._intro_page.cancel.connect(self.reject)

        self._progress_bar_page = InstallerProgressPage()
        self.progress_bar = self._progress_bar_page

        self._progress_bar_page.setVisible(False)
        # noinspection PyUnresolvedReferences
        self._progress_bar_page.close.connect(self.close)

        self._main_layout.addWidget(self._intro_page)
        self._main_layout.addWidget(self._progress_bar_page)

        self.setLayout(self._main_layout)

    def install(self):
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        progress_bar_test(self, 10000)
        self._progress_bar_page.set_complete()


def progress_bar_test(ui, size):
    ui.progress_bar.set_tasks(size)
    ui.progress_bar.set_status("*******")

    for i in range(size):
        print("*******")
        ui.progress_bar.add()


class InstallerIntroPage(QtW.QWidget):
    install = QtC.Signal()
    cancel = QtC.Signal()

    def __init__(self):
        super(InstallerIntroPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._installer_btn_layout = QtW.QVBoxLayout()

        self._install_lb = QtW.QLabel()
        self._install_lb.setText("RenderFarming Installer")

        self._main_image_lb = QtW.QLabel()
        self._main_image_pxmp = QPixmap("UI\\render_farming_icon_01.256.png")
        self._main_image_lb.setAlignment(QtC.Qt.AlignCenter)

        self._main_image_lb.setPixmap(self._main_image_pxmp)

        self._install_btn = QtW.QPushButton()
        self._install_btn.setText("Install")
        # noinspection PyUnresolvedReferences
        self._install_btn.clicked.connect(self._install_btn_handler)

        self._cancel_btn = QtW.QPushButton()
        self._cancel_btn.setText("Cancel")
        # noinspection PyUnresolvedReferences
        self._cancel_btn.clicked.connect(self._cancel_btn_handler)

        self.setLayout(self._main_layout)

        self._main_layout.addLayout(self._installer_btn_layout)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._installer_btn_layout.addWidget(self._main_image_lb)
        self._installer_btn_layout.addWidget(self._install_lb)
        self._installer_btn_layout.addWidget(self._install_btn)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._main_layout.addWidget(self._cancel_btn)

    def _install_btn_handler(self):
        # noinspection PyUnresolvedReferences
        self.install.emit()

    def _cancel_btn_handler(self):
        # noinspection PyUnresolvedReferences
        self.cancel.emit()


class InstallerProgressPage(QtW.QWidget):
    close = QtC.Signal()

    def __init__(self):
        super(InstallerProgressPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._progress_bar_layout = QtW.QVBoxLayout()

        self._close_btn = QtW.QPushButton()
        self._close_btn.setText("Close")
        self._close_btn.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self._close_btn.clicked.connect(self._close_btn_handler)

        self._progress_bar = QtW.QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)

        self._main_lb = QtW.QLabel()
        self._main_lb.setText("Installing:")
        self._task_lb = QtW.QLabel()
        self._task_lb.setText(str())

        self.setLayout(self._main_layout)

        self._main_layout.addLayout(self._progress_bar_layout)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._progress_bar_layout.addWidget(self._main_lb)
        self._progress_bar_layout.addWidget(self._progress_bar)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._main_layout.addWidget(self._close_btn)

    def _close_btn_handler(self):
        # noinspection PyUnresolvedReferences
        self.close.emit()

    def get_progress_bar(self):
        return self._progress_bar

    def set_complete(self):
        self._progress_bar.setValue(self._progress_bar.maximum())
        self._close_btn.setEnabled(True)
        self._main_lb.setText("Complete!")
        self._task_lb.setText(str())

    def set_tasks(self, task_number):
        if task_number > 0:
            self._progress_bar.setTextVisible(True)
            self._progress_bar.setRange(0, task_number)
        else:
            self._progress_bar.setTextVisible(False)
            self._progress_bar.setRange(0, 0)

    def add(self):
        self._progress_bar.setValue(self._progress_bar.value() + 1)

    def set_status(self, status):
        self._task_lb.setText(status)


if __name__ == "__main__":
    main()
