"""Miscellanious helper utils."""
import errno
import os
import logging
import sys
import json

import jsmin

def get_logger(name, level=logging.INFO, channel=sys.stderr):
    """Return a Logger object."""
    logger_format = '[%(levelname)s] %(message)s'
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(channel)
    handler.setLevel(level)
    formatter = logging.Formatter(logger_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def merge(dict1, dict2):
    """Return merged dictionaries (repeated keys are set to dict2 values)."""
    dict3 = dict1.copy()
    dict3.update(dict2)
    return dict3

def pad_list(lst, size):
    """Return list with exactly <size> elements."""
    return lst[:size] + [None] * (size - len(lst))

def output(obj):
    """Print to stdout."""
    print(str(obj))

def mkdir_p(path):
    """Create directory if non-existing, otherwise do nothing."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def pretty_json(obj):
    """Return pretty JSON string representation of a Python object."""
    return json.dumps(obj, indent=2)

def load_json(json_string):
    """Return Python object from JSON string."""
    return json.loads(jsmin.jsmin(json_string))
