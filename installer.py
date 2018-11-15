import ctypes
import sys
import os
import shutil
import _winreg

import PySide2.QtWidgets as QtW
from PySide2.QtCore import Signal, Slot, Qt, QThread
from PySide2.QtGui import QPixmap
from tempfile import gettempdir


def is_admin():
    if "-dev" in sys.argv:
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


# ---------------------------------------------------
#                Installer Classes
# ---------------------------------------------------


class DirectoryLocator:
    max_version_dict = {"2018": "20.0", "2019": "21.0"}

    def __init__(self, max_version="2018"):

        self._max_version = max_version

        self._appdata_dir = os.getenv('LOCALAPPDATA')
        self._temp = os.path.join(gettempdir(), '.{}'.format(hash(os.times())))

        self._max_dir = self._find_max_dir()

        self._enu_dir = self._find_enu_dir()

        self._user_macros = self._find_user_macros_dir()
        self._user_scripts = self._find_user_scripts_dir()
        self._user_startup = self._find_user_startup_dir()

        self._install_dir = os.path.join(self._user_scripts, "BDF", "renderFarming")
        self._light_icons, self._dark_icons = self._find_icons()

    def _find_max_dir(self):
        key_str = "Software\\Autodesk\\3dsMax\\{}".format(self.max_version_dict.get(self._max_version, "20.0"))
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_str)
        value = _winreg.QueryValueEx(key, "Installdir")[0]
        key.Close()
        if os.path.isdir(value):
            return value
        else:
            return "C:\\Program Files\\Autodesk\\3ds Max {}\\".format(self._max_version)

    def _find_enu_dir(self):
        return os.path.realpath(os.path.join(self._appdata_dir,
                                             'Autodesk',
                                             '3dsMax',
                                             '{} - 64bit'.format(self._max_version),
                                             'ENU'))

    def _find_user_macros_dir(self):
        return os.path.realpath(os.path.join(self._enu_dir, 'usermacros'))

    def _find_user_scripts_dir(self):
        return os.path.realpath(os.path.join(self._enu_dir, 'scripts'))

    def _find_user_startup_dir(self):
        return os.path.realpath(os.path.join(self._enu_dir, 'startup'))

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

    def get_user_startup(self):
        return self._user_startup

    def get_render_farming_install(self):
        return self._install_dir

    def get_dark_icons(self):
        return self._dark_icons

    def get_light_icons(self):
        return self._light_icons

    def __str__(self):
        return str(self.__repr__()).replace(', ', '\n').replace('{', '').replace('}', '').replace('\'', '')

    def __repr__(self):
        dt = {
            "3ds Max Version": self._max_version,
            "3ds Max Directory": self._max_dir,
            "3ds Max User Scripts": self._user_scripts,
            "3ds Max User Macros": self._user_macros,
            "RenderFarming Directory": self._install_dir,
            "RenderFarming Dark Icons": self._dark_icons,
            "RenderFarming Light Icons": self._light_icons,
            "Temp Directory": self._temp,
            "Local AppData Directory": self._appdata_dir
        }
        return dt


