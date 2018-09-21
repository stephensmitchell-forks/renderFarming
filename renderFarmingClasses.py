import os
import logging
from ConfigParser import NoSectionError

import renderFarmingTools as rFT

mlg = logging.getLogger("renderFarming.Classes")


class RenderSettings:

    def __init__(self, rt, user_scripts, code):

        clg = logging.getLogger("renderFarming.Classes.RenderSettings")

        self._rt = rt

        self._dir = os.path.join(user_scripts, "bdf", "renderFarming", "rps")
        rFT.verify_dir(self._dir)

        self._code = code
        self._filename = "spinachLast.rps"
        self._path = os.path.join(self._dir, self._filename)

        self._written = False
        clg.debug("Created a copy of the Render Settings")
        clg.debug("Project{0}, .RPS File: {1}".format(self._code, self._path))

        self._settings_dict = dict()

    def capture(self):
        cd = dict()
        # Common
        cd = cd.update(self._capture_common())

        # V-Ray
        cd = cd.update(self._capture_common())

        # GI
        cd = cd.update(self._capture_common())

        # Settings
        cd = cd.update(self._capture_common())

        # Render Elements
        cd = cd.update(self._capture_common())

        # finishing
        self._settings_dict = cd
        return

    def _capture_common(self):
        com_cd = dict()
        # Time Output
        self._rt.rendTimeType = 1
        return com_cd

    def capture_rps(self):
        flg = logging.getLogger("renderFarming.Classes.RenderSettings.capture")
        flg.debug("Saving Render Preset")
        try:
            self._rt.renderpresets.SaveAll(0, self._path)
            flg.debug("Saving Success")
            self._written = True
        except IOError as e:
            flg.error("IO Error, Failed to save Render Presets: {0}, file: {1}".format(e, self._path))
            self._written = False
        except os.error as e:
            flg.error("Error, Failed to save Render Presets: {0}, file: {1}".format(e, self._path))
            self._written = False

    def set_rps(self):
        flg = logging.getLogger("renderFarming.Classes.RenderSettings.set")
        flg.debug("Loading Render Preset")
        if self._written:
            try:
                self._rt.renderpresets.LoadAll(0, self._path)
                flg.debug("Loading Success")
            except IOError as e:
                flg.error("IO Error, Failed to load Render Presets: {0}, file: {1}".format(e, self._path))
            except os.error as e:
                flg.error("Error, Failed to load Render Presets: {0}, file: {1}".format(e, self._path))


class Camera:
    def __init__(self, name):
        self._name = name


class TokenizedString:
    # Class for handling tokenized strings
    # Assumes token format as ${section:option} and returns value
    def __init__(self, raw_string, cfg):
        self._cfg = cfg

        self._tokenDict = {"code": Token("project", "code", self._cfg),
                           "project": Token("paths", "projects_directory", self._cfg),
                           "userScripts": Token("paths", "user_scripts", self._cfg)
                           }

        self._raw_string = raw_string
        self._expanded_string = str()

        self._array = list()

        self._split_tokens(raw_string)

        self._expand()

    def __str__(self):
        return

    def _split_tokens(self, tokenized_string):
        """
        Splits string into a list, creating token objects for each token and keeping the other strings in order
        :param tokenized_string: The string with tokens in it
        :return: sets class attribute to result
        """
        token_split = tokenized_string.split('$')
        string_array = list()
        for i in token_split:
            # checks if i is a token or a normal string
            if '}' in i:
                split_array = i.replace('{', '').split('}')

                # Creates token object
                tk = self._tokenDict.get(split_array[0])

                if tk is None:
                    Token("split_array[0]", "ERROR", self._cfg)

                string_array.append(tk)
                string_array = string_array + split_array[1:]
            else:
                string_array.append(i)
        self._array = string_array

    def _expand(self):
        """
        Gets the expanded tokens and re builds the string with the expanded values substituting the tokens
        :return: sets class attribute to result
        """
        tokenized_string = str()
        for i in self._array:
            if isinstance(i, Token):
                tokenized_string = tokenized_string + i.get_value()
            else:
                tokenized_string = tokenized_string + i
        self._expanded_string = tokenized_string

    def get_expanded(self):
        return self._expanded_string


class Token:
    # Class for handling Tokens
    # Assumes token format as section:option and returns value
    def __init__(self, section, option, cfg):
        self._value = str()
        self._section = section
        self._option = option
        self._cfg = cfg

        self._expand()

    def __str__(self):
        return self._value

    def __repr__(self):
        return self.__str__()

    def _expand(self):
        """
        Looks up the section and option in the config dict and applies them to the class value.
        Warnings for missing or incorrect data will be returned
        as part of the string, rather than raising an exception here.
        :return: sets class attribute to result
        """
        try:
            self._value = self._cfg.get_config_by_section(self._section, self._option)
            return
        except NoSectionError:
            self._section = "$MISSING SECTION - {0}".format(self._section)
        except KeyError:
            self._option = "$MISSING OPTION - {0}".format(self._option)
        self._value = "{0}:{1}".format(self._section, self._option)

    def get_value(self):
        return self._value


class VRayImageFilterSet:
    def __init__(self, rt, filter_index):
        """

        :param rt: The pymxs Runtime
        :param filter_index: The index of the filter in the VRay drop down menu
        """
        self._clg = logging.getLogger("renderFarming.Classes.VRayImageFilterSet")

        self._rt = rt
        self._filter_index = filter_index

        if filter_index < 0 or filter_index > 16:
            msg = "The filter index is outside of the acceptable range.  Index: {}".format(filter_index)
            self._clg.error(msg)
            raise IndexError(msg)

    def get_filter(self):
        filt = self._filter_index
        if filt is 16:
            self._clg.debug("VRayMitNetFilter")
            return self._rt.VRayMitNetFilter()
        elif filt is 15:
            self._clg.debug("VRayTriangleFilter")
            return self._rt.VRayTriangleFilter()
        elif filt is 14:
            self._clg.debug("VRayBoxFilter")
            return self._rt.VRayBoxFilter()
        elif filt is 13:
            self._clg.debug("VRaySincFilter")
            return self._rt.VRaySincFilter()
        elif filt is 12:
            self._clg.debug("VRayLanczosFilter")
            return self._rt.VRayLanczosFilter()
        elif filt is 11:
            self._clg.debug("Mitchell Netravali")
            return self._rt.Mitchell_Netravali()
        elif filt is 10:
            self._clg.debug("Blackman")
            return self._rt.Blackman()
        elif filt is 9:
            self._clg.debug("Blend")
            return self._rt.Blend()
        elif filt is 8:
            self._clg.debug("Cook Variable")
            return self._rt.Cook_Variable()
        elif filt is 7:
            self._clg.debug("Soften")
            return self._rt.Soften()
        elif filt is 6:
            self._clg.debug("Video")
            return self._rt.Video()
        elif filt is 5:
            self._clg.debug("Cubic")
            return self._rt.Cubic()
        elif filt is 4:
            self._clg.debug("Quadratic")
            return self._rt.Quadratic()
        elif filt is 3:
            self._clg.debug("Plate Match/MAX R2")
            return self._rt.Plate_Match_MAX_R2()
        elif filt is 2:
            self._clg.debug("Catmull Rom")
            return self._rt.Catmull_Rom()
        elif filt is 1:
            self._clg.debug("Sharp Quadtratic")
            return self._rt.Sharp_Quadtratic()
        elif filt is 0:
            self._clg.debug("Area")
            return self._rt.Area()
        else:
            self._clg.debug("Area")
            return self._rt.Area()
