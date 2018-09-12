import os
import logging

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
        self._filename = "spinachLast.rps"
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


class Camera:
    def __init__(self, name):
        self._name = name
