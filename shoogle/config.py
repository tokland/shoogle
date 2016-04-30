import logging
import os
import sys

from . import lib

logger = lib.get_logger("shoogle", level=logging.ERROR, channel=sys.stderr)
config_dir = os.path.join(os.path.expanduser("~"), ".shoogle")
cache_dir = os.path.join(config_dir, "cache")
credentials_base_dir = os.path.join(config_dir, "credentials")
