#!/usr/local/bin/python
"""Convert, tag, and upload podcast episodes."""
# to do
# - configuration files
# - allow the title and description to be set from the command line
# for public release
# - make it compatible with mp3s
# - check for existence of LAME


import datetime
import os
import sys
import re
import mutagen.id3
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


def parseArgs():
    """Parse the command line arguments and return the filename."""
    # Check for the appropriate number of arguments
    if len(sys.argv) != 2:
        print ansiColor.YELLOW + "Usage: " + sys.argv[0] + " <WAV>", \
            ansiColor.NOCOLOR
        exit()
    # Check that the supplied file exists
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        throwFatalError("\"" + filename + "\" is not a file.")
    # Check that it is a WAV
    fileroot, fileExtension = os.path.splitext(filename)
    if fileExtension.lower() != ".wav":
        throwFatalError("\"" + filename + "\" is not a WAV.")
    log("Processing \'" + fileroot + "\'...")
    return fileroot


def promptUserInput():
    """Get input from the user for the title and the description."""
    # Get the title
    title = unicode(raw_input(ansiColor.BLUE + "Enter a title: " +
                              ansiColor.NOCOLOR))
    if not title:
        throwFatalError("A title must be supplied.")
    if containsInvalidXmlTextChars(title):
        throwFatalError("\'Title\' may only contain valid XML" +
                        "characters (e.g., not '<' and '&').")
    # Get the description
    desc = unicode(raw_input(ansiColor.BLUE + "Enter a description: " +
                             ansiColor.NOCOLOR))
    if not desc:
        throwFatalError("A description must be supplied.")
    if containsInvalidXmlTextChars(desc):
        throwFatalError("\'Description\' may only contain valid XML" +
                        "characters (e.g., not '<' and '&').")
    return title, desc


def transcodeAudio(fileroot):
    """Convert the WAV to an MP3 using Lame."""
    log("Transcoding to MP3...")
    # Check if the mp3 already exists
    if os.path.isfile(fileroot + ".mp3"):
        throwFatalError("\'" + fileroot + ".mp3\' already exists.")
    # Transcode the mp3
    try:
        os.system("lame -V2 -h  --quiet %s.wav %s.mp3" % (fileroot, fileroot))
    except OSError:
        raise
    return fileroot + ".mp3"


def addTags(filename, title, desc):
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
    meta["artist"] = unicode("Sharptown Church")
    meta["date"] = unicode(str(datetime.datetime.now().year))
    meta["album"] = unicode("Sharptown Church Podcast")
    meta.save()
    # Create the image tag
    log("Adding the Cover Image...")
    imageFilename = "podcastLogo1400.jpg"
    _, imageFileExtension = os.path.splitext(imageFilename)
    imageTag = APIC()
    # Determine the file type
    if imageFileExtension.lower() == ".png":
        imageTag.mime = 'image/png'
    elif imageFileExtension.lower() == ".jpg":
        imageTag.mime = 'image/jpeg'
    else:
        throwFatalError("Invalid cover image. Must be a PNG or JPG.")
    # Set the image tags
    imageTag.encoding = 3  # 3 is for utf-8
    imageTag.type = 3      # 3 is for cover image
    imageTag.desc = u'Cover'
    imageTag.data = open(imageFilename, 'rb').read()
    # Add the tag using ID3
    try:
        audio = MP3(filename, ID3=ID3)
        audio.tags.add(imageTag)
        audio.save()
    except:
        raise


def addEntryToXml(filename, title, desc):
    """Add an entry into the XML for this episode."""
    log("Adding entry to the XML file...")
    # Create the backup directory if it doesn't already exist
    backupDir = "./xmlBackups"
    try:
        os.makedirs(backupDir)
    except OSError:
        if not os.path.isdir(backupDir):
            raise
    # Get the date in UTC
    utcnow = datetime.datetime.utcnow()
    # Create the backup file by copying the XML file into the backup directory
    xmlFilename = "sharptownPodcast.xml"
    if not os.path.isfile(xmlFilename):
        throwFatalError("\'" + xmlFilename + "\' is not a file.")
    try:
        os.system("cp %s %s/%s_%s.xml" % (xmlFilename, backupDir,
                  xmlFilename[:-4], utcnow.strftime("%Y%m%d-%H%M%S")))
    except OSError:
        raise
    # Open the XML file for reading
    try:
        f = open(xmlFilename, 'r')
        # Read all the lines from the backup which will be written into the new
        # file along with the new entry
        lines = f.readlines()
        f.close()
    except IOError:
        raise
    # Open the XML file for writing
    try:
        f = open(xmlFilename, 'w')
        # Calculate the length of the episode in hours, minutes, and seconds
        try:
            audioFile = MP3(filename)
            hours, rem = divmod(audioFile.info.length, 3600)
            mins, secs = divmod(rem, 60)
        except:
            raise
        # Write the header
        for i in range(32):
            f.write(lines[i])
        f.write("<lastBuildDate>" + utcnow.strftime("%a, %d %b %Y %H:%M:%S") +
                "</lastBuildDate>\n")
        # Write the new entry
        f.write("<item>\n")
        f.write(" <title>" + title + "</title>\n")
        f.write(" <link>http://sharptown.org</link>\n")
        f.write(" <itunes:author>Sharptown Church</itunes:author>\n")
        f.write(" <dc:creator>Sharptown Church</dc:creator>\n")
        f.write(" <description>" + desc + "</description>\n")
        f.write(" <content:encoded>" + desc + "</content:encoded>\n")
        f.write(" <pubDate>" + utcnow.strftime("%a, %d %b %Y %H:%M:%S") +
                " UTC</pubDate>\n")
        f.write(" <itunes:summary>" + desc + "</itunes:summary>\n")
        f.write(" <itunes:keywords>Sharptown, Methodist, Church, " +
                "Christianity, Religion, Jesus, God</itunes:keywords>\n")
        f.write(" <itunes:duration>%02d:%02d:%02d</itunes:duration>\n"
                % (hours, mins, secs))
        f.write(" <category>Religion &amp; Spirituality</category>\n")
        f.write(" <enclosure url=\"http://sharptown.org/podcast/" +
                sys.argv[1] + "\" length=\"" +
                str(os.path.getsize(filename)) +
                "\" type=\"audio/mpeg3\" />\n")
        f.write(" <guid>http://sharptown.org/podcast/" + filename +
                "</guid>\n")
        f.write(" <itunes:explicit>no</itunes:explicit>\n")
        f.write("</item>\n")
        # Write the remainder of the file
        for i in range(33, len(lines)):
            f.write(lines[i])
        # Clean up!
        f.close()
    except IOError:
        raise


def main():
    """Main function."""
    fileroot = parseArgs()
    title, desc = promptUserInput()
    mp3Filename = transcodeAudio(fileroot)
    addTags(mp3Filename, title, desc)
    addEntryToXml(mp3Filename, title, desc)
    print ansiColor.GREEN + "++ Done. " + u'\u2714' + ansiColor.NOCOLOR


if __name__ == "__main__":
    main()
