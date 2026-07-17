#!/usr/bin/env python3
"""Enables `python -m app.cli ...` as the invocation style."""

from app.cli.main import app

if __name__ == "__main__":
    app()