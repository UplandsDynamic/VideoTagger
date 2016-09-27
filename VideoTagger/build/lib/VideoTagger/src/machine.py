#!/usr/bin/env python3
import os
import sys
from yaml import load, dump
import random

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

CONFIG_DIR = '{}/.config/video_tagger'.format(os.getenv('USERPROFILE') or os.getenv('HOME'))
CONFIG_FILENAME = 'video_tagger.conf'
FULL_CONFIG_FILE_PATH = '{}/{}'.format(CONFIG_DIR, CONFIG_FILENAME)
SAVE_TYPE_YAML = 'Save as YAML file'


class Setup:
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
                # ensure permission to open file if already exists
                try:
                    os.chmod('{}/{}.yaml'.format(notes_dir, title_to_filename(video_title)), 0o644)
                except FileNotFoundError:
                    pass
                with open('{}/{}.yaml'.format(notes_dir, title_to_filename(video_title)), 'a') as f:
                    # write the file
                    dump([{'Note':
                               [{'Timestamp': video_timestamp},
                                {'Video Source': video_source},
                                {'Video Title': video_title},
                                {'Note': '\n{}\n'.format(note)}, ]}], f,
                         Dumper=Dumper, default_flow_style=False, explicit_start=False)
                # change permissions on the file to r/o
                os.chmod('{}/{}.yaml'.format(notes_dir, title_to_filename(video_title)), 0o444)
                return True
            except Exception as e:
                print('There was an error saving the note: {}'.format(e))
        else:
            print('This save type is not currently supported.')
        return False

    @staticmethod
    def get_note(notes_file, save_type=SAVE_TYPE_YAML):
        if save_type is SAVE_TYPE_YAML:
            try:
                with open(notes_file, 'r') as f:
                    return load(f, Loader=Loader, )
            except FileNotFoundError:
                pass
        return None

    @staticmethod
    def edit_notes(notes_file):
        if notes_file:
            return sort_by_timestamp(NoteMachine.get_note(notes_file=notes_file))
        return None

    @staticmethod
    def save_edit(notes_filename, notes_dir, note_data, save_type=SAVE_TYPE_YAML):
        if save_type is SAVE_TYPE_YAML:
            try:
                os.chmod('{}/{}'.format(notes_dir, notes_filename), 0o644)
                with open('{}/{}'.format(notes_dir, notes_filename), 'w') as f:
                    # write the file
                    dump(note_data, f,
                         Dumper=Dumper, default_flow_style=False, explicit_start=False)
                os.chmod('{}/{}'.format(notes_dir, notes_filename), 0o444)
                return True
            except Exception as e:
                print('There was an error saving the note: {}'.format(e))
        else:
            print('This save type is not currently supported.')
        return False


''' HELPERS '''


def sort_by_timestamp(note_data):
    timestamps = []
    sorted_data = []
    for i, d in enumerate(note_data):
        timestamps.append((d['Note'][0]['Timestamp'], i))
    timestamps.sort()
    for i, d in enumerate(timestamps):
        sorted_data.append(note_data[d[1]])
    return sorted_data


def title_to_filename(video_title):
    # applies suitable filename formatting to title
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
    allowed_characters = [':', '.', ' ', '|', '-', '~', '*', '/', '\[', '\]', '!', '_', '#']
    return ''.join([c if c.isalnum() or c in allowed_characters else '' for c in incoming])


def secs_to_minsec(secs):
    try:
        secs = float(secs)
        # takes seconds, returns minutes, seconds (to tenths)
        minutes = int(secs // 60)
        seconds = round(secs % 60, 1)
    except (ValueError, TypeError):
        minutes = seconds = 0
    return {'min': minutes, 'sec': seconds}


def generate_new_id():
    ran = random.randrange(10 ** 80)
    hex = "%064x" % ran
    # limit string to 32 characters (default 64)
    hex = hex[:32]
    return hex
