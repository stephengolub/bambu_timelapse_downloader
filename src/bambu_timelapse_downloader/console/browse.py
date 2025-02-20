from functools import partial

import click

from bambu_timelapse_downloader.console.download import _download
from bambu_timelapse_downloader.ftp import FTPBrowser, TUIFTPBrowser


@click.command(name='browse')
@click.argument('path', type=str, default='/')
@click.pass_context
def browse(ctx, path):
    """Browse the files on the FTP server"""
    if ctx.obj['beta']:
        ftp_browser = TUIFTPBrowser(
            ctx.obj['ftp_args'],
            downloader=partial(
                _download,
                ctx,
            )
        )
        ftp_browser.run()
    else:
        FTPBrowser(
            ctx.obj['ftp_client'],
            downloader=partial(
                _download,
                ctx,
            )
        ).browse(path)
