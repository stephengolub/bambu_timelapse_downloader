import logging
import os
import pathlib
from datetime import datetime
from logging.handlers import RotatingFileHandler

from bambu_timelapse_downloader.config import get_settings


def setup_logging(console_only):
    config = get_settings()

    # Get base logger
    if config.logger_name:
        logger = logging.getLogger(config.logger_name)
    else:
        logger = logging.getLogger()

    logger.setLevel(config.log.default_level)

    # Setup console logging
    log_format_console = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"

    log_console_handler = logging.StreamHandler()
    log_console_handler.setLevel(config.log.console_level)
    log_console_handler.setFormatter(logging.Formatter(log_format_console))
    logger.addHandler(log_console_handler)

    if not console_only:
        today = datetime.today()
        year = today.strftime('%Y')
        month = today.strftime('%m')
        log_name_ = config.logger_name.rstrip('.log') + f'_{os.getlogin()}' + '.log'
        log_name = today.strftime(f'%Y%m%d_{log_name_}')
        # create an initial logger. It will only log to console and it will disabled
        log_format_file = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"
        log_date_format = '%Y%m%d %H:%M:%S'
        log_directory = pathlib.Path(config.log_root_directory).joinpath(str(year)).joinpath(str(month)).expanduser()
        if not log_directory.exists():
            logger.debug('create log dir %s', log_directory)
            log_directory.mkdir(parents=True, exist_ok=True)

        log_file_path = log_directory.joinpath(log_name)
        logger.debug('add log file handler %s', log_file_path)
        log_file_handler = RotatingFileHandler(filename=log_file_path, mode='a',
                                               maxBytes=config.log.file_max_byte_size,
                                               backupCount=config.log.file_max_backup,
                                               delay="false",
                                               encoding='utf8')
        log_file_handler.setLevel(config.log.file_level)
        log_file_handler.setFormatter(logging.Formatter(log_format_file, datefmt=log_date_format))

        logger.addHandler(log_file_handler)
    return logger
