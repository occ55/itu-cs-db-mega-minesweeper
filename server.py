from src.init import app


from src.api.pages import *
from src.api.auth import *
from src.api.competitions import *

if __name__ == "__main__":
    app.run()
