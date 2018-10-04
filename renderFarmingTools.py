import os
import logging

mlg = logging.getLogger("renderFarming.Tools")

# ---------------------------------------------------
#                     Utilities
# ---------------------------------------------------


def str_to_dir(path):
    """
    Converts a string of a file system path to an os.path
    :param path: A string containing the Path to be converted
    :return: An os.path for the string
    """

    dir_list = path.split('/')

    dir_joined = ''

    for l in dir_list:
        dir_joined = os.path.join(dir_joined, l)

    return dir_joined


def html_color_text(text, color):
    presets = {"Orange": "#FFA500", "Red": "#ff3232", "Green": "#4ca64c"}
    if color in presets:
        hex_code = presets[color]
    else:
        hex_code = color
    return " <font color=\"{1}\">{0}</font>".format(text, hex_code)


def verify_dir(directory):
    """
    Verifies that a folder exists and creates it if it doesn't
    :param directory: The path to the APPDATA Folder
    :return: True for success, False for failure
    """

    flg = logging.getLogger("renderFarming.Tools.verify_dir")

    flg.debug("Verifying Directory: {}".format(directory))

    try:
        if not os.path.isdir(directory):
            flg.debug("Directory does not exist, creating now.")
            os.makedirs(directory)
        else:
            flg.debug("Directory Exists!")
        return True
    except IOError as e:
        flg.error("IO Error, Failed to create default config: {}".format(e))
        return False
    except os.error as e:
        flg.error("Error, Failed to create default config: {}".format(e))
        return False


def verify_vray(rt):
    """
    Checks that VRay is the current render engine and sets it if it is not
    :param rt: An instance of the MaxScript Runtime Environment
    :return: True for success, False for failure
    """
    renderer = rt.renderers.current
    flg = logging.getLogger("renderFarming.Tools.verify_VRay")

    name_string = str(renderer)

    flg.debug("Render Engine is {}".format(name_string.split(':')[1]))

    if "V_Ray_Adv" in name_string:
        return True
    else:
        rc = rt.RendererClass.classes
        renderer_list = list(rc)
        index = -1
        for i in range(0, len(renderer_list)):
            if "V_Ray_Adv" in str(renderer_list[i]):
                index = i
        if index < 0:
            return False
        try:
            rt.renderers.current = rc[index]()
        except IndexError:
            flg.error("VRay not loaded, Unable to continue")
            return False
        flg.debug("Renderer set to {0}".format(str(rt.renderers.current).split(':')[1]))
        return True


def calculate_increment_padding(start, end, increment):
    length = end - start
    last_inc_length = length % increment
    if last_inc_length is 0:
        return end
    else:
        last_increment_start = end - last_inc_length
        new_end = last_increment_start + increment
        return new_end


def clean_title(title):
    """
    Give a version of a string that has underscores replaced with spaces and title case applied
    :param title: A title in it's raw form
    :return: A cleaned up title
    """
    title = title.replace('_', ' ')
    return title.title()


def match_prefix(file_name, code, html=True):
    """
    Checks if a filename has the same prefix code as the configuration
    :param file_name: the max file name
    :param code: the prefix code
    :param html: Whether or not to return an html string
    :return: A String with the warning message or nothing
    """
    ind = file_name.find('_')
    prefix = file_name[:ind]

    if code != prefix:
        wrn = html_color_text("Warning:", "Orange") if html else "Warning:"
        msg = "File Prefix: {} does not match Project Code: {}".format(prefix, code)
        return "{0} {1}".format(wrn, msg)
    else:
        return None
