#!/usr/local/bin/python
"""Convert, tag, and upload podcast episodes."""
# to do
# - configuration files
# - cp the backup back to the original if the write fails
# - dynamically generate the feed header everytime

import argparse
import logging

import audio
import xml

# Configure logger globally
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class ansiColor:
    """ANSI terminal colors."""

    RED = '\033[1;31m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[1;34m'
    PURPLE = '\033[1;35m'
    NOCOLOR = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def parseArgs():
    """Parse the command line arguments."""
    # Define the parser
    parser = argparse.ArgumentParser(description='Transcode, tag, and upload \
                                     podcast episodes.')
    parser.add_argument('-c', '--config', required=True,
                        help='Configuration file with the feed parameters.')
    parser.add_argument('-t', '--title', type=str, required=False,
                        help='Title of the episode.')
    parser.add_argument('-d', '--description', type=str, required=False,
                        help='Description of the episode.')
    parser.add_argument('audioFile', help='WAV or MP3 file to be added to the \
                        feed. WAV files will be transcoded to 128 Kbps MP3s.')

    # Returns a namespace containing the parsed arguments
    return parser.parse_args()


def validateTextField(field, fieldName):
    """Validate a text field. Prompt if empty."""
    # Get the title if it wasn't passed in on the command line.
    if not field:
        field = unicode(raw_input(ansiColor.BLUE +
                                  "Enter the " +
                                  fieldName.lower() +
                                  ": " +
                                  ansiColor.NOCOLOR))

        # Check that something was entered, enforcing a non-empty title
        if not field:
            logging.fatal("\'" + fieldName + "\' must be supplied.")
            exit(1)

    if xml.containsInvalidTextChars(field):
        logger.fatal("\'" + fieldName + "\' may only contain valid XML" +
                     "characters (e.g., not '<' and '&').")
        exit(1)

    return field


def main():
    """Main function."""
    args = parseArgs()
    config = xml.parseConfigFile(args.config)
    title = validateTextField(args.title, "Title")
    desc = validateTextField(args.description, "Description")
    filename, length = audio.process(args.audioFile, config, title, desc)
    xml.addItem(filename, config, title, desc, length)
    logger.info(ansiColor.GREEN + "++ Done. " + u'\u2714' + ansiColor.NOCOLOR)


if __name__ == "__main__":
    main()
