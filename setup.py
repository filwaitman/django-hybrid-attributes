import sys

from setuptools import setup

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 6)
if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write('This project does not support your Python version.')
    sys.exit(1)

setup()
