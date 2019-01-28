import logging
import renderFarmingTools as rFT

import PySide2.QtCore as QtC
from PySide2.QtCore import Signal


class Kale(QtC.QObject):
    set_tasks = Signal(int)
    add_task = Signal(int)

    def __init__(self, rt, cfg):
        super(Kale, self).__init__()
        self._clg = logging.getLogger("renderFarming.Kale")

        self._rt = rt
        self._cfg = cfg

        self._vr = None
        self._verify_vray()

        self._found_items = list()

        # Switches
        # --------------------

        self._priorities = {
            0: "Low",
            1: "Medium",
            2: "High",
            3: "Critical"
        }

        # Checks
        # --------------------

        self.set_tasks.emit(8)

        self.match_prefix()
        self._global_switches()
        self._image_sampler()
        self._environment_overrides()
        self._atmosphere_effects()
        self._frame_buffer_effects()
        self._camera_check()
        self._color_mapping()

    # ---------------------------------------------------
    #                  Setter Functions
    # ---------------------------------------------------

    def append_item(self, kale_item):
        self._found_items.append(kale_item)

    # ---------------------------------------------------
    #                  Getter Functions
    # ---------------------------------------------------

    def get_list(self):
        return self._found_items

    def get_priorities(self):
        return self._priorities

    # ---------------------------------------------------
    #              Scene Checker Functions
    # ---------------------------------------------------

    def match_prefix(self):
        file_name = self._rt.maxFileName
        code = self._cfg.get_project_code()

        ind = file_name.find('_')

        prefix = file_name[:ind]

        if code != prefix:
            self.append_item(KaleItem("match_prefix",
                                      "File Prefix: {} does not match Project Code: {}".format(prefix, code),
                                      "Scene",
                                      2))

    def _verify_vray(self):
        """
        Checks that VRAY is the current renderer and if not, attempts to set it as such
        :return: True for success, False for failure
        """
        flg = logging.getLogger("renderFarming.Kale.verify_vray")
        renderer = rFT.verify_vray(self._rt)
        if renderer is None:
            flg.error("Cannot set renderer to VRay")
            return False
        else:
            self._vr = renderer
            return True

    def _global_switches(self):
        if self._vr.options_dontRenderImage:
            self.append_item(KaleItem("Don't Render Final Image",
                                      "Don't Render Final Image is enabled", "Settings", 2))
        if not self._vr.options_reflectionRefraction:
            self.append_item(KaleItem("Reflection and Refraction Disabled",
                                      "Reflections and refractions are globally disabled", "Settings", 1))
        if self._vr.options_defaultLights is 1:
            self.append_item(KaleItem("Default Lights Enabled",
                                      "Default lights are enabled", "Settings", 1))
        if not self._vr.options_lights:
            self.append_item(KaleItem("Lights Disabled",
                                      "Lights are globally disabled", "Settings", 1))
        if not self._vr.options_shadows:
            self.append_item(KaleItem("Shadows Disabled",
                                      "Shadows are globally disabled", "Settings", 1))
        if not self._vr.options_glossyEffects:
            self.append_item(KaleItem("Glossy Effects Disabled",
                                      "Glossy Effects are globally disabled", "Settings", 1))
        if not self._vr.options_maps:
            self.append_item(KaleItem("Maps Disabled",
                                      "Maps are globally disabled", "Settings", 1))
        if self._vr.options_overrideMtl_on:
            self.append_item(KaleItem("Override Material",
                                      "An Override Material is enabled", "Settings", 1))
        if self._vr.options_hiddenLights:
            self.append_item(KaleItem("Hidden Lights",
                                      "Hidden lights are enabled", "Settings", 0))
        self.add_task.emit(1)

    def _image_sampler(self):
        if self._vr.imageSampler_renderMask_type == 1:
            self.append_item(KaleItem("Texture Render Mask",
                                      "A texture render mask is enabled", "Settings", 1))
            if self._vr.imageSampler_renderMask_texmap is None:
                self.append_item(KaleItem("Texture Render Mask Missing",
                                          "A texture render mask is enabled, but there is no texture specified",
                                          "Settings", 3))
        elif self._vr.imageSampler_renderMask_type == 2:
            self.append_item(KaleItem("Selection Render Mask",
                                      "A selection render mask is enabled.  This CANNOT be rendered using Backburner",
                                      "Settings", 3))
        elif self._vr.imageSampler_renderMask_type == 3:
            self.append_item(KaleItem("Include/Exclude Render Mask",
                                      "An include/exclude list render mask is enabled", "Settings", 1))
        elif self._vr.imageSampler_renderMask_type == 4:
            self.append_item(KaleItem("Layer Render Mask",
                                      "A layers render mask is enabled", "Settings", 1))
            if self._vr.imageSampler_renderMask_layers.count == 0:
                self.append_item(KaleItem("Layer Render Mask Missing",
                                          "A layer render mask is enabled, but there are no layers specified",
                                          "Settings", 3))
        elif self._vr.imageSampler_renderMask_type == 4:
            self.append_item(KaleItem("Object ID Render Mask",
                                      "An Object ID render mask is enabled", "Settings", 1))
            if self._vr.imageSampler_renderMask_objectIDs == '':
                self.append_item(KaleItem("Object ID Render Mask Missing",
                                          "An object ID render mask is enabled, but there are no object IDs specified",
                                          "Settings", 3))
        self.add_task.emit(1)

    def _environment_overrides(self):
        if self._vr.environment_gi_on:
            self.append_item(KaleItem("Global Illumination Override",
                                      "A GI environment override is enabled", "Settings", 1))

        if self._vr.environment_rr_on:
            self.append_item(KaleItem("Reflection Override",
                                      "A reflection/refraction environment override is enabled", "Settings", 1))

        if self._vr.environment_refract_on:
            self.append_item(KaleItem("Refraction Override",
                                      "A refraction environment override is enabled", "Settings", 1))

        if self._vr.environment_secondaryMatte_on:
            self.append_item(KaleItem("Secondary Matte Override",
                                      "A secondary matte environment override is enabled", "Settings", 1))
        if not self._rt.useEnvironmentMap:
            self.append_item(KaleItem("No Environment Map",
                                      "Environment is not using a map", "Scene", 1))
        self.add_task.emit(1)

    def _atmosphere_effects(self):
        num_atmos = self._rt.numAtmospherics
        list_atmos = list()
        num_active = 0
        vray_toon_active = False
        vray_env_fog_active = False
        if num_atmos > 0:
            # collect all atmospheres from the scene
            for a in range(1, num_atmos + 1):
                list_atmos.append(self._rt.getAtmospheric(a))

            for a in list_atmos:
                if self._rt.isActive(a):
                    num_active = num_active + 1
                    if str(self._rt.classof(a)) == "VRayToon":
                        vray_toon_active = True
                    if str(self._rt.classof(a)) == "VRayEnvironmentFog":
                        vray_env_fog_active = True

            if num_active > 1:
                self.append_item(KaleItem("Multiple Atmospheres Active",
                                          "More than one atmosphere is active in the scene", "Scene", 2))
            if vray_toon_active:
                self.append_item(KaleItem("V-Ray Toon",
                                          "A VRay toon effect is active in the scene", "Scene", 2))
            if vray_env_fog_active:
                self.append_item(KaleItem("Environment Fog",
                                          "A VRay environment fog effect is active in the scene", "Scene", 2))
        self.add_task.emit(1)

    def _frame_buffer_effects(self):
        if self._rt.vrayVFBGetRegionEnabled():
            self.append_item(KaleItem("Region Render",
                                      "Region rendering is enabled", "VFB", 3))
        if self._rt.vfbControl(self._rt.name("exposure"))[0]:
            self.append_item(KaleItem("VFB Exposure",
                                      "The exposure adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("whitebalance"))[0]:
            self.append_item(KaleItem("VFB WB",
                                      "The white balance adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("huesat"))[0]:
            self.append_item(KaleItem("VFB HSL",
                                      "The hue and saturation adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("colorbalance"))[0]:
            self.append_item(KaleItem("VFB Color Balance",
                                      "The color balance adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("levels"))[0]:
            self.append_item(KaleItem("VFB Levels",
                                      "The levels adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("curve"))[0]:
            self.append_item(KaleItem("VFB Curve",
                                      "The curve adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("lut"))[0]:
            self.append_item(KaleItem("VFB Look Up Table",
                                      "The look up table adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("ocio"))[0]:
            self.append_item(KaleItem("BFB OCIO",
                                      "The OpenColorIO adjustment is enabled", "VFB", 2))
        if self._rt.vfbControl(self._rt.name("icc"))[0]:
            self.append_item(KaleItem("VFB ICC",
                                      "An ICC profile adjustment is enabled", "VFB", 2))
        if not self._rt.vfbControl(self._rt.name("srgb"))[0]:
            self.append_item(KaleItem("VFB is not sRGB",
                                      "The VFB is not displaying in sRGB space", "VFB", 1))
        if self._rt.vfbControl(self._rt.name("bkgr"))[0]:
            self.append_item(KaleItem("VFB Background",
                                      "A background image is applied", "VFB", 3))
        if self._rt.vfbControl(self._rt.name("stamp"))[0]:
            self.append_item(KaleItem("VFB Stamp",
                                      "A stamp is enabled", "VFB", 1))
        if self._rt.vfbControl(self._rt.name("bloom"))[0]:
            self.append_item(KaleItem("VFB Bloom",
                                      "The bloom effect is enabled", "VFB", 1))
        if self._rt.vfbControl(self._rt.name("glare"))[0]:
            self.append_item(KaleItem("VFB Glare",
                                      "The glare effect is enabled", "VFB", 1))
        self.add_task.emit(1)

    def _render_passes(self):
        return

    def _camera_check(self):
        cam = self._rt.getActiveCamera()
        if cam is None:
            self.append_item(KaleItem("Active Camera is Viewport",
                                      "The active camera is assigned to a viewport camera", "Camera", 1))
        elif self._rt.classOf(cam) != self._rt.Physical:
            self.append_item(KaleItem("Camera is not Physical",
                                      "The active camera is not a Max Physical Camera", "Camera", 1))
        else:
            exp = cam.exposure_value
            if exp < 10:
                self.append_item(KaleItem("Camera Exposure too High",
                                          "The active camera's exposure target ({}) is very high".format(exp),
                                          "Camera",
                                          1))
            elif exp > 18:
                self.append_item(KaleItem("Camera Exposure too Low",
                                          "The active camera's exposure target ({}) is very low".format(exp),
                                          "Camera",
                                          1))

            if cam.motion_blur_enabled:
                self.append_item(KaleItem("Camera Motion Blur",
                                          "The active camera has motion blur enabled", "Camera", 2))
            if cam.use_dof:
                self.append_item(KaleItem("Camera Depth of Field",
                                          "The active camera has depth of field enabled", "Camera", 2))
        self.add_task.emit(1)

    def _color_mapping(self):
        gamma = self._vr.colorMapping_gamma
        if not rFT.isclose(gamma, 2.2, 0.001):
            self.append_item(KaleItem("Gamma {0}".format(round(gamma, 3)),
                                      "Color mapping gamma is set to a value of \"{0}\". ".format(round(gamma, 3)) +
                                      "Typically, this is set to a value of \"2.2\".",
                                      "Settings", 0))

        mode_index = self._vr.colorMapping_type
        if mode_index != 6:
            mapping_modes = {
                0: "Linear Multiply",
                1: "Exponential",
                2: "HSV Exponential",
                3: "Intensity Exponential",
                4: "Gamma Correction",
                5: "Intensity Gamma",
                6: "Reinhard"
            }
            mode = mapping_modes.get(mode_index, 0)
            self.append_item(KaleItem("Color Mapping Mode {0}".format(mode),
                                      "Color mapping mode is set to \"{0}\". ".format(mode) +
                                      "Typically, this is set to \"Reinhard\".",
                                      "Settings", 2))

        adaptation_mode_index = self._vr.colorMapping_adaptationOnly
        if adaptation_mode_index != 2:
            adaptation_mode = {
                0: "Color mapping and gamma",
                1: "None (Don't apply anything)",
                2: "Color mapping only (No Gamma)",
            }
            mode = adaptation_mode.get(adaptation_mode_index, 0)
            msg = "Color mapping adaptation mode is set to \"{0}\". ".format(mode)
            msg2 = "Typically, this is set to \"Color mapping only (No Gamma)\"."

            self.append_item(KaleItem("Color Mapping Adaptation Mode {0}".format(mode), msg + msg2, "Settings", 2))

        if self._vr.colorMapping_clampOutput:
            clamp_level = round(self._vr.colorMapping_clampLevel, 2)
            msg = "Output clamping enabled, this will clamp HDR images to a maximum value of {0}".format(clamp_level)
            self.append_item(KaleItem("Output Clamp", msg, "Settings", 3))

        if self._vr.colorMapping_subpixel:
            msg = "Sub-Pixel mapping is enabled, this is not recommended in VRay 3"
            self.append_item(KaleItem("Sub-Pixel Mapping", msg, "Settings", 3))
        self.add_task.emit(1)


class KaleItem:
    def __init__(self, title, text, category, priority):
        """
        A problem, irregularity, or general piece of information that Kale wishes to inform the user of
        :param title: A name for the issue
        :param text: An explanation of the item
        :param category: The category of the item
            -Scene: Involves the Global scene
            -VFB: A problem with the V-Ray frame Buffer
            -Camera: An issue with the camera
            -Effects: Involves Atmospheres, Effects, Environment and exposure
            -Settings: Problems with the render settings
        :param priority: The priority of the item
            -0: Low: Can probably be ignored, but should still be brought up for consideration
            -1: Medium: Should be addressed eventually
            -2: High: This should be addressed or verified before rendering
            -3: Critical: If this is not addressed, the scene will most likely fail to render
        """
        self._clg = logging.getLogger("renderFarming.KaleItem")

        self._title = title
        self._text = text
        self._category = category
        self._priority = priority

        self._clg.debug("Kale Item found: {0} - {1} - priority: {2}".format(self._text, self._category, self._priority))

    # ---------------------------------------------------
    #                  Getter Functions
    # ---------------------------------------------------

    def get_title(self):
        return self._title

    def get_text(self):
        return self._text

    def get_category(self):
        return self._category

    def get_priority(self):
        return self._priority

    # ---------------------------------------------------
    #                Standard Functions
    # ---------------------------------------------------

    def __str__(self):
        return "{0} - {1} - {2}".format(self._text, self._category, self._priority)

    def __repr__(self):
        return self.__str__()


label_list = "Title", "Text", "Category", "Priority"
