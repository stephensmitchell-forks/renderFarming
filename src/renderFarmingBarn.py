import MaxPlus
import pymxs
from random import randrange

import os

import renderFarmingTools as rFT

import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

from _version import __version__

rt = pymxs.runtime

vr = rFT.verify_vray(rt)

Signal = QtC.Signal
Slot = QtC.Slot


class RFMsg(object):
    def __init__(self, message, level):
        super(RFMsg, self).__init__()
        self._message = str(message)
        self._level = str(level)

    def get_message(self):
        return self._message

    def get_level(self):
        return self._level


class RenderFarmingBarnUI(QtW.QDialog):
    def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
        super(RenderFarmingBarnUI, self).__init__(parent)

        # ---------------------------------------------------
        #                 Layouts
        # ---------------------------------------------------

        self._main_layout = QtW.QVBoxLayout()
        self._sheep_layout = QtW.QHBoxLayout()

        # ---------------------------------------------------
        #                 Window
        # ---------------------------------------------------

        self.setWindowTitle("Barn - RenderFarming{}".format(__version__))

        # ---------------------------------------------------
        #                 Widgets
        # ---------------------------------------------------

        # A list of constructors for objects inheriting the Sheep class

        self._sheep = [
            ToggleSphericalWidget(),
            ClearMaterial(),
            WireColorEdits(),
            VisibilityToggle(),
            QuickExporter()
        ]

        self._display_message_mw = MessageWidget()

        # ---------------------------------------------------
        #                 Initialization
        # ---------------------------------------------------

        for widget in self._sheep:
            self._sheep_layout.addWidget(widget)
            widget.Message.connect(self._display_message_handler)
            widget.InitStatusBar.connect(self._display_status_bar_handler)
            widget.StAdd.connect(self._add_status_bar_handler)

        # ---------------------------------------------------
        #                 Final Setup
        # ---------------------------------------------------

        self.setLayout(self._main_layout)
        self._main_layout.addLayout(self._sheep_layout)
        self._main_layout.addWidget(self._display_message_mw)

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    @ Slot(RFMsg)
    def _display_message_handler(self, message_object):
        self._display_message_mw.set_message(message_object)

    @Slot(int)
    def _display_status_bar_handler(self, amount):
        self._display_message_mw.set_message(amount)

    @Slot(int)
    def _add_status_bar_handler(self, add):
        self._display_message_mw.set_message(add)


class MessageWidget(QtW.QFrame):
    def __init__(self):
        super(MessageWidget, self).__init__()
        self._message_layout = QtW.QHBoxLayout()

        self._display_message_lb = QtW.QLabel()

        self._display_message_title_lb = QtW.QLabel()
        self._display_message_title_lb.setText("Status: ")
        self._display_message_title_lb.setSizePolicy(QtW.QSizePolicy.Maximum, QtW.QSizePolicy.Preferred)

        self.setFrameStyle(QtW.QFrame.Panel)
        self.setLayout(self._message_layout)

        self._message_layout.addWidget(self._display_message_title_lb)
        self._message_layout.addWidget(self._display_message_lb)

    def set_message(self, message):
        self._display_message_lb.setText(message.get_message())
        self._display_message_title_lb.setText("{}: ".format(message.get_level()))


class QHLine(QtW.QFrame):
    """
    Credit to Stack Overflow User Michael Leonard: https://stackoverflow.com/a/41068447
    From: https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
    """
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtW.QFrame.HLine)
        self.setFrameShadow(QtW.QFrame.Sunken)