class ManifestTranslator:
    """
    Translates the raw manifest file to a list of InstallerItem objects
    """
    def __init__(self, directory, manifest):
        self._dir = directory
        self._man = manifest
        self._man.read()
        self._wd = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self._item_list = list()

        self._dir_dict = {
            "$(main)": self._dir.get_render_farming_install(),
            "$(macro)": self._dir.get_user_macros(),
            "$(startup)": self._dir.get_user_startup(),
            "$(dark_icons)": self._dir.get_dark_icons(),
            "$(light_icons)": self._dir.get_light_icons()
        }

        self._translate()

    def _translate(self):
        """
        Converts the manifest to InstallerItem objects
        :return: appends InstallerItem objects to self._item_list
        """
        for num, line in enumerate(self._man.get_data()):
            self._item_list.append(self._line_to_data(line, num))

    # noinspection PyMethodMayBeStatic
    def _line_to_data(self, line, number):
        """
        Converts a string line from the Manifest file to an InstallerItem object
        :param line: A string containing a single line from the Manifest file
        :param number: The line Number in the file
        :return: an InstallerItem Object
        """
        # Lines should be formatted as src:dst
        # dst can be a token of a absolute path, but not both
        # all source objects should be relative to the directory in which this script is contained
        spl = line.split('|')
        if len(spl) == 2:
            src = spl[0].replace('\"', '')
            src = os.path.join(self._wd, src)

            # raises an exception if this file is not present in the __file__ directory
            if not os.path.exists(src):
                raise ManifestError(
                    "Manifest line {}({}) is unable to resolve the file source: {}".format(number + 1, spl, src)
                )

            # chooses between a token or absolute path
            if (spl[1])[0] is '$':
                dst = self._expand_token(spl[1])
            else:
                dst = spl[1].replace('\"', '')

            dst = os.path.join(dst, os.path.split(src)[1])
            datum = InstallerItem(src, dst)
            return datum

        # Raises an exception if the line cannot be split
        else:
            raise ManifestError("Manifest line {}({}) is incorrectly Formatted".format(number + 1, spl))

    # noinspection PyMethodMayBeStatic
    def _expand_token(self, token):
        """
        Expands a string token to a directory in the self._dir_dict
        :param token: the token in format $(token)
        :return: the resolved string from the dictionary
        """
        try:
            exp = self._dir_dict[token]
        # Raises a Manifest error if a key error is caught
        except KeyError as e:
            raise ManifestError("Key Error: {} does not resolve.".format(e))
        else:
            return exp

    def get_items(self):
        return self._item_list

    def __str__(self):
        ret_str = str()
        for item in self._item_list:
            ret_str = ret_str + str(item) + '\n'
        return ret_str

    def __repr__(self):
        return self._item_list


class ManifestHeader:
    def __init__(self, manifest):
        self._man = manifest
        self._data = dict()

        self._translate()

    def _translate(self):
        """
        Converts the manifest Header to a dict
        :return: adds keys to self._data dictionary
        """
        for num, line in enumerate(self._man.get_header()):
            self._line_to_data(line, num)

    # noinspection PyMethodMayBeStatic
    def _line_to_data(self, line, number):
        """

        :param line: A string containing a single line from the Manifest file
        :param number: The line Number in the file
        :return:
        """
        line = line.replace('#', '')
        spl = line.split('|')
        if len(spl) == 2:
            try:
                self._data[spl[0]] = spl[1]
            except KeyError as e:
                raise ManifestError("Key Error: {} does not resolve.".format(e))

        # Raises an exception if the line cannot be split
        else:
            raise ManifestError("Manifest Header line {}({}) is incorrectly Formatted".format(number + 1, spl))

    def version(self):
        return self._data.get("version", "UNKNOWN")

    def get_data(self):
        return self._data


class Manifest:
    def __init__(self, manifest_file):
        self._manifest_file = manifest_file
        self._data = list()
        self._header = list()

    def read(self):
        if not os.path.exists(self._manifest_file):
            raise ManifestError("Manifest file: {} does not exist.".format(self._manifest_file))
        with open(self._manifest_file, 'r') as man_file:
            data = man_file.readlines()
            self._set_formatted_data(data)

    def write(self):
        directory = os.path.split(self._manifest_file)[0]
        if not os.path.isdir(directory):
            raise ManifestError("Manifest Directory: {} does not exist.".format(directory))
        with open(self._manifest_file, 'w') as man_file:
            man_file.write(self._get_formatted_data())

    def _get_formatted_data(self):
        main_str = str()
        for line in self._header:
            main_str = main_str + line + '\n'
        for line in self._data:
            main_str = main_str + line + '\n'
        return main_str

    def _set_formatted_data(self, data):
        for line in data:
            line = line.rstrip()
            if line[0] == '#':
                self._header.append(line)
            else:
                self._data.append(line)

    def get_data(self):
        return self._data

    def get_header(self):
        return self._header

    def set_data(self, data_list):
        for i in data_list:
            self._data.append("\"{}\":\"{}\"".format(i.get_source(), i.get_destination()))

    def set_header(self, header_dict):
        for i in header_dict.keys():
            self._header.append("#{}:{}".format(i, header_dict[i]))

    def add_self(self):
        self._data.append("\"{}\":\"{}\"".format(self._manifest_file, ''))

    def __str__(self):
        ret_str = str()
        for item in self.__repr__():
            ret_str = ret_str + str(item) + '\n'
        return ret_str

    def __repr__(self):
        return self._header + self._data


