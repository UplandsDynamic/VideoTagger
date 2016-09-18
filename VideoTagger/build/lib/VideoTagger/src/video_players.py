import random
import python_mpv_zws as mpv
from . import engine_room
import _thread
import time


class VideoPlayers:
    def __init__(self, treestore=None, slider=None):
        self.video_players = {}
        # reference to treestore - model containing display text for the states treeview
        self.treestore = treestore
        self.player_seek_back_time = -5
        self.player_seek_forward_time = 5

    ''' GETTERS '''

    def get_player(self, player_id):
        try:
            return self.video_players[player_id]
        except KeyError:
            return None

    ''' SETTERS'''

    def set_player_seek_back_time(self, seconds=1):
        self.player_seek_back_time = seconds

    def set_player_seek_forward_time(self, seconds=1):
        self.player_seek_forward_time = seconds

    ''' DO-ERS '''

    def register_player(self, video_player):
        self.video_players[video_player.get_player_id()] = video_player

    def remove_player(self, player_id):
        if player_id:
            try:
                del self.video_players[player_id]
            except KeyError:
                print('That player ID does not exist!')

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
        # load lua for the OSD for those who are starting via libmpv
        mpv.load_lua()
        # create the player instance
        self.mpv_player = mpv.MPV('input-vo-keyboard',
                                  log_handler=self.logger,
                                  ytdl=True,
                                  input_default_bindings=True,
                                  input_vo_keyboard=True,
                                  cache=100000,
                                  osc='yes'
                                  )
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
        # timing
        self.video_length = None
        self.length_lock = False  # only allow length to be set once per video!
        self.time_remaining = 0
        self.pos = 0

    ''' OBSERVERS '''

    # self.mpv observe_property watches the ongoing property value for changes & feeds to the lambda
    # callback. Useful for times, watching for realtime changes, etc. Use get_property for static gets.

    # def remaining_time_observer(self):  # UNNECESSARY TO OBSERVE AT PRESENT
    #     self.mpv_player.observe_property('time-remaining',
    #                                      lambda observed_value: self.set_time_remaining(
    #                                   observed_value=observed_value))

    # def video_position_observer(self):  # UNNECESSARY TO OBSERVE AT PRESENT
    #     self.mpv_player.observe_property('time-pos', lambda pos: self.set_current_video_position(pos))

    ''' SETTERS '''

    def set_player_state(self, state):
        self.state = state
        self.state = state

    def set_time_remaining(self, observed_value):  # NOT USED AT PRESENT
        self.time_remaining = observed_value

    def set_video_length(self):
        if not self.length_lock:  # only allow to be set ONCE for each video!
            _thread.start_new_thread(self.video_length_setter, ())

    def video_length_setter(self):
        self.length_lock = True
        # run in own thread so doesn't block whilst looping until mpv returns value
        for attempt in range(61):
            if self.get_time_remaining():
                self.video_length = self.get_time_remaining()
                # log it
                self.logger('info', 'cplayer', 'Video length set as: {}'.format(
                    str(self.get_time_remaining())))
                return True  # ends the thread by returning True when value set
            elif not self.get_time_remaining():
                try:
                    player = self.mpv_player  # check player still exists
                    self.logger('info', 'cplayer', 'No video length retrieved yet ...')
                    time.sleep(1)
                except AttributeError:
                    break
        self.logger('error', 'cplayer', 'MVP did not return a valid video length')

    def set_current_video_position(self, pos):  # NOT USED AT PRESENT
        # sets pos param from observer method
        self.pos = pos

    def set_new_video_position(self, new_pos_secs):  # USED FOR USER "SEEK TO" OPTION
        self.mpv_player._set_property('time-pos', new_pos_secs)

    def set_notes_dir_callback(self, notes_directory):
        # set the directory attribute
        self.notes_dir = engine_room.sanitize_filter(notes_directory)
        # update the treestore
        self.video_players_group.treestore.set_value(
            self.treestore_note_location_field, 1, self.notes_dir)
        return True


    ''' GETTERS '''

    def get_player_state(self):
        try:
            # check and set ACTUAL mpv instance state for paused
            self.set_player_state(self.PAUSED) if self.mpv_player._get_property(name='pause', proptype=bool) \
                                                  is True else self.set_player_state(self.PLAYING)
        except AttributeError:
            pass  # player probably stopped, hence mpv object no longer exists
        return self.state

    def get_player_id(self):
        return self.player_id

    def get_time_remaining(self):
        return self.time_remaining

    def get_video_length(self):
        return self.video_length

    def get_video_position(self):
        return self.pos

    def get_notes_dir(self):
        return self.notes_dir

    ''' DO-ERS '''

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

    def gen_note(self):
        return {'Note': '',
                'Timestamp': self.mpv_player._get_property('time-pos'),
                'Video Source': self.source,
                'Video Title': engine_room.title_formatter(self.video_players_group.treestore.get_value(
                    self.treestore_title_field, 1))} or self.logger(
            'error', 'note', 'There was an error opening the note file!')

    def play(self):
        # define fullscreen
        self.mpv_player.fullscreen = False
        # define whether loops
        self.mpv_player.loop = 'no'
        # Option access, in general these require the core to reinitialize
        self.mpv_player['vo'] = 'opengl'
        # set seek hr-seek
        self.mpv_player._set_property(name='hr-seek', value='no', proptype=str)
        # start with osd on, at level 3
        self.mpv_player._set_property(name='osd-level', value=3, proptype=int)
        # mute
        self.mpv_player._set_property(name='mute', value=False, proptype=bool)

        # custom key bindings
        def my_q_binding(state, key):
            if state[0] == 'd':
                print('The d key was pressed!')  # debug

        def my_close_binding(state, key):
            self.stop()

        self.mpv_player.register_key_binding('d', my_q_binding)
        self.mpv_player.register_key_binding('CLOSE_WIN', my_close_binding)

        if self.source:
            # start video
            self.mpv_player.loadfile(filename=self.source, mode='replace')
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
            self.mpv_player.observe_property('media-title',
                                             lambda text: self.video_players_group.treestore.set_value(
                                          self.treestore_title_field, 1, '{}'.format(text)) if text
                                      else None)
            print('Starting player with ID: {}'.format(self.get_player_id()))
        else:
            self.logger('error', 'cplayer', 'No source, there is no source, where is my source?!')
            self.stop()

    def stop(self):
        try:
            # remove from the treestore
            self.video_players_group.treestore.remove(self.treestore_id_field)
            self.mpv_player.quit()
            self.mpv_player.terminate()
            del self.mpv_player
        except AttributeError:
            print('No player to stop with ID: {}'.format(self.get_player_id()))

    def pause(self, paused=False):
        # pause or resume (according to paused value)
        self.mpv_player._set_property(name='pause', value=paused)
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
            self.mpv_player.seek(amount=secs)
            # set the player state to paused (as stepping back pauses the stream by default)
            self.set_player_state(self.PAUSED)
        except AttributeError:
            print('No player to control with that ID')

    def toggle_osd(self):
        current_level = self.mpv_player._get_property('osd-level')
        if current_level == '0':
            self.mpv_player._set_property(name='osd-level', value=3, proptype=int)
        else:
            self.mpv_player._set_property(name='osd-level', value=0, proptype=int)

    @staticmethod
    def generate_new_id():
        ran = random.randrange(10 ** 80)
        hex = "%064x" % ran
        # limit string to 32 characters (default 64)
        hex = hex[:32]
        return hex
