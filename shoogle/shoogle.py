import argparse
import collections
import errno
import glob
import inspect
import json
import logging
import os
import re
import string
import sys
import uuid

import jsmin
import httplib2
import apiclient
import oauth2client.client
import googleapiclient.errors
import googleapiclient.discovery

from shoogle import __version__
from . import auth
from . import lib
from . import common
from . import config
from .commands import show
from .commands import execute


# Main

#class ThrowingArgumentParser(argparse.ArgumentParser):
#    def error(self, message):
#        raise ArgumentParserError(message)
# or
#
# except SystemExit:

default_logger = lib.get_logger("shoogle", level=logging.DEBUG, channel=sys.stderr)

def get_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--version', action="store_true", 
        help="Show version")

    subparsers = parser.add_subparsers(help='Commands', dest="command")
    subparsers.required = False
    show.add_parser(subparsers, "show")
    execute.add_parser(subparsers, "execute")
    return parser

def run(args):
    """Acces to Google API services."""
    parser = get_parser("Command-line interface for the Google API.")
    options = parser.parse_args(args)

    if options.version:
        lib.output(__version__)
    elif options.command == "show":
        show.run(options)
    elif options.command == "execute":
        execute.run(options)
    else:
        parser.print_help(sys.stderr)
        return 2

def main(args, logger=default_logger):
    try:
        return run(args)
    except TypeError as error:
        frm = inspect.trace()[-1]
        mod = inspect.getmodule(frm[0])
        if mod.__name__ == 'googleapiclient.discovery':
            logger.error("googleapiclient.discovery: {}".format(error))
        else:
            raise 
    except common.ShoogleException as error:
        logger.error(error)
        return 1
    except googleapiclient.errors.HttpError as error:
        status = error.resp["status"]
        data = bytes.decode(error.content).strip()
        logger.error("Server error response ({0}): {1}".format(status, data))
        return 1
    except oauth2client.client.FlowExchangeError as error:
        logger.error("OAuth 2 error: {}".format(error))
    except json.decoder.JSONDecodeError as error:
        logger.error("JSONDecodeError: " + str(error))
        logger.error("JSON was: " + error.doc)
        return 1

if __name__ == '__main__':
    sys.exit(run(sys.argv[:1]))
