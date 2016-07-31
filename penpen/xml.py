#!/usr/bin/env python
"""Convert, tag, and upload podcast episodes."""


import datetime
import logging
import os
import re

import fileUtils

# Configure logger globally
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def addItem(filename, config, title, desc, length):
    """Add an item into the XML feed."""
    logger.info("Adding entry to the XML file...")

    # Get the date in UTC
    utcnow = datetime.datetime.utcnow()

    # Read all the lines from the backup which will be written into the new
    # file along with the new entry
    with open(filename, 'r') as f:
        lines = f.readlines()

    writeHeader(filename, lines, utcnow)
    appendItem(filename, config, title, desc, length, utcnow)
    appendBody(filename, lines)


def writeHeader(filename, lines, time):
    """Write the XML feed header."""
    # Open the file for writing
    with open(filename, 'w') as f:
        # Write the header
        for i in range(32):
            f.write(lines[i])
        f.write("<lastBuildDate>" + time.strftime("%a, %d %b %Y %H:%M:%S") +
                "</lastBuildDate>\n")


def appendItem(filename, config, title, desc, length, utcnow):
    """Append the new item to the top of the feed."""
    # Open the file for appending
    with open(filename, 'a') as f:
        f.write("<item>\n")
        f.write(" <title>" + title + "</title>\n")
        f.write(" <link>" + config["link"] + "</link>\n")
        f.write(" <itunes:author>" + config["itunesAuthor"] +
                "</itunes:author>\n")
        f.write(" <dc:creator>" + config["dcCreator"] + "</dc:creator>\n")
        f.write(" <description>" + desc + "</description>\n")
        f.write(" <content:encoded>" + desc + "</content:encoded>\n")
        f.write(" <pubDate>" + utcnow.strftime("%a, %d %b %Y %H:%M:%S") +
                " UTC</pubDate>\n")
        f.write(" <itunes:summary>" + desc + "</itunes:summary>\n")
        f.write(" <itunes:keywords>" + config["itunesKeywords"] +
                "</itunes:keywords>\n")
        f.write(" <itunes:duration>%02d:%02d:%02d</itunes:duration>\n"
                % (length[0], length[1], length[2]))
        f.write(" <category>" + config["category"] + "</category>\n")

        # The "webFolder" must end in a slash
        webFolder = config["webFolder"]
        if not webFolder.endswith('/'):
            webFolder += "/"

        f.write(" <enclosure url=\"" + webFolder +
                filename + "\" length=\"" +
                str(os.path.getsize(filename)) +
                "\" type=\"audio/mpeg3\" />\n")
        f.write(" <guid>" + webFolder + filename + "</guid>\n")
        f.write(" <itunes:explicit>" + config["itunesExplicit"] +
                "</itunes:explicit>\n")
        f.write("</item>\n")


def appendBody(filename, lines):
    """Write the remainder of the body after the item has been added."""
    # Open the file for appending
    with open(filename, 'a') as f:
        # Write the remainder of the file
        for i in range(33, len(lines)):
            f.write(lines[i])


def createBackup(config):
    """Create a backup of the XML file."""
    # Get the date in UTC
    utcnow = datetime.datetime.utcnow()

    # Create the XML backup directory if it doesn't already exist
    backupDir = config["xmlBackupDir"]
    try:
        os.makedirs(backupDir)
    except OSError:
        if not os.path.isdir(backupDir):
            raise

    # Create the backup file by copying the XML file into the backup directory
    xmlFilepath = config["xmlFilepath"]
    if not os.path.isfile(xmlFilepath):
        logger.fatal("\'" + xmlFilepath + "\' is not a file.")
        exit(1)

    try:
        os.system("cp %s %s/%s_%s.xml" % (xmlFilepath,
                                          backupDir,
                                          xmlFilepath[:-4],
                                          utcnow.strftime("%Y%m%d-%H%M%S")))
    except OSError:
        raise


def parseConfigFile(configFile):
    """Parse the configuration file."""
    # Read in the config file
    if not fileUtils.exists(configFile):
        logger.fatal("\'" + configFile + "\' does not exist.")
        exit(1)
    with open(configFile) as f:
        contents = f.readlines()

    # Load the contents into a dictionary
    config = dict()

    for line in contents:
        # Each line should have a single parameter delimited by "=".
        # Skip if the line is only whitespace.
        if line.isspace():
            continue

        # Skip if the line if it is a comment (starts with "#")
        if line[0] == "#":
            continue
        fields = line.split('=', 1)
        if len(fields) < 2:
            logger.warning("\'" + fields[0] + "\' has not been specified.")

        # Assign the key value pair and strip whitespace
        key = fields[0].lstrip().rstrip()
        value = fields[1].lstrip().rstrip()

        # Strip doubles quotes from the value if it has it
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]

        config[key] = value

    return config


def containsInvalidTextChars(xmlString):
    """Check the string for invalid XML characters.

    This is not intended to validate the XML. It's only meant catch characters
    in the text (i.e., '<' and '&').
    """
    illegalXmlCharsRE = re.compile("[<&]")
    match = illegalXmlCharsRE.search(xmlString)
    if not match:
        return False    # no invalid characters found
    else:
        return True     # string contains an invalid character
