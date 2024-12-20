from functools import lru_cache
import logging
import pathlib
import sys

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LoggingConfig(BaseModel):
    directory: str | pathlib.Path  = "logs"
    name: str = ""
    file_max_byte_size: int = 104857
    file_max_backup: int = 3
    default_level: int = logging.DEBUG
    console_level: int = logging.INFO
    file_level: int = logging.DEBUG


class Config(BaseSettings):
    app_name: str = "bambu_timelapse_downloader"
    application_path: pathlib.Path = pathlib.Path(
        sys.executable if getattr(sys, 'frozen', False) else __file__
    ).parent
    log: LoggingConfig = LoggingConfig()
    timezone: str = "UTC"

    @property
    def log_root_directory(self):
        return self.application_path.joinpath(self.log.directory or "logs")

    @property
    def logger_name(self):
        return self.log.name or self.app_name


@lru_cache()
def get_settings():
    return Config()
