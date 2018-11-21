macroScript renderFarming category:"renderFarming" tooltip:"Render Farming" 
iconName: "RenderFarming/renderFarming1000_main"
(
	python.execute("import sys, os, pymxs\nrt = pymxs.runtime\nsys.path.append(os.path.realpath(os.path.join(self._appdata_dir, 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU')))")

	python.execute("import renderFarming")
	
	python.execute("renderFarming.rf_open()")
)

