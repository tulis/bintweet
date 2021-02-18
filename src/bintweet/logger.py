from __future__ import annotations
from loguru import logger

import config
import loguru
import re
import sys


def loguru_format(record: loguru.Record):
    format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | \
<level>{level: <8}</level> | \
<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}\n{exception}</level>"

    if record["extra"].get("sensitive") and not config.is_debug_mode():
        omit_fields = []
        for field in record["extra"]:
            if field == "sensitive":
                continue
            else:
                omit_fields.append(record["extra"][field])

        record["message"] = re.sub(
            "|".join(re.escape(omit_field) for omit_field in omit_fields),
            "***redacted***",
            record["message"],
        )

    return format


logger.configure(
    handlers=[
        dict(
            sink=sys.stdout,
            diagnose=True if config.is_debug_mode() else False,
            format=loguru_format,
        ),
    ],
)