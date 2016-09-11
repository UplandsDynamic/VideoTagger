===============
**VideoTagger**
===============

---------------
**Description**
---------------

Please note, this is a very early beta prototype.

This is a GTK 3.x application that allows easy timestamped note taking for video clips.

Clips may be played from local files, or streamed from remote sources such as YouTube.

It acts as an interface to control the excellent Open Source MPV player, at: https://mpv.io/.

The application builds on an Open Source project that provides Python bindings to the MPV
player, at: https://github.com/jaseg/python-mpv

Notes are saved in a user nominated directory as YAML files. These are easily human
readable and editable.

------------
**Features**
------------

- Take timestamped notes at any point in a video at the tap of a button.
- Run, control and note-take on multiple video streams.

---------
**Usage**
---------

- Type or paste a video file URL (either a local file, or remote) into the "Video Source" field.
  Video files can also be dragged into this field - the source should automatically populate.

- Wait for the video to begin playing. The video should open in MPV player.

- A video session ID will appear in the main application window. The needs to be selected by
  a single click/tap. Once selected, it will be highlighted. It is important to ensure that
  the session you wish to control is selected. Multiple streams may be controlled by
  selecting the appropriate ID before using the control bar to control the selected session.

- The video may be controlled via the application's control bar:

  - Play button: Plays the video.
  - Back button: Seeks back by 5 seconds (unit of time should be user definable in future versions).
  - Stop button: Stops the video and destroys the instance. Only click this if you're done.
  - Pause button: Pauses or resumes from a paused state.
  - Forward button: Seeks forward by 5 seconds (unit of time should be user definable in future).
  - "OSD" button: Toggles MPV's 'On Screen Display'.
  - "Take Note" button: Tap this to take a note. This will pause the player and open up a timestamped
    note. The user will also be prompted to select a directory in which to store the note if that has
    note already been selected earlier in video play session. Users should be aware that clicking
    the Stop button will destroy the video session for that stream, and so subsequent opening of the
    same video will require reselection of the storage directory. Once the note has been taken
    (or cancelled), the player should automatically resume playing.

-----------
**Version**
-----------

For the current version number, see VideoTagger/VERSION.rst

---------------
**Availabilty**
---------------

This application is available for Arch Linux, from the Arch User Repository (AUR). Installing from the AUR
pulls the latest stable version from github/master. The AUR page is here:

https://aur.archlinux.org/packages/videotagger

"Snap" packages for other Linux distributions, and a FreeBSD port, may be available in due course.

The source code is published on GitHub, here:

https://github.com/ZWS2014/VideoTagger

The application is also available as a Python package, which may be installed on many platforms, from PyPi.

However, only major version changes are published to PyPi. The PyPi repository is here:

https://pypi.python.org/pypi/VideoTagger

-----------
**License**
-----------

Code author: Dan Bright

Code author email: productions@zaziork.com

Code author website: https://www.zaziork.com

This application is made available under the GNU General Public License, Version 3.

For further license details, please refer to the LICENSE.txt file which should be
bundled with this software.