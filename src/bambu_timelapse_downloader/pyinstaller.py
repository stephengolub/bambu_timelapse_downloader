import PyInstaller.__main__ as pyinstaller_main
from pathlib import Path

from bambu_timelapse_downloader.config import get_settings


path_to_main = Path(__file__).parent / "console.py"


def install():
    pyinstaller_main.run([
        str(path_to_main),
        '--onefile',
        '--name',
        get_settings().app_name,
        '--exclude-module',
        '_bootlocale',
    ])
