import MaxPlus
import pymxs
from random import randrange

import renderFarmingTools as rFT

import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

rt = pymxs.runtime

vr = rFT.verify_vray(rt)

Signal = QtC.Signal
Slot = QtC.Slot


class RFMsg(object):
    def __init__(self, message):
        super(RFMsg, self).__init__()
        self._message = message

    def get_message(self):
        return self._message


class RenderFarmingBarnUI(QtW.QDialog):
    def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
        super(RenderFarmingBarnUI, self).__init__(parent)

        self._main_layout = QtW.QHBoxLayout()
        self.setLayout(self._main_layout)

        # ---------------------------------------------------
        #                 Widgets
        # ---------------------------------------------------

        self._sheep = [
            ToggleSphericalWidget(),
            ClearMaterial(),
            WireColorEdits()
        ]

        # ---------------------------------------------------
        #                 Initialization
        # ---------------------------------------------------

        for widget in self._sheep:
            self._main_layout.addWidget(widget)
            widget.Message.connect(self._display_message_handler)

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

    # ---------------------------------------------------
    #                  Handler Function
    # ---------------------------------------------------

    @ Slot(RFMsg)
    def _display_message_handler(self, message_object):
        print(message_object.get_message())


class RenderFarmingSheep(QtW.QWidget):
    Message = Signal(RFMsg)

    def __init__(self, parent=None):
        super(RenderFarmingSheep, self).__init__(parent)

        self._super_layout = QtW.QVBoxLayout()
        self.MainLayout = QtW.QVBoxLayout()

        self.setLayout(self._super_layout)
        self._super_layout.addLayout(self.MainLayout)

    def msg(self, message):
        self.Message.emit(RFMsg(message))


class ToggleSphericalWidget(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(ToggleSphericalWidget, self).__init__(parent)

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
            self.msg("WARNING: Multiple VRayStereoscopic helpers found.  Please clean them up.")
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
            self.msg("ERROR: Unable to Decode Units.  Intraocular Distance may be incorrect.")

        self._VRayStereoscopic_node = new_helper

        # Viewport needs to be redrawn after so that the new node appears
        rt.redrawViews()


class ClearMaterial(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(ClearMaterial, self).__init__(parent)

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

        # set materials to be Undefined
        for obj in sel:
            obj.material = rt.undefined

        # Redraw the viewport
        rt.redrawViews()


class WireColorEdits(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(WireColorEdits, self).__init__(parent)

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

    def _random_wire_color_handler(self):
        sel = rt.getCurrentselection()

        for obj in sel:
            obj.wirecolor = self._random_color()

        # Redraw the viewport
        rt.redrawViews()

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


ui = RenderFarmingBarnUI()
ui.show()
