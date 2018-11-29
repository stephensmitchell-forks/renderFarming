import ctypes
import sys
import os
import shutil
import _winreg
import zipfile

import PySide2.QtWidgets as QtW
from PySide2.QtCore import Signal, Slot, Qt, QThread
from PySide2.QtGui import QPixmap, QMovie, QIcon
from tempfile import gettempdir


def is_admin():
    """
    Checks if the script is running with administrator uac privileges
    :return: Boolean of admin status
    """
    if "--admin-ignore" in sys.argv:
        return True
    else:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as error:
            print("Unable to retrieve UAC Elevation level: %s" % error)
            return False


def main():
    """
    Main, runs on execution
    :return: None
    """
    # Checks if the script has elevated privileges
    if is_admin():
        run_q_app()
    else:
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__), None, 1)


def run_q_app():
    """
    Function for starting the Q Application
    :return: None
    """
    app = QtW.QApplication(sys.argv)
    w = RenderFarmingInstallerMainWindow()
    w.show()
    app.exec_()


# noinspection PyBroadException
def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    By Stack Overflow user max: https://stackoverflow.com/users/1889973/max
    From: https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # noinspection PyProtectedMember,PyUnresolvedReferences
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# ---------------------------------------------------
#                Installer Classes
# ---------------------------------------------------


class DirectoryLocator:
    """
    Class For locating directories
    Uses registries to find the 3ds Max directory
    """
    max_version_dict = {"2018": "20.0", "2019": "21.0"}

    def __init__(self, max_version="2018"):

        self._max_version = max_version

        self._temp = os.path.join(gettempdir(), "RenderFarming")
        self._hashed_temp = os.path.join(self._temp, '{}'.format(hash(os.times())))

        self._appdata_dir = os.getenv('LOCALAPPDATA')
        self._max_dir = self._find_max_dir()

        self._dev_check()

        self._enu_dir = self._find_enu_dir()

        self._user_macros = self._find_user_macros_dir()
        self._user_scripts = self._find_user_scripts_dir()
        self._user_startup = self._find_user_startup_dir()

        self._bdf_dir = os.path.join(self._user_scripts, "BDF")
        self._install_dir = os.path.join(self._bdf_dir, "renderFarming")
        self._config = os.path.join(self._bdf_dir, "logs")
        self._logs = os.path.join(self._bdf_dir, "config")

        self._light_icons, self._dark_icons = self._find_icons()

        self._unprotected = self._find_unprotected()

    def _find_max_dir(self):
        """
        Finds the directory that 3ds Max is installed in
        :return: STR: A Path
        """
        # Locates the max directory using the autodesk Registry keys
        key_str = "Software\\Autodesk\\3dsMax\\{}".format(self.max_version_dict.get(self._max_version, "20.0"))
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, key_str)
        value = _winreg.QueryValueEx(key, "Installdir")[0]
        key.Close()
        if os.path.isdir(value):
            return value
        else:
            # If the registry leads you astray, it will default back to the good old default install
            default = "C:\\Program Files\\Autodesk\\3ds Max {}\\".format(self._max_version)
            # Doesn't hurt to be sure
            if os.path.isdir(default):
                return default
            else:
                raise RuntimeError(
                    "3ds Max does not appear to be installed.  3ds Max must be installed before RenderFarming"
                )

    def _dev_check(self):
        """
        Checks if the installer is in dev mode
        :return: sets the appdata path and 3ds Max path to be located in the temp folder
        """
        # Lets things safely be copied without deleting important files
        # if "--dev" in sys.argv:
        if "--dev" in sys.argv:
            print("DEV:")
            save = self._max_dir, self._appdata_dir

            new_max = os.path.join(self._temp, (os.path.splitdrive(self._max_dir)[1])[1:])
            new_appdata = os.path.join(self._temp, (os.path.splitdrive(self._appdata_dir)[1])[1:])

            self._max_dir = new_max
            self._appdata_dir = new_appdata

            print("{} ~becomes~ {}".format(save[0], self._max_dir))
            print("{} ~becomes~ {}".format(save[1], self._appdata_dir))

    def _find_enu_dir(self):
        """
        Finds the English language folder in the 3ds Max LOCALAPPDATA folder
        :return: STR: A Path
        """
        return os.path.realpath(os.path.join(self._appdata_dir,
                                             'Autodesk',
                                             '3dsMax',
                                             '{} - 64bit'.format(self._max_version),
                                             'ENU'))

    def _find_unprotected(self):
        """
        Generates a list of directories that are allowed to be deleted
        :return: a List
        """
        unprotected = list()
        unprotected.append(self._dark_icons)
        unprotected.append(self._light_icons)
        unprotected.append(self._config)
        unprotected.append(self._logs)
        unprotected.append(self._bdf_dir)
        unprotected.append(self._install_dir)
        unprotected.append(self._user_macros)
        unprotected.append(os.path.join(self._hashed_temp, "install"))
        return unprotected

    def _find_user_macros_dir(self):
        """
        Finds the user Macros folder
        :return: STR: A Path
        """
        return os.path.realpath(os.path.join(self._enu_dir, 'usermacros'))

    def _find_user_scripts_dir(self):
        """
        Finds the user Scripts folder
        :return: STR: A Path
        """
        return os.path.realpath(os.path.join(self._enu_dir, 'scripts'))

    def _find_user_startup_dir(self):
        """
        Finds the Startup Scripts Folder
        :return: STR: A Path
        """
        return os.path.realpath(os.path.join(self._enu_dir, 'startup'))

    def _find_icons(self):
        """
        Finds both Icon directories used by RenderFarming
        :return: STR: A Path
        """
        icons_light_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Light", "RenderFarming")
        icons_dark_dir = os.path.join(self._max_dir, "UI_ln", "Icons", "Dark", "RenderFarming")
        return icons_light_dir, icons_dark_dir

    def get_hashed_temp(self):
        return self._hashed_temp

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

    def get_bdf_folder(self):
        return self._bdf_dir

    def get_config_folder(self):
        return self._config

    def get_log_folder(self):
        return self._logs

    def get_unprotected(self):
        return self._unprotected

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
            "Temp Directory": self._hashed_temp,
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
        self._tmp = os.path.join(self._dir.get_hashed_temp(), "install")
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
        offset = len(self._man.get_header())
        for num, line in enumerate(self._man.get_data()):
            self._item_list.append(self._line_to_data(line, offset + num))

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
        # all source objects should be relative to the temp directory
        spl = line.split('|')
        if len(spl) == 2:
            src = spl[0].replace('\"', '')

            if os.path.splitdrive(src)[0] is "":

                src = os.path.join(self._tmp, src)

                # raises an exception if this file is not present in the temp directory
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
        ls = ["***MANIFEST***", self._man.get_filename]
        return ls.append(self._item_list)


