import sys

import googleapiclient
import httplib2

from .. import lib
from .. import common
from .. import config

logger = config.logger

def add_parser(subparsers, name):
    parser = subparsers.add_parser(name)
    
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
    service_id, resource_name, method_name = lib.pad_list(options.api_path.split(".", 2), 3)
    method_options = lib.load_json((sys.stdin if options.json_request == "-" 
        else open(options.json_request)).read())
    response = do_request(service_id, resource_name, method_name, method_options, options)
    lib.output(lib.pretty_json(response))

def execute_media_request(request):
    while 1:
        status, response = request.next_chunk()
        if response:
            return response

def build_service(service_id, credentials):
    base_http = httplib2.Http()
    http = (credentials.authorize(base_http) if credentials else base_http) 
    service_name, version = service_id.split(":", 1)
    return googleapiclient.discovery.build(service_name, version, http=http)

def get_credentials(scopes, options):
    if scopes and options.client_secret_file:
        if options.credentials_file:
            if os.path.exists(options.credentials_file):
                credentials_path = options.credentials_file
            else:
                raise common.ShoogleException("Credentials file not found: {}".
                    format(options.credentials_file))
        else:
            credentials_path = get_credentials_path(scopes, options.credentials_profile)
        get_code = (auth.browser.get_code if options.browser_auth else auth.console.get_code)
        client_secret = options.client_secret_file            
        return auth.get_credentials(client_secret, credentials_path, scopes, get_code)
    else:
        return None

def do_request(service_id, resource_name, method_name, method_options, options):
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
            media_body = apiclient.http.MediaFileUpload(options.media_file, 
                chunksize=-1, resumable=True, mimetype="application/octet-stream")
            logger.debug("Request: " + lib.pretty_json(lib.merge(method_options, 
                {"media_body": "MediaFileUpload({})".format(options.media_file)})))
            all_options = lib.merge(method_options, {"media_body": media_body})
            request = method_func(**all_options)
            return execute_media_request(request)
        else:
            logger.debug("Request: " + lib.pretty_json(method_options))
            request = method_func(**method_options)
            return request.execute()

