import sys
import os
import pymxs
import MaxPlus

sys.path.append(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

import renderFarmingUI as rFUI

rt = pymxs.runtime

uif = "E:\\dump\\scripts\\renderFarming"

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