class ManifestHeader:
    """
    Converts the Manifest Header to a dictionary
    """
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
        Adds a line of the header to the dictionary
        :param line: A string containing a single line from the Manifest file header
        :param number: The line Number in the file
        :return: Adds a key to the self._data dictionary
        """
        line = line.replace('#', '')
        spl = line.split('|')
        if len(spl) == 2:
            try:
                # Assigns the split pieces using the first part as a key and the second as a value
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

    def __str__(self):
        return str(self.__repr__()).replace(', ', '\n').replace('{', '').replace('}', '').replace('\'', '')

    def __repr__(self):
        return self._data


class Manifest:
    """
    A function for dealing with the creation and reading of ".man" files
    The ".man" file is formatted as follows:
        Each line in the header has a '#' as it's leading character and is treated like a key, value pair
        The key is separated from the value by a pipe '|' character
            Example:
                #key|value
                #version|0020
        The rest of the file is split into sources and destinations
        These are separated with a pipe '|' character as well
            Example:
                "src"|"dst"
                "__init__.py"|$(main)
            "C:\Users\abrown\AppData\Local\Autodesk\3dsMax\2018 - 64bit\ENU\scripts\BDF\renderFarming\__init__.py"|"."
        The source must be a valid file.  The install.man keeps sources as relative files to itself.  The uninstall.man
        keeps the full path.
        The destination can be either an absolute path, or a token.  The tokens must correspond to entries in an
        internal dictionary that correspond to paths from the DirectoryLocator.  The uninstall.man does not use
        destinations, and anything here will be ignored.
            Valid Tokens:
                "$(main)": render farming install
                "$(macro)": user macros
                "$(startup)": user startup
                "$(dark_icons)": dark icons
                "$(light_icons)": light icons
    """

    def __init__(self, manifest_file):
        """
        Constructs a Manifest Object
        :param manifest_file: The filename of the text file containing the manifest or
                              of a zip file with a manifest in it
        """
        self._manifest_file = manifest_file
        self._data = list()
        self._header = list()

        self._is_zip = True if isinstance(self._manifest_file, ZipHandler) else False

    def read(self):
        """
        Reads the manifest file specified
        :return: self._data and self._header are assigned the appropriate lines
        """
        # Zip files need to be read before hand because they need the zip_handler passed to the read function
        if self._is_zip:
            data = self._manifest_file.open_read_lines("install.man")
        else:
            # Checks to make sure there is a file to read from
            if not os.path.exists(self._manifest_file):
                raise ManifestError("Manifest file: {} does not exist.".format(self._manifest_file))
            with open(self._manifest_file, 'r') as man_file:
                data = man_file.readlines()

        self._set_formatted_data(data)

    def write(self):
        """
        Writes the stored data to the file
        :return: a happy little file somewhere on your filesystem
        """
        directory = os.path.split(self._manifest_file)[0]
        # Checks to make sure there is a directory to write to
        if not os.path.isdir(directory):
            raise ManifestError("Manifest Directory: {} does not exist.".format(directory))
        with open(self._manifest_file, 'w') as man_file:
            man_file.write(self._get_formatted_data())

    def _get_formatted_data(self):
        """
        Properly formats the data for file writing.  This is mostly just putting the list into
        one long string and adding newlines
        :return: A string containing the appropriate file contents
        """
        main_str = str()
        # Header
        for line in self._header:
            main_str = main_str + line + '\n'
        # Data
        for line in self._data:
            main_str = main_str + line + '\n'
        return main_str

    def _set_formatted_data(self, data):
        """
        Sets the internal lists to the data read from a file
        :param data: The data to be processed
        :return: self._data and self._header appended with the appropriate data
        """
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

    def get_filename(self):
        return self._manifest_file

    def set_data(self, data_list):
        """
        Converts a list of InstallerItem objects to a list of strings and sets self._data to this new list
        :param data_list: a list of InstallerItem objects
        :return: self._data replaced with the converted data_list
        """
        # clears old data
        self._data = list()
        for i in data_list:
            self._data.append("\"{}\"|\"{}\"".format(i.get_source(), i.get_destination()))

    def set_header(self, header_dict):
        """
            Converts a dictionary to a list of strings and sets self._header to this new list
            :param header_dict: a dictionary containing header data
            :return: self._header replaced with the converted header_dict
            """
        # clears old header
        self._header = list()
        for i in header_dict.keys():
            self._header.append("#{}|{}".format(i, header_dict[i]))

    def add_self(self):
        """
        Adds the manifest file itself to the end of the manifest (Only for uninstall.man)
        :return: self._data appended with the manifest file
        """
        self._data.append("\"{}\"|\"{}\"".format(self._manifest_file, ''))

    def __str__(self):
        ret_str = str()
        for item in self.__repr__():
            ret_str = ret_str + str(item) + '\n'
        return ret_str

    def __repr__(self):
        return self._header + self._data


class InstallerItem:
    """
    A class the contains a source path and a destination path for handling of files
    """
    def __init__(self, source, destination, is_dir=False):
        self._src = source
        self._dst = destination
        self._isDir = is_dir

    def get_source(self):
        return os.path.normpath(self._src)

    def get_destination(self):
        return os.path.normpath(self._dst)

    def get_destination_dir(self):
        """
        :return: the path to a self._src 's directory
        """
        return os.path.normpath(os.path.split(self._dst)[0])

    def get_source_dir(self):
        """
            :return: the path to a self._dst 's directory
            """
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
    :signal print_error: Emits when an error occurs an transmits that error's message
    :signal complete: Emits when the script is completed
    """
    set_tasks = Signal(int)
    add_task = Signal(int)
    print_error = Signal(str)
    complete = Signal()

    def __init__(self, zip_file, dir_loc):
        super(RenderFarmingInstaller, self).__init__()
        self._items = list()
        self._dirs = dir_loc
        self._install_temp = os.path.join(self._dirs.get_hashed_temp(), "install")
        self._zip = zip_file
        self._man = None
        self._man_translated = None
        self._record = list()
        self._dir_del_queue = list()

    def run(self, **kwargs):
        """
        QThread function that executes the class in a separate thread
        :param kwargs:
        :return: None
        """
        install_type = kwargs.get("install_type", "install")
        try:
            self.set_tasks.emit(3)

            # Checks which type of manifest to load
            if install_type == "install":
                # Installs will load the bundled install.man
                self._zip.extract_all(self._install_temp)

                man_path = os.path.join(self._install_temp, "install.man")
                self._man = Manifest(man_path)
            else:
                # Uninstalls will attempt to load the uninstall.man in the installation directory
                man_path = os.path.join(self._dirs.get_render_farming_install(), "uninstall.man")
                self._man = Manifest(man_path)

            self._add()

            # Translates the manifest to InstallerItems
            self._man_translated = ManifestTranslator(self._dirs, self._man)
            self._add()

            # Retrieves these InstallerItems
            self._items = self._man_translated.get_items()
            self._add()

            # Checks which functions to run
            if install_type == "install":
                self.run_installation()
            elif install_type == "upgrade":
                self.run_uninstallation()
            else:
                self.run_uninstallation()
                self.run_cleaner()

        # Catches errors and prints them to the UI rather than crashing
        except (IOError, OSError, RuntimeError, WindowsError, ManifestError) as e:
            self.print_error.emit(str(e))
            print(self._man_translated)
        else:
            # If no Errors, set UI to complete
            self.complete.emit()
        finally:
            # Always terminate the QThread
            self.terminate()

    def run_installation(self):
        self.set_tasks.emit(len(self._items) * 2)

        self._create_directories()
        self._copy_files()
        self._generate_uninstall_manifest()
        self._clean_up_temp_folder()

    def run_uninstallation(self):
        self.set_tasks.emit(len(self._items))

        self._delete_files()

        self._delete_dirs()

    def run_cleaner(self):
        self._clean_up_bdf_folder()

    def _clean_up_bdf_folder(self):
        """
        Deletes files from the logs and config but will back out if it discovers anything from another script
        :return: None
        """
        folders = self._dirs.get_config_folder(), self._dirs.get_log_folder(), self._dirs.get_bdf_folder()
        for fold in folders:
            fold = str(fold)
            # If the folder is empty of files, delete it
            if os.path.isdir(fold):
                if self._clean_up_files(fold, "renderFarming"):
                    self._delete_dir(fold)

    def _clean_up_temp_folder(self):
        """
        Deletes extracted files from the temp folder
        :return: None
        """
        root = self._dirs.get_hashed_temp()
        # If the folder is empty of files, delete it
        if os.path.isdir(root):
            self._nuke_directory(root)

    def _nuke_directory(self, directory):
        # deletes all contained files
        self._clean_up_files(directory)
        children = os.listdir(directory)
        # finds children
        if len(children) > 0:
            for child in children:
                # attempts to recursively nuke delete everything left behind
                path = os.path.join(directory, child)
                if os.path.isdir(path):
                    self._nuke_directory(path)
                    self._delete_dir(path)
        print("os.rmdir({})".format(directory))
        os.rmdir(directory)

    def _clean_up_files(self, directory, del_str=None):
        """
        Cleans all files with a name containing a certain string in the name from a directory
        :param directory: The directory to clean
        :return: True if the directory is empty, False if not
        """
        ret = True
        # Get a list of contents
        children = os.listdir(directory)
        # Check contents
        if len(children) > 0:
            # attempt to delete all of the contents
            for child in children:
                full_path = os.path.join(directory, child)
                # if the object is a directory attempt to delete it
                # If it cannot be deleted
                if os.path.isdir(full_path):
                    a = self._delete_dir(full_path)
                    if not a:
                        ret = False
                # If the object is a file, attempt to remove it
                elif os.path.isfile(full_path):
                    # If del_str is not empty, check for it
                    if del_str is not None:
                        # If del_str is in the filename, can it
                        if child.find(del_str) != -1:
                            print("os.remove({})".format(full_path))
                            os.remove(full_path)
                        # Else, mark the folder to not be deleted
                        else:
                            ret = False
                    # Otherwise, it all must go
                    else:
                        print("os.remove({})".format(full_path))
                        os.remove(full_path)
                # If the object is neither a file not directory, best not to mess around
                else:
                    return False
            # Returns False if a file or directory has not been deleted
            return ret
        # If there are no contents, do nothing
        else:
            return True

    def _generate_uninstall_manifest(self):
        """
        Creates a manifest with a list of files to delete when unintalling
        :return: A file called uninstall.man in the install directory
        """
        self.set_tasks.emit(4)
        new_man = Manifest(os.path.join(self._dirs.get_render_farming_install(), "uninstall.man"))
        self._add()

        new_man.set_data(self._record)
        self._add()

        # Copies the header from the install.man file
        new_head = ManifestHeader(self._man)
        new_man.set_header(new_head.get_data())
        self._add()

        new_man.add_self()

        new_man.write()
        self._add()

    def _create_directories(self):
        """
        Creates directories to accommodate files in the manifest list
        :return: None
        """
        for item in self._items:
            directory = item.get_destination_dir()
            if not os.path.isdir(directory):
                self._create_dir(directory)
            self._add()

    def _create_dir(self, directory, original=None, depth=0):
        """
        Recursively creates a directory and records it
        :param directory: Which directory to create
        :return: Records which directory was created for the uninstall.man list
        """
        # Infinite loop prevention
        max_depth = 130
        if depth >= max_depth:
            raise RuntimeError("{}\n{}\n{}\n{}".format("The folder creation recursion depth has exceeded the limit.",
                                                       "This is Fatal and the installer cannot continue.",
                                                       "Current Folder: {}".format(directory),
                                                       "Original Folder: {}".format(original)
                                                       ))
        # If the directory exists, do nothing.
        if not os.path.isdir(directory):
            parent = os.path.split(directory)[0]
            # If the directory's parent exists, make the directory.
            if os.path.isdir(parent):
                # record making it for later deletion.
                self._record.append(InstallerItem(directory, '', True))
                # Remove this print later
                print("os.makedirs({})".format(directory))

                os.makedirs(directory)

                # If the directory is not the top level requested originally, then the function must recur.
                if depth != 0:
                    self._create_dir(original, None, 0)

            # If the directory's parent does not exist, the parent has to be made as well.
            else:
                # If this is the first run, then the directory needs to be copied into "original"
                # because it is otherwise set to None.
                if depth == 0:
                    original = directory
                depth += 1
                self._create_dir(parent, original, depth)

    def _copy_files(self):
        """
        Uses shutil.copy2 to copy items form the manifest list
        :return: Records which file was copied for the uninstall.man list
        """
        for item in self._items:
            src = os.path.join(item.get_source())
            dst = os.path.join(item.get_destination())
            print("shutil.copy2({}, {})".format(src, dst))

            shutil.copy2(src, dst)

            # Records the files that have been copied
            self._record.append(InstallerItem(dst, ''))
            self._add()

    def _delete_files(self):
        """
        Uses os.remove to delete all files from the manifest list
        :return: None
        """
        for item in self._items:
            file_name = item.get_source()
            if os.path.isfile(file_name):
                # Only deletes files in unprotected directories
                # These are pre-defined by the installer
                if self._check_protected(item.get_source_dir()):
                    print("os.remove({})".format(file_name))
                    os.remove(file_name)

                    # Checks for Python Bytecode files and deletes them as well
                    spl = os.path.splitext(file_name)
                    if spl[1] == '.py':
                        # Split the extension off and rejoin to a different extension
                        pyc = spl[0] + '.pyc'
                        # Only delete them if they exist though
                        if os.path.isfile(pyc):
                            print("os.remove({})".format(pyc))
                            os.remove(pyc)
            # if the file is directory, put it on the queue
            elif os.path.isdir(file_name):
                self._dir_del_queue.append(item)
            self._add()

    def _delete_dirs(self):
        for item in self._dir_del_queue:
            directory = item.get_source()

            self._delete_dir(directory)

    def _check_protected(self, directory):
        """
        Verifies that the directory is safe to be deleted
        :param directory: a path
        :return: False for protected, True for safe to delete
        """
        protect = self._dirs.get_unprotected()
        if directory in self._dirs.get_unprotected():
            return True
        else:
            # Checks if the parent is an unprotected directory
            for item in protect:
                if directory.find(item) != -1:
                    return True
                return False

    def _delete_dir(self, directory):
        """
        Recursively creates a directory and records it
        :param directory: Which directory to create
        :return: Records which directory was created for the uninstall.man list
        """
        # No need to fool around with non-existent directories
        if os.path.isdir(directory):
            if self._check_protected(directory):
                children = os.listdir(directory)
                # If the directory has children, delete them first
                if len(children) > 0:
                    # delete each child
                    for child in children:
                        child_path = os.path.join(directory, child)
                        # Only mess with directories, any files should already be cleaned up
                        if os.path.isdir(child_path):
                            # If the child is a directory, recur the function upon it
                            if not self._delete_dir(child_path):
                                return False
                        # If the children are files or anything other, do not delete the folder
                        else:
                            return False
                    # When done with the children, delete the directory
                    print("os.rmdir({})".format(directory))
                    os.rmdir(directory)
                # If there are no children, delete the directory
                else:
                    print("os.rmdir({})".format(directory))
                    os.rmdir(directory)
            # If the directory is protected, don't delete it
            else:
                return False
        # If the directory doesn't exist, do nothing.
        else:
            return True

    def _add(self):
        # Shortened function for emitting task complete messages
        self.add_task.emit(1)


