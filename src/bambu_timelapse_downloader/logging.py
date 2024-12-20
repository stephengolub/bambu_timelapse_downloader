import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from .config import get_settings


def setup_logging():
    config = get_settings()

    today = datetime.today()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    log_name_ = config.logger_name.rstrip('.log') + f'_{os.getlogin()}' + '.log'
    log_name = today.strftime(f'%Y%m%d_{log_name_}')
    # create an initial logger. It will only log to console and it will disabled
    log_format_console = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"
    log_format_file = "[%(asctime)s:%(filename)s:%(lineno)s:%(name)s.%(funcName)s()] %(levelname)s %(message)s"
    log_date_format = '%Y%m%d %H:%M:%S'
    if config.logger_name:
        logger = logging.getLogger(config.logger_name)
    else:
        logger = logging.getLogger()
    log_directory = config.log_root_directory.joinpath(str(year)).joinpath(str(month))
    if not log_directory.exists():
        logger.debug('create log dir %s', log_directory)
        log_directory.mkdir(parents=True, exist_ok=True)

    log_file_path = f'{log_directory}/{log_name}'
    logger.debug('add log file handler %s', log_file_path)
    log_file_handler = RotatingFileHandler(filename=log_file_path, mode='a',
                                           maxBytes=config.log.file_max_byte_size,
                                           backupCount=config.log.file_max_backup,
                                           delay="false",
                                           encoding='utf8')
    log_console_handler = logging.StreamHandler()
    log_console_handler.setLevel(config.log.console_level)
    log_console_handler.setFormatter(logging.Formatter(log_format_console))

    log_file_handler.setLevel(config.log.file_level)
    log_file_handler.setFormatter(logging.Formatter(log_format_file, datefmt=log_date_format))

    logger.setLevel(config.log.default_level)
    logger.addHandler(log_console_handler)
    logger.addHandler(log_file_handler)
    return logger
