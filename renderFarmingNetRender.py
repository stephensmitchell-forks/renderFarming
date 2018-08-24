import pymxs
import logging

mlg = logging.getLogger("renderFarming.NetRender")

rt = pymxs.runtime
vr = rt.renderers.current


def submit_current_file():
    flg = logging.getLogger("renderFarming.NetRender.submit_current_file")
    flg.debug("Activating Render Submission Dialog")

    rt.macros.run("Render", "RenderButtonMenu_Submit_to_Network_Rendering")
    print ("\\(0.0)/")

    flg.debug("Render Submission Dialog ended")
    return
