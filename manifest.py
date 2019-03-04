import os
import zipfile


class ManifestTranslator:
    """
    Translates the raw manifest file to a list of InstallerItem objects
    """
    def __init__(self, directory, manifest):
        self._man = manifest
        self._man.read()
        self._tmp = os.path.join(directory.get_hashed_temp(), "install")
        self._wd = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self._item_list = list()

        self._token_dict = directory.get_tokens()

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
            spl_dst = (spl[1]).replace('\"', '')
            if len(spl_dst) > 0:
                if spl_dst[0] is '$':
                    dst = self._expand_token(spl_dst)
                else:
                    dst = spl_dst
            else:
                dst = spl[1]

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
            exp = self._token_dict[token]
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