class ZipHandler:
    def __init__(self, zip_file):
        self._zip_file = zip_file

    def extract_file(self, file_name, destination):
        with zipfile.ZipFile(self._zip_file, 'r') as open_zip:
            open_zip.extract(file_name, destination)

    def extract_all(self, destination):
        with zipfile.ZipFile(self._zip_file, 'r') as open_zip:
            open_zip.extractall(destination)

    def open_read_lines(self, file_name):
        """
        Opens a file from the zip file and reads the lines
        :param file_name: the Zip file to open
        :return: the contents of the zip file
        """
        with zipfile.ZipFile(self._zip_file, 'r') as open_zip:
            with open_zip.open(file_name, 'r') as f:
                return f.readlines()

    def get_filename(self):
        return self._zip_file


# ---------------------------------------------------
#                  User Interface
# ---------------------------------------------------


class RenderFarmingInstallerMainWindow(QtW.QDialog):

    def __init__(self, parent=None):
        super(RenderFarmingInstallerMainWindow, self).__init__(parent)
        self._zip = ZipHandler(resource_path('install.zip'))
        self._max_version = "2018"
        self._dirs = DirectoryLocator(self._max_version)
        self._busy = False

        self._style_sheet = str()

        self.setWindowIcon(QIcon(resource_path("UI\\render_farming_icon_01.48.png")))
        with open(resource_path("UI\\installerStyle.qss"), 'r') as sheet:
            self._style_sheet = sheet.read()
        self.setStyleSheet(self._style_sheet)

        self._main_layout = QtW.QVBoxLayout()

        self._intro_page = InstallerIntroPage()
        self._intro_page.install.connect(self.install_handler)
        self._intro_page.cancel.connect(self.reject)
        self._intro_page.upgrade.connect(self.upgrade_handler)
        self._intro_page.uninstall.connect(self.uninstall_handler)

        self._rf_versions = self.old_version_check()

        self.setWindowTitle("RenderFarming{}".format(self._rf_versions[0]))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setSizeGripEnabled(False)

        self._progress_bar_page = InstallerProgressPage()
        self.progress_bar = self._progress_bar_page

        self._progress_bar_page.setVisible(False)
        self._progress_bar_page.close.connect(self.close)
        self._progress_bar_page.allow_close.connect(self._allow_close_handler)

        self._main_layout.addWidget(self._intro_page)
        self._main_layout.addWidget(self._progress_bar_page)

        self.setLayout(self._main_layout)

        self._installer = RenderFarmingInstaller(self._zip, self._dirs)
        self._installer.set_tasks.connect(self._progress_bar_page.set_tasks)
        self._installer.add_task.connect(self._progress_bar_page.add)
        self._installer.print_error.connect(self._progress_bar_page.print_error)
        self._installer.complete.connect(self._progress_bar_page.set_complete)

        self._admin_check()

    def install_handler(self):
        self._busy = True
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._installer.run(install_type="install")

    def uninstall_handler(self):
        self._busy = True
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._progress_bar_page.set_uninstall()
        self._installer.run(install_type="uninstall")

    def upgrade_handler(self):
        self._busy = True
        self._intro_page.setVisible(False)
        self._progress_bar_page.setVisible(True)
        self._progress_bar_page.set_uninstall()
        self._installer.run(install_type="upgrade")
        self._progress_bar_page.set_install()
        self._installer.run(install_type="install")

    def old_version_check(self):
        u_man_path = os.path.join(self._dirs.get_render_farming_install(), "uninstall.man")
        man = Manifest(self._zip)
        man.read()
        head = ManifestHeader(man)

        if os.path.isfile(u_man_path):
            u_man = Manifest(u_man_path)
            u_man.read()
            u_head = ManifestHeader(u_man)

            if u_head.version() < head.version():
                self._intro_page.set_upgrade()
            elif u_head.version() == head.version():
                self._intro_page.set_uninstall()
            else:
                self._intro_page.set_old_version()
            return head.version(), u_head.version()
        else:
            self._intro_page.set_install()
            return head.version(), "0000"

    def _admin_check(self):
        if not is_admin():
            self._intro_page.admin_error()

    def _allow_close_handler(self):
        self._busy = False

    def closeEvent(self, event):
        if self._busy:
            event.ignore()
        else:
            event.accept()


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
        self._main_image_pxmp = QPixmap(resource_path("UI\\render_farming_icon_01.256.png"))
        self._main_image_lb.setAlignment(Qt.AlignCenter)

        self._main_image_lb.setPixmap(self._main_image_pxmp)

        self._install_btn = QtW.QPushButton()
        self._install_btn.setText("INSTALL")
        self._install_btn.clicked.connect(self._install_btn_handler)
        self._install_btn.setVisible(False)

        self._uninstall_btn = QtW.QPushButton()
        self._uninstall_btn.setText("UNINSTALL")
        self._uninstall_btn.clicked.connect(self._uninstall_btn_handler)
        self._uninstall_btn.setVisible(False)

        self._repair_btn = QtW.QPushButton()
        self._repair_btn.setText("REPAIR")
        self._repair_btn.clicked.connect(self._upgrade_btn_handler)
        self._repair_btn.setVisible(False)

        self._upgrade_btn = QtW.QPushButton()
        self._upgrade_btn.setText("UPGRADE")
        self._upgrade_btn.clicked.connect(self._upgrade_btn_handler)
        self._upgrade_btn.setVisible(False)

        self._cancel_btn = QtW.QPushButton()
        self._cancel_btn.setText("CANCEL")
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

    def admin_error(self):
        self._install_btn.setEnabled(False)
        self._uninstall_btn.setEnabled(False)
        self._repair_btn.setEnabled(False)
        self._upgrade_btn.setEnabled(False)
        self._install_lb.setText("{} Installer requires administrator privileges.".format(tx_er("Error:")))


