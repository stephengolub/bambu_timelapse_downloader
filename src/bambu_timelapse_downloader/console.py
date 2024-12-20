import ftplib
import logging
import os
import pathlib
import sys
from importlib import metadata

import click
import click_params as cp

from .ffmpeg import convert_to_mp4, ConversionError
from .ftp import ImplicitFTP_TLS
from .logging import setup_logging


version = metadata.version('bambu_timelapse_downloader')


@click.command()
@click.argument('ip', type=cp.IPV4_ADDRESS, required=True)
@click.option('--port', type=int, default=990, help="The Port, should not need changed unless Bambu gets creative")
@click.option('--user', type=str, default="bblp", help="The User, should not need changed unless Bambu get creative")
@click.option('--access-code', '--password', type=str, help="The Access Code for the printer; found in network settings")
@click.option('--download-dir', type=click.Path(file_okay=False, dir_okay=True), default=pathlib.Path.cwd().joinpath("timelapse"), help="The directory to save the timelapse files to")
@click.option('--convert/--no-convert', type=bool, default=False, help="Convert the downloaded files to mp4, deleting the original. Requires ffmpeg")
@click.option('-t', '--ftp-timelapse-folder', type=str, default="timelapse")
@click.option('-d', '--delete-sd-card-files-after-download', type=bool, default=False)
@click.version_option(version)
def ftp_download(
    ip: cp.IP_ADDRESS,
    port: int,
    user: str,
    access_code: str,
    download_dir: pathlib.Path,
    ftp_timelapse_folder: str,
    convert: bool,
    delete_sd_card_files_after_download: bool,
):
    """Download timelapse files from the specified IP"""
    logger = setup_logging()

    logger.info('Starting bambu timelapse downloader v%s', version)
    download_dir.mkdir(exist_ok=True)

    # Check pre-existing downloads and remove the suffix for later comparison
    downloaded_files = {fname.with_suffix('') for fname in download_dir.iterdir() if fname.suffix in ('.avi', '.mp4')}

    try:
        logger.info('Connecting to printer %s@%s:%d', user, ip, port)
        ftp_client = ImplicitFTP_TLS()
        ftp_client.connect(host=str(ip), port=port)
        ftp_client.login(user=user, passwd=access_code)
        ftp_client.prot_p()
        logger.info('Connected.')
    except Exception as e:
        logger.exception('FTP connection failed')
        sys.exit(1)

    try:
        if ftp_timelapse_folder in ftp_client.nlst():
            ftp_client.cwd(ftp_timelapse_folder)
            try:
                logger.info('Looking avi or mp4 files for download.')
                ftp_timelapse_files = {
                    fname for fname in ftp_client.nlst()
                    if (fname.endswith('.avi') or fname.endswith('.mp4')) and
                    fname.rsplit('.', 1)[0] not in downloaded_files
                }

                if ftp_timelapse_files:
                    logger.info('Found %d files for download.', len(ftp_timelapse_files))
                    for fname in ftp_timelapse_files:
                        filesize = ftp_client.size(fname) or 0
                        filesize_mb = round(filesize/1024/1024, 2)
                        download_file_path = download_dir.joinpath(fname)
                        if filesize == 0:
                            logger.info('Filesize of file %s is 0, skipping file and continue', fname)
                            continue
                        try:
                            logger.info('Downloading file "%s" size: %d MB', fname, filesize_mb)
                            with open(download_file_path, 'wb') as fhandle:
                                ftp_client.retrbinary('RETR %s' % fname, fhandle.write)
                        except Exception as e:
                            os.remove(download_file_path)
                            logger.error('failed to download file %s: %s, continue with next file', fname, e)
                            continue
                        else:
                            if delete_sd_card_files_after_download:
                                try:
                                    ftp_client.delete(fname)
                                except Exception as e:
                                    logger.error('Failed to delete file after download, continue with next file')
                                    continue
                            if convert and fname.endswith('.avi'):
                                try:
                                    convert_to_mp4(download_file_path, delete_original=True)
                                except ConversionError:
                                    logger.exception("failed to convert file (%s) to mp4", download_file_path)
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


# Testing
if getattr(sys, 'frozen', False):
    ftp_download(sys.argv[1:])