class RenderFarmingSheep(QtW.QWidget):
    Message = Signal(RFMsg)
    InitStatusBar = Signal(int)
    StAdd = Signal(int)

    def __init__(self, parent=None):
        super(RenderFarmingSheep, self).__init__(parent)

        self._super_layout = QtW.QVBoxLayout()
        self._frame_interior_layout = QtW.QVBoxLayout()
        self.MainLayout = QtW.QVBoxLayout()

        self._frame = QtW.QFrame()
        self._sheep_tilte_lb = QtW.QLabel()

        # Labels have default text set to untitled
        self._sheep_tilte_lb.setText("Untitled")

        # Structure:
        # - A super Layout containing the entire UI
        #   - A Frame around the buttons
        #       - A Layout for the frame interior
        #           - A Label
        #           - The MainLayout which is accesable from children
        #           - A Stretch

        self.setLayout(self._super_layout)
        self._super_layout.addWidget(self._frame)
        self._frame.setLayout(self._frame_interior_layout)

        self._frame_interior_layout.addWidget(self._sheep_tilte_lb)
        self._frame_interior_layout.addLayout(self.MainLayout)
        self._frame_interior_layout.addStretch()

        self._frame.setFrameStyle(QtW.QFrame.Panel)

    def msg(self, message, level="info"):
        self.Message.emit(RFMsg(message, level))

    def stadd(self, amount=1):
        self.StAdd.emit(amount)

    def initialize_status_bar(self, length):
        self.InitStatusBar.emit(length)

    # Using Qt naming convention instead
    # noinspection PyPep8Naming
    def setTitle(self, text):
        self._sheep_tilte_lb.setText(text)


