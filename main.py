import sys
import os
import pymxs
import MaxPlus

sys.path.append(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

import renderFarmingConfig
import renderFarmingUI as rFUI

rt = pymxs.runtime

cfg = renderFarmingConfig.Configuration()
cfg.set_max_system_directories(rt)

uif = "E:\\dump\\scripts\\renderFarming"

# Destroys instances of the dialog before recreating it
# noinspection PyBroadException
try:
    # noinspection PyUnboundLocalVariable
    ui.close()
except:
    pass

app = MaxPlus.GetQMaxMainWindow()
ui = rFUI.RenderFarmingUI(uif, rt, cfg, app)
ui.show()
