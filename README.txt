# PenPen
Encode audio podcast episodes and generate the RSS feed.

![alt tag](http://vignette1.wikia.nocookie.net/evangelion/images/6/60/Pen_Pen_(NGE).png)

Features:
- Works with WAVs or MP3s (encodes WAVs to ).
- Adds ID3 tags to the file.
- Generates the RSS feed.
- Creates RSS feed backups.

# Usage
1. Create a custom configuration file specifying the details of the RSS feed. See `configurationExample.conf` for an example.

1. Run:
```bash
penpen -c [CONFIG_FILE] [AUDIO_FILE]
```
  At runtime, the user will be prompted to provide the episode title and description.

  If a WAV file is provided, it will be encoded to MP3. ID3 tags and cover art
will be written.

  If the RSS feed doesn't exist yet, a new one will be generated, otherwise
the episode will be appended to the existing file and a backup of the feed will be generated.

1. Upload the newly encoded audio file and newly generated RSS xml file to
your hosting.


# Requirements
- LAME MP3 encoder
    - Debian: `sudo apt-get install lame`
    - OS X: `brew install lame`
- Mutagen Metadata handler
    - All: `pip install mutagen`


# Additional Resources
- [RSS 2.0 Specification](https://cyber.law.harvard.edu/rss/rss.html)
- [RSS Languages](https://cyber.law.harvard.edu/rss/languages.html)
- [iTunes Podcast Best Practices](https://help.apple.com/itc/podcasts_connect/#/itc2b3780e76)
- [iTunes Podcast Requirements](https://help.apple.com/itc/podcasts_connect/#/itc1723472cb)
- [Podcast Categories](https://www.podcastmotor.com/itunes-podcast-category-list/)


# TODO
- Configuration file parser needs to handle multi-line strings.
- Support links in tag values.
- Enforce subtitle 255 character limit.
- Support episode subtitles.
- Allow for up to 3 categories.
- Allow episode images to be added at runtime.
- Support Python 3.
- Add parameter for LAME encoding options.
- Check on installation into virtual environments.