class ToggleSphericalWidget(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(ToggleSphericalWidget, self).__init__(parent)

        self.setTitle("Toggle Spherical")

        # ---------------------------------------------------
        #                 Attributes
        # ---------------------------------------------------

        self._spherical_on = False
        self._stereo_on = False
        self._VRayStereoscopic_node = None

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._toggle_btn = QtW.QPushButton()
        self.MainLayout.addWidget(self._toggle_btn)
        self._toggle_btn.setText("Toggle Spherical")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(self._check_spherical())

        self._stereo_btn = QtW.QPushButton()
        self.MainLayout.addWidget(self._stereo_btn)
        self._stereo_btn.setText("Toggle Stereo")
        self._stereo_btn.setCheckable(True)
        self._stereo_btn.setChecked(self._check_stereo())

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # noinspection PyUnresolvedReferences
        self._toggle_btn.toggled.connect(self._spherical_toggle_handler)
        # noinspection PyUnresolvedReferences
        self._stereo_btn.toggled.connect(self._stereo_toggle_handler)

    # ---------------------------------------------------
    #                  Handler Functions
    # ---------------------------------------------------

    def _spherical_toggle_handler(self):
        # Just Triggers the right handler for each state
        if self._spherical_on:
            self._spherical_off_handler()
        else:
            self._spherical_on_handler()

    def _stereo_toggle_handler(self):
        # Creates a Helper object if one doesn't already exist
        # Triggers the right handler for each state
        if self._VRayStereoscopic_node is not None:
            # sets the state to the opposite of the current
            if self._stereo_on:
                self._VRayStereoscopic_node.enabled = False
            else:
                self._VRayStereoscopic_node.enabled = True

            # Flipping the boolean
            self._stereo_on = not self._stereo_on
        else:
            # Creates a New Handler
            self._create_new_helper()
            self._stereo_on = True

    def _spherical_on_handler(self):
        # Sets the VRay settings to render a spherical camera
        vr.camera_type = 9
        vr.camera_overrideFOV = True
        vr.camera_fov = 360.0
        vr.camera_cyl_height = 180.0

        self._spherical_on = True

    def _spherical_off_handler(self):
        # Sets the Vray settings to disable spherical camera rendering
        vr.camera_type = 0
        vr.camera_overrideFOV = False
        vr.camera_fov = 45.0
        vr.camera_cyl_height = 90.0

        self._spherical_on = False

    # ---------------------------------------------------
    #                  Checking Functions
    # ---------------------------------------------------

    def _check_spherical(self):
        # if the camera type is set to 9, VRay is put into spherical mode
        a = (vr.camera_type == 9)
        self._spherical_on = a
        return a

    def _check_stereo(self):
        # Looks for a _VRayStereoscopic helper node which is how stereo settings are enabled
        if self._search_for_stereo_helper():
            a = self._VRayStereoscopic_node.enabled
            self._stereo_on = a
            return a
        else:
            # If one doesn't exist, False is returned
            return False

    def _search_for_stereo_helper(self):
        # Searches for instances of the VRayStereoscopic class
        objects = rt.getClassInstances(rt.VRayStereoscopic)
        if len(objects) == 1:
            # This is the ideal state
            self._VRayStereoscopic_node = objects[0]
            return True
        elif len(objects) > 1:
            # If there are more than one nodes, it gives a warning asking for the user to delete them
            self._VRayStereoscopic_node = objects[0]
            self.msg("Multiple VRayStereoscopic helpers found.  Please clean them up.", "Warning")
            return True
        else:
            # Nothing found
            return False

    def _create_new_helper(self):
        # Creates a New Stereo Helper with the right settings for spherical renderings
        new_helper = rt.VRayStereoscopic()
        new_helper.adjust_resolution = True
        new_helper.output_layout = 1

        # The RT decoder is liable to fail, so it is wrapped in a Try statement
        try:
            new_helper.eye_distance = rt.units.decodeValue("63mm")
        except RuntimeError:
            self.msg("Unable to Decode Units.  Intraocular Distance may be incorrect.", "Error")

        self._VRayStereoscopic_node = new_helper

        # Viewport needs to be redrawn after so that the new node appears
        rt.redrawViews()


class ClearMaterial(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(ClearMaterial, self).__init__(parent)

        self.setTitle("Material Clear")

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._clear_materials_btn = QtW.QPushButton()
        self.MainLayout.addWidget(self._clear_materials_btn)
        self._clear_materials_btn.setText("Clear Materials")

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # noinspection PyUnresolvedReferences
        self._clear_materials_btn.clicked.connect(self._clear_materials_handler)

    # noinspection PyMethodMayBeStatic
    def _clear_materials_handler(self):
        # Collect selection
        sel = rt.getCurrentselection()

        sel_len = len(sel)

        if sel_len < 1:
            self.msg("No objects selected")
        else:
            # set materials to be Undefined
            for obj in sel:
                obj.material = rt.undefined

            # Redraw the viewport
            rt.redrawViews()
            self.msg("Cleared Materials from {0} {1}".format(sel_len, pluralize("object", sel_len)))


class VisibilityToggle(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(VisibilityToggle, self).__init__(parent)

        self.setTitle("Visibility Toggle")

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._visibility_on = QtW.QPushButton()
        self.MainLayout.addWidget(self._visibility_on)
        self._visibility_on.setText("Make Visible")

        self._visibility_off = QtW.QPushButton()
        self.MainLayout.addWidget(self._visibility_off)
        self._visibility_off.setText("Make Invisible")

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # noinspection PyUnresolvedReferences
        self._visibility_on.clicked.connect(self._visibility_on_handler)
        self._visibility_off.clicked.connect(self._visibility_off_handler)

    # noinspection PyMethodMayBeStatic
    def _visibility_on_handler(self):
        with pymxs.undo(True, "Visibility On"):
            # Collect selection
            sel = rt.getCurrentselection()

            sel_len = len(sel)

            if sel_len < 1:
                self.msg("No objects selected")
            else:
                # set visibility to be on
                for obj in sel:
                    obj.visibility = True

                # Redraw the viewport
                rt.redrawViews()
                self.msg("Visibility set to 1.0 on {0} {1}".format(sel_len, pluralize("object", sel_len)))

    # noinspection PyMethodMayBeStatic
    def _visibility_off_handler(self):
        with pymxs.undo(True, "Visibility Off"):
            # Collect selection
            sel = rt.getCurrentselection()

            sel_len = len(sel)

            if sel_len < 1:
                self.msg("No objects selected")
            else:
                # set visibility to be on
                for obj in sel:
                    obj.visibility = False

                # Redraw the viewport
                rt.redrawViews()
                self.msg("Visibility set to 0.0 on {0} {1}".format(sel_len, pluralize("object", sel_len)))


class WireColorEdits(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(WireColorEdits, self).__init__(parent)

        self.setTitle("Wire Color Editor")

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._fix_wire_colors_btn = QtW.QPushButton()
        self.MainLayout.addWidget(self._fix_wire_colors_btn)
        self._fix_wire_colors_btn.setText("Fix Bad Wire Colors")

        self._random_wire_color = QtW.QPushButton()
        self.MainLayout.addWidget(self._random_wire_color)
        self._random_wire_color.setText("Random Wire Color")

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # noinspection PyUnresolvedReferences
        self._fix_wire_colors_btn.clicked.connect(self._fix_wire_colors_handler)
        self._random_wire_color.clicked.connect(self._random_wire_color_handler)

    def _fix_wire_colors_handler(self):
        sel = rt.getCurrentselection()
        layers = list()
        to_fix = list()

        sel_len = len(sel)

        if sel_len < 1:
            self.msg("No objects selected")
        else:
            # First step is to analyze the objects
            for obj in sel:
                # If objects are using layer colors, then they will get fixed as well
                if obj.colorByLayer is True:
                    layers.append(obj.layer)
                else:
                    # Bad colors go into the to_fix list
                    if not self._analyze_wire_color(obj.wirecolor):
                        to_fix.append(obj)

            # Then analyze the Layers
            for lay in layers:
                # Bad colors go into the to_fix list
                if not self._analyze_wire_color(lay.wireColor):
                    to_fix.append(lay)

            for obj in to_fix:
                obj.wirecolor = self._random_color()

            # Redraw the viewport
            rt.redrawViews()
            self.msg("Wire Color fixed on {0}/{1} {2}".format(len(to_fix), sel_len, pluralize("object", sel_len)))

    def _random_wire_color_handler(self):
        sel = rt.getCurrentselection()

        sel_len = len(sel)

        if sel_len < 1:
            self.msg("No objects selected")
        else:
            for obj in sel:
                obj.wirecolor = self._random_color()

            # Redraw the viewport
            rt.redrawViews()
            self.msg("Wire Color randomized on {0} {1}".format(sel_len, pluralize("object", sel_len)))

    def _analyze_wire_color(self, color):
        # Checks saturation and value
        if not self._check_saturation(color):
            return False
        elif not self._check_value(color):
            return False
        else:
            return True

    # noinspection PyMethodMayBeStatic
    def _check_saturation(self, color):
        return True if color.s > 50 else False

    # noinspection PyMethodMayBeStatic
    def _check_value(self, color):
        return True if color.v > 20 else False

    # noinspection PyMethodMayBeStatic
    def _random_color(self):
        return rt.color(randrange(3, 255), randrange(3, 255), randrange(3, 255))


def pluralize(text, count):
    return text + 's' if (count > 1) else text


class QuickExporter(RenderFarmingSheep):
    def __init__(self):
        super(QuickExporter, self).__init__()

        self.setTitle("Quick Export")

        self._exp_directory = str()
        self._exp_filename = str()
        self._exp_format = str()

        self._mesh_classes_list = [
            "editable_poly",
            "polymeshobject",
            "editable_mesh",
            "sphere",
            "ProBoolean",
            "box"
        ]

        self._export_formats_list = {
            "OBJ": rt.ObjExp,
            "DAE": rt.DAEEXP,
            "FBX": rt.FBXEXP
        }

        self._export_context = True
        self._export_context_list = {
            "Single File": False,
            "One File Per Object": True
        }

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        # Main ----------------------------------------------
        # ---- Export Directory -----------------------------

        self._exp_dir_le = QtW.QLineEdit()
        self._exp_dir_browse_btn = QtW.QToolButton()

        self._exp_dir_browse_btn.setText("...")
        self._exp_dir_le.setText("Export Directory")

        self._exp_dir_layout = QtW.QHBoxLayout()
        self._exp_dir_layout.addWidget(self._exp_dir_le)
        self._exp_dir_layout.addWidget(self._exp_dir_browse_btn)

        # ---- Other ----------------------------------------

        self._export_btn = QtW.QPushButton()
        self._export_format_cmbx = QtW.QComboBox()
        self._export_context_cmbx = QtW.QComboBox()

        self._export_btn.setText("Export")
        self._export_format_cmbx.addItems(self._export_formats_list.keys())
        self._export_format_cmbx.setCurrentText("FBX")

        self._export_context_cmbx.addItems(self._export_context_list.keys())
        self._export_context_cmbx.setCurrentText("One File Per Object")

        # Options -------------------------------------------

        self._options_gb = QtW.QGroupBox()
        self._options_layout = QtW.QVBoxLayout()

        self._pivot_to_origin_chbx = QtW.QCheckBox("Pivot to Origin")
        self._pivot_to_origin_chbx.setChecked(True)
        self._options_layout.addWidget(self._pivot_to_origin_chbx)

        self._collapse_stack_chbx = QtW.QCheckBox("Collapse Modifier Stack")
        self._collapse_stack_chbx.setChecked(True)
        self._options_layout.addWidget(self._collapse_stack_chbx)

        self._rotate_for_unity_chbx = QtW.QCheckBox("Rotate for Unity")
        self._rotate_for_unity_chbx.setChecked(True)
        self._options_layout.addWidget(self._rotate_for_unity_chbx)

        self._reset_x_form = QtW.QCheckBox("Reset X-Forms")
        self._reset_x_form.setChecked(True)
        self._options_layout.addWidget(self._reset_x_form)

        self._options_gb.setLayout(self._options_layout)

        # Layouts -------------------------------------------

        self.MainLayout.addWidget(self._export_context_cmbx)
        self.MainLayout.addWidget(QHLine())
        self.MainLayout.addLayout(self._exp_dir_layout)
        self.MainLayout.addWidget(self._export_format_cmbx)
        self.MainLayout.addWidget(self._options_gb)
        self.MainLayout.addWidget(self._export_btn)

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        self._exp_dir_browse_btn.clicked.connect(self._exp_dir_browse_btn_handler)
        self._export_btn.clicked.connect(self._export_handler)
        self._export_context_cmbx.activated.connect(self._export_type_cmbx_handler)

        self._set_dir(rt.GetDir(rt.name("export")))

    def _single_mesh_context(self):
        self._pivot_to_origin_chbx.setChecked(False)
        self._pivot_to_origin_chbx.setVisible(False)
        self._rotate_for_unity_chbx.setChecked(False)
        self._rotate_for_unity_chbx.setVisible(False)
        self._export_format_cmbx.setVisible(False)
        self._export_context = False

    def _one_per_file_context(self):
        self._pivot_to_origin_chbx.setChecked(True)
        self._pivot_to_origin_chbx.setVisible(True)
        self._rotate_for_unity_chbx.setChecked(True)
        self._rotate_for_unity_chbx.setVisible(True)
        self._export_format_cmbx.setVisible(True)
        self._export_context = True

    def _set_dir(self, directory):
        if os.path.isdir(directory):
            self._exp_dir_le.setText(directory)
            self._exp_dir_le.setToolTip(directory)
            self._exp_directory = directory
        else:
            self.msg("Directory: {} does not exist".format(directory), "Warning")

    def _set_filename(self, file_name):
        self._exp_filename = file_name

    def _exp_dir_browse_btn_handler(self):
        if self._export_context:
            # noinspection PyCallByClass
            file_name = QtW.QFileDialog.getExistingDirectory(
                self,
                "Choose Export Directory",
                self._exp_directory,
            )
            if file_name:
                self._set_dir(file_name)
        else:
            # noinspection PyCallByClass
            file_names_list = QtW.QFileDialog.getSaveFileName(
                self,
                "Export Selected",
                self._exp_directory,
                "*.fbx;;*.dae;;*.obj"
            )
            if file_names_list[0]:
                directory, file_name = os.path.split(file_names_list[0])
                self._set_dir(directory)
                self._set_filename(file_name)

    def _export_handler(self):
        if self._export_context:
            if os.path.isdir(self._exp_directory):
                    self._process_file_per_object()
            else:
                self.msg("Directory: {} does not exist".format(self._exp_directory), "Warning")
        else:
            if os.path.isdir(self._exp_directory):
                self._process_single_file()
            else:
                self.msg("Directory: {} does not exist".format(self._exp_directory), "Warning")

    def _export_type_cmbx_handler(self):
        if self._export_context_list.get(self._export_context_cmbx.currentText()):
            self._one_per_file_context()
        else:
            self._single_mesh_context()

    def _process_file_per_object(self):
        sel = rt.getCurrentselection()
        sel_len = len(sel)
        count = 0

        if sel_len < 1:
            self.msg("No objects selected")
        else:
            # disables viewport redraw
            with pymxs.redraw(False):
                for obj in sel:
                    # clone object
                    obj_clone = rt.copy(obj)
                    try:
                        if (str(rt.classof(obj))).lower() in self._mesh_classes_list:
                            self._prep_for_export(
                                obj,
                                obj_clone,
                                pivot_to_origin=self._pivot_to_origin_chbx.isChecked(),
                                rotate_for_unity=self._rotate_for_unity_chbx.isChecked(),
                                collapse_stack=self._collapse_stack_chbx.isChecked(),
                                reset_x_forms=self._reset_x_form.isChecked()
                            )
                            count += 1
                            self._export_file_per_object(obj_clone, self._export_format_cmbx.currentText())
                    except RuntimeError as e:
                        self.msg(e, "Error")
                        return
                    except AttributeError as e:
                        self.msg(e, "Error")
                        return
                    finally:
                        rt.redrawViews()
                        rt.delete(obj_clone)

            self.msg("Exported {0}/{1} {2}".format(count, sel_len, pluralize("object", sel_len)))

    def _process_single_file(self):
        sel = rt.getCurrentselection()
        sel_len = len(sel)
        count = 0

        clones = list()

        if sel_len < 1:
            self.msg("No objects selected")
        else:
            # disables viewport redraw
            with pymxs.redraw(False):
                try:
                    # prep clones
                    for obj in sel:
                        # clone object
                        obj_clone = rt.copy(obj)
                        if (str(rt.classof(obj))).lower() in self._mesh_classes_list:
                            self._prep_for_export(
                                obj,
                                obj_clone,
                                pivot_to_origin=False,
                                rotate_for_unity=False,
                                collapse_stack=self._collapse_stack_chbx.isChecked(),
                                reset_x_forms=self._reset_x_form.isChecked()
                            )
                            clones.append(obj_clone)
                            count += 1
                    # export clones
                    self._export_single(clones)
                except RuntimeError as e:
                    self.msg(e, "Error")
                    return
                except AttributeError as e:
                    self.msg(e, "Error")
                    return
                finally:
                    rt.redrawViews()
                    rt.delete(clones)

            self.msg("Exported {0}/{1} {2}".format(count, sel_len, pluralize("object", sel_len)))

    def _export_file_per_object(self, obj, exp_format):
        rt.select(obj)
        file_name = os.path.join(
            self._exp_directory, "{0}.{1}".format(
                obj.name,
                exp_format.lower()
            )
        )
        rt.exportFile(
            file_name,
            rt.name("noPrompt"),
            using=self._export_formats_list.get(exp_format, rt.FBXEXP),
            selectedOnly=True
        )

    def _export_single(self, objects):
        rt.select(*rt.array(objects))
        file_name = os.path.join(
            self._exp_directory, self._exp_filename
        )
        rt.exportFile(
            file_name,
            rt.name("noPrompt"),
            using=self._export_formats_list.get(self._exp_format, rt.FBXEXP),
            selectedOnly=True
        )

    # noinspection PyMethodMayBeStatic
    def _prep_for_export(self, original, clone, **kwargs):
        # Translated to python from "3dsmax 2016 small export script" by lops
        # http://www.scriptspot.com/3ds-max/scripts/3dsmax-2016-small-export-script

        rt.select(clone)

        if kwargs.get("rotate_for_unity", False):
            # rotate clone by 90 degrees
            current_xform = original.transform
            rt.PreRotate(current_xform, rt.eulerToQuat(rt.EulerAngles(90, 0, 0)))
            clone.transform = current_xform

        # Reset X-Froms
        if kwargs.get("reset_x_forms", False):
            rt.ResetXForm(clone)
        if kwargs.get("collapse_stack", False):
            rt.macros.run("Modifier Stack", "Convert_to_Poly")

        # Record Info
        obj_name = original.name
        clone.name = obj_name

        # Set pivot to origin
        if kwargs.get("pivot_to_origin", False):
            clone.position = rt.Point3(0, 0, 0)


ui = RenderFarmingBarnUI()
ui.show()
