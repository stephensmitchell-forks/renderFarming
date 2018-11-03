import ctypes
import sys
import os

import PySide2.QtWidgets as QtW


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


def get_enu_dir():
    return os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU'))


def get_user_scripts_dir():
    return os.path.realpath(os.path.join(get_enu_dir(), 'scripts'))


def get_user_macros_dir():
    return os.path.realpath(os.path.join(get_enu_dir(), 'usermacros'))


def copy_icons(icons, folders):
    return


def copy_file_list(files, folder):
    return


def run_installation(ui):
    ui.progress_bar.set_tasks(10)
    icons = get_icons()
    scripts = get_scripts()
    macros = get_macros()

    max_dir = get_max_dir()
    icons_light_dir = os.path.join(max_dir, "UI_ln", "Icons", "Light", "RenderFarming")
    icons_dark_dir = os.path.join(max_dir, "UI_ln", "Icons", "Dark", "RenderFarming")

    max_user_scripts_dir = get_user_scripts_dir()
    install_dir = os.path.join(max_user_scripts_dir, "BDF", "renderFarming")

    max_user_macros_dir = get_user_macros_dir()

    ui.progress_bar.add()

    try:
        create_directory(icons_light_dir)
        ui.progress_bar.add()
        create_directory(icons_dark_dir)
        ui.progress_bar.add()
        create_directory(install_dir)
        ui.progress_bar.add()
    except (IOError, os.error) as e:
        ui.error_msg(e)
        return

    try:
        copy_icons(icons, icons_light_dir)
        copy_file_list(scripts, install_dir)
        copy_file_list(macros, max_user_macros_dir)
        # ui.progress_bar.add()
    except (IOError, os.error) as e:
        ui.error_msg(e)
        return

    print("Bada Bing")


class RenderFarmingInstaller:

    def __init__(self, ui):
        self._max_version = "2018"


class RenderFarmingInstallerMainWindow(QtW.QDialog):

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)

        self._main_layout = QtW.QVBoxLayout()
        self._intro_page = InstallerIntroPage()

        self._main_layout.addLayout(self._intro_page)

        self.setLayout(self._main_layout)


class InstallerIntroPage(QtW.QVBoxLayout):

    def __init__(self):
        super(InstallerIntroPage, self).__init__()
        self._installer_btn_layout = QtW.QVBoxLayout()
        self._install_btn = QtW.QPushButton()
        self._install_lb = QtW.QLabel()

        self._cancel_btn = QtW.QPushButton()

        self.addLayout(self._installer_btn_layout)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._installer_btn_layout.addWidget(self._install_lb)
        self._installer_btn_layout.addWidget(self._install_btn)
        self._installer_btn_layout.insertStretch(-1, 0)
        self.addWidget(self._cancel_btn)


if __name__ == "__main__":
    main()
