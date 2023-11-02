#!/bin/bash

ls -R ${DY_SIDECAR_PATH_INPUTS}

INPUT_1=${DY_SIDECAR_PATH_INPUTS}/input_1
export INPUT_1

python3 /docker/runner.py setup 
python3 /docker/runner.py start
