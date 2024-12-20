import ftplib
import logging
import os
import pathlib
import sys
from importlib import metadata

import click
import click_params as cp

from .ftp import ImplicitFTP_TLS

from .logging import setup_logging


version = metadata.version('bambu_timelapse_downloader')


@click.command()
@click.argument('ip', type=cp.IPV4_ADDRESS, required=True)
@click.option('--port', type=int, default=990)
@click.option('--user', type=str, default="bblp")
@click.option('--password', type=str)
@click.option('--download-dir', type=click.Path(file_okay=False, dir_okay=True), default=pathlib.Path("./timelapse"))
@click.option('-t', '--ftp-timelapse-folder', type=str, default="timelapse")
@click.option('-d', '--delete-sd-card-files-after-download', type=bool, default=False)
@click.version_option(version)
def ftp_download(
    ip: cp.IP_ADDRESS,
    port: int,
    user: str,
    password: str,
    download_dir: pathlib.Path,
    ftp_timelapse_folder: str,
    delete_sd_card_files_after_download: bool,
):
    logger = setup_logging()

    logger.info('Starting bambu timelapse downloader v%s', version)

    try:
        download_dir.mkdir(exist_ok=True)

        downloaded_files = {fname for fname in download_dir.iterdir() if fname.suffix == '.avi'}

        logger.info('Connecting to printer %s@%s:%d', user, ip, port)
        ftp_client = ImplicitFTP_TLS()
        ftp_client.connect(host=str(ip), port=port)
        ftp_client.login(user=user, passwd=password)
        ftp_client.prot_p()
        logger.info('Connected.')
    except Exception as e:
        logger.exception('FTP connection failed')
        sys.exit(1)

    try:
        if ftp_timelapse_folder in ftp_client.nlst():
            ftp_client.cwd(ftp_timelapse_folder)
            try:
                logger.info('Looking avi files for download.')
                ftp_timelapse_files = {fname for fname in ftp_client.nlst() if fname.endswith('.avi')} - downloaded_files

                if ftp_timelapse_files:
                    logger.info('Found %d files for download.', len(ftp_timelapse_files))
                    for fname in ftp_timelapse_files:
                        filesize = ftp_client.size(fname) or 0
                        filesize_mb = round(filesize/1024/1024, 2)
                        download_file_name = fname
                        download_file_path = f'{download_dir}/{download_file_name}'
                        if filesize == 0:
                            logger.info('Filesize of file %s is 0, skipping file and continue', fname)
                            continue
                        try:
                            logger.info('Downloading file "%s" size: %d MB', fname, filesize_mb)
                            fhandle = open(download_file_path, 'wb')
                            ftp_client.retrbinary('RETR %s' % fname, fhandle.write)
                            if delete_sd_card_files_after_download:
                                try:
                                    ftp_client.delete(fname)
                                except Exception as e:
                                    logger.error('Failed to delete file after download, continue with next file')
                                    continue
                        except Exception as e:
                            fhandle.close()
                            os.remove(download_file_path)
                            logger.error('failed to download file %s: %s, continue with next file', fname, e)
                            continue
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
