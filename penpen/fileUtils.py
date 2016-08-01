#!/usr/bin/env python
"""Utility functions for inspecting files."""

import logging
import os

# Configure logger globally
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def extValid(filename, ext):
    """Check that the file has the specified extension."""
    _, fileExtension = os.path.splitext(filename)
    if fileExtension.lower() == ext.lower():
        return True
    else:
        return False


def which(exe):
    """Locate an executable in the user's path.

    Python 2.7 does not provide a `which` equivalent command so we implement it
    where by searching the user's path
    """
    path = os.getenv('PATH')

    # Search the path and check if the exe exists in any of them.
    for pDir in path.split(os.path.pathsep):
        fPath = os.path.join(pDir, exe)
        if os.path.exists(fPath) and os.access(fPath, os.X_OK):
            return fPath
