import renderFarmingTools as rFT
import renderFarmingClasses as rFC
import renderFarmingNetRender as rFNR
import os
import logging

# Get Camera from Viewport
# Validate Camera
# Get Current File Settings and store them
#   > Gi Engine
#   > IR Mode and Light Cache Mode
#   > IR Path and LC Path
#   > Auto save Check
#   > Don't Delete Check
# Set GI Engine to Irradiance and Light Cache
# Make sure Use Camera Path is checked
# Set Light Cache and Irradiance Map paths based on name for both auto-save and read
# Set Light Cache and irradiance map to pre-pass settings
# Set Not Final Render
# Submit job to Backburner using camera name and workstation group
# Un-set Not Final Render
# Set Light cache and Irradiance Map to from file
# Set frames directory
# Submit to backburner with dependency on previous job
# Return file settings to defaults


class SpinachJob:
    def __init__(self, rt, cfg):
        clg = logging.getLogger("renderFarming.Spinach")
        clg.debug("Running Spinach")

        self._rt = rt

        self._vr = self._rt.renderers.current

        self._cfg = cfg

        self._ir_file = self._cfg.get_irradiance_cache_path()
        self._lc_file = self._cfg.get_light_cache_path()
        self._frames_dir = self._cfg.get_frames_path()

        self._cam = None
        self._cam_name = str()

        self._ready = False

    def _cycle_render_dialog(self, dialog):
        flg = logging.getLogger("renderFarming.Spinach._cycle_render_dialog")
        flg.debug("Cycling tabs of render dialog")
        for i in range(0, len(dialog.get_tabs)):
            dialog.set_current_tab(i)

    def _verify_paths(self, *args):
        flg = logging.getLogger("renderFarming.Spinach._verify_paths")

        for p in args:
            if not rFT.verify_dir(p):
                flg.error("Path Error: {} does not resolve and cannot be created".format(p))
                return False
        return True

    def _rsd_open(self):
        flg = logging.getLogger("renderFarming.Spinach._rsd_open")
        flg.debug("Opening \"Render Scene Dialog\" if closed")
        self._rt.renderSceneDialog.open()

    def _rsd_close(self):
        flg = logging.getLogger("renderFarming.Spinach._rsd_close")
        flg.debug("Closing \"Render Scene Dialog\" if open")
        self._rt.renderSceneDialog.close()

    def _set_gi_paths(self):
        flg = logging.getLogger("renderFarming.Spinach._set_gi_paths")
        flg.debug("Applying Irradiance Map paths")

        self._vr.adv_irradmap_autoSaveFileName = self._ir_file
        self._vr.adv_irradmap_loadFileName = self._ir_file

        flg.debug("Applying Light Cache paths")

        self._vr.lightcache_autoSaveFileName = self._lc_file
        self._vr.lightcache_loadFileName = self._lc_file

    def _set_gi_type(self):
        flg = logging.getLogger("renderFarming.Spinach._set_gi_prepass")

        flg.debug("Setting Gi Engines to Irradiance Map and Light Cache")

        self._vr.gi_primary_type = 0
        self._vr.gi_secondary_type = 3

    def _set_gi_save_to_frame(self):
        flg = logging.getLogger("renderFarming.Spinach._set_gi_prepass")

        flg.debug("Setting Irradiance Map to save single frame mode")

        self._vr.adv_irradmap_mode = 0
        self._vr.adv_irradmap_dontDelete = False
        self._vr.adv_irradmap_autoSave = True
        self._vr.adv_irradmap_switchToSavedMap = True
        self._vr.gi_irradmap_multipleViews = True

        flg.debug("Setting Irradiance Map to save single frame mode")

        self._vr.lightcache_mode = 0
        self._vr.lightcache_dontDelete = False
        self._vr.lightcache_autoSave = True
        self._vr.lightcache_switchToSavedMap = True
        self._vr.lightcache_multipleViews = True

    def _verify_vray(self):
        flg = logging.getLogger("renderFarming.Spinach.verify_vray")
        if not rFT.verify_vray(self._rt):
            flg.error("Cannot set renderer to VRay")
            return False
        else:
            return True

    def _set_output(self):
        flg = logging.getLogger("renderFarming.Spinach._set_output")
        self._rt.rendSaveFile = True

        flg.debug("Setting output directory to the folder specified for the camera")
        flg.debug("{0}\\frame_.exr".format(self._frames_dir))

        self._rt.rendOutputFilename = "{0}\\frame_.exr".format(self._frames_dir)

    # ---------------------------------------------------
    #                       Public
    # ---------------------------------------------------

    def cycle_render_dialog(self):
        self._rsd_open()
        self._cycle_render_dialog(rFC.TabbedDialog("#render", self._rt))
        self._rsd_close()

    def prepare_job(self):
        flg = logging.getLogger("renderFarming.Spinach.prepare_job")
        self._cam = self.get_cam()

        if self._cam is None:
            self._cam_name = "viewport"
            return
        else:
            self._cam_name = self._cam.name

        if not self._verify_vray():
            return

        self._ir_file = self._cfg.get_irradiance_cache_path() + "{0}.vrmap".format(self._cam_name)
        self._lc_file = self._cfg.get_light_cache_path() + "{0}.vrlmap".format(self._cam_name)
        self._frames_dir = os.path.join(self._cfg.get_frames_path(), self._cam_name)

        flg.debug("Irradiance Map: {}".format(self._ir_file))
        flg.debug("Light Cache: {}".format(self._lc_file))
        flg.debug("Frames Directory: {}".format(self._frames_dir))

        self._verify_paths(self._cfg.get_irradiance_cache_path(), self._cfg.get_light_cache_path(), self._frames_dir)

        flg.debug("Capturing Original Render Settings")

        orig_settings = rFC.RenderSettings(self._rt, self._frames_dir, self._cfg.get_project_code(), self._cam)
        orig_settings.capture()

        self._ready = True

    def get_cam(self):
        flg = logging.getLogger("renderFarming.Spinach._get_cam")
        cam = self._rt.getActiveCamera()
        if cam is None:
            flg.error("No camera viewpoint")
        else:
            flg.debug("Active camera selected: {}".format(cam.name))
        return cam

    def single_frame_prepass(self):
        flg = logging.getLogger("renderFarming.Spinach.single_frame_prepass")

        if not self._ready:
            flg.info("Spinach reports not ready, job submission cannot continue")
            return

        self._rsd_close()

        self._set_gi_paths()
        self._set_gi_type()
        self._set_gi_save_to_frame()

        flg.debug("Setting VRay to render only GI")

        self._vr.options_dontRenderImage = True

        flg.debug("Turning VRay Frame Buffer on")

        self._vr.output_on = True

        flg.debug("Setting render time output to \"Single Frame\"")

        self._rt.rendTimeType = 1

        flg.debug("\"Render Time Type\" is set to: {}".format(self._rt.rendTimeType))

        self._rsd_open()

    def from_file(self):
        flg = logging.getLogger("renderFarming.Spinach.from_file")

        if not self._ready:
            flg.info("Spinach reports not ready, job submission cannot continue")
            return

        self._rsd_close()

        flg.debug("Setting Irradiance Map to from file mode")
        flg.debug("Setting Light Cache to from file mode")

        self._vr.lightcache_mode = 2
        self._vr.adv_irradmap_mode = 2

        flg.debug("Setting VRay to render final image")

        self._vr.options_dontRenderImage = False

        flg.debug("Turning VRay Frame Buffer off")

        self._vr.output_on = False

        flg.debug("Setting render time output to \"User Range\"")

        self._rt.rendTimeType = 3

        flg.debug("\"Render Time Type\" is set to: {}".format(self._rt.rendTimeType))

        flg.debug("Setting \"Save File\" on")

        self._set_output()

        self._rsd_open()

        flg.debug("File Ready for Final Render")

    def get_ready_status(self):
        return self._ready

    def submit(self):
        flg = logging.getLogger("renderFarming.Spinach.submit")
        flg.debug("Submitting file to Backburner")
        rFNR.submit_current_file()
        flg.debug("File submitted to Backburner")
