import re
import logging
import sys
import json

import jsmin
import httplib2

def get_logger(name, level=logging.INFO, format='[%(levelname)s] %(message)s', channel=sys.stderr):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler(channel)
    handler.setLevel(level)
    formatter = logging.Formatter(format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def first(it):
    return next(it, None)

def merge(d1, d2):
    d3 = d1.copy()
    d3.update(d2)
    return d3

def pad_list(lst, n):
    return lst[:n] + [None] * (n - len(lst))

def pretty_json(obj):
    return json.dumps(obj, indent=2)

def output(obj):
    print(str(obj))

def download(url, cache_directory, logger):
    logger.info("GET {}".format(url))
    http = httplib2.Http(cache=cache_directory)
    headers, content = http.request(url, "GET")
    if re.match("2..", str(headers.status)):
        return content.decode('utf-8')
    else:
        raise ShoogleException("GET {} - Error: {}".format(url, headers.status))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
            
def load_json(s):
    return json.loads(jsmin.jsmin(s))    
