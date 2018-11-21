set PATH=%PATH%;C:\Program Files\7-Zip\

del install.zip

7z a install.zip .\src\*

pyinstaller --noconfirm --log-level=INFO ^
 --onefile^
 --clean^
 --manifest RenderFarming0039_INSTALLER.exe.manifest^
 --name RenderFarming0039_INSTALLER^
 --uac-admin^
 --icon=UI/renderFarmingInstaller.ico^
 --add-data "install.zip;."^
 --add-data "UI/*;UI"^
 installer.py

  @rem --noconsole^