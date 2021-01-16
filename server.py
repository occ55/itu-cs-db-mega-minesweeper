from src.init import app

import sys

from src.api.pages import *
from src.api.auth import *
from src.api.competitions import *
from src.api.logs import *

from src.periodic import *

if __name__ == "__main__":
    sys.setrecursionlimit(32000)
    app.run(debug=True)