class InstallerItem:

    def __init__(self, source, destination, is_dir=False):
        self._src = source
        self._dst = destination
        self._isDir = is_dir

    def get_source(self):
        return os.path.normpath(self._src)

    def get_destination(self):
        return os.path.normpath(self._dst)

    def get_destination_dir(self):
        return os.path.normpath(os.path.split(self._dst)[0])

    def get_source_dir(self):
        return os.path.normpath(os.path.split(self._src)[0])

    def get_is_dir(self):
        return self._isDir

    def __str__(self):
        return "{}:{}".format(self._src, self._dst)

    def __repr__(self):
        return self.__str__()


class RenderFarmingInstaller(QThread):
    """
    This class contains all of the steps needed to install or uninstall RenderFarming

    :signal set_tasks: Emits to communicate the initial task size to the progress bar
    :signal add_task: Emits when a task has completed and the progress bar should be advanced
    :signal error: Emits when an error occurs an transmits that error's message
    """
    set_tasks = Signal(int)
    add_task = Signal(int)
    print_error = Signal(str)
    complete = Signal()

    def __init__(self, max_version):
        super(RenderFarmingInstaller, self).__init__()
        self._3ds_max_version = max_version
        self._items = list()
        self._dir_loc = None
        self._man = None
        self._man_translated = None
        self._record = list()

    def run(self, uninstall=False):
        try:
            self.set_tasks.emit(4)

            self._dir_loc = DirectoryLocator(self._3ds_max_version)
            self._add()

            if uninstall:
                self._man = Manifest(os.path.join(self._dir_loc.get_render_farming_install(), "uninstall.man"))
            else:
                self._man = Manifest("install.man")

            self._add()

            self._man_translated = ManifestTranslator(self._dir_loc, self._man)
            self._add()

            self._items = self._man_translated.get_items()
            self._add()

            if uninstall:
                self.run_uninstallation()
            else:
                self.run_installation()

        except (IOError, OSError, ManifestError) as e:
            self.print_error.emit(str(e))
        else:
            self.complete.emit()
        finally:
            self.terminate()

    def run_installation(self):
        self.set_tasks.emit(len(self._items) * 2)

        self._create_directories()
        self._copy_files()
        self._generate_uninstall_manifest()

    def run_uninstallation(self):
        self.set_tasks.emit(len(self._items))

        self._delete_files()

    def _generate_uninstall_manifest(self):
        self.set_tasks.emit(4)
        new_man = Manifest(os.path.join(self._dir_loc.get_render_farming_install(), "uninstall.man"))
        self._add()

        new_man.set_data(self._record)
        self._add()

        new_head = ManifestHeader(self._man)
        new_man.set_header(new_head.get_data())
        self._add()

        new_man.add_self()

        new_man.write()
        self._add()

    def _create_directories(self):
        for item in self._items:
            directory = item.get_destination_dir()
            if not os.path.isdir(directory):
                self._create_dir(directory)
            self._add()

    def _create_dir(self, directory):
        if not os.path.isdir(directory):
            parent = os.path.split(directory)[0]
            if os.path.isdir(parent):
                self._record.append(InstallerItem(directory, '', True))
                print("os.makedirs({})".format(directory))
                # os.makedirs(directory)
            else:
                self._create_dir(parent)

    def _copy_files(self):
        for item in self._items:
            src = os.path.join(item.get_source())
            dst = os.path.join(item.get_destination())
            print("shutil.copy2({}, {})".format(src, dst))
            self._record.append(InstallerItem(dst, ''))
            # shutil.copy2(src, dst)
            self._add()

    def _delete_files(self):
        for item in self._items:
            file_name = item.get_source()
            if os.path.isfile(file_name):
                print("os.remove({})".format(file_name))
                # os.remove(file_name)
                self._add()

    def _add(self):
        self.add_task.emit(1)


