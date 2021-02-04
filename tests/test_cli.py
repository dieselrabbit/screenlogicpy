import os
import platform

command = "screenlogicpy.cli get json"

python = ""
if platform.system() == "Windows":
    python = "C:/Users/Kevin/AppData/Local/Programs/Python/Python36-32/python.exe"
else:
    python = "/usr/bin/python3.6"

return_code = os.system("{} -m {}".format(python, command))
#print(return_code)