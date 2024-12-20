import PyInstaller.__main__
from pathlib import Path

from bambu_timelapse_downloader.config import get_settings


HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "console.py")


def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--name',
        get_settings().app_name,
        '--exclude-module',
        '_bootlocale',
    ])