# ---------------------------------------------------
#                  User Interface
# ---------------------------------------------------


class RenderFarmingInstallerMainWindow(QtW.QDialog):

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)
        self._max_version = "2018"

        self._main_layout = QtW.QVBoxLayout()

        self._intro_page = InstallerIntroPage()
        self._intro_page.install.connect(self.install)
        self._intro_page.cancel.connect(self.reject)
        self._intro_page.upgrade.connect(self.upgrade)
        self._intro_page.uninstall.connect(self.uninstall)

        self.old_version_check()

        self._progress_bar_page = InstallerProgressPage()
        self.progress_bar = self._progress_bar_page

        self._progress_bar_page.setVisible(False)
        self._progress_bar_page.close.connect(self.close)

        self._main_layout.addWidget(self._intro_page)
        self._main_layout.addWidget(self._progress_bar_page)

        self.setLayout(self._main_layout)

        self._installer = RenderFarmingInstaller(self._max_version)
        self._installer.set_tasks.connect(self._progress_bar_page.set_tasks)
        self._installer.add_task.connect(self._progress_bar_page.add)
        self._installer.print_error.connect(self._progress_bar_page.print_error)
        self._installer.complete.connect(self._progress_bar_page.set_complete)

    def install(self):
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._installer.run(False)

    def uninstall(self):
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._progress_bar_page.set_uninstall()
        self._installer.run(True)

    def upgrade(self):
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._progress_bar_page.set_uninstall()
        self._installer.run(True)
        self._progress_bar_page.set_install()
        self._installer.run(False)

    def old_version_check(self):
        dirs = DirectoryLocator(self._max_version)
        u_man_path = os.path.join(dirs.get_render_farming_install(), "uninstall.man")
        if os.path.isfile(u_man_path):
            u_man = Manifest(u_man_path)
            u_head = ManifestHeader(u_man)
            man = Manifest("install.man")
            head = ManifestHeader(man)
            if u_head.version() < head.version():
                self._intro_page.set_upgrade()
            elif u_head.version() == head.version():
                self._intro_page.set_uninstall()
            else:
                self._intro_page.set_old_version()
        else:
            self._intro_page.set_install()


