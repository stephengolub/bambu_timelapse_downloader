from pathlib import Path
from unittest import mock

from bambu_timelapse_downloader import pyinstaller as subject_module
from bambu_timelapse_downloader.config import get_settings


def test_path():
    assert subject_module.path_to_main == Path(subject_module.__file__).parent / "console.py"


def test_install():
    call_args = [
        str(subject_module.path_to_main),
        '--onefile',
        '--name',
        get_settings().app_name,
        '--exclude-module',
        '_bootlocale',
    ]
    with mock.patch(
        "bambu_timelapse_downloader.pyinstaller.pyinstaller_main",
        spec=mock.PropertyMock,
    ) as pyinstaller_main:
        pyinstaller_main.run = mock.MagicMock()
        subject_module.install()

        # TODO: Figure out why assert_called_once_with doesn't work here
        assert pyinstaller_main.run.call_count == 1
        assert pyinstaller_main.run.call_args.args[0] == call_args
