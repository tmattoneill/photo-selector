#!/bin/bash

python -m venv .venv && source .venv/bin/activate
pip install pytest requests python-dotenv
export BASE_URL="http://localhost:6500/api"   # adjust to your alpha backend
export TEST_IMAGE_DIR="/absolute/path/to/a/folder/with/images"
pytest -q
