#!/bin/sh

pip install alembic

alembic upgrade head

python3 main.py