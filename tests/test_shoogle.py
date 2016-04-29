#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_shoogle
----------------------------------

Tests for `shoogle` module.
"""

import sys
import re
import json
import unittest
from io import StringIO
from contextlib import contextmanager
import logging
import tempfile

from shoogle import shoogle
from shoogle import lib

import jsmin

def load_json(s):
    return json.loads(jsmin.jsmin(s))    

@contextmanager
def temporal_file(contents):
    with tempfile.NamedTemporaryFile() as fd:
        fd.write(bytes(contents, "utf8"))
        fd.flush()
        yield fd.name

@contextmanager
def main(*args, **kwargs):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    new_stdout, new_stderr = StringIO(), StringIO()
    sys.stdout, sys.stderr = new_stdout, new_stderr
    debug_logger = lib.get_logger("shoogle", level=logging.ERROR, channel=new_stderr)
    kwargs_with_logger = lib.merge(kwargs, dict(logger=debug_logger))
    try:
        status = shoogle.main(*args, **kwargs_with_logger)
    finally:
        sys.stdout, sys.stderr  = old_stdout, old_stderr
    yield (new_stdout.getvalue(), new_stderr.getvalue(), status)

class TestShoogle(unittest.TestCase):
    def test_main_without_arguments_shows_usage_and_help_messages(self):
        with main([]) as (out, err, status):
            self.assertEqual(2, status)
            self.assertIn("usage: ", err)
            self.assertIn("positional arguments:", err)
            self.assertIn("{show,execute} ", err)
            self.assertIn("optional arguments:", err)

    def test_main_with_option_shows_usage_and_help_messages(self):
        with main(["-h"]) as (out, err, status):
            self.assertEqual(2, status)
            self.assertIn("usage: ", out)
            self.assertIn("positional arguments:", out)
            self.assertIn("{show,execute} ", out)
            self.assertIn("optional arguments:", out)

    def test_main_with_option_shows_version(self):
        with main(["-v"]) as (out, err, status):
            self.assertEqual(0, status)
            self.assertEqual(shoogle.__version__, out.strip())

    def test_main_with_empty_show_command_shows_all_services_sorted(self):
        with main(["show"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            services = [line.split()[0] for line in lines]
            self.assertIn("webmasters:v3", services)
            self.assertIn("youtube:v3", services)
            self.assertEqual(list(sorted(services)), services)

    def test_main_with_string_show_command_shows_services_with_that_string(self):
        with main(["show", "youtu"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            services = [line.split()[0] for line in lines]
            self.assertEqual(list(sorted(services)), services)
            for service in services:
              self.assertIn("youtu", service)

    def test_main_with_exact_service_string_shows_all_resources_sorted(self):
        with main(["show", "youtube:v3"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            services = [line.split()[0] for line in lines]
            self.assertIn("youtube:v3.activities", services)
            self.assertIn("youtube:v3.videos", services)
            resources = [service.split(".")[-1] for service in services]
            self.assertEqual(list(sorted(resources)), resources)

    def test_main_with_partial_resource_string_shows_resources_sorted(self):
        with main(["show", "youtube:v3.vid"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            resources = [line.split()[0] for line in lines]
            
            self.assertNotIn("youtube:v3.activities", resources)
            self.assertIn("youtube:v3.videos", resources)
            self.assertEqual(list(sorted(resources)), resources)

    def test_main_with_exact_resource_string_shows_all_methods_sorted(self):
        with main(["show", "youtube:v3.videos"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            methods = [line.split()[0] for line in lines]
            self.assertIn("youtube:v3.videos.list", methods)
            self.assertIn("youtube:v3.videos.insert", methods)
            self.assertEqual(list(sorted(methods)), methods)

    def test_main_with_partial_method_string_shows_matching_methods_sorted(self):
        with main(["show", "youtube:v3.videos.li"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            methods = [line.split()[0] for line in lines]
            self.assertIn("youtube:v3.videos.list", methods)
            self.assertNotIn("youtube:v3.videos.insert", methods)
            self.assertEqual(list(sorted(methods)), methods)

    def test_main_with_exact_method_shows_request_and_response_details(self):
        with main(["show", "youtube:v3.videos.list"]) as (out, err, status):
            self.assertEqual(0, status)
            lines = out.splitlines()
            self.assertTrue("Request" in line for line in lines)
            self.assertTrue("Response" in line for line in lines)

    def test_main_with_exact_method_shows_request_with_minimal_params(self):
        with main(["show", "urlshortener:v1.url.get"]) as (out, err, status):
            self.assertEqual(0, status)
            jsons = re.findall("^\{$.*?^\}$", out, re.MULTILINE | re.DOTALL)
            self.assertEqual(2, len(jsons))
            request_json = load_json(jsons[0])
            response_json = load_json(jsons[1])
            self.assertEqual(["shortUrl"], list(request_json.keys()))
            self.assertEqual({"$ref": 'Url'}, response_json)

    def test_main_execute(self):
        request = """{
            "key": "AIzaSyArB_DJbBDIOpRTKAKyu4cfv0bL56pad0U",
            "shortUrl": "http://goo.gl/Du5PSN"
        }"""
        
        with temporal_file(request) as request_file:
            args = ["execute", "urlshortener:v1.url.get", request_file]
            with main(args) as (out, err, status):
                self.assertEqual(0, status)
                response = load_json(out)
                self.assertEqual(set(["id", "kind", "longUrl", "status"]), 
                    set(response.keys()))
                self.assertEqual(response["status"], "OK")

    def test_main_execute_with_missing_parameter(self):
        with temporal_file("{}") as request_file:
            args = ["execute", "urlshortener:v1.url.get", request_file]
            with main(args) as (out, err, status):
                self.assertEqual(0, status)
                self.assertIn('Missing required parameter "shortUrl"', err)
        
if __name__ == '__main__':
    sys.exit(unittest.main())
