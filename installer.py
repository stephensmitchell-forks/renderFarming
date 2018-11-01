import ctypes
import sys


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as error:
        print("Unable to retrieve UAC Elevation level: %s" % error)
        return False


if is_admin():
    # Code of your program here
    print("Admin")
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, u"runas", unicode(sys.executable), unicode(__file__), None, 1)
