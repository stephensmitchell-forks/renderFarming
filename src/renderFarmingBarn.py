import MaxPlus
import pymxs

import renderFarmingTools as rFT

import PySide2.QtWidgets as QtW
import PySide2.QtCore as QtC
import PySide2.QtGui as QtG

rt = pymxs.runtime

vr = rFT.verify_vray(rt)


class RenderFarmingBarnUI(QtW.QDialog):
    def __init__(self, parent=MaxPlus.GetQMaxMainWindow()):
        super(RenderFarmingBarnUI, self).__init__(parent)

        self._main_layout = QtW.QHBoxLayout()
        self.setLayout(self._main_layout)

        # ---------------------------------------------------
        #                 Widget Definitions
        # ---------------------------------------------------

        self._toggle_spherical_sheep = ToggleSphericalWidget()
        self._main_layout.addWidget(self._toggle_spherical_sheep)

        # ---------------------------------------------------
        #               Function Connections
        # ---------------------------------------------------

        # ---------------------------------------------------
        #                  Handler Function
        # ---------------------------------------------------


class RenderFarmingSheep(QtW.QWidget):
    def __init__(self, parent=None):
        super(RenderFarmingSheep, self).__init__(parent)

        self._super_layout = QtW.QVBoxLayout()
        self.MainLayout = QtW.QVBoxLayout()

        self.setLayout(self._super_layout)
        self._super_layout.addLayout(self.MainLayout)


class ToggleSphericalWidget(RenderFarmingSheep):
    def __init__(self, parent=None):
        super(ToggleSphericalWidget, self).__init__(parent)

        self._spherical_on = False
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
        if self._spherical_on:
            self._spherical_off_handler()
        else:
            self._spherical_on_handler()

    def _stereo_toggle_handler(self):
        if self._stereo_on:
            self._VRayStereoscopic_node.enabled = False
        else:
            self._VRayStereoscopic_node.enabled = True

        self._stereo_on = not self._stereo_on

    def _spherical_on_handler(self):
        vr.camera_type = 9
        vr.camera_overrideFOV = True
        vr.camera_fov = 360.0
        vr.camera_cyl_height = 180.0

        self._spherical_on = True

    def _spherical_off_handler(self):
        vr.camera_type = 0
        vr.camera_overrideFOV = False
        vr.camera_fov = 45.0
        vr.camera_cyl_height = 90.0

        self._spherical_on = False

    # ---------------------------------------------------
    #                  Checking Functions
    # ---------------------------------------------------

    def _check_spherical(self):
        a = vr.camera_type == 9
        self._spherical_on = a
        return a

    def _check_stereo(self):
        if self._VRayStereoscopic_node is None:
            self._search_for_stereo_helper()

        a = self._VRayStereoscopic_node.enabled
        self._stereo_on = a
        return a

    def _search_for_stereo_helper(self):
        objects = rt.getClassInstances(rt.VRayStereoscopic)
        print(objects)
        if len(objects) == 1:
            self._VRayStereoscopic_node = objects[0]
        elif len(objects) > 1:
            self._VRayStereoscopic_node = objects[0]
            print("ERROR: Multiple VRayStereoscopic helpers found.  Please clean them up.")
        else:
            new_helper = rt.VRayStereoscopic()
            new_helper.adjust_resolution = True
            new_helper.output_layout = 1

            try:
                new_helper.eye_distance = rt.units.decodeValue("63mm")
            except RuntimeError:
                print("ERROR: Unable to Decode Units.  Intraocular Distance may be incorrect.")

            self._VRayStereoscopic_node = new_helper


ui = RenderFarmingBarnUI()
ui.show()
