#!/usr/bin/python3

MODULE_PATH = "fileset/mymodule/__init__.py"
MODULE_NAME = "mymodule"
import importlib
import sys
spec = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

import mymodule

f = open('fileset/test.txt')
content = mymodule.titlecase(f.read())
f.close()

print(content)
