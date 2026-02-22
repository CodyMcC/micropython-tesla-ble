#!/bin/bash
# Wrapper for upydev to handle spaces in path
source .venv/bin/activate
python .venv/bin/upydev "$@"
