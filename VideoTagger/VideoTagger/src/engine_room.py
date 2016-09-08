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
                with open('{}/{}_ts_{}.yaml'.format(notes_dir,
                                                    title_formatter(video_title),
                                                    video_timestamp), 'w+') as f:
                    # write the file
                    dump({'VideoTagger Data':
                              [{'Timestamp': video_timestamp},
                               {'Video Source': video_source},
                               {'Video Title': title_formatter(video_title)},
                               {'Note': '\n{}'.format(note)}, ]}, f,
                         Dumper=Dumper, default_flow_style=False, explicit_start=True)
                return True
            except Exception as e:
                print('There was an error saving the note: {}'.format(e))
        else:
            print('This save type is not currently supported.')
        return False

    @staticmethod
    def get_note(notes_dir, video_title, video_source, video_timestamp, save_type=SAVE_TYPE_YAML):
        if save_type is SAVE_TYPE_YAML:
            try:
                # if note exists for exact dir/title/timestamp, simply return the data
                with open('{}/{}_ts_{}.yaml'.format(notes_dir,
                                                    title_formatter(video_title),
                                                    video_timestamp), 'r') as f:
                    # return ''.join(f.readline())
                    return load(f, Loader=Loader)
            except FileNotFoundError:
                pass  # pass to return video values for new note creation
        return {'Note': '[NOTE START] ',
                'Timestamp': video_timestamp,
                'Video Source': video_source,
                'Video Title': title_formatter(video_title)}


''' HELPERS '''


def title_formatter(video_title):
    space_replace = '_'.join(video_title.split())
    return sanitize_filter(space_replace)


def sanitize_filter(incoming=None):
    if not incoming: return None
    # sanitize the strings
    allowed_characters = [':', '.', ' ', '|', '-', '~', '*', '/', '\[', '\]', '!', '_']
    return ''.join([c if c.isalnum() or c in allowed_characters else '' for c in incoming])
