import os
import logging

import renderFarmingTools as rFT


class ArugulaJob:

    def __init__(self, rt, user_scripts, code):

        self._clg = logging.getLogger("renderFarming.Classes.RenderSettings")

        self._rt = rt
        self._vr = self._rt.renderers.current

        self._dir = os.path.join(user_scripts, "bdf", "renderFarming", "rps")
        rFT.verify_dir(self._dir)

        self._code = code
        self._rps_filename = "spinachLast.rps"
        self._path = os.path.join(self._dir, self._rps_filename)

        self._written = False
        self._clg.debug("Created a copy of the Render Settings")
        self._clg.debug("Project{0}, RPS File: {1}".format(self._code, self._path))

        self._settings_dict = dict()

    def capture(self):
        cd = dict()
        # Common
        cd['Common'] = self._capture_common()

        # Renderer
        cd['Renderer'] = self._capture_renderer()

        # finishing
        self._settings_dict = cd
        return

    def _capture_renderer(self):
        rd = dict()
        for prop in self._rt.getPropNames(self._vr):
            rd[prop] = self._rt.getProperty(self._vr, prop)
        return rd

    def _set_renderer(self, rd):
        for prop in rd:
            value = rd.get(prop)

            if str(self._rt.classOf(value)) not in "UndefinedClass":
                self._rt.setProperty(self._vr, prop, value)
            else:
                self._clg.warning("Renderer Property \"{}\" is undefined".format(prop))
                self._clg.debug("Setting {} to an empty string".format(prop))
                self._rt.setProperty(self._vr, prop, "")

    def _capture_common(self):
        com_cd = dict()

        # Time Output
        com_cd['rendTimeType'] = self._rt.rendTimeType
        com_cd['rendNThFrame'] = self._rt.rendNThFrame
        com_cd['rendStart'] = self._rt.rendStart
        com_cd['rendEnd'] = self._rt.rendEnd
        com_cd['rendFileNumberBase'] = self._rt.rendFileNumberBase
        com_cd['rendPickupFrames'] = self._rt.rendPickupFrames
        com_cd['rendTimeType'] = self._rt.rendTimeType

        # Area to Render
        com_cd['getRenderType'] = self._rt.getRenderType()

        # Output Size
        com_cd['renderWidth'] = self._rt.renderWidth
        com_cd['renderHeight'] = self._rt.renderHeight
        com_cd['renderPixelAspect'] = self._rt.renderPixelAspect

        # Options Group

        com_cd['rendAtmosphere'] = self._rt.rendAtmosphere
        com_cd['renderEffects'] = self._rt.renderEffects
        com_cd['renderDisplacements'] = self._rt.renderDisplacements
        com_cd['rendColorCheck'] = self._rt.rendColorCheck
        com_cd['rendFieldRender'] = self._rt.rendFieldRender
        com_cd['rendHidden'] = self._rt.rendHidden
        com_cd['rendSimplifyAreaLights'] = self._rt.rendSimplifyAreaLights
        com_cd['rendForce2Side'] = self._rt.rendForce2Side
        com_cd['rendSuperBlack'] = self._rt.rendSuperBlack

        # Render Output Group

        com_cd['rendSaveFile'] = self._rt.rendSaveFile
        com_cd['rendOutputFilename'] = self._rt.rendOutputFilename
        com_cd['rendUseDevice'] = self._rt.rendUseDevice
        com_cd['rendShowVFB'] = self._rt.rendShowVFB
        com_cd['rendUseNet'] = self._rt.rendUseNet
        com_cd['skipRenderedFrames'] = self._rt.skipRenderedFrames

        return com_cd

    def _set_common(self, com_cd):

        # Time Output
        self._rt.rendTimeType = com_cd['rendTimeType']
        self._rt.rendNThFrame = com_cd['rendNThFrame']
        self._rt.rendStart = com_cd['rendStart']
        self._rt.rendEnd = com_cd['rendEnd']
        self._rt.rendFileNumberBase = com_cd['rendFileNumberBase']
        self._rt.rendPickupFrames = com_cd['rendPickupFrames']
        self._rt.rendTimeType = com_cd['rendTimeType']

        # Area to Render
        self._rt.setRenderType(com_cd['getRenderType'])

        # Output Size
        self._rt.renderWidth = com_cd['renderWidth']
        self._rt.renderHeight = com_cd['renderHeight']
        self._rt.renderPixelAspect = com_cd['renderPixelAspect']

        # Options Group

        self._rt.rendAtmosphere = com_cd['rendAtmosphere']
        self._rt.renderEffects = com_cd['renderEffects']
        self._rt.renderDisplacements = com_cd['renderDisplacements']
        self._rt.rendColorCheck = com_cd['rendColorCheck']
        self._rt.rendFieldRender = com_cd['rendFieldRender']
        self._rt.rendHidden = com_cd['rendHidden']
        self._rt.rendSimplifyAreaLights = com_cd['rendSimplifyAreaLights']
        self._rt.rendForce2Side = com_cd['rendForce2Side']
        self._rt.rendSuperBlack = com_cd['rendSuperBlack']

        # Render Output Group

        self._rt.rendSaveFile = com_cd['rendSaveFile']
        self._rt.rendOutputFilename = com_cd['rendOutputFilename']
        self._rt.rendUseDevice = com_cd['rendUseDevice']
        self._rt.rendShowVFB = com_cd['rendShowVFB']
        self._rt.rendUseNet = com_cd['rendUseNet']
        self._rt.skipRenderedFrames = com_cd['skipRenderedFrames']

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


class ArugulaSetting:
    def __init__(self, address, value):
        self._set_add = address
        self._value = value
        self._type = type(value)

    def get_address(self):
        return self._set_add

    def get_type(self):
        return self._type

    def get_value(self):
        return self._value

    def apply(self, runtime):
        return


class ArugulaFunctionSetting(ArugulaSetting):
    def __init__(self, address, value):
        super(ArugulaFunctionSetting, self).__init__(address, value)

    def apply(self, runtime):
        return
