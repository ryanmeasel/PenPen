#!/usr/local/bin/python
"""Convert, tag, and upload podcast episodes."""
# to do
# - configuration files
# - dynamically generate the feed header everytime

import argparse
import datetime
import mutagen.id3
import os
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3


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


def throwFatalError(errorMessage):
    """Convenience function to throw error messages and exit the program."""
    print ansiColor.RED + "**ERROR**: " + errorMessage + ansiColor.NOCOLOR
    exit()


def throwWarning(warnMessage):
    """Convenience function to print warning messages."""
    print ansiColor.YELLOW + "**WARNING**: " + warnMessage + ansiColor.NOCOLOR


def log(logMessage):
    """Convenience function for printing log messages to the console."""
    print ansiColor.PURPLE + "++ " + logMessage + ansiColor.NOCOLOR


def containsInvalidXmlTextChars(xmlString):
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


def fileExists(filename):
    """Check that the file exists."""
    if os.path.isfile(filename):
        return True
    else:
        return False


def extensionValid(filename, ext):
    """Check that the file has the specified extension."""
    _, fileExtension = os.path.splitext(filename)
    if fileExtension.lower() == ext.lower():
        return True
    else:
        return False


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


def processTitleAndDesc(title, desc):
    """Acquite and validate the title and description of the episode."""
    # Get the title if it wasn't passed in on the command line.
    if not title:
        title = unicode(raw_input(ansiColor.BLUE + "Enter a title: " +
                                  ansiColor.NOCOLOR))

        # Check that something was entered, enforcing a non-empty title
        if not title:
            throwFatalError("A title must be supplied.")

    if containsInvalidXmlTextChars(title):
        throwFatalError("\'Title\' may only contain valid XML" +
                        "characters (e.g., not '<' and '&').")
    log("Title is valid.")

    # Get the description if it wasn't passed in on the command line.
    if not desc:
        desc = unicode(raw_input(ansiColor.BLUE + "Enter a description: " +
                                 ansiColor.NOCOLOR))
        if not desc:
            throwFatalError("A description must be supplied.")

    if containsInvalidXmlTextChars(desc):
        throwFatalError("\'Description\' may only contain valid XML" +
                        "characters (e.g., not '<' and '&').")
    log("Description is valid.")

    return title, desc


def processAudio(filename):
    """Validate the audio file and transcode if necessary."""
    # Check that the file exists
    if not fileExists(filename):
        throwFatalError("\'" + filename + "\' does not exist.")

    # Check that the file is either a WAV or an MP3
    if not extensionValid(filename, '.WAV') and \
       not extensionValid(filename, '.MP3'):
        throwFatalError("The audio file must be a WAV or MP3.")

    # If it's a WAV, then transcode it to MP3
    if extensionValid(filename, '.WAV'):
        return transcodeAudio(filename)
    else:
        return filename


def transcodeAudio(filename):
    """Convert the WAV to an MP3 using Lame."""
    log("Transcoding to MP3...")
    # Check if the mp3 already exists
    fileroot, _ = os.path.splitext(filename)
    if fileExists(fileroot + ".mp3"):
        throwFatalError("\'" + fileroot + ".mp3\' already exists.")

    # Transcode the mp3
    try:
        os.system("lame -V2 -h  --quiet %s.wav %s.mp3" % (fileroot, fileroot))
    except OSError:
        raise
    return fileroot + ".mp3"


def addTags(config, filename, title, desc):
    """Add ID3 tags and cover image to the mp3."""
    log("Adding ID3 tags...")

    # Use EasyID3 to apply text tags since it's less complicated than ID3.
    # Sadly, EasyID3 can not handle album art so we'll do that separate.
    try:
        meta = EasyID3(filename)
    except mutagen.id3.ID3NoHeaderError:
        meta = MP3(filename, ID3=EasyID3)
        meta.add_tags()

    # Set tags
    meta["title"] = title
    meta["artist"] = unicode(config["artist"])
    meta["date"] = unicode(str(datetime.datetime.now().year))
    meta["album"] = unicode(config["album"])
    meta.save()

    # Create the image tag
    log("Adding the Cover Image...")
    imageFilepath = config["imageFilepath"]
    _, imageFileExtension = os.path.splitext(imageFilepath)
    imageTag = APIC()

    # Determine the file type
    if imageFileExtension.lower() == ".png":
        imageTag.mime = 'image/png'
    elif imageFileExtension.lower() == ".jpg":
        imageTag.mime = 'image/jpeg'
    else:
        throwFatalError("Cover image must be a PNG or JPG.")

    # Set the image tags
    imageTag.encoding = 3  # 3 is for utf-8
    imageTag.type = 3      # 3 is for cover image
    imageTag.desc = u'Cover'
    with open(imageFilepath, 'rb') as f:
        imageTag.data = f.read()

    # Add the tag using ID3
    try:
        audio = MP3(filename, ID3=ID3)
        audio.tags.add(imageTag)
        audio.save()
    except:
        raise


def addEntryToXml(config, filename, title, desc):
    """Add an entry into the XML for this episode."""
    log("Adding entry to the XML file...")

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
        throwFatalError("\'" + xmlFilepath + "\' is not a file.")
    try:
        os.system("cp %s %s/%s_%s.xml" % (xmlFilepath, backupDir,
                  xmlFilepath[:-4], utcnow.strftime("%Y%m%d-%H%M%S")))
    except OSError:
        raise

    # Read all the lines from the backup which will be written into the new
    # file along with the new entry
    with open(xmlFilepath, 'r') as f:
        lines = f.readlines()

    # Calculate the length of the episode in hours, minutes, and seconds
    try:
        audioFile = MP3(filename)
        hours, rem = divmod(audioFile.info.length, 3600)
        mins, secs = divmod(rem, 60)
    except:
        raise

    # Open the XML file for writing
    with open(xmlFilepath, 'w') as f:
        # Write the header
        for i in range(32):
            f.write(lines[i])
        f.write("<lastBuildDate>" + utcnow.strftime("%a, %d %b %Y %H:%M:%S") +
                "</lastBuildDate>\n")

        # Write the new entry
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
                % (hours, mins, secs))
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

        # Write the remainder of the file
        for i in range(33, len(lines)):
            f.write(lines[i])


def parseConfigFile(configFile):
    """Parse the configuration file."""
    # Read in the config file
    if not fileExists(configFile):
        throwFatalError("\'" + configFile + "\' does not exist.")
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
            throwWarning("\'" + fields[0] + "\' has not been specified.")

        # Assign the key value pair and strip whitespace
        key = fields[0].lstrip().rstrip()
        value = fields[1].lstrip().rstrip()

        # Strip doubles quotes from the value if it has it
        if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
        config[key] = value
    return config


def main():
    """Main function."""
    args = parseArgs()
    config = parseConfigFile(args.config)
    title, desc = processTitleAndDesc(args.title, args.description)
    mp3Filename = processAudio(args.audioFile)
    addTags(config, mp3Filename, title, desc)
    addEntryToXml(config, mp3Filename, title, desc)
    print ansiColor.GREEN + "++ Done. " + u'\u2714' + ansiColor.NOCOLOR


if __name__ == "__main__":
    main()
