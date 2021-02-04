import os
import sys
import platform

command = "screenlogicpy.cli get json"

python = ""
plat = platform.system()
if plat == "Windows":
    python = "C:/Users/Kevin/AppData/Local/Programs/Python/Python36-32/python.exe"
elif plat == "Linux":
    python = "/usr/bin/python3.6"
else:
    print("Unknown system")
    sys.exit(1)

return_code = os.system("{} -m {}".format(python, command))
#print(return_code)