import os
import logging
from MaxPlus import Core as MPc

mlg = logging.getLogger("renderFarming.Classes")


class RenderSettings:

    def __init__(self, rt, frames_dir, code, cam):

        clg = logging.getLogger("renderFarming.Classes.RenderSettings")

        self._rt = rt

        self._dir = frames_dir
        self._code = code
        if cam is None:
            self._cam_name = "viewport"
        else:
            self._cam_name = cam.name
        self._filename = "{0}_{1}.rps".format(self._code, self._cam_name)
        self._path = os.path.join(self._dir, self._filename)
        self._written = False
        clg.debug("Created a copy of the Render Settings")
        clg.debug("Camera: {0}, Project{1}, .RPS File: {2}".format(self._cam_name, self._code, self._path))

    def capture(self):
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

    def set(self):
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


class TabbedDialogPage:
    # One page of a tabbed dialog
    # Used for interfacing with Max's goofy tabbed dialog system
    # Stores the class id that max needs to find a tab because an array is too hard I guess
    def __init__(self):

        self._class_id = None
        self._name = str()

    def set_name(self, name):
        self._name = name

    def set_class_id(self, class_id):
        self._class_id = class_id

    def get_name(self):
        return self._name

    def get_class_id(self):
        return self._class_id

    def __str__(self):
        return "{0}, {1}".format(self._name, self._class_id)

    def __repr__(self):
        return self.__str__()


class TabbedDialog:
    # Interfaces with max's tabbed dialog system.
    # There is no way to do this directly through python, so it jankily MaxScript instead and picks up
    # variables with the runtime.  Doesn't work more than once apparently, probably because Max's
    # garbage collection is crap.  Don't use this
    def __init__(self, class_id, rt):
        self._rt = rt

        self._tab_array = list()
        self._id = class_id

        MPc.EvalMAXScript("dialog_is_open = tabbedDialogs.isOpen {0}".format(self._id))

        if rt.dialog_is_open:
            self._collect_tabs()

    def _collect_tabs(self):
        MPc.EvalMAXScript("page_num = tabbedDialogs.getNumPages {0}".format(self._id))

        page_num = self._rt.page_num

        for i in range(0, page_num):
            MPc.EvalMAXScript("class_id = tabbedDialogs.getPageID {0} {1}".format(self._id, i + 1))

            tab = TabbedDialogPage()

            tab.set_class_id(str(self._rt.class_id))

            MPc.EvalMAXScript(
                "class_name = tabbedDialogs.getPageTitle  {0} {1}".format(self._id, tab.get_class_id()))

            tab.set_name(str(self._rt.class_name))

            self._tab_array.append(tab)

    def collect_tabs(self):
        MPc.EvalMAXScript("dialog_is_open = tabbedDialogs.isOpen {0}".format(self._id))

        if self._rt.dialog_is_open:
            self._collect_tabs()
            return True
        else:
            return False

    def get_tabs(self):
        return self._tab_array

    def set_current_tab(self, index):
        tab = self._tab_array[index]
        MPc.EvalMAXScript("tabbedDialogs.setCurrentPage {0} {1}".format(self._id, tab.get_class_id()))

    def __str__(self):
        return str(self._tab_array)

    def __repr__(self):
        return self.__str__()
