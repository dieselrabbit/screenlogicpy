import os
import sys

args = "get json"

return_code = os.system(f"{sys.executable} -m screenlogicpy.cli {args}")
if return_code != 0:
    print(return_code)