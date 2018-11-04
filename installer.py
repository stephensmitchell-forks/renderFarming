import ctypes
import sys
import os
import shutil

import PySide2.QtWidgets as QtW
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


def create_directory(directory):
    if not os.path.isdir(directory):
        os.makedirs(directory)


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
            directory = item
            if not os.path.isdir(directory):
                os.makedirs(directory)
            self._ui.progress_bar.add()

    def _copy_files(self):
        for item in self._items:
            src = os.path.join(self._temp, item.key())
            dst = os.path.join(item, item.key())
            shutil.copy2(src, dst)
            self._ui.progress_bar.add()

    def _delete_files(self):
        for item in self._items:
            file_name = os.path.join(item, item.key())
            if os.path.exists(file_name):
                os.remove(file_name)
                self._ui.progress_bar.add()

def copy_icons(self):
    icons_light_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Light", "RenderFarming")
    icons_dark_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Dark", "RenderFarming")
    return

def copy_file_list(self):
    install_dir = os.path.join(self._max_user_scripts_dir, "BDF", "renderFarming")
    return

def get_enu_dir():
    return os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU'))


class RenderFarmingInstallerMainWindow(QtW.QDialog):

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)

        self._main_layout = QtW.QVBoxLayout()
        self._intro_page = InstallerIntroPage(self)

        self._main_layout.addLayout(self._intro_page)

        self.setLayout(self._main_layout)

    def install(self):
        return


class InstallerIntroPage(QtW.QVBoxLayout):

    def __init__(self, parent):
        super(InstallerIntroPage, self).__init__()

        self._parent = parent

        self._installer_btn_layout = QtW.QVBoxLayout()

        self._install_btn = QtW.QPushButton()
        self._install_btn.setText("Install")

        self._install_lb = QtW.QLabel()
        self._install_lb.setText("RenderFarming Installer")

        self._cancel_btn = QtW.QPushButton()
        self._cancel_btn.setText("Cancel")

        self.addLayout(self._installer_btn_layout)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._installer_btn_layout.addWidget(self._install_lb)
        self._installer_btn_layout.addWidget(self._install_btn)
        self._installer_btn_layout.insertStretch(-1, 0)
        self.addWidget(self._cancel_btn)

    def _install_btn_handler(self):
        self._parent.install()

    def _cancel_btn_handler(self):
        self._parent.reject()


if __name__ == "__main__":
    main()
