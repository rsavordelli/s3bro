#!/usr/bin/env bash

if [ "$1" == "make" ]; then
    $0 clean > /dev/null
    virtualenv build_env
    source build_env/bin/activate
    pip install twine --no-cache-dir
    python2.7 setup.py sdist
elif [ "$1" == "clean" ]; then
    echo -n "Roger that. "
    rm -rf build_env/
    rm -rf build/
    rm -rf dist/
    rm -rf *egg-info*
    echo "Sector clear."
elif [ "$1" == "install" ]; then
    $0 make
    source build_env/bin/activate
    twine upload dist/*
    $0 clean > /dev/null
else
    echo "No action defined. Options: clean,make,install."
fi
