import os
import ConfigParser
import shutil
import sys
import time

from renderFarmingClasses import TokenizedString
from _version import __version__


class Configuration:
    # Class for working with Configuration file present in the
    # %LOCALAPPDATA%/Autodesk\3dsMax\2018 - 64bit\ENU\scripts\BDF\renderFarming/ folder

    def __init__(self, default=False):
        self._Config = ConfigParser.ConfigParser()

        self._default = default

        # Locating the config file

        self._configFile = 'renderFarmingConfig'
        self._defaultConfigFile = 'rFDefault'
        self._directory = os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax',
                                                        '2018 - 64bit', 'ENU', 'scripts', 'BDF', 'config'))

        # Environment set up

        self._username = os.getenv('username')

        self._version = __version__

        # Reading Config from Disk

        self._read_config()

        # Project Related Variables

        self._defaultOptions = self._config_by_section("project")

        # NetRender Variables

        self._netRenderOptions = self._config_by_section("netrender")

        # Logging Variables

        self._loggingOptions = self._config_by_section("logging")

        # Path Variables

        self._pathOptions = self._config_by_section("paths")

    def _read_config(self, attempts=0):
        """
        Reads the Config File from the Appdata Directory.
        Will initiate creation of this file if it is found not to exist
        :param attempts: Recursive depth limit
        :return: None
        """
        config_path = os.path.join(self._directory, "{0}_{1}.ini".format(self._configFile, self._version))

        if not os.path.isfile(config_path):
            self._create_default_config(self._directory,
                                        self._defaultConfigFile,
                                        self._configFile,
                                        self._version)
        try:
            self._Config.read(config_path)
        except IOError as e:
            if attempts > 2:
                sys.exit("IO Error, Failed to read default config: {}".format(e))
            else:
                print("IO Error, Failed to read default config: {} \n Attempting to load again...".format(e))
                self._read_config(attempts + 1)

    # noinspection PyMethodMayBeStatic
    def _create_default_config(self, directory, default_config_file, working_config_file, version):
        """
        Copies the the Config file to the specified directory
        :param directory: The path to the Appdata Folder
        :param default_config_file: The name of the default file
        :param working_config_file: The name to be assigned to the working config file
        :param version: The version number
        :return: None
        """
        try:
            if not os.path.isdir(directory):
                os.makedirs(directory)
            location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
            shutil.copy2(os.path.join(location, "{0}.ini".format(default_config_file)),
                         os.path.join(directory, "{0}_{1}.ini".format(working_config_file, version)))
        except IOError as e:
            print("IO Error, Failed to create default config: {}".format(e))
            raise
        except os.error as e:
            print("Error, Failed to create default config: {}".format(e))
            raise

    # From the python wiki: https://wiki.python.org/moin/ConfigParserExamples
    # returns a dict representing the sections given

    def _config_by_section(self, section):
        """
        Reads the Config by specified section
        :param section: The section which data is trying to be read from
        :return: A dictionary of all data in the section
        """
        config_dict = {}
        options = self._Config.options(section)
        for o in options:
            try:
                config_dict[o] = self._Config.get(section, o)
                if config_dict[o] == -1:
                    print("skip: {}".format(o))
            except KeyError as e:
                print("exception on {0}:\n{e!".format(o, e))
                config_dict[o] = None
        return config_dict

    def _expand_tokens(self, path):
        """
        Expands tokens within a string, token format is ${section:option} and should return the value
        :param path: The string with tokens in it
        :return: The expanded string
        """
        if '$' in path:
            ts = TokenizedString(path, self)
            return ts.get_expanded()
        else:
            return path

    def _set_config_by_section(self, section, option, value):
        """
        Allows for the config data to altered by the user
        :param section: The section to be written
        :param option: The option to be written in that section
        :param value: The value to be written to that Option
        :return: None
        """
        self._Config.set(section, option, value)

    def _save_config(self):
        """
        Config alterations happens in memory, and then this function must be
        called to write in to the config file on disk
        :return: True for success, False for failure
        """
        fullname = os.path.join(self._directory, "{0}_{1}.ini".format(self._configFile, self._version))
        try:
            f = open(fullname, 'w')
            self._Config.write(f)
            f.close()
            return True
        except IOError as e:
            print("IO Error, Failed to save config: {}".format(e))
            return False

    # noinspection PyMethodMayBeStatic
    def _verify_dir(self, directory):
        """
        Verifies that a folder exists and creates it if it doesn't
        :param directory: The path to the folder to be verified
        :return: True for success, False for failure
        """
        try:
            if not os.path.isdir(directory):
                os.makedirs(directory)
            return True
        except IOError as e:
            print("IO Error, Failed to create directory: {}".format(e))
            return False
        except os.error as e:
            print("Error, Failed to create directory: {}".format(e))
            return False

    # ---------------------------------------------------
    #                       Getters
    # ---------------------------------------------------

    def get_config_by_section(self, section, option):
        """
        Wrapper for _config_by_section
        :param section: The section which data is trying to be read from
        :param option: The option within that section
        :return: The value recorded for that option
        """
        return self._config_by_section(section)[option]

    def _get_path_option(self, section, option, raw=False):
        path = self._Config.get(section, option)
        if not raw:
            path = self._expand_tokens(path)
        return os.path.normpath(path)

    def get_project_code(self):
        return self._Config.get("project", "code")

    def get_project_full_name(self):
        return self._Config.get("project", "full_name")

    def get_working_path(self):
        return os.path.join(self.get_projects_path(), self.get_project_code())

    def get_projects_path(self, raw=False):
        return self._get_path_option("paths", "projects_directory", raw)

    def get_log_path(self, raw=False):
        return self._get_path_option("paths", "log_directory", raw)

    def get_frames_path(self, raw=False):
        return self._get_path_option("paths", "frames_directory", raw)

    def get_light_cache_path(self, raw=False):
        return self._get_path_option("paths", "irradiance_cache_directory", raw)

    def get_irradiance_cache_path(self, raw=False):
        return self._get_path_option("paths", "light_cache_directory", raw)

    def get_log_level(self):
        return self._Config.get("logging", "level")

    def get_version(self):
        return self._version

    def get_log_file(self):
        log_name = "{0}-renderFarming_v{1}-{2}-{3}-{4}.log".format(time.strftime("%y%m%d"),
                                                                   self.get_version(),
                                                                   self.get_project_code(),
                                                                   self._username,
                                                                   time.strftime("%H.%M.%S"))
        log_folder_path = self.get_log_path(False)
        self._verify_dir(log_folder_path)

        return os.path.join(log_folder_path, log_name)

    def get_net_render_manager(self):
        return self._Config.get("netrender", "manager")

    def get_user_scripts_path(self):
        return self._get_path_option("paths", "user_scripts", True)

    def get_interface_setting(self, option, get_type=0):
        """
        Gets entries from the interface section which is not directly managed like the rest
        :param option: String: the name of the option
        :param get_type: Integer: the type of data
            -0: Raw
            -1: an integer
            -2 a float
            -3 a bool
        :return: the data contained in the specified option
        """
        defaults = {
            0: "",
            1: 0,
            2: 0.0,
            3: False
        }
        try:
            if get_type is 1:
                return self._Config.getint("interface", option)
            elif get_type is 2:
                return self._Config.getfloat("interface", option)
            elif get_type is 3:
                return self._Config.getboolean("interface", option)
            else:
                return self._Config.get("interface", option)
        except ConfigParser.NoOptionError:
            data = defaults.get(get_type, 0)
            self._Config.set("interface", option, data)
            return data

    def __str__(self):
        cfg_str = ""
        cfg_array = list()

        cfg_array.append(self.get_project_code())
        cfg_array.append(self.get_project_full_name())

        cfg_array.append(self.get_projects_path())
        cfg_array.append(self.get_frames_path())
        cfg_array.append(self.get_irradiance_cache_path())
        cfg_array.append(self.get_light_cache_path())
        cfg_array.append(self.get_log_path())

        cfg_array.append(self.get_net_render_manager())

        cfg_array.append(self.get_log_level())

        for i in cfg_array:
            cfg_str = "{0}{1}\n".format(cfg_str, i)

        return cfg_str

    # ---------------------------------------------------
    #                 Command Wrappers
    # ---------------------------------------------------

    def save_config(self):
        """
        Wrapper for _save_config()
        :return: True for success, False for failure
        """
        return self._save_config()

    # ---------------------------------------------------
    #                       Setters
    # ---------------------------------------------------

    def set_max_system_directories(self, rt):
        """
        Gets some environment variables from max and saves them for future use
        :param rt: The PYMXS runtime environment
        :return:
        """
        user_scripts = os.path.realpath(rt.getDir(rt.name('userScripts')))
        self._set_user_scripts_path(user_scripts)
        self._save_config()

    def set_project_code(self, code):
        self._set_config_by_section("project", "code", code)

    def set_project_full_name(self, name):
        self._set_config_by_section("project", "full_name", name)

    def set_projects_path(self, path):
        self._set_config_by_section("paths", "projects_directory", path)

    def set_log_path(self, path):
        self._set_config_by_section("paths", "log_directory", path)

    def set_log_level(self, level):
        self._set_config_by_section("logging", "level", level)

    def set_net_render_manager(self, manager):
        self._set_config_by_section("netrender", "manager", manager)

    def set_frames_path(self, path):
        self._set_config_by_section("paths", "frames_directory", path)

    def set_light_cache_path(self, path):
        self._set_config_by_section("paths", "light_cache_directory", path)

    def set_irradiance_cache_path(self, path):
        self._set_config_by_section("paths", "irradiance_cache_directory", path)

    def _set_user_scripts_path(self, path):
        self._set_config_by_section("paths", "user_scripts", path)

    def set_interface_setting(self, option, value):
        return self._set_config_by_section("interface", option, value)


# config = Configuration()
#
# print (config.get_projects_path())
# print (config.get_irradiance_cache_path())
# print (config)
# print('* ' * 20)
#
# config.set_project_code('_best')
# config.save_config()
#
# print (config.get_irradiance_cache_path())
# print (config)
# print('* ' * 20)
