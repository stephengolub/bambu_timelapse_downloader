import pathlib
import subprocess


class ConversionError(Exception):
    def __init__(self, filename: pathlib.Path, exception: Exception):
        self.filename = filename
        self.exception = exception

        super().__init__(f"Failed to convert {self.filename} due to {self.exception}")


def convert_to_mp4(filename: pathlib.Path | str, delete_original: bool = False) -> pathlib.Path :
    """Convert the file to an mp4 file using ffmpeg."""
    filename = pathlib.Path(filename)
    assert filename.suffix != ".mp4", "No need to convert an mp4 to an mp4"

    target_filename = filename.with_suffix('.mp4')

    try:
        subprocess.run([
            "ffmpeg",
            "-i",
            str(filename),
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            str(target_filename)
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise ConversionError(filename, e) from None

    if not target_filename.exists():
        raise ConversionError(filename, Exception("Missing target"))

    if delete_original:
        filename.unlink()

    return target_filename
