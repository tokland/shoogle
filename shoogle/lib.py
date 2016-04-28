import errno
import os
import logging
import sys
import json

import jsmin

def get_logger(name, level=logging.INFO, channel=sys.stderr):
    logger_format = '[%(levelname)s] %(message)s'
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(channel)
    handler.setLevel(level)
    formatter = logging.Formatter(logger_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def first(it):
    return next(it, None)

def merge(dict1, dict2):
    dict3 = dict1.copy()
    dict3.update(dict2)
    return dict3

def pad_list(lst, size):
    return lst[:size] + [None] * (size - len(lst))

def pretty_json(obj):
    return json.dumps(obj, indent=2)

def output(obj):
    print(str(obj))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def load_json(json_string):
    return json.loads(jsmin.jsmin(json_string))
