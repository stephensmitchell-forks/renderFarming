macroScript renderFarming category:"renderFarming" tooltip:"Render Farming" 
iconName: "RenderFarming/renderFarming1000_main"
(
	python.execute("import sys, os, pymxs\nrt = pymxs.runtime\nsys.path.append(os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU', 'scripts', 'BDF')))")

	python.execute("import renderFarming")
	
	python.execute("renderFarming.rf_open()")
)

macroScript renderFarmingBarn category:"renderFarming" tooltip:"Render Farming Barn"
iconName: "RenderFarming/renderFarming1000_barn"
(
	python.execute("import sys, os, pymxs\nrt = pymxs.runtime\nsys.path.append(os.path.realpath(os.path.join(os.getenv('LOCALAPPDATA'), 'Autodesk', '3dsMax', '2018 - 64bit', 'ENU', 'scripts', 'BDF')))")

	python.execute("import renderFarming")

	python.execute("renderFarming.rf_barn_open()")
)

