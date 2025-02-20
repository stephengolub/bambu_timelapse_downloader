import pathlib
import sys

import click

from bambu_timelapse_downloader.ffmpeg import convert_to_mp4, ConversionError


def _download(
    ctx: click.Context,
    fname: str,
    delete_remote: bool = False,
):
    logger = ctx.obj['logger']
    ftp_client = ctx.obj['ftp_client']
    convert = ctx.obj['convert']

    download_dir = ctx.obj['download_dir']
    download_dir.mkdir(parents=True, exist_ok=True)

    filesize = ftp_client.sizemb(fname)
    download_file_path = download_dir.joinpath(fname.name())
    if filesize == 0:
        logger.info('Filesize of file %s is 0, skipping file and continue', fname)
        return
    try:
        logger.info(
            'Downloading file "%s" size: %d MB',
            fname,
            filesize,
        )
        ftp_client.download(fname, download_file_path)
    except Exception as e:
        logger.error('failed to download file %s: %s, continue with next file', fname, e)
    else:
        if delete_remote:
            try:
                ftp_client.delete(fname)
            except Exception:
                logger.error('Failed to delete file after download, continue with next file')
                return
        if convert and fname.endswith('.avi'):
            logger.info("Converting %s to mp4", fname)
            try:
                new_fname = convert_to_mp4(download_file_path, delete_original=True)
            except ConversionError:
                logger.exception("failed to convert file (%s) to mp4", download_file_path)
            else:
                logger.info("Conversion complete: %s", new_fname.name)


@click.command()
@click.option(
    '--download-dir',
    type=click.Path(file_okay=False, dir_okay=True),
    default=pathlib.Path.cwd().joinpath("timelapse"),
    help="The directory to save the timelapse files to",
)
@click.option(
    '--convert/--no-convert',
    type=bool,
    default=False,
    help="Convert the downloaded files to mp4, deleting the original. Requires ffmpeg",
)
@click.option('-t', '--ftp-timelapse-folder', type=str, default="timelapse")
@click.option('-d', '--delete-sd-card-files-after-download', type=bool, default=False)
@click.option('--dry-run/--execute', type=bool, default=False)
@click.pass_context
def download(
    ctx: click.Context,
    ftp_timelapse_folder: str,
    delete_sd_card_files_after_download: bool,
    dry_run: bool,
):
    """Download timelapse files from the printer"""
    logger = ctx.obj['logger']
    ftp_client = ctx.obj['ftp_client']
    convert = ctx.obj['convert']

    download_dir = ctx.obj['download_dir']

    # Check pre-existing downloads and remove the suffix for later comparison
    downloaded_files = {
        fname.with_suffix('').name
        for fname in download_dir.iterdir()
        if fname.suffix in ('.avi', '.mp4')
    }

    try:
        if ftp_timelapse_folder in ftp_client.nlst():
            ftp_client.cwd(ftp_timelapse_folder)
            try:
                logger.info('Looking avi or mp4 files for download.')
                ftp_timelapse_files = {
                    fname for fname in ftp_client.nlst()
                    if (
                        fname.endswith('.avi') or fname.endswith('.mp4')
                    ) and fname.rsplit('.', 1)[0] not in downloaded_files
                }

                if not ftp_timelapse_files:
                    logger.info("No new timelapse files found")
                    sys.exit(0)

                logger.info('Found %d files for download.', len(ftp_timelapse_files))
                if dry_run:
                    split_token = "\n • "
                    if downloaded_files:
                        print(f"Previously Downloaded:{split_token}{split_token.join(downloaded_files)}")

                    print(f"To Download:{split_token}{split_token.join(ftp_timelapse_files)}")
                    return

                for fname in ftp_timelapse_files:
                    _download(ctx, fname, delete_remote=delete_sd_card_files_after_download)
            except ftplib.error_perm as resp:
                if str(resp) == "550 No files found":
                    logger.error("No files in this directory")
                else:
                    raise
        else:
            logger.error('%s not found on ftp server.', ftp_timelapse_folder)
            sys.exit(1)
    except Exception:
        logger.exception('Program failed')
        sys.exit(1)
