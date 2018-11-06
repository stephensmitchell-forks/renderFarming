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


def get_icons():
    return "icon1", "icon2"


def get_scripts():
    return "script1", "script2"


def get_macros():
    return list("macro1")


def get_max_dir():
    return "C:\\Program Files\\Autodesk\\3ds Max 2018\\"


def get_user_scripts_dir():
    return os.path.realpath(os.path.join(get_enu_dir(), 'scripts'))


def get_user_macros_dir():
    return os.path.realpath(os.path.join(get_enu_dir(), 'usermacros'))


def copy_icons(self):
    icons_light_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Light", "RenderFarming")
    icons_dark_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Dark", "RenderFarming")
    return icons_light_dir, icons_dark_dir


def copy_file_list(self):
    install_dir = os.path.join(self._max_user_scripts_dir, "BDF", "renderFarming")
    return install_dir


def get_enu_dir():
    return os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU'))


class RenderFarmingInstaller:

    def __init__(self, items, ui):
        self._ui = ui
        self._items = items
        self._temp = os.path.join(gettempdir(), '.{}'.format(hash(os.times())))

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
    cancel = QtC.Signal()

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)

        self._main_layout = QtW.QVBoxLayout()

        self._intro_page = InstallerIntroPage()
        # noinspection PyUnresolvedReferences
        self._intro_page.install.connect(self.install)
        # noinspection PyUnresolvedReferences
        self._intro_page.cancel.connect(self.reject)

        self._progress_bar_page = InstallerProgressPage()
        self._progress_bar = self._progress_bar_page.get_progress_bar()

        self._progress_bar_page.setVisible(False)
        # noinspection PyUnresolvedReferences
        self._progress_bar_page.cancel.connect(self.install_cancel)

        self._main_layout.addWidget(self._intro_page)
        self._main_layout.addWidget(self._progress_bar_page)

        self.setLayout(self._main_layout)

    def install(self):
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        progress_bar_test(self, 10000)

    def install_cancel(self):
        # noinspection PyUnresolvedReferences
        self.cancel.emit()

    def progress_bar_set_tasks(self, task_number):
        if task_number > 0:
            self._progress_bar.setTextVisible(True)
            self._progress_bar.setRange(0, task_number)
        else:
            self._progress_bar.setTextVisible(False)
            self._progress_bar.setRange(0, 0)

    def progress_bar_add(self):
        self._progress_bar.setValue(self._progress_bar.value() + 1)

    def progress_bar_complete(self):
        self._progress_bar.setValue(self._progress_bar.maximum())


def progress_bar_test(ui, size):
    ui.progress_bar_set_tasks(size)

    for i in range(size):
        print("*******")
        ui.progress_bar_add()

    ui.progress_bar_complete()


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
        self._main_image_pxmp = QPixmap("render_farming_icon_01.256.png")
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
    cancel = QtC.Signal()

    def __init__(self):
        super(InstallerProgressPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._progress_bar_layout = QtW.QVBoxLayout()

        self._cancel_btn = QtW.QPushButton()
        self._cancel_btn.setText("Cancel")
        # noinspection PyUnresolvedReferences
        self._cancel_btn.clicked.connect(self._cancel_btn_handler)

        self._progress_bar = QtW.QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)

        self._install_lb = QtW.QLabel()
        self._install_lb.setText("RenderFarming Installer")

        self.setLayout(self._main_layout)

        self._main_layout.addLayout(self._progress_bar_layout)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._progress_bar_layout.addWidget(self._install_lb)
        self._progress_bar_layout.addWidget(self._progress_bar)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._main_layout.addWidget(self._cancel_btn)

    def _cancel_btn_handler(self):
        # noinspection PyUnresolvedReferences
        self.cancel.emit()

    def get_progress_bar(self):
        return self._progress_bar


if __name__ == "__main__":
    main()
