import os
import re
import sys
import json
import glob
import uuid
import string
import httplib2
import optparse
import itertools
import urllib.request

import apiclient
import googleapiclient.errors
import googleapiclient.discovery

import auth

def first(it):
    return next(it, None)

def merge(d1, d2):
    d3 = d1.copy()
    d3.update(d2)
    return d3

def pad_list(lst, n):
    if len(lst) >= n:
        return lst[:n]
    else:
        return lst + [None] * (n - len(lst))

def pretty_json(obj):
    return json.dumps(obj, indent=2)

def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in s if c in valid_chars).replace(' ','_')

def debug(msg=""):
    print(str(msg), file=sys.stderr)
    
def _download(url):
    response = urllib.request.urlopen(url)
    return response.read().decode('utf-8')

def download(url):
    path = os.path.join("cache", format_filename(url))
    if os.path.exists(path):
        return open(path).read()
    else:
        data = _download(url)
        open(path, "w").write(data)
        return data

### App

def get_apis():
    apis_json = download("https://www.googleapis.com/discovery/v1/apis")
    items = json.loads(apis_json)["items"]
    return {tuple(item["id"].split(":")): item for item in items}

def show_apis(api_name = ""):
    items = [item for item in get_apis().values() if re.search(api_name, item["name"])]
    sorted_items = sorted(items, key=lambda item: (item["name"], item["version"]))
    for name, itemsit in itertools.groupby(sorted_items, lambda item: item["name"]):
        items = list(itemsit)
        item = items[-1]
        versions = [item["version"] for item in items]
        names_with_version = ", ".join("{name}:{version}".
            format(name=item["name"], version=version) for version in versions)
        debug("{names_with_version} - {title}".format(
            names_with_version=names_with_version, 
            description=item["description"], 
            title=item["title"]))

def get_api_info(apiname, version):
    apis = get_apis()
    api = apis[(apiname, version)]
    service_json = download(api["discoveryRestUrl"])
    return json.loads(service_json)
    
def execute_media_request(request):
    while 1:
        status, response = request.next_chunk()
        if response:
            return response

def get_credential_path(directory, required_scopes):
    debug("Searching credentials with scopes: " + str(required_scopes))
    for path in glob.glob(os.path.join(directory, "*.json")):
        credentials = json.load(open(path))
        credentials_scope = set(credentials.get("scopes", []))
        if credentials_scope.issuperset(required_scopes):
            debug("Using credentials: {}".format(path))
            return path
    uuid_value = str(uuid.uuid1())
    new_path = os.path.join(directory, "credentials-{uuid}.json".format(uuid=uuid_value))
    debug("No credential found, creating a new file: " + new_path)
    return new_path
        
def api_request(api, version, resource, method, method_options, options):
    info = get_api_info(api, version)
    method_info = info["resources"][resource]["methods"][method]
    if method_info.get("request") and not options.body:
        raise ValueError("Method need a body (--body=JSON)")
    elif method_info.get("supportsMediaUpload") and not options.media_file:
        raise ValueError("Method {} requires a media file (--media-file=PATH)".format(method))
    scopes = method_info.get("scopes", [])
    credentials_path = get_credential_path("credentials", scopes)
    credentials = auth.get_credentials("client_id.json", credentials_path, scopes)
    http = credentials.authorize(httplib2.Http())
    api = googleapiclient.discovery.build(api, version, http=http)
    
    resource_func = getattr(api, resource)
    method_func = getattr(resource_func(), method)
    all_options = merge(method_options, ({"body": json.loads(options.body)} if options.body else {}))
    if options.media_file:
        media_body = apiclient.http.MediaFileUpload(options.media_file, chunksize=-1, 
            resumable=True, mimetype="application/octet-stream")
        all_options2 = merge(all_options, {"media_body": media_body})
        debug("Request: " + pretty_json(all_options2))
        request = method_func(**all_options2)
        return execute_media_request(request)
    else:
        debug("Request: " + pretty_json(all_options))
        request = method_func(**all_options)
        return request.execute()

def show_request(api, version, resource, method, data, options):
    method_options = json.loads(data)
    response = api_request(api, version, resource, method, method_options, options)
    if response:
        debug(pretty_json(response))

def show_resources(api, version):
    info = get_api_info(api, version)
    for resource_name, resource in info["resources"].items():
        debug("{api}:{version}.{name}".format(api=api, version=version, name=resource_name))

def show_methods(api, version, resource_name):
    info = get_api_info(api, version)
    for method_name, method in info["resources"][resource_name]["methods"].items():
        debug("{api}:{version}.{resource}.{name} - {description}".format(
            api=api, 
            version=version, 
            resource=resource_name, 
            name=method_name,
            description=method["description"],
        ))
    
def show_method(api, version, resource_name, method_name, options):
    info = get_api_info(api, version)
    schemas = info["schemas"]
    debug("{api}:{version}.{resource}.{method}".
        format(api=api, version=version, resource=resource_name, method=method_name))
    method = info["resources"][resource_name]["methods"][method_name]
    api_params = info.get("parameters", {})
    method_params = method.get("parameters", {})
    all_parameters = list(api_params.items()) + list(method_params.items())
    
    debug()
    debug("Method parameters (--all-parameters to show all):")
    parameters = sorted(all_parameters, 
        key=lambda pair: (not (pair[1].get("required") or False), pair[0]))
    for parameter_name, parameter in parameters:
        description = parameter["description"].split("\n")[0]
        extra_info = {
            "default": parameter.get("default"),
            "values": ", ".join(parameter.get("enum", []))
        }
        extra_info_string = ", ".join("{}: {}".format(k, v) for (k, v) in extra_info.items() if v)
        parameter_info = "{name}[{type}]{required} - {description} {default}".format(
            name=parameter_name,
            type=parameter["type"],
            required=("*" if parameter.get("required") else ""),
            description=description,
            default=("({})".format(extra_info_string) if extra_info_string else ""),
        )
        debug("  " + parameter_info)

    if method.get("request"):
        debug()
        debug("Request body (--body=BODY):")

        for parameter_name, parameter in replace_schemas(schemas, method["response"], max_level=1).items():
            description = parameter["description"].split("\n")[0]
            if parameter.get("$ref"):
                parameter_info = "{ref_name} - {description}".format(
                    ref_name=parameter["$ref"],
                    description=description,
                )
            else:
                extra_info = {
                    "default": parameter.get("default"),
                    "values": ", ".join(parameter.get("enum", []))
                }
                extra_info_string = ", ".join("{}: {}".format(k, v) for (k, v) in extra_info.items() if v)
                parameter_info = "{name}[{type}]{required} - {description} {default}".format(
                    name=parameter_name,
                    type=parameter["type"],
                    required=("*" if parameter.get("required") else ""),
                    description=description,
                    default=("({})".format(extra_info_string) if extra_info_string else ""),
                )
            debug("  " + parameter_info)

    debug()
    debug("Response (--debug-response-level=N to change the levels shown) {}".format(pretty_json(replace_schemas(schemas, method["response"], max_level=options.debug_response_level))))

def replace_schemas(schemas, params, max_level, level=0):
    output = {}
    for key, value in params.items():
        if max_level is not None and level >= max_level:
            output[key] = value
        elif key == "$ref":
            output.update(replace_schemas(schemas, schemas[value]["properties"], max_level, level + 1))
        else:
            output[key] = (replace_schemas(schemas, value, max_level, level + 1) 
                if isinstance(value, dict) else value)
    return output

def main(sysargs):
    """Google API CLI."""
    usage = """Usage: %prog [OPTIONS] API:VERSION.RESOURCE.METHOD JSON_STRING|-

    Command-line interface for the Google API."""
    parser = optparse.OptionParser(usage)

    parser.add_option('-b', '--body', dest='body', 
        type="string", help='Body JSON for methods requiring a separate request body')
    parser.add_option('-f', '--media-file', dest='media_file', 
        type="string", help='File to use for media-related methods')

    parser.add_option('', '--debug-response-level', dest='debug_response_level', 
        type="int", default=0, help='Levels to show of the response schema on debug messages')

    # Add options:
    #
    # list
    # auth-gui
    # secrets_file
    # credetials_directory
    # credentials_file
    # response-json-pointer

    options, args = parser.parse_args(sysargs)
    # to send options to function that wants to show options
    # parser.option_list[1].dest
    # parser.option_list[1].get_opt_string()

    s = (args[0] if len(args) > 0 else "")
    api_with_version, resource, method = pad_list(s.split(".", 2), 3)
    data = (args[1] if len(args) > 1 else None)
    api, version = pad_list((api_with_version or "").split(":", 1), 2)  
    if not api:
        show_apis()
    elif not version:
        show_apis(api)
    elif not resource:
        show_resources(api, version)
    elif not method:
        show_methods(api, version, resource)
    elif not data:
        show_method(api, version, resource, method, options)
    else:
        jsondata = (sys.stdin.read() if data == "-" else data)
        show_request(api, version, resource, method, jsondata, options)

if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except TypeError as error:
        debug("Request error: " + str(error))
        sys.exit(1)
    except googleapiclient.errors.HttpError as error:
        status = error.resp["status"]
        debug("Server response: {1}".format(status, bytes.decode(error.content).strip()))
        sys.exit(1)
    except json.decoder.JSONDecodeError as error:
        debug("JSONDecodeError: " + str(error))
        debug("Document: " + error.doc)
        sys.exit(1)
