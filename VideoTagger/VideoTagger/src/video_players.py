import random
import mpv
from . import engine_room

class VideoPlayers:
    def __init__(self, treestore=None):
        self.video_players = {}
        # reference to treestore - model containing display text for the states treeview
        self.treestore = treestore
        self.player_seek_back_time = -5
        self.player_seek_forward_time = 5

    def register_player(self, video_player):
        self.video_players[video_player.get_player_id()] = video_player

    def get_player(self, player_id):
        try:
            return self.video_players[player_id]
        except KeyError:
            return None

    def remove_player(self, player_id):
        if player_id:
            try:
                del self.video_players[player_id]
            except KeyError:
                print('That player ID does not exist!')

    def set_player_seek_back_time(self, seconds=1):
        self.player_seek_back_time = seconds

    def set_player_seek_forward_time(self, seconds=1):
        self.player_seek_forward_time = seconds

    def __str__(self):
        return 'Object containing a group of VideoPlayer objects. Should be unique per gui instance.'


class VideoPlayer:
    PLAYING = 'Video is playing'
    PAUSED = 'Video is paused'
    STOPPED = 'Video stream destroyed!'
    REWIND = 'Video player rewind'
    FORWARD = 'Video player forward'

    def __str__(self):
        return 'An instance of an MPV video player'

    def __init__(self, source, video_players_group):
        self.video_players_group = video_players_group
        self.state = None
        self.source = source
        self.mpv = mpv.MPV(log_handler=self.logger,
                           ytdl=True,
                           input_default_bindings=True,
                           input_vo_keyboard=True)
        # generate a new ID when new player is initialised
        self.player_id = self.generate_new_id()
        # add the PRIMARY VIDEO PLAYER ROW to the treestore for display. See self.play() for child row defs.
        self.treestore_id_field = self.video_players_group.treestore.prepend(
            None, ['Video Player ID', self.player_id])
        self.treestore_state_field = None
        self.treestore_title_field = None
        self.treestore_note_location_field = None
        self.treestore_source_field = None
        self.notes_dir = None
        self.note = None

    def set_player_state(self, state):
        self.state = state
        self.state = state

    def get_player_state(self):
        try:
            # check and set ACTUAL mpv instance state for paused
            self.set_player_state(self.PAUSED) if self.mpv._get_property(name='pause', proptype=bool) \
                                                  is True else self.set_player_state(self.PLAYING)
        except AttributeError:
            pass  # player probably stopped, hence mpv object no longer exists
        return self.state

    def get_player_id(self):
        return self.player_id

    def logger(self, loglevel, component, message):
        # incoming log entries
        if 'error' in loglevel:
            self.log_error_handler(loglevel, component, message)
        elif 'info' in loglevel:
            self.log_info_handler(loglevel, component, message)
        else:
            self.log_catchall_handler(loglevel, component, message)

    def log_error_handler(self, loglevel, component, message):
        # do something with the error - action and/or write to a log file
        print('[{}] {}: {}'.format(loglevel, component, message))
        if component == 'file':
            self.stop()

    def log_info_handler(self, loglevel, component, message):
        # do something with the info - write to file, or print to console
        print('[{}] {}: {}'.format(loglevel, component, message))

    def log_catchall_handler(self, loglevel, component, message):
        # do something with the message - write to file, or print to console
        print('[{}] {}: {}'.format(loglevel, component, message))

    def set_notes_dir_callback(self, notes_directory):
        # set the directory attribute
        self.notes_dir = engine_room.sanitize_filter(notes_directory)
        # update the treestore
        self.video_players_group.treestore.set_value(
            self.treestore_note_location_field, 1, self.notes_dir)
        return True

    def save_note(self, note):
        if note:
            if engine_room.NoteMachine.save_note(notes_dir=self.notes_dir,
                                                 video_title=note.get('video_title'),
                                                 video_source=note.get('video_source'),
                                                 video_timestamp=note.get('timestamp'),
                                                 note=note.get('note_data')
                                                 ):
                self.logger('info', 'note', 'Note taken!')
                return True
        self.logger('error', 'note', 'Error: Note not taken!')

    def get_notes_dir(self):
        return self.notes_dir

    def get_note(self):
        note = engine_room.NoteMachine.get_note(
            notes_dir=self.notes_dir,
            video_title=self.video_players_group.treestore.get_value(
                self.treestore_title_field, 1),
            video_timestamp=self.mpv._get_property('time-pos'),
            video_source=self.source,
        )
        return note or self.logger('error', 'note', 'There was an error opening the note file!')

    def play(self):

        ''' NOTE on get/set/observer properties'''
        # self.mpv.get_property gets the current value of the property. Likewise for set_property.
        #
        # self.mpv observe_property watches the ongoing property value for changes and feeds it into the lambda
        # callback. Useful for times, watching for realtime changes, etc.

        # Property access, these can be changed at runtime
        # keep printing time to console
        self.mpv.observe_property('time-pos', lambda pos: print('Now playing at {:.2f}s'.format(pos)))
        # define fullscreen
        self.mpv.fullscreen = False
        # define whether loops
        self.mpv.loop = 'inf'
        # Option access, in general these require the core to reinitialize
        self.mpv['vo'] = 'opengl'
        # set seek hr-seek to yes, to be precise rather than nearest keyframe when possible
        self.mpv._set_property(name='hr-seek', value='yes', proptype=str)
        # start with osd on, at level 3
        self.mpv._set_property(name='osd-level', value=3, proptype=int)

        # mute
        self.mpv._set_property(name='mute', value=True, proptype=bool)

        # custom key bindings
        def my_q_binding(state, key):
            if state[0] == 'd':
                print('The d key was pressed @: '.
                      format(self.mpv.observe_property('time-pos',
                                                       lambda pos: print('{:.2f}s'.
                                                                         format(pos)))))

        self.mpv.register_key_binding('d', my_q_binding)

        if self.source:
            # start video
            self.mpv.loadfile(filename=self.source, mode='replace')
            self.set_player_state(self.PLAYING)

            # # # DEFINE TREESTORE CHILDREN
            # set the displayed state
            self.treestore_state_field = self.video_players_group.treestore.append(
                self.treestore_id_field, ['Player State', self.get_player_state()])
            # set the displayed title (to connect it as a child to the ID)
            self.treestore_title_field = self.video_players_group.treestore.prepend(
                self.treestore_id_field, ['Video Title', None]
            )
            # set the displayed source
            self.treestore_source_field = self.video_players_group.treestore.append(
                self.treestore_id_field, ['Video Source', self.source])
            # set the note location field
            self.treestore_note_location_field = self.video_players_group.treestore.append(
                self.treestore_id_field, ['Video Notes Location', None]
            )
            # observe title (set to change in realtime when updated)
            self.mpv.observe_property('media-title',
                                      lambda text: self.video_players_group.treestore.set_value(
                                          self.treestore_title_field, 1, '{}'.format(text)) if text
                                      else None)
            print('Starting player with ID: {}'.format(self.get_player_id()))
        else:
            print('No source, there is no source!')
            self.stop()

            # self.player.wait_for_playback()
            # del self.player

    def stop(self):
        try:
            # remove from the treestore
            self.video_players_group.treestore.remove(self.treestore_id_field)
            self.mpv.quit()
            self.mpv.terminate()
            del self.mpv
        except AttributeError:
            print('No player to stop with ID: {}'.format(self.get_player_id()))

    def pause(self, paused=False):
        # pause or resume (according to paused value)
        self.mpv._set_property(name='pause', value=paused)
        # set state
        if paused is True:
            self.set_player_state(self.PAUSED)
        else:
            self.set_player_state(self.PLAYING)
        # update the displayed state
        self.video_players_group.treestore.set_value(
            self.treestore_state_field, 1, self.get_player_state())

    def seek(self, dir):
        try:
            secs = self.video_players_group.player_seek_back_time if dir is self.REWIND else \
                self.video_players_group.player_seek_forward_time
            # seek back
            self.mpv.seek(amount=secs)
            # set the player state to paused (as stepping back pauses the stream by default)
            self.set_player_state(self.PAUSED)
        except AttributeError:
            print('No player to control with that ID')

    def toggle_osd(self):
        current_level = self.mpv._get_property('osd-level')
        if current_level == '0':
            self.mpv._set_property(name='osd-level', value=3, proptype=int)
        else:
            self.mpv._set_property(name='osd-level', value=0, proptype=int)

    @staticmethod
    def generate_new_id():
        ran = random.randrange(10 ** 80)
        hex = "%064x" % ran
        # limit string to 32 characters (default 64)
        hex = hex[:32]
        return hex
