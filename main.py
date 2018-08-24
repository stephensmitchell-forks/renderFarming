import sys
import os
import pymxs
import MaxPlus
import logging

sys.path.append(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))))

import renderFarmingConfig
import renderFarmingUI as rFUI


cfg = renderFarmingConfig.Configuration()

lg = logging.getLogger("renderFarming")
lg.setLevel(cfg.get_log_level())

log_file = cfg.get_log_file()
fh = logging.FileHandler(log_file)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
lg.addHandler(fh)
lg.info("Render Farming: Starting")

lg.debug("Executing Spinach")

rt = pymxs.runtime

uif = "E:\\dump\\scripts\\renderFarming\\renderFarmingUI.ui"

app = MaxPlus.GetQMaxMainWindow()
form = rFUI.RenderFarmingUI(uif, rt, cfg, lg)
# sys.exit(app.exec_())

# spinach = rFS.SpinachJob(rt, cfg)
#
# spinach.single_frame_prepass()
#
# spinach.from_file()

# lg.debug("Complete")
# logging.shutdown()
# print("*** ! ***")
