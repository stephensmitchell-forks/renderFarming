import pymxs
import MaxPlus
import os

import renderFarmingUI as rFUI

rt = pymxs.runtime

uif = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def rf_open():
    # Destroys instances of the dialog before recreating it
    # noinspection PyBroadException
    try:
        # noinspection PyUnboundLocalVariable,PyUnresolvedReferences
        ui.close()
    except NameError:
        pass

    app = MaxPlus.GetQMaxMainWindow()
    ui = rFUI.RenderFarmingUI(uif, rt, app)
    ui.show()
