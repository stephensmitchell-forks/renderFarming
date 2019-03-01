set PATH=%PATH%;C:\Program Files\7-Zip\;C:\Python27

del install.zip
del install.man

7z a install.zip .\src\*

python .\generateManifest.py .\src

7z a install.zip install.man

pyinstaller --noconfirm --log-level=INFO ^
 --onefile^
 --clean^
 --name RenderFarming0045_INSTALLER^
 --uac-admin^
 --icon=UI/renderFarmingInstaller.ico^
 --add-data "install.zip;."^
 --add-data "UI/*;UI"^
 installer.py

  @rem --noconsole^