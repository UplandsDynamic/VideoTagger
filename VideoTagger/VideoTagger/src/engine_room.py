#!/usr/bin/env python3
import os
import sys
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

CONFIG_DIR = '{}/.config/video_tagger'.format(os.getenv('USERPROFILE') or os.getenv('HOME'))
CONFIG_FILENAME = 'video_tagger.conf'
FULL_CONFIG_FILE_PATH = '{}/{}'.format(CONFIG_DIR, CONFIG_FILENAME)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SAVE_TYPE_YAML = 'Save as YAML file'


class Engine:
    @staticmethod
    def make_config_dir(path=None):
        if path:
            if not os.path.exists(path):
                os.mkdir(path)
                return True


class NoteMachine:
    @staticmethod
    def save_note(notes_dir, video_title, video_source, video_timestamp, note, save_type=SAVE_TYPE_YAML):
        if save_type is SAVE_TYPE_YAML:
            try:
                with open('{}/{}.yaml'.format(notes_dir, title_formatter(video_title)), 'a') as f:
                    # write the file
                    dump([{'Data':
                               [{'Timestamp': video_timestamp},
                                {'Video Source': video_source},
                                {'Video Title': title_formatter(video_title)},
                                {'Note': '\n{}\n'.format(note)}, ]}], f,
                         Dumper=Dumper, default_flow_style=False, explicit_start=False)
                return True
            except Exception as e:
                print('There was an error saving the note: {}'.format(e))
        else:
            print('This save type is not currently supported.')
        return False

    @staticmethod
    def get_note():
        # ToDo ... retrieve notes for reader functionality ...
        ''' EXAMPLE:
        if save_type is SAVE_TYPE_YAML:
            try:
                with open('{}/{}.yaml'.format(notes_dir, title_formatter(video_title)), 'r') as f:
                    data = load(f, Loader=Loader)
            except FileNotFoundError:
                pass  # do something if file not found
        '''
        pass


''' Blurbs '''


class Blurb:
    USAGE_BLURB = '''
    * Type or paste a video file URL (either a local file, or remote) into the "Video Source" field.
      Video files can also be dragged into this field - the source should automatically populate.

    * Wait for the video to begin playing. The video should open in MPV player.

    * A video session ID will appear in the main application window, which may be selected by a click.

    * The video may be controlled via the application's control bar:

      - Play button: Plays the video.

      - Back button: Seeks back by 5 seconds (unit of time should be user definable in future versions).

      - Stop button: Stops the video and destroys the instance. Only click this if you're done.

      - Pause button: Pauses or resumes from a paused state.

      - Forward button: Seeks forward by 5 seconds (unit of time should be user definable in future).

      - "OSD" button: Toggles MPV's 'On Screen Display'.

      - "Take Note" button: Tap this to take a note. This will pause the player and open up a timestamped
        note. The user will also be prompted to select a directory in which to store the note if no
        directory has already been defined.

      - Users should be aware that clicking the Stop button will destroy the video session for that stream,
        and so subsequent opening of the same video will require reselection of the storage directory.
        Once the note has been taken (or cancelled), the player should automatically resume playing.
'''
    ABOUT_BLURB = '''
    This is an application that creates timestamped notes for video clips.

    Clips may be played from local files, or streamed from remote sources such as YouTube.

    It acts as an interface to control the excellent Open Source MPV player.



















    '''

    def __init__(self):
        pass

    def __str__(self):
        return 'Class containing strings used in the application'


''' HELPERS '''


def title_formatter(video_title):
    space_replace = '_'.join(video_title.split())
    return sanitize_filter(space_replace)


def source_filter(source):
    # return, optimised to cope with local paths if a local file
    if 'file://' in source:
        return "{}".format(source.replace('file://', '')
                           .replace('%20', ' ').strip())
    else:
        return source


def sanitize_filter(incoming=None):
    if not incoming: return None
    # sanitize the strings
    allowed_characters = [':', '.', ' ', '|', '-', '~', '*', '/', '\[', '\]', '!', '_']
    return ''.join([c if c.isalnum() or c in allowed_characters else '' for c in incoming])
