import sys
import os
from streamlit.web import cli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "ui/app.py"]
    sys.exit(cli.main())