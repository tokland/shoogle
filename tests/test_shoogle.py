#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_shoogle
----------------------------------

Tests for `shoogle` module.
"""

import collections
from contextlib import contextmanager
import json
from io import StringIO
import logging
import re
import sys
import tempfile
import unittest

import shoogle
from shoogle import lib
from shoogle import config
from . import secrets

import jsmin

def load_json(string):
    return json.loads(jsmin.jsmin(string))

@contextmanager
def temporal_file(contents):
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(bytes(contents, "utf8"))
        fd.flush()
        yield fd.name

Execution = collections.namedtuple("Execution", ["status", "out", "err"])

def main(*args, **kwargs):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    new_stdout, new_stderr = StringIO(), StringIO()
    sys.stdout, sys.stderr = new_stdout, new_stderr
    config.logger = lib.get_logger("shoogle-test", level=logging.ERROR, channel=new_stderr)
    try:
        status = shoogle.main(*args, **kwargs)
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    return Execution(status=status, out=new_stdout.getvalue(), err=new_stderr.getvalue())

class TestShoogle(unittest.TestCase):
    def test_main_without_arguments_shows_usage_and_help_messages(self):
        e = main([])

        self.assertEqual(2, e.status)
        self.assertIn("usage: ", e.err)
        self.assertIn("positional arguments:", e.err)
        self.assertIn("{show,execute}", e.err)
        self.assertIn("optional arguments:", e.err)

    def test_main_with_option_shows_usage_and_help_messages(self):
        e = main(["-h"])

        self.assertEqual(2, e.status)
        self.assertIn("usage: ", e.out)
        self.assertIn("positional arguments:", e.out)
        self.assertIn("{show,execute}", e.out)
        self.assertIn("optional arguments:", e.out)

    def test_main_with_option_shows_version(self):
        e = main(["-v"])

        self.assertEqual(0, e.status)
        self.assertEqual(shoogle.__version__, e.out.strip())

    def test_main_with_empty_show_command_shows_all_services_sorted(self):
        e = main(["show"])

        self.assertEqual(0, e.status)
        lines = e.out.splitlines()
        services = [line.split()[0] for line in lines]
        self.assertIn("webmasters:v3", services)
        self.assertIn("youtube:v3", services)
        self.assertEqual(list(sorted(services)), services)

    def test_main_with_string_show_command_shows_services_with_that_string(self):
        e = main(["show", "youtu"])

        self.assertEqual(0, e.status)
        lines = e.out.splitlines()
        services = [line.split()[0] for line in lines]
        self.assertEqual(list(sorted(services)), services)
        for service in services:
            self.assertIn("youtu", service)

    def test_main_with_exact_service_string_shows_all_resources_sorted(self):
        e = main(["show", "youtube:v3"])

        self.assertEqual(0, e.status)
        lines = e.out.splitlines()
        services = [line.split()[0] for line in lines]
        self.assertIn("youtube:v3.activities", services)
        self.assertIn("youtube:v3.videos", services)
        resources = [service.split(".")[-1] for service in services]
        self.assertEqual(list(sorted(resources)), resources)

    def test_main_with_partial_resource_string_shows_resources_sorted(self):
        e = main(["show", "youtube:v3.vid"])
        lines = e.out.splitlines()
        resources = [line.split()[0] for line in lines]

        self.assertEqual(0, e.status)
        self.assertNotIn("youtube:v3.activities", resources)
        self.assertIn("youtube:v3.videos", resources)
        self.assertEqual(list(sorted(resources)), resources)

    def test_main_with_exact_resource_string_shows_all_methods_sorted(self):
        e = main(["show", "youtube:v3.videos"])
        lines = e.out.splitlines()
        methods = [line.split()[0] for line in lines]

        self.assertEqual(0, e.status)
        self.assertIn("youtube:v3.videos.list", methods)
        self.assertIn("youtube:v3.videos.insert", methods)
        self.assertEqual(list(sorted(methods)), methods)

    def test_main_with_partial_method_string_shows_matching_methods_sorted(self):
        e = main(["show", "youtube:v3.videos.li"])
        lines = e.out.splitlines()
        methods = [line.split()[0] for line in lines]

        self.assertEqual(0, e.status)
        self.assertIn("youtube:v3.videos.list", methods)
        self.assertNotIn("youtube:v3.videos.insert", methods)
        self.assertEqual(list(sorted(methods)), methods)

    def test_main_with_exact_method_shows_request_and_response_details(self):
        e = main(["show", "youtube:v3.videos.list"])
        lines = e.out.splitlines()

        self.assertEqual(0, e.status)
        self.assertTrue("Request" in line for line in lines)
        self.assertTrue("Response" in line for line in lines)

    def test_main_with_exact_method_shows_request_with_minimal_params(self):
        e = main(["show", "urlshortener:v1.url.get"])
        jsons = re.findall(r"^\{$.*?^\}$", e.out, re.MULTILINE | re.DOTALL)

        self.assertEqual(0, e.status)
        self.assertEqual(2, len(jsons))
        request_json = load_json(jsons[0])
        response_json = load_json(jsons[1])
        self.assertEqual(["shortUrl"], list(request_json.keys()))
        self.assertEqual({"$ref": 'Url'}, response_json)

    def test_main_execute(self):
        request = """{
            "key": "%s",
            "shortUrl": "http://goo.gl/Du5PSN"
        }""" % secrets.server_key

        with temporal_file(request) as request_file:
            e = main(["execute", "urlshortener:v1.url.get", request_file])
            self.assertEqual(0, e.status)
            response = load_json(e.out)
            self.assertEqual(set(["id", "kind", "longUrl", "status"]), set(response.keys()))
            self.assertEqual(response["status"], "OK")

    def test_main_execute_with_missing_parameter(self):
        with temporal_file("{}") as request_file:
            e = main(["execute", "urlshortener:v1.url.get", request_file])
            self.assertEqual(0, e.status)
            self.assertIn('Missing required parameter "shortUrl"', e.err)
        
if __name__ == '__main__':
    sys.exit(unittest.main())
