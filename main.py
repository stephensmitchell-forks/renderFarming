import sys
import os
import pymxs
import MaxPlus
import logging

sys.path.append(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

import renderFarmingConfig
import renderFarmingUI as rFUI

rt = pymxs.runtime

cfg = renderFarmingConfig.Configuration()
cfg.set_max_system_directories(rt)

lg = logging.getLogger("renderFarming")
lg.setLevel(cfg.get_log_level())

log_file = cfg.get_log_file()
print(log_file)
fh = logging.FileHandler(log_file)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
lg.addHandler(fh)
lg.info("Render Farming: Starting")

lg.debug("Executing Spinach")

uif = "E:\\dump\\scripts\\renderFarming\\renderFarmingUI.ui"


def shutdown():
    logging.shutdown()
    sys.exit()


# Destroys instances of the dialog before recreating it
# noinspection PyBroadException
try:
    # noinspection PyUnboundLocalVariable
    ui.close()
except:
    pass

app = MaxPlus.GetQMaxMainWindow()
ui = rFUI.RenderFarmingUI(uif, rt, cfg, lg, app)
ui.show()
