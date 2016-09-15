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
