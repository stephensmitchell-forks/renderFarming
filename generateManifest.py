import os
import sys
import re
from manifest import Manifest, InstallerItem


def main():
    script_dir = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

    # Source code path
    src = os.path.realpath(sys.argv[1])
    if not os.path.isdir(src):
        raise TypeError("Must have a valid directory as an argument")

    # The directory that the script is writing to
    manifest_dir = str()
    # if a directory is not provided, the script will write to it's own directory
    if len(sys.argv) > 2:
        os.path.realpath(sys.argv[2])
    else:
        manifest_dir = script_dir
    if not os.path.isdir(manifest_dir):
        raise TypeError("If a second argument is provided, it must be a valid directory")

    record = gather_records(src)

    generate_manifest(record, manifest_dir, get_version(src))


def generate_manifest(record, directory, version):
    """
    Generates the manifest file and writes it to the specified directory
    :param record: The data being written to the manifest file: A list of InstallerItem objects
    :param directory: The directory to write to: String
    :param version: The version number from _version.py: String
    :return: None
    """
    new_man = Manifest(os.path.join(directory, "install.man"))

    new_man.set_data(record)

    # Copies the header from the install.man file
    new_man.set_header({"version": version})

    new_man.write()


def get_version(directory):
    """
    Gets the version from the _version.py file in the source code
    :param directory: the directory in which the _version.py file is located
    :return: the version number as a string
    """
    ver_file = os.path.join(directory, "_version.py")

    if not os.path.isfile(ver_file):
        raise IOError("_version.py file not found")

    # from https://stackoverflow.com/a/7071358
    # adapted to fit my coding style
    with open(ver_file, "rt") as vf:
        version_string_line = vf.read()

    pattern = r"^__version__ = ['\"]([^'\"]*)['\"]"
    capture_group = re.search(pattern, version_string_line, re.M)

    if capture_group:
        return capture_group.group(1)
    else:
        raise RuntimeError("Unable to find version string in {}.".format(ver_file))


def gather_records(directory):
    files = collect_files(directory)
    record = list()

    for fl in files:
        dst = destination_from_folder(fl)
        record.append(InstallerItem(fl, dst, False))

    return record


def destination_from_folder(filename):
    spl = os.path.split(filename)

    if spl[0] is str():
        return "$(main)"
    else:
        return "$({})".format(spl[0])


def collect_files(directory):
    children = os.listdir(directory)

    # sorts children into files and directories

    files = list()
    directories = list()

    for ch in children:
        child_path = os.path.join(directory, ch)
        if os.path.isdir(child_path):
            directories.append(ch)
        else:
            files.append(ch)

    # searches directories for files

    for dr in directories:
        dir_path = os.path.join(directory, dr)
        children = collect_files(dir_path)

        for ch in children:
            files.append(os.path.join(dr, ch))

    return files


if __name__ == "__main__":
    main()
