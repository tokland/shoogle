"""Execute command: send request to service."""
import inspect
import os
import sys

import apiclient
import googleapiclient
import httplib2

from .. import auth
from .. import common
from .. import config
from .. import lib

def add_parser(main_parser, name):
    """Add specific execute command parser."""
    parser = main_parser.add_parser(name)

    parser.add_argument('-c', '--client-secret-file', metavar="PATH",
                        help="Use a client secret JSON file")
    parser.add_argument('-f', '--media-file', metavar="PATH",
                        help='File to use for media-related methods')
    parser.add_argument('--browser-auth', action="store_true",
                        help="Use a browser to authentify")
    parser.add_argument('--credentials-file',
                        metavar="PATH", help="Select credentials file to use")
    parser.add_argument('--credentials-profile', default="default",
                        metavar="NAME", help="Select credentials profile to use")
    parser.add_argument('api_path', metavar="API_PATH",
                        help="SERVICE:VERSION.RESOURCE.METHOD")
    parser.add_argument('json_request', metavar="JSON_FILE",
                        help="File containing the request JSON (use '-' to read from STDIN)")

def run(options):
    """Run command execute."""
    service_id, resource_name, method_name = lib.pad_list(options.api_path.split(".", 2), 3)
    request_fd = (sys.stdin if options.json_request == "-" else open(options.json_request))
    method_options = lib.load_json(request_fd.read())
    try:
        response = do_request(service_id, resource_name, method_name, method_options, options)
        lib.output(lib.pretty_json(response))
    except TypeError as error:
        frm = inspect.trace()[-1]
        mod = inspect.getmodule(frm[0])
        if mod.__name__ == 'googleapiclient.discovery':
            config.logger.error("googleapiclient.discovery: {}".format(error))
        else:
            raise

def execute_media_request(request):
    """Process a request containing a MediaFileUpload."""
    while 1:
        status, response = request.next_chunk()
        if status:
            config.logger.debug("MediaFileUpload status: {}".format(status))
        if response:
            return response

def build_service(service_id, credentials):
    """Return service object from ID and credentials."""
    base_http = httplib2.Http()
    http = (credentials.authorize(base_http) if credentials else base_http)
    service_name, version = service_id.split(":", 1)
    return googleapiclient.discovery.build(service_name, version, http=http)

def get_credentials(scopes, options):
    """Return path of the reusable credentials JSON file for given scopes."""
    if scopes and options.client_secret_file:
        if options.credentials_file:
            if os.path.exists(options.credentials_file):
                credentials_path = options.credentials_file
            else:
                msg = "Credentials file not found: {}".format(options.credentials_file)
                raise common.ShoogleException(msg)
        else:
            credentials_path = common.get_credentials_path(scopes, options.credentials_profile)
        if options.browser_auth:
            from shoogle.auth import browser
            get_code = auth.browser.get_code
        else:
            from shoogle.auth import console
            get_code = auth.console.get_code
        client_secret = options.client_secret_file
        return auth.get_credentials(client_secret, credentials_path, scopes, get_code)
    else:
        return None

def get_method_options_with_media(method_options, media_file):
    """Return options to send the method caller from base options and media file."""
    media_body = apiclient.http.MediaFileUpload(
        media_file,
        chunksize=-1,
        resumable=True,
        mimetype="application/octet-stream",
    )
    media_file_field = "MediaFileUpload({})".format(media_file)
    printable_request = lib.merge(method_options, {"media_body": media_file_field})
    config.logger.debug("Request: " + lib.pretty_json(printable_request))
    return lib.merge(method_options, {"media_body": media_body})

def do_request(service_id, resource_name, method_name, method_options, options):
    """Send request to API and return JSON response."""
    service = common.get_service(service_id)
    method = common.get_method(service, resource_name, method_name)

    if method.get("request") and "body" not in method_options:
        raise common.ShoogleException("This method need a body property in the request")
    elif method.get("supportsMediaUpload") and not options.media_file:
        raise common.ShoogleException("This method requires a media file (--media-file=PATH)")
    else:
        scopes = method.get("scopes", [])
        credentials = get_credentials(scopes, options)
        service_obj = build_service(service_id, credentials)
        resource_func = getattr(service_obj, resource_name)
        method_func = getattr(resource_func(), method_name)

        if options.media_file:
            method_options_with_media = \
                get_method_options_with_media(method_options, options.media_file)
            request = method_func(**method_options_with_media)
            return execute_media_request(request)
        else:
            config.logger.debug("Request: " + lib.pretty_json(method_options))
            request = method_func(**method_options)
            return request.execute()
