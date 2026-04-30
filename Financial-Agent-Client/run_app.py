import sys
import os
from pathlib import Path
from streamlit.web import cli

if __name__ == "__main__":
    # Change to the script's directory so relative paths (ui/app.py) resolve correctly
    os.chdir(Path(__file__).parent)
    sys.argv = ["streamlit", "run", "ui/app.py", "--server.port", "8502"]
    sys.exit(cli.main())