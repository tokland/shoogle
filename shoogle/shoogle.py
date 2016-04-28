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

# Globals

global logger
logger = lib.get_logger("shoogle", level=logging.CRITICAL)

config_dir = os.path.join(os.path.expanduser("~"), ".shoogle")
cache_dir = os.path.join(config_dir, "cache")
credentials_base_dir = os.path.join(config_dir, "credentials")
output = lib.output

### App common

class ShoogleException(Exception): 
    pass

def get_services():
    apis = lib.download("https://www.googleapis.com/discovery/v1/apis", cache_dir, logger)
    services = lib.load_json(apis)["items"]
    return dict((service["id"], service) for service in services)
            
def get_credentials_path(required_scopes, credentials_profile):
    logger.debug("Searching credentials with scopes: " + str(required_scopes))
    credentials_dir = os.path.join(credentials_base_dir, credentials_profile)
    lib.mkdir_p(credentials_dir)
    
    for path in glob.glob(os.path.join(credentials_dir, "*.json")):
        credentials = json.load(open(path))
        credentials_scope = set(credentials.get("scopes", []))
        if credentials_scope.issuperset(required_scopes):
            logger.info("Using credentials: {}".format(path))
            return path
    uuid_value = str(uuid.uuid1())
    filename = "credentials-{uuid}.json".format(uuid=uuid_value)
    new_path = os.path.join(credentials_dir, filename)
    logger.debug("No credentials for scopes found, creating a new file: " + new_path)
    return new_path

def get_service(service_id):
    services = get_services()
    if service_id not in services:
        raise ShoogleException("Service API not found: {}".format(service_id))
    else:        
        service = services[service_id]
        service_json = lib.download(service["discoveryRestUrl"], cache_dir, logger)
        return lib.load_json(service_json)

def get_method(service, resource_name, method_name):
    if resource_name not in service["resources"]:
        raise ShoogleException("Resource not found: {}".format(resource_name))
    elif method_name not in service["resources"][resource_name]["methods"]:
        raise ShoogleException("Method not found: {}".format(method_name))
    else:
        return service["resources"][resource_name]["methods"][method_name]
            
def replace_schemas(schemas, params, max_level=None, level=0):
    output = collections.OrderedDict()
    for key, value in sorted(params.items()):
        if max_level is not None and level >= max_level:
            output[key] = value
        elif key == "$ref":
            properties = schemas[value].get("properties", schemas[value])
            output.update(replace_schemas(schemas, properties, max_level, level + 1))
        elif isinstance(value, dict):
            output[key] = replace_schemas(schemas, value, max_level, level + 1)
        else:
            output[key] = value
    return output

# Show

def show_services(search_service_id, options):
    services = get_services()
    filtered_services = [(service_id, item) for (service_id, item) in services.items() 
        if re.search(search_service_id, service_id)]
    if len(filtered_services) == 0:
        logger.info("API service not found: {}".format(search_service_id))
    elif len(filtered_services) == 1 and search_service_id in services:
        show_resources(search_service_id, "", options)
    else:    
        for service_id, item in sorted(filtered_services):
            if re.search(search_service_id, service_id):
                output("{id} - {title}".format(id=service_id, title=item["title"]))

def show_resources(service_id, search_resource_name, options):
    resources = get_service(service_id)["resources"]
    filtered_resources = [
        (resource_name, resource) 
        for (resource_name, resource) in resources.items() 
        if re.search(search_resource_name, resource_name)
    ]

    if len(filtered_resources) == 0:
        logger.info("Resource not found in service {}: {}".format(service_id, search_resource_name))
    elif len(filtered_resources) == 1 and search_resource_name in resources:
        show_methods(service_id, search_resource_name, "", options)
    else:    
        for resource_name, resource in sorted(filtered_resources):
            output("{service}.{name}".format(
                service=service_id, 
                name=resource_name,
            ))

def show_methods(service_id, resource_name, search_method_name, options):
    service = get_service(service_id)
    logger.info("Service documentation: {}".format(service["documentationLink"]))
    methods = service["resources"][resource_name]["methods"]

    filtered_methods = [
        (method_name, method) 
        for (method_name, method) in methods.items() 
        if re.search(search_method_name, method_name)
    ]

    if len(filtered_methods) == 0:
        logger.info("Method not found in {service}.{resource}: {method}".format(
            service=service_id, 
            resource=resource_name, 
            method=search_method_name,
        ))
    elif len(filtered_methods) == 1 and search_method_name in methods:
        show_method(service, methods[search_method_name], options)
    else:    
        for method_name, method in sorted(filtered_methods):
            output("{service}.{resource}.{name} - {description}".format(
                service=service_id, 
                resource=resource_name, 
                name=method_name,
                description=method["description"],
            ))

def get_example_request(params, schemas, max_level):
    request = collections.OrderedDict()
    for parameter_name, parameter in sorted(params):
        if isinstance(parameter, dict):
            request[parameter_name] = replace_schemas(schemas, parameter, max_level, 1)
        else:
            opts = parameter.opts
            description = re.sub("\.\s*$", "", opts["description"].splitlines()[0])
            extra_info = {
                "default": opts.get("default"),
                "values": ", ".join(opts.get("enum", []))
            }
            extra_info_string = ", ".join("{}: {}".format(k, v) for (k, v) in extra_info.items() if v)
            parameter_info = " - ".join(["({type}) {description}", "{required}{default}"]).format(
                name=parameter_name,
                type=opts["type"],
                required=("required" if opts.get("required") else "optional"),
                description=description,
                default=(" ({})".format(extra_info_string) if extra_info_string else ""),
            )
            request[parameter_name] = parameter_info
    return request 

