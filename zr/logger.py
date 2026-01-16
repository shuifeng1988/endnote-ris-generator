from __future__ import annotations
import logging
import pathlib
import time

def make_logger(log_dir: pathlib.Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("zotero_restore")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    # console
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # file
    fn = log_dir / f"agent_{time.strftime('%Y%m%d')}.log"
    fh = logging.FileHandler(fn, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

