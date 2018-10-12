import renderFarmingTools as rFT
# import renderFarmingClasses as rFC
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
        # Logging
        self._clg = logging.getLogger("renderFarming.Spinach")
        self._clg.debug("Running Spinach")

        # Variables

        self._rt = rt
        self._vr = None
        self._verify_vray()

        self._rem = self._rt.maxOps.GetCurRenderElementMgr()

        self._cfg = cfg

        # Paths

        self._ir_file = self._cfg.get_irradiance_cache_path()
        self._lc_file = self._cfg.get_light_cache_path()
        self._frames_dir = self._cfg.get_frames_path()

        # Cameras

        self._cam = None
        self._cam_name = str()

        # Messaging system attributes

        self._ready = False

        self._status_message = "Initialized"
        self._log_status(self._clg)
        self._rsd_state = False

        # HTML Message macros

        self._rd_er_tx = rFT.html_color_text("ERROR:", "Red")
        self._grn_rdy_tx = rFT.html_color_text("Ready!", "Green")
        self._org_n_rdy_tx = rFT.html_color_text("Not Ready:", "Orange")

        # UI Settings Attributes

        self._frame_buffer_type = 0
        self._image_filter_override = 17
        self._frames_sub_folder = "$(cam)"

        self._multi_frame_increment = 50
        self._pad_gi = False

        self._nth_frame = 1
        self._sp_sub_fold_name_gi = False

        # Other Attributes

        # self._orig_settings = rFC.RenderSettings(self._rt,
        #                                          self._cfg.get_user_scripts_path(),
        #                                          self._cfg.get_project_code())
        # self._orig_settings.capture_rps()

    def _log_status(self, handler=logging.getLogger("renderFarming.Spinach")):
        """
        Logs the current program status to the debug level
        :param handler: The logging handler
        :return: None
        """
        flg = handler
        flg.debug("Spinach Status: {}".format(self._status_message))

    def _verify_paths(self, *args):
        """
        A wrapper for verify_dir() in the render Farming Tools
        :param args: A list containing multiple file system paths
        :return: True for success, False for failure
        """
        flg = logging.getLogger("renderFarming.Spinach._verify_paths")

        for p in args:
            # If any of the paths can't be found or made, returns false
            if not rFT.verify_dir(p):
                flg.error("Path Error: {} does not resolve and cannot be created".format(p))
                self._status_message = "{} One or more paths are invalid".format(self._rd_er_tx)
                return False
        return True

    def _rsd_open(self):
        """
        Opens the 3DS Max render dialog
        Wraps the pymxs function in order to log that it was done, but this is probably super unnecessary
        :return: None
        """
        self._clg.debug("Opening \"Render Scene Dialog\" if closed")
        self._rt.renderSceneDialog.open()

    def _rsd_close(self):
        """
        Closes the 3DS Max render dialog
        Wraps the pymxs function in order to log that it was done, but this is probably super unnecessary
        :return: None
        """
        self._clg.debug("Closing \"Render Scene Dialog\" if open")
        self._rt.renderSceneDialog.close()

    def _set_gi_paths(self):
        """
        Sets GI paths to ones stored in the Job
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach._set_gi_paths")
        flg.debug("Applying Irradiance Map paths")

        self._vr.adv_irradmap_autoSaveFileName = self._ir_file
        self._vr.adv_irradmap_loadFileName = self._ir_file

        flg.debug("Applying Light Cache paths")

        self._vr.lightcache_autoSaveFileName = self._lc_file
        self._vr.lightcache_loadFileName = self._lc_file

    def _set_animation_prepass_path(self):
        # Checks if the containing folder should be named using the user specified sub folder field
        if self._sp_sub_fold_name_gi:
            sub_fold = self._expand_frames_sub_folder()
        else:
            sub_fold = self._cam_name

        # Defines the folder in which the Prepass frames will be stored
        folder = os.path.join(self._cfg.get_irradiance_cache_path(), sub_fold)

        # checks this folder's existence or writability
        if rFT.verify_dir(folder):
            # sets the _ir_file string
            self._ir_file = folder + "\\{0}_frame_.vrmap".format(sub_fold)
        else:
            # Displays an error message and returns
            self._status_message = "Unable to find or create path for animation prepass rendering"
            self._log_status(self._clg)
            self._ready = False
            return

    def _set_gi_engine(self, render_type=6):
        """
        Sets the GI type to the one specified
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
            -0:   Single Frame Irradiance Map, Light Cache
            -1:   From File Single Frame Irradiance Map, Light Cache
            -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache
            -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1)
            -4:   Animation Prepass Irradiance Map, Light Cache
            -5:   Animation Interpolated Irradiance Map, no secondary
            -6:   Brute Force, Light Cache
            -7:   Brute Force, From File Light Cache
            -8:   Brute Force, Light Cache with a new Light Cache every frame
            -9:   Brute Force, Brute Force
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach._set_gi_engine")
        flg.debug("Using Render Type {}".format(render_type))

        if render_type in (0, 1, 2, 3, 4):
            flg.debug("Setting Gi Engines to Irradiance Map and Light Cache")
            self._vr.gi_primary_type = 0
            self._vr.gi_secondary_type = 3

        elif render_type is 5:
            flg.debug("Setting Gi Engines to Irradiance Map and None")
            self._vr.gi_primary_type = 0
            self._vr.gi_secondary_type = 0

        elif render_type in (6, 7, 8):
            flg.debug("Setting Gi Engines to Brute Force and Light Cache")
            self._vr.gi_primary_type = 2
            self._vr.gi_secondary_type = 3

        elif render_type is 9:
            flg.debug("Setting Gi Engines to Brute Force and Brute Force")
            self._vr.gi_primary_type = 2
            self._vr.gi_secondary_type = 2

    def _set_frame_time_type(self, render_type=6):
        """
        Sets the frame settings based on type
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
            -0:   Single Frame Irradiance Map, Light Cache
            -1:   From File Single Frame Irradiance Map, Light Cache
            -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache
            -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1)
            -4:   Animation Prepass Irradiance Map, Light Cache
            -5:   Animation Interpolated Irradiance Map, no secondary
            -6:   Brute Force, Light Cache
            -7:   Brute Force, From File Light Cache
            -8:   Brute Force, Light Cache with a new Light Cache every frame
            -9:   Brute Force, Brute Force
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach._set_frame_time_type")
        flg.debug("Using Render Type {}".format(render_type))

        if render_type is 2:
            if not self._pad_gi:
                flg.debug("Setting time to Active Segment frame")
                self._rt.rendTimeType = 2
            else:
                flg.debug("Padding Multi Frame Incremental GI Range")
                end = int(self._rt.animationRange.end)
                start = int(self._rt.animationRange.start)
                new_end = rFT.calculate_increment_padding(start, end, self._multi_frame_increment)

                flg.debug("Range padded from frame {0} to frame {1}".format(end, new_end))

                self._rt.rendTimeType = 3
                self._rt.rendStart = start
                self._rt.rendEnd = new_end

            flg.debug("Setting time to every Nth frame with an increment of {}".format(self._multi_frame_increment))
            self._rt.rendNThFrame = self._multi_frame_increment

        elif render_type in (0, 6):
            flg.debug("Setting time to single frame")
            self._rt.rendTimeType = 1
            self._rt.rendNThFrame = self._nth_frame

        elif render_type is 4:
            self._rt.rendNThFrame = 1

            if not self._pad_gi:
                flg.debug("Setting time to Active Segment frame")
                self._rt.rendTimeType = 2

            else:
                flg.debug("Padding Animation Prepass GI Range")
                self._rt.rendTimeType = 3

                interp_frames = self._vr.gi_irradmap_interpFrames

                flg.debug("Padding Frame Range by {} Frames on either side".format(interp_frames))

                self._rt.rendStart = int(self._rt.animationRange.start) - interp_frames
                self._rt.rendEnd = int(self._rt.animationRange.end) + interp_frames

        elif render_type in (1, 3, 5, 7, 8, 9):
            flg.debug("Setting time to Active Segment frame")
            self._rt.rendTimeType = 2
            self._rt.rendNThFrame = self._nth_frame
            return

    def _set_gi_save_to_frame(self, render_type=6):
        """
        Sets the GI options to save frame
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
            -0:   Single Frame Irradiance Map, Light Cache
            -1:   From File Single Frame Irradiance Map, Light Cache
            -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache
            -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1)
            -4:   Animation Prepass Irradiance Map, Light Cache
            -5:   Animation Interpolated Irradiance Map, no secondary
            -6:   Brute Force, Light Cache
            -7:   Brute Force, From File Light Cache
            -8:   Brute Force, Light Cache with a new Light Cache every frame
            -9:   Brute Force, Brute Force
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach._set_gi_save_to_frame")
        flg.debug("Using Render Type {}".format(render_type))

        self._vr.adv_irradmap_dontDelete = False
        self._vr.adv_irradmap_switchToSavedMap = False
        self._vr.gi_irradmap_multipleViews = True

        self._vr.lightcache_switchToSavedMap = False
        self._vr.lightcache_dontDelete = False
        self._vr.lightcache_multipleViews = True

        # ----------------
        # Irradiance Cache
        # ----------------

        if render_type is 0:
            flg.debug("Setting Irradiance Map to save single frame mode")
            self._vr.adv_irradmap_mode = 0
            self._vr.adv_irradmap_autoSave = True

        if render_type in (1, 3):
            flg.debug("Setting Irradiance Map to read From File mode")
            self._vr.adv_irradmap_mode = 2
            self._vr.adv_irradmap_autoSave = False

        elif render_type is 2:
            flg.debug("Setting Irradiance Map to Multi Frame Incremental Mode")
            self._vr.adv_irradmap_mode = 1
            self._vr.adv_irradmap_autoSave = True
            self._vr.gi_irradmap_multipleViews = False

        elif render_type is 4:
            flg.debug("Setting Irradiance Map to Animation Prepass Mode")
            self._vr.adv_irradmap_mode = 6
            self._vr.adv_irradmap_autoSave = True

        elif render_type is 5:
            flg.debug("Setting Irradiance Map to Animation Rendering Mode")
            self._vr.adv_irradmap_mode = 7
            self._vr.adv_irradmap_autoSave = False

        # -----------
        # Light Cache
        # -----------

        if render_type in (0, 6):
            flg.debug("Setting Light Cache to save single frame mode")
            self._vr.lightcache_mode = 0
            self._vr.lightcache_autoSave = True

        elif render_type is 2:
            flg.debug("Setting Light Cache to save single frame mode")
            self._vr.lightcache_mode = 0
            self._vr.lightcache_autoSave = True
            self._vr.lightcache_switchToSavedMap = True

        elif render_type in (1, 3, 7):
            flg.debug("Setting Light Cache to read from file mode")
            self._vr.lightcache_mode = 2
            self._vr.lightcache_autoSave = True

        elif render_type is 4:
            flg.debug("Setting Light Cache to prepass single frame mode")
            self._vr.lightcache_mode = 0
            self._vr.lightcache_autoSave = False

        elif 8 is render_type:
            flg.debug("Setting Light Cache to calculate each frame mode")
            self._vr.lightcache_mode = 0
            self._vr.lightcache_autoSave = False
            self._vr.lightcache_dontDelete = True

    def _verify_vray(self):
        """
        Checks that VRAY is the current renderer and if not, attempts to set it as such
        :return: True for success, False for failure
        """
        flg = logging.getLogger("renderFarming.Spinach.verify_vray")
        renderer = rFT.verify_vray(self._rt)

        if not renderer:
            flg.error("Cannot set renderer to VRay")
            self._status_message = "{} Cannot set renderer to VRay".format(self._rd_er_tx)
            return False
        else:
            self._vr = renderer
            return True

    def _set_output(self, fb_type, beauty=True):
        """
        Sets the output to the frames folder stored in the job
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach._set_output")
        if beauty:
            if fb_type is 0:
                self._rt.rendSaveFile = True
                self._vr.output_on = False
                flg.debug("3ds Max Frame Buffer is on")

                self._vr.output_splitgbuffer = False

                flg.debug("Setting 3ds Max Frame Buffer output directory to the folder specified for the camera")
                flg.debug("{0}\\frame_.exr".format(self._frames_dir))

                self._rt.rendOutputFilename = "{0}\\frame_.exr".format(self._frames_dir)
                self._set_render_element_output()

                self._vr.output_splitFileName = ""

            elif fb_type is 1:
                self._rt.rendSaveFile = False
                self._vr.output_on = True
                flg.debug("VRay Frame Buffer is on")

                self._vr.output_splitgbuffer = True

                flg.debug("Setting VRay Frame Buffer output directory to the folder specified for the camera")
                flg.debug("{0}\\frame_.exr".format(self._frames_dir))

                self._vr.output_splitFileName = "{0}\\frame_.exr".format(self._frames_dir)
                self._rt.rendOutputFilename = ""

        else:
            if fb_type is 0:
                self._rt.rendSaveFile = False
                self._vr.output_on = False
                flg.debug("3ds Max Frame Buffer is on")

                self._vr.output_splitgbuffer = False

                flg.debug("Clearing Output Directory")
                self._rt.rendOutputFilename = ""
                self._vr.output_splitFileName = ""

            elif fb_type is 1:
                self._rt.rendSaveFile = False
                self._vr.output_on = True
                flg.debug("VRay Frame Buffer is on")

                self._vr.output_splitgbuffer = False

                flg.debug("Clearing Output Directory")
                self._rt.rendOutputFilename = ""
                self._vr.output_splitFileName = ""

    def _override_image_filter(self):
        flg = logging.getLogger("renderFarming.Spinach._override_image_filter")
        filt = self._image_filter_override

        if filt is 18:
            flg.debug("Image Filter set to Off")
            self._vr.filter_on = False
        elif filt is 17:
            flg.debug("Image Filter will not be changed")
        else:
            self._vr.filter_on = True
            flg.debug("Image Filter set to index {}".format(self._image_filter_override))
            self._vr.filter_kernel = rFT.max_aa_filter(self._rt, filt)

    def _expand_frames_sub_folder(self):
        self._clg.debug("Sub Folder Edited")
        return self._frames_sub_folder.replace("$(cam)", self._cam_name)

    # noinspection PyMethodMayBeStatic
    def _gi_type_status_msg(self, render_type):
        """
        Returns a status message per GI Type
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
            -0:   Single Frame Irradiance Map, Light Cache
            -1:   From File Single Frame Irradiance Map, Light Cache
            -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache
            -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1)
            -4:   Animation Prepass Irradiance Map, Light Cache
            -5:   Animation Interpolated Irradiance Map, no secondary
            -6:   Brute Force, Light Cache
            -7:   Brute Force, From File Light Cache
            -8:   Brute Force, Light Cache with a new Light Cache every frame
            -9:   Brute Force, Brute Force
        :return: None
        """
        msg = {
            0: "Single Frame IR Prepass",
            1: "Single Frame IR Beauty",
            2: "Multi Frame IR Prepass",
            3: "Multi Frame IR Beauty",
            4: "Animated IR Prepass",
            5: "Animated IR Beauty",
            6: "Single Frame LC Prepass",
            7: "Single Frame LC Beauty",
            8: "Every Frame LC Beauty",
            9: "BF Beauty"
        }

        return msg.get(render_type, "{} Something has been goofed".format(rFT.html_color_text("Whoops: ", "Orange")))

    def _set_render_element_output(self):
        """
        Sets all of the scene's render elements to use the frames_dir path
        :return:
        """
        flg = logging.getLogger("renderFarming.Spinach._set_render_element_output")
        # Max's render element manger uses indexes instead of returning actual objects
        num = self._rem.NumRenderElements()
        flg.debug("Setting Output for {} Render Elements".format(num))

        for i in range(num):
            # retrieves the element and gets its name
            el = self._rem.GetRenderElement(i)
            el_name = str(el.elementname)

            # compiles a filename for the element in the correct path
            file_name = "{0}\\frame_{1}.exr".format(self._frames_dir, el_name)

            flg.debug("Assigning render element: {0} to file name: {1}".format(el_name, file_name))

            # Sets the filename for the element
            self._rem.SetRenderElementFilename(i, file_name)

    # ---------------------------------------------------
    #                       Public
    # ---------------------------------------------------

    def prepare_job(self):
        """
        Does all of the prep work to set up a job to run
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach.prepare_job")

        self._cam = self.get_cam()

        # Checks the validity of the camera
        if self._cam is None:
            # Sets Camera name to a string instead of returning a None object
            self._cam_name = "viewport"
            return
        else:
            # Gets a string of the camera's name
            self._cam_name = self._cam.name

        # Checks if VRay exists
        if self._vr is None:
            return

        # Checks if the containing folder should be named using the user specified sub folder field
        if self._sp_sub_fold_name_gi:
            gi_name = self._expand_frames_sub_folder()
        else:
            gi_name = self._cam_name

        # Sets file paths for the GI files
        self._ir_file = self._cfg.get_irradiance_cache_path() + "\\{0}.vrmap".format(gi_name)
        self._lc_file = self._cfg.get_light_cache_path() + "\\{0}.vrlmap".format(gi_name)

        # Sets file path for frames
        self._frames_dir = os.path.join(self._cfg.get_frames_path(), self._expand_frames_sub_folder())

        # Prints this to the Log
        flg.info("Irradiance Map: {}".format(self._ir_file))
        flg.info("Light Cache: {}".format(self._lc_file))
        flg.info("Frames Directory: {}".format(self._frames_dir))

        # Checks these directories
        if not self._verify_paths(self._cfg.get_irradiance_cache_path(),
                                  self._cfg.get_light_cache_path(),
                                  self._frames_dir):
            return

        # Prints a message
        self._status_message = self._grn_rdy_tx
        self._ready = True

    def single_frame_prepass(self):
        """
        Sets up a job to run an Irradiance Map job using single frame
        :return:
        """
        self.prepare_prepass(0)

    def from_file(self):
        """
        Sets up a job to run using a pre-baked Irradiance Map and Light Cache
        :return: None
        """
        self.prepare_beauty_pass(1)

    def prepare_prepass(self, render_type):
        """
        Sets up the render for a prepass
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
                -0:   Single Frame Irradiance Map, Light Cache
                -2:   Multi Frame Incremental Irradiance Map, Single Frame Light Cache
                -4:   Animation Prepass Irradiance Map, Light Cache
                -6:   Brute Force, Light Cache
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach.prepare_prepass")

        self.rsd_toggle()

        if render_type in (1, 3, 5, 7, 8, 9):
            flg.error("Attempting to render a beauty pass as a prepass")
            self._status_message = "{} Attempting to render a beauty pass as a prepass".format(self._rd_er_tx)
            return

        if not self._ready:
            flg.info("Spinach reports not ready, job submission cannot continue")
            nr = rFT.html_color_text("Not Ready:", "Orange")
            self._status_message = "{0}: {1}".format(nr, self._status_message)
            return

        # if is an Animation Prepass Irradiance Map, Light Cache, the ir path must be changed
        if render_type is 4:
            self._set_animation_prepass_path()

        self._set_gi_paths()
        self._set_gi_engine(render_type)
        self._set_gi_save_to_frame(render_type)

        flg.debug("Setting VRay to render only GI")
        self._vr.options_dontRenderImage = True

        flg.debug("Setting render time output")
        self._set_frame_time_type(render_type)

        flg.debug("Overriding Image Filter")
        self._override_image_filter()

        self._status_message = "{0} - {1}".format(self._grn_rdy_tx,
                                                  self._gi_type_status_msg(render_type))
        self._log_status(flg)

        flg.debug("Setting Output")
        self._set_output(self._frame_buffer_type, False)

        self.rsd_toggle(True)

    def prepare_beauty_pass(self, render_type):
        """
        Sets up the render for the beauty pass
        :param render_type: The combination of Gi settings used by the renderer
        Types supported:
                -1:   From File Single Frame Irradiance Map, Light Cache
                -3:   From File Multi Frame Incremental Irradiance Map, Light Cache (Duplicate of 1)
                -5:   Animation Interpolated Irradiance Map, no secondary
                -7:   Brute Force, From File Light Cache
                -8:   Brute Force, Light Cache with a new Light Cache every frame
                -9:   Brute Force, Brute Force
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach.prepare_beauty")

        self.rsd_toggle()

        if not self._ready:
            flg.info("Spinach reports not ready, job submission cannot continue")
            self._status_message = "{0}: {1}".format(self._org_n_rdy_tx, self._status_message)
            return

        if render_type in (0, 2, 4, 6):
            flg.error("Attempting to render a prepass as a beauty pass")
            nr = rFT.html_color_text("Not Ready:", "Orange")
            self._status_message = "{} Attempting to render a prepass as a beauty pass".format(nr)
            return

            # if is an Animation Prepass Irradiance Map, Light Cache, the ir path must be changed
        if render_type is 5:
            self._set_animation_prepass_path()

        self._set_gi_paths()
        self._set_gi_engine(render_type)
        self._set_gi_save_to_frame(render_type)

        flg.debug("Setting VRay to render final image")
        self._vr.options_dontRenderImage = False

        flg.debug("Setting render time output")
        self._set_frame_time_type(render_type)

        flg.debug("Setting Output")
        self._set_output(self._frame_buffer_type, True)

        flg.debug("Overriding Image Filter")
        self._override_image_filter()

        flg.debug("File Ready for Final Render")
        self._status_message = "{0} - Beauty - {1}".format(self._grn_rdy_tx,
                                                           self._gi_type_status_msg(render_type))

        self.rsd_toggle(True)

    def check_camera(self):
        """
        Makes sure that camera updates trigger a job reset
        :return: None
        """
        if self.get_cam() is not self._cam:
            self._ready = False

    def rsd_toggle(self, restore=False):
        """
        If the render scene dialog is open, this will close it and reopen it after the script is run
        :return: None
        """
        if not restore:
            if self._rt.renderSceneDialog.isOpen():
                self._rsd_state = True
                self._clg.debug("Closing \"Render Scene Dialog\"")
                self._rt.renderSceneDialog.close()
            else:
                self._rsd_state = False

        else:
            self._clg.debug("Updating \"Render Scene Dialog\"")
            self._rt.renderSceneDialog.update()

            self._clg.debug("\"Render Scene Dialog\" state: {}".format(self._rsd_state))
            if self._rsd_state:
                self._clg.debug("Opening \"Render Scene Dialog\"")
                self._rt.renderSceneDialog.open()

    # def restore_original_render_settings(self):
    #     if self._orig_settings is not None:
    #         self._orig_settings.set_rps()

    def reset_renderer(self):
        flg = logging.getLogger("renderFarming.Spinach.reset_renderer")
        self.rsd_toggle()

        rc = self._rt.RendererClass.classes
        renderer_list = list(rc)

        vray_ind = -1
        scan_ind = -1
        for i in range(0, len(renderer_list)):
            renderer_name = str(renderer_list[i])
            if "V_Ray_Adv" in renderer_name:
                vray_ind = i
            elif "Default_Scanline_Renderer" in renderer_name:
                scan_ind = i
        try:
            self._rt.renderers.current = rc[scan_ind]()
            self._rt.renderers.current = rc[vray_ind]()
        except IndexError:
            flg.error("One or more renderers are not loaded, Unable to continue")
            return None

        self._verify_vray()
        self._status_message = "VRay has been reset"
        self.rsd_toggle(True)

    # noinspection PyMethodMayBeStatic
    def submit(self):
        """
        Submits the current file to Backburner
        :return: None
        """
        flg = logging.getLogger("renderFarming.Spinach.submit")
        flg.debug("Submitting file to Backburner")
        rFNR.submit_current_file()
        flg.debug("File submitted to Backburner")

    # ---------------------------------------------------
    #                       Getters
    # ---------------------------------------------------

    def get_cam(self):
        """
        Gets the active 3DS Max camera
        :return: a 3DS Max Camera object
        """
        flg = logging.getLogger("renderFarming.Spinach._get_cam")
        cam = self._rt.getActiveCamera()
        if cam is None:
            flg.error("Active view is not a valid camera")
            self._status_message = "{} Active view is not a valid camera".format(self._rd_er_tx)
        else:
            flg.debug("Active camera selected: {}".format(cam.name))
        return cam

    def get_ready_status(self):
        """
        Ascertains if the job has cleared and is ready to be rendered
        :return: Boolean: Status
        """
        return self._ready

    def get_status_message(self):
        return self._status_message

    # ---------------------------------------------------
    #                       Setters
    # ---------------------------------------------------

    def set_frame_buffer_type(self, fb_type):
        flg = logging.getLogger("renderFarming.Spinach.set_frame_buffer_type")
        if fb_type > 1:
            flg.error("Index Error: Index is greater than allowed")
            self._frame_buffer_type = 0
        elif fb_type < 0:
            flg.error("Index Error: Index is less than 0")
            self._frame_buffer_type = 0
        else:
            flg.debug("Changing Frame Buffer Type to {}".format("Max" if fb_type is 0 else "VRay"))
            self._frame_buffer_type = fb_type

    def set_image_filter_override(self, if_type):
        flg = logging.getLogger("renderFarming.Spinach.set_frame_buffer_type")
        if if_type > 18:
            flg.error("Index Error: Index is greater than allowed")
            self._image_filter_override = if_type
        elif if_type < 0:
            flg.error("Index Error: Index is less than 0")
            self._image_filter_override = if_type
        else:
            flg.debug("Changing Image Filter to index: {}".format(if_type))
            self._image_filter_override = if_type

    def set_frames_sub_folder(self, fsf_string):
        self._frames_sub_folder = fsf_string

    def set_pad_gi(self, is_checked):
        self._pad_gi = is_checked

    def set_multi_frame_increment(self, increment):
        flg = logging.getLogger("renderFarming.Spinach.set_multi_frame_increment")
        if increment < 1:
            flg.error("Index Error: Index is less than 1")
        else:
            self._multi_frame_increment = increment

    def set_nth_frame(self, nth_frame):
        self._nth_frame = nth_frame

    def set_sub_folder_as_gi_name(self, ckbx_bool):
        self._sp_sub_fold_name_gi = ckbx_bool
