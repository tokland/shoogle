import collections
import re

from .. import lib
from .. import common
from ..config import logger

def add_parser(subparsers, name):
    parser = subparsers.add_parser(name)

    parser.add_argument('--debug-request-level', type=int, default=1,
        help='Levels to show of the example request body')
    parser.add_argument('--debug-response-level', type=int, default=0,
        help='Levels to show of the response schema on debug messages')
    parser.add_argument('api_path', metavar="API_PATH", nargs='?', default="",
        help="SERVICE:VERSION.RESOURCE.METHOD")

def run(options):
    parts = options.api_path.split(".")
    if len(parts) >= 2 and parts[1].isdigit():
        parts = [f"{parts[0]}.{parts[1]}"] + parts[2:]
    service_id, resource_name, method_name = lib.pad_list(parts, 3)

    if resource_name is None:
        show_services(service_id, options)
    elif method_name is None:
        show_resources(service_id, resource_name, options)
    else:
        show_methods(service_id, resource_name, method_name, options)

def show_services(search_service_id, options):
    services = common.get_services()
    filtered_services = [(service_id, item) for (service_id, item) in services.items() 
        if re.search(search_service_id, service_id)]

    if len(filtered_services) == 0:
        logger.info("API service not found: {}".format(search_service_id))
    elif len(filtered_services) == 1 and search_service_id in services:
        show_resources(search_service_id, "", options)
    else:    
        for service_id, item in sorted(filtered_services):
            if re.search(search_service_id, service_id):
                lib.output("{id} - {title}".format(id=service_id, title=item["title"]))

def show_resources(service_id, search_resource_name, options):
    resources = common.get_service(service_id)["resources"]
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
            lib.output("{service}.{name}".format(
                service=service_id, 
                name=resource_name,
            ))

def show_methods(service_id, resource_name, search_method_name, options):
    service = common.get_service(service_id)
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
            lib.output("{service}.{resource}.{name} - {description}".format(
                service=service_id, 
                resource=resource_name, 
                name=method_name,
                description=method["description"],
            ))

def get_example_request(params, schemas, max_level):
    request = collections.OrderedDict()
    for parameter_name, parameter in sorted(params):
        if isinstance(parameter, dict):
            request[parameter_name] = common.replace_schemas(schemas, parameter, max_level, 1)
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
    response = common.replace_schemas(schemas, method.get("response", {}), max_level=max_level)
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

    lib.output("{id}: {description}".format(id=method["id"], description=method["description"]))    
    lib.output("Request (level={max_level}, --debug-request-level=N to change):\n{request}"
        .format(max_level=level, request=lib.pretty_json(request)))
    lib.output("Response (level={max_level}, --debug-response-level=N to change):\n{response}"
        .format(max_level=max_level, response=lib.pretty_json(response)))
