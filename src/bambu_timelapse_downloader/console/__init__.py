import pathlib
import sys
from importlib import metadata

import click
import click_params as cp

from bambu_timelapse_downloader.console.browse import browse as browse_cmd
from bambu_timelapse_downloader.console.download import download as download_cmd
from bambu_timelapse_downloader.ftp import ImplicitFTP_TLS
from bambu_timelapse_downloader.logging import setup_logging


version = metadata.version('bambu_timelapse_downloader')


@click.group(name="bambu-timelapse-downloader")
@click.option(
    '--ip',
    '-i',
    type=cp.IPV4_ADDRESS,
    required=True,
    envvar="BBTL_IP",
)
@click.option('--port', '-p', type=int, default=990, help="The Port, should not need changed unless Bambu gets creative")
@click.option('--user', '-U', type=str, default="bblp", help="The User, should not need changed unless Bambu get creative")
@click.option(
    '--access-code',
    '--password',
    '-P',
    type=str,
    help="The Access Code for the printer; found in network settings",
    envvar="BBTL_ACCESS_CODE",
)
@click.option('--console-only-logging/--all-logging', type=bool, default=False)
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
@click.option(
    '--beta',
    is_flag=True,
    help="Enable beta features",
    envvar="BBTL_BETA",
)
@click.version_option(version)
@click.pass_context
def cli(
    ctx: click.Context,
    ip: cp.IP_ADDRESS,
    port: int,
    user: str,
    access_code: str,
    console_only_logging: bool,
    download_dir: pathlib.Path,
    convert: bool,
    beta: bool,
):
    logger = setup_logging(console_only_logging)

    logger.info('Starting bambu timelapse downloader v%s', version)

    ctx.ensure_object(dict)
    ctx.obj['logger'] = logger
    ctx.obj['download_dir'] = pathlib.Path(download_dir)
    ctx.obj['convert'] = convert
    ctx.obj['beta'] = beta

    ctx.obj['ftp_args'] = (str(ip), port, user, access_code)

    try:
        logger.info('Connecting to printer %s@%s:%d', user, ip, port)
        ftp_client = ImplicitFTP_TLS()
        ftp_client.connect(host=str(ip), port=port)
        ftp_client.login(user=user, passwd=access_code)
        ftp_client.prot_p()
        logger.info('Connected.')
    except Exception:
        logger.exception('FTP connection failed')
        sys.exit(1)
    else:
        ctx.obj['ftp_client'] = ftp_client


cli.add_command(browse_cmd)
cli.add_command(download_cmd)


# Testing
if getattr(sys, 'frozen', False):
    cli(sys.argv[1:])
