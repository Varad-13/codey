#!/bin/bash

# Build source and wheel distributions
python3 -m pip install --upgrade setuptools wheel
python3 setup.py sdist bdist_wheel

# List created files
ls -l dist/
