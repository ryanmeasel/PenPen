#!/usr/bin/env python
"""Utility functions for inspecting files."""

import logging
import os

# Configure logger globally
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def exists(filename):
    """Check that the file exists."""
    if os.path.isfile(filename):
        return True
    else:
        return False


def extValid(filename, ext):
    """Check that the file has the specified extension."""
    _, fileExtension = os.path.splitext(filename)
    if fileExtension.lower() == ext.lower():
        return True
    else:
        return False
