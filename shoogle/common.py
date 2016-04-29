"""Common utility function for shoogle commands."""
import collections
import uuid
import json
import glob
import os
import re

import httplib2

from . import lib
from . import config
from .config import logger

class ShoogleException(Exception):
    """Used for controlled exceptions of the app."""
    pass

def download(url):
    """
    Return the content of a URL if the HTTP_STATUS is 2XX, otherwise raise
    a ShoogleException with a description of the problem.
    """
    logger.info("GET {}".format(url))
    http = httplib2.Http(cache=config.cache_dir)
    headers, content = http.request(url, "GET")
    if re.match("2..", str(headers.status)):
        return content.decode('utf-8')
    else:
        raise ShoogleException("GET {} ({})".format(url, headers.status))

def get_services():
    """Return a dictionary {service_id, service}."""
    apis = download("https://www.googleapis.com/discovery/v1/apis")
    services = lib.load_json(apis)["items"]
    return dict((service["id"], service) for service in services)

def get_credentials_path(required_scopes, credentials_profile):
    """Return the path of the credentials file."""
    logger.debug("Searching credentials with scopes: " + str(required_scopes))
    basedir = config.credentials_base_dir
    credentials_dir = os.path.join(basedir, credentials_profile)
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
    logger.debug("No credentials for scopes, create new file: " + new_path)
    return new_path

def get_service(service_id):
    """Return the service from its ID. Raise ShoogleException if not found."""
    services = get_services()
    if service_id not in services:
        raise ShoogleException("Service API not found: {}".format(service_id))
    else:
        service = services[service_id]
        service_json = download(service["discoveryRestUrl"])
        return lib.load_json(service_json)

def get_method(service, resource_name, method_name):
    """Return the method for a service/resource. Raise ShoogleException if not found."""
    if resource_name not in service["resources"]:
        raise ShoogleException("Resource not found: {}".format(resource_name))
    elif method_name not in service["resources"][resource_name]["methods"]:
        raise ShoogleException("Method not found: {}".format(method_name))
    else:
        return service["resources"][resource_name]["methods"][method_name]

def replace_schemas(schemas, params, max_level=None, level=0):
    """Replace JSON references (key=$ref) for properties."""
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