def show_method(service, method, options):
    schemas = service["schemas"]

    max_level = options.debug_response_level
    response = replace_schemas(schemas, method.get("response", {}), max_level=max_level)
        
    output("{id}: {description}".format(id=method["id"], description=method["description"]))

    build_param = collections.namedtuple("Param", ["opts"])
    service_params = [(k, build_param(v)) for (k, v) in service.get("parameters", {}).items()]
    method_params = [(k, build_param(v)) for (k, v) in method.get("parameters", {}).items()]
    required_service_params = [(k, p) for (k, p) in service_params if p.opts.get("required")]
    required_method_params = [(k, p) for (k, p) in method_params if p.opts.get("required")]
    body_params = ([("body", method.get("request"))] if method.get("request") else [])
    minimal_params = sorted(required_service_params + required_method_params) + body_params
    all_params = sorted(service_params + method_params + body_params) 
    level = options.debug_request_level
    request = get_example_request(minimal_params, schemas, level)
    
    output("Request (level={max_level}, --debug-request-level=N to change):\n{request}"
        .format(max_level=level, request=lib.pretty_json(request)))

    output("Response (level={max_level}, --debug-response-level=N to change):\n{response}"
        .format(max_level=max_level, response=lib.pretty_json(response)))

# Command: execute

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
                raise ShoogleException("Credentials file not found: {}".
                    format(options.credentials_file))
        else:
            credentials_path = get_credentials_path(scopes, options.credentials_profile)
        get_code = (auth.browser.get_code if options.browser_auth else auth.console.get_code)
        client_secret = options.client_secret_file            
        return auth.get_credentials(client_secret, credentials_path, scopes, get_code)
    else:
        return None

def do_request(service_id, resource_name, method_name, method_options, options):
    service = get_service(service_id)
    method = get_method(service, resource_name, method_name)
    
    if method.get("request") and "body" not in method_options:
        raise ShoogleException("This method need a body property in the request")
    elif method.get("supportsMediaUpload") and not options.media_file:
        raise ShoogleException("This method requires a media file (--media-file=PATH)")
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

# Main

#class ThrowingArgumentParser(argparse.ArgumentParser):
#    def error(self, message):
#        raise ArgumentParserError(message)
# or
#
# except SystemExit:

def get_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-v', '--version', action="store_true", 
        help="Show version")

    subparsers = parser.add_subparsers(help='Commands', dest="command")
    subparsers.required = False
    
    # Command: show
    
    parser_show = subparsers.add_parser('show', help='Show API services')

    parser_show.add_argument('--debug-request-level', type=int, default=1, 
        help='Levels to show of the example request body')
    parser_show.add_argument('--debug-response-level', type=int, default=0, 
        help='Levels to show of the response schema on debug messages')
    parser_show.add_argument('api_path', metavar="API_PATH", nargs='?', default="",
        help="SERVICE:VERSION.RESOURCE.METHOD")
    
    # Command: execute
    
    parser_execute = subparsers.add_parser('execute', help='Execute an API request')
    
    parser_execute.add_argument('-c', '--client-secret-file', metavar="PATH", 
        help="Use a client secret JSON file")
    parser_execute.add_argument('-f', '--media-file', metavar="PATH",
        help='File to use for media-related methods')
    parser_execute.add_argument('--browser-auth', action="store_true", 
        help="Use a browser to authentify")
    parser_execute.add_argument('--credentials-file', 
        metavar="PATH", help="Select profile to use (with separate credentials)")
    parser_execute.add_argument('--credentials-profile', default="default",
        metavar="NAME", help="Select profile to use (wtih separate credentials)")

    parser_execute.add_argument('api_path', metavar="API_PATH",
        help="SERVICE:VERSION.RESOURCE.METHOD")
    parser_execute.add_argument('json_request', metavar="JSON_FILE",
        help="File containing the request JSON (use '-' to read from stdin)")
        
    return parser

def run(args):
    """Acces to Google API services."""
    parser = get_parser("Command-line interface for the Google API.")
    options = parser.parse_args(args)

    if options.version:
        output(__version__)
    elif options.command == "show":
        service_id, resource_name, method_name = lib.pad_list(options.api_path.split(".", 2), 3)
        if resource_name is None:
            show_services(service_id, options)
        elif method_name is None:
            show_resources(service_id, resource_name, options)
        else:
            show_methods(service_id, resource_name, method_name, options)
    elif options.command == "execute":
        service_id, resource_name, method_name = lib.pad_list(options.api_path.split(".", 2), 3)
        method_options = lib.load_json((sys.stdin if options.json_request == "-" 
            else open(options.json_request)).read())
        response = do_request(service_id, resource_name, method_name, method_options, options)
        output(lib.pretty_json(response))
    else:
        parser.print_help(sys.stderr)
        return 2

def main(args):
    logger = lib.get_logger("shoogle", level=logging.DEBUG, channel=sys.stderr)
    try:
        return run(args)
    except TypeError as error:
        frm = inspect.trace()[-1]
        mod = inspect.getmodule(frm[0])
        if mod.__name__ == 'googleapiclient.discovery':
            logger.error("googleapiclient.discovery: {}".format(error))
        else:
            raise 
    except ShoogleException as error:
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
