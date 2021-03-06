# -*- coding: utf-8 -*-

"""
RenderFarming

by Avery Brown


Thanks to:

Josh Hollander
Chris Cerrone
Seiji Anderson
John Szot


RenderFarming is a 3ds Max script which handles many scene management tasks with a PySide2 based interface

Sub-Modules:
    - Spinach: Render Preparation System
    - Kale: Scene Checker
    - Arugula: Render Settings Handler
    - Barn: Toolbar with helpful utilities

External Dependencies:
    - 3ds Max 2018 (2019 may work?)
    - PyMXS
    - MaxPlus
    - PySide2
    - PyInstaller (For compiling the automatic installer)

Copyright ©2019 Brooklyn Digital Foundry
"""

import pymxs
import MaxPlus
import os

import renderFarmingUI as rFUI
import renderFarmingBarn as rFB
from _version import __version__

rt = pymxs.runtime

uif = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def rf_open():
    # Destroys instances of the dialog before recreating it
    # noinspection PyBroadException
    try:
        # noinspection PyUnboundLocalVariable,PyUnresolvedReferences
        rf_ui.close()
    except NameError:
        pass

    app = MaxPlus.GetQMaxMainWindow()
    rf_ui = rFUI.RenderFarmingUI(uif, app)
    rf_ui.show()


def rf_barn_open():
    # Destroys instances of the dialog before recreating it
    # noinspection PyBroadException
    try:
        # noinspection PyUnboundLocalVariable,PyUnresolvedReferences
        rf_barn_ui.close()
    except NameError:
        pass

    app = MaxPlus.GetQMaxMainWindow()

    rf_barn_ui = rFB.RenderFarmingBarnUI()
    rf_barn_ui.show()