class InstallerIntroPage(QtW.QWidget):
    install = Signal()
    uninstall = Signal()
    upgrade = Signal()
    cancel = Signal()

    def __init__(self):
        super(InstallerIntroPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._installer_btn_layout = QtW.QVBoxLayout()

        self._install_lb = QtW.QLabel()
        self._install_lb.setText("Init")

        self._main_image_lb = QtW.QLabel()
        self._main_image_pxmp = QPixmap("UI\\render_farming_icon_01.256.png")
        self._main_image_lb.setAlignment(Qt.AlignCenter)

        self._main_image_lb.setPixmap(self._main_image_pxmp)

        self._install_btn = QtW.QPushButton()
        self._install_btn.setText("Install")
        self._install_btn.clicked.connect(self._install_btn_handler)
        self._install_btn.setVisible(False)

        self._uninstall_btn = QtW.QPushButton()
        self._uninstall_btn.setText("Uninstall")
        self._uninstall_btn.clicked.connect(self._uninstall_btn_handler)
        self._uninstall_btn.setVisible(False)

        self._repair_btn = QtW.QPushButton()
        self._repair_btn.setText("Repair")
        self._repair_btn.clicked.connect(self._upgrade_btn_handler)
        self._repair_btn.setVisible(False)

        self._upgrade_btn = QtW.QPushButton()
        self._upgrade_btn.setText("Upgrade")
        self._upgrade_btn.clicked.connect(self._upgrade_btn_handler)
        self._upgrade_btn.setVisible(False)

        self._cancel_btn = QtW.QPushButton()
        self._cancel_btn.setText("Cancel")
        self._cancel_btn.clicked.connect(self._cancel_btn_handler)

        self.setLayout(self._main_layout)

        self._main_layout.addLayout(self._installer_btn_layout)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._installer_btn_layout.addWidget(self._main_image_lb)
        self._installer_btn_layout.addWidget(self._install_lb)
        self._installer_btn_layout.addWidget(self._install_btn)
        self._installer_btn_layout.addWidget(self._uninstall_btn)
        self._installer_btn_layout.addWidget(self._upgrade_btn)
        self._installer_btn_layout.addWidget(self._repair_btn)
        self._installer_btn_layout.insertStretch(-1, 0)
        self._main_layout.addWidget(self._cancel_btn)

    def set_upgrade(self):
        self._install_lb.setText("RenderFarming Upgrade Installer")
        self._upgrade_btn.setVisible(True)
        self._install_btn.setVisible(False)
        self._uninstall_btn.setVisible(False)
        self._repair_btn.setVisible(False)

    def set_install(self):
        self._install_lb.setText("RenderFarming Installer")
        self._upgrade_btn.setVisible(False)
        self._install_btn.setVisible(True)
        self._uninstall_btn.setVisible(False)
        self._repair_btn.setVisible(False)

    def set_uninstall(self):
        self._install_lb.setText("RenderFarming Uninstaller")
        self._upgrade_btn.setVisible(False)
        self._install_btn.setVisible(False)
        self._uninstall_btn.setVisible(True)
        self._repair_btn.setVisible(True)

    def _install_btn_handler(self):
        self.install.emit()

    def _uninstall_btn_handler(self):
        self.uninstall.emit()

    def _cancel_btn_handler(self):
        self.cancel.emit()

    def _upgrade_btn_handler(self):
        self.upgrade.emit()


class InstallerProgressPage(QtW.QWidget):
    close = Signal()

    def __init__(self):
        super(InstallerProgressPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._progress_bar_layout = QtW.QVBoxLayout()

        self._close_btn = QtW.QPushButton()
        self._close_btn.setText("Close")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._close_btn_handler)

        self._progress_bar = QtW.QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setTextVisible(False)

        self._main_lb = QtW.QLabel()
        self.set_install()
        self._task_lb = QtW.QLabel()
        self._task_lb.setText(str())

        self.setLayout(self._main_layout)

        self._main_layout.addLayout(self._progress_bar_layout)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._progress_bar_layout.addWidget(self._main_lb)
        self._progress_bar_layout.addWidget(self._progress_bar)
        self._progress_bar_layout.addWidget(self._task_lb)
        self._progress_bar_layout.insertStretch(-1, 0)
        self._main_layout.addWidget(self._close_btn)

    def _close_btn_handler(self):
        self.close.emit()

    def get_progress_bar(self):
        return self._progress_bar

    def set_complete(self):
        self._progress_bar.setValue(self._progress_bar.maximum())
        self._close_btn.setEnabled(True)
        self._main_lb.setText("Complete!")
        self._task_lb.setText(str())

    def set_install(self):
        self._main_lb.setText("Installing:")

    def set_uninstall(self):
        self._main_lb.setText("Uninstalling:")

    @Slot(int)
    def set_tasks(self, task_number):
        if task_number > 0:
            self._progress_bar.setTextVisible(True)
            self._progress_bar.setRange(0, task_number)
        else:
            self._progress_bar.setTextVisible(False)
            self._progress_bar.setRange(0, 0)

    @Slot(int)
    def add(self, num=1):
        self._progress_bar.setValue(self._progress_bar.value() + num)

    @Slot(str)
    def print_error(self, message):
        self._task_lb.setText(message)
        self._main_lb.setText("ERROR!")
        self._close_btn.setEnabled(True)

    def set_status(self, status):
        self._task_lb.setText(status)


# ---------------------------------------------------
#                     Exceptions
# ---------------------------------------------------


class ManifestError(Exception):
    """
    Exception raised for errors in the Manifest List.
    :attribute message: explanation of the error
    """

    def __init__(self, message):
        fatal_error = "This is a Fatal Error and the Installer will not continue."
        self.message = "{0}  {1}".format(message, fatal_error)

    def __str__(self):
        return str(self.message)


if __name__ == "__main__":
    main()
