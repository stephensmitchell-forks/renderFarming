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
    return " <font color=\"{1}\">{0}</font>".format(text, color)


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
