#!/bin/bash
set -e 
alembic upgrade head
python -m src.api.main
