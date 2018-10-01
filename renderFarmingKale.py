import logging
import renderFarmingTools as rFT


class Kale:
    def __init__(self, rt, cfg):
        self._clg = logging.getLogger("renderFarming.Kale")

        self._rt = rt
        self._cfg = cfg

        self._verify_vray()
        self._vr = self._rt.renderers.current

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

        self.match_prefix()
        self._global_switches()

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

        ind = file_name.find('_') - 1

        prefix = file_name[:ind]

        if code not in prefix:
            self.append_item(KaleItem("match_prefix", "File Prefix does not match Project Code", "Scene", 2))

    def _verify_vray(self):
        """
        Checks that VRAY is the current renderer and if not, attempts to set it as such
        :return: True for success, False for failure
        """
        flg = logging.getLogger("renderFarming.Kale.verify_vray")
        if not rFT.verify_vray(self._rt):
            flg.error("Cannot set renderer to VRay")
            return False
        else:
            return True

    def _global_switches(self):
        if self._vr.options_dontRenderImage:
            self.append_item(KaleItem("options_render_final_image",
                                      "Don't Render Final Image is enabled", "Settings", 2))
        if not self._vr.options_reflectionRefraction:
            self.append_item(KaleItem("options_reflection_refraction",
                                      "Reflections and refractions are globally disabled", "Settings", 1))
        if self._vr.options_defaultLights is 1:
            self.append_item(KaleItem("options_default_lights",
                                      "Default lights are enabled", "Settings", 1))
        if not self._vr.options_lights:
            self.append_item(KaleItem("options_lights",
                                      "Lights are globally disabled", "Settings", 1))
        if not self._vr.options_shadows:
            self.append_item(KaleItem("options_shadows",
                                      "Shadows are globally disabled", "Settings", 1))
        if not self._vr.options_glossyEffects:
            self.append_item(KaleItem("options_glossy_effects",
                                      "Glossy Effects are globally disabled", "Settings", 1))
        if not self._vr.options_maps:
            self.append_item(KaleItem("options_maps",
                                      "Maps are globally disabled", "Settings", 1))
        if self._vr.options_overrideMtl_on:
            self.append_item(KaleItem("options_override_material",
                                      "An Override Material is enabled", "Settings", 1))
        if self._vr.options_hiddenLights:
            self.append_item(KaleItem("options_hidden_lights",
                                      "Hidden lights are enabled", "Settings", 0))


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
