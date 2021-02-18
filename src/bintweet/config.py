from __future__ import annotations
from distutils.util import strtobool
from dotenv import dotenv_values

import typing

DEBUG = "DEBUG"

T = typing.TypeVar("T")

_config = {
    **dotenv_values(".env"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
}


def get(key: str, default: (typing.Any | T) = None) -> (typing.Any | T):
    return _config.get(key, default)


def is_debug_mode() -> bool:
    return bool(strtobool(_config.get(DEBUG) or "FALSE"))
