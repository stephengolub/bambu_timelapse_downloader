from itertools import chain
import pathlib
import subprocess


class ConversionError(Exception):
    def __init__(self, filename: pathlib.Path, exception: Exception):
        self.filename = filename
        self.exception = exception

        super().__init__(f"Failed to convert {self.filename} due to {self.exception}")


_ffmpeg_args = {
    "-c:v": "libx264",
    "-crf": "19",
    "-preset": "slow",
    "-c:a": "libfdk_aac",
    "-b:a": "192k",
    "-ac": "2",
}


def convert_to_mp4(
    filename: pathlib.Path | str,
    delete_original: bool = False,
    force_convert: bool = False,
) -> pathlib.Path :
    """Convert the file to an mp4 file using ffmpeg.

    Args:
        filename: The path to the file that is to be converted.
        delete_original: Should the original file be kept?
        force_convert: Should we ignore the extension and convert anyway?

    Returns:
        The path to the new file.
    """
    filename = pathlib.Path(filename)
    assert force_convert or filename.suffix != ".mp4", "No need to convert an mp4 to an mp4"

    target_filename = filename.with_suffix('.mp4')

    try:
        subprocess.run([
            "ffmpeg",
            "-i",
            str(filename),
        ] + list(chain.from_iterable(_ffmpeg_args.items())) + [
            str(target_filename)
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        raise ConversionError(filename, e) from None

    if not target_filename.exists():
        raise ConversionError(filename, Exception("Missing target"))

    if delete_original:
        filename.unlink()

    return target_filename