class InstallerProgressPage(QtW.QWidget):
    allow_close = Signal()
    close = Signal()

    def __init__(self):
        super(InstallerProgressPage, self).__init__()

        self._main_layout = QtW.QVBoxLayout()
        self._progress_bar_layout = QtW.QVBoxLayout()

        self._close_btn = QtW.QPushButton()
        self._close_btn.setText("CLOSE")
        self._close_btn.setEnabled(False)
        self._close_btn.clicked.connect(self._close_btn_handler)

        self._main_image_lb = QtW.QLabel()
        self._main_gif_mov = QMovie(resource_path("UI\\dog_haircut.gif"))
        self._main_image_lb.setAlignment(Qt.AlignCenter)

        self._main_image_lb.setMovie(self._main_gif_mov)
        self._main_gif_mov.start()

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
        self._progress_bar_layout.addWidget(self._main_image_lb)
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
        self.allow_close.emit()

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
        self._main_lb.setText(tx_er("ERROR!"))
        self._close_btn.setEnabled(True)
        self._main_gif_mov.setPaused(True)
        self.allow_close.emit()

    def set_status(self, status):
        self._task_lb.setText(status)


def tx_er(text):
    return html_color_text(text, "red")


def html_color_text(text, color):
    presets = {"Orange": "#FFA500", "Red": "#ff3232", "Green": "#4ca64c"}
    if color in presets:
        hex_code = presets[color]
    else:
        hex_code = color
    return " <font color=\"{1}\">{0}</font>".format(text, hex_code)


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
