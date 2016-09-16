#!/usr/bin/env python3
import os
import gi
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from .video_players import VideoPlayer, VideoPlayers
from . import engine_room


class Main:
    PROJECT_ROOT = engine_room.PROJECT_ROOT
    # control buttons
    PLAY = 'Play the video'
    STOP = 'Stop the video'
    PAUSE = 'Pause video'
    RESUME = 'Resume video'
    SEEK_BACK = 'Seek back'
    SEEK_FORWARD = 'Seek forward'
    TOGGLE_OSD = 'Toggles OSD on'
    TAKE_NOTE = 'Triggers note taking'
    GEN_NOTE = 'Generates note metadata'
    GET_PAUSE_BUTTON_STATE = 'Gets current pause state & sets button state'
    GET_NOTES_DIR = 'Gets the currently selected notes directory for the player'
    SET_NOTES_DIR = 'Callback to set the player notes directory'
    MAKE_CONFIG_DIR = False  # Unnecessary for now ...
    GET_PROGRESS_SLIDER_STATE = 'Gets progress slider for selected video'
    SEEK_TO = 'Seeks to position in video stream'
    GET_POSITION = 'Gets current video position in stream'

    def __init__(self):

        # if MAKE_CONFIG_DIR set, make the config directory if does not exist
        if self.MAKE_CONFIG_DIR:
            user_home = os.getenv('USERPROFILE') or os.getenv('HOME')
            engine_room.Engine.make_config_dir(path='{}/.config/video_tagger'.format(user_home))

        # set version number from file
        with open('{}/VERSION.rst'.format(self.PROJECT_ROOT)) as in_file:
            self.app_version = engine_room.sanitize_filter(in_file.read())[0:7]

        ''' GLADE '''
        # # # TOP LEVEL GLADE SETUP
        self.glade_file = '{}/resources/videotagger.glade'.format(self.PROJECT_ROOT)
        # create builder and add the glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_file)
        # connect the signals
        self.builder.connect_signals(self)
        # get the top level glade object
        self.window = self.builder.get_object('main_window')
        # # CREATE INSTANCE REFERENCES TO WIDGETS
        self.start_button = self.builder.get_object('start_button')
        self.stop_button = self.builder.get_object('stop_button')
        self.pause_button = self.builder.get_object('pause_button')
        self.seek_back_button = self.builder.get_object('seek_back_button')
        self.seek_forward_button = self.builder.get_object('seek_forward_button')
        self.osd_button = self.builder.get_object('toggle_osd')
        self.take_note_button = self.builder.get_object('take_note_button')
        self.select_dir_button = self.builder.get_object('notes_dir_button')
        self.video_source = self.builder.get_object('video_source')
        self.note_dialog_grid = self.builder.get_object('note_dialog_grid')
        self.mpv_seek_adjustment = self.builder.get_object('mpv_seek_adjustment')
        self.about_dialog = self.builder.get_object('aboutdialog')

        # video player
        self.video_player_list_container = self.builder.get_object('video_player_list_container')
        # # CREATE TREEVIEW / TREESTORE
        # create treestore
        self.treestore = Gtk.TreeStore(str, str)
        # create treeview
        self.treeview = Gtk.TreeView(self.treestore)
        # define treeview properties
        self.treeview.set_reorderable(False)
        self.treeview.set_activate_on_single_click(True)
        # connect action, when treeview row selected
        self.treeview_selected = self.treeview.connect('row-activated', self.on_treeview_row_activated)
        # define main column
        self.tvcol = Gtk.TreeViewColumn('PROPERTY')
        self.tvcol_cell = Gtk.CellRendererText()
        self.tvcol_cell.set_fixed_size(250, -1)
        self.tvcol.pack_start(self.tvcol_cell, expand=False)
        self.tvcol.add_attribute(self.tvcol_cell, 'text', 0)
        # self.tvcol.set_sort_column_id(0)  # uncomment to make sortable (but then references to rows will break)
        # define action column
        self.tv_action_col = Gtk.TreeViewColumn('VALUE')
        self.tv_action_cell = Gtk.CellRendererText()
        self.tv_action_cell.set_fixed_size(-1, -1)
        self.tv_action_col.pack_start(self.tv_action_cell, expand=True)
        self.tv_action_col.add_attribute(self.tv_action_cell, 'text', 1)
        # self.tv_action_col.set_sort_column_id(1)
        # add the columns to the treeview
        self.treeview.append_column(self.tvcol)
        self.treeview.append_column(self.tv_action_col)
        # add the treeview to the container
        self.video_player_list_container.pack_start(self.treeview, True, True, 0)
        # get reference to video players group
        self.video_players = VideoPlayers(treestore=self.treestore, slider=self.mpv_seek_adjustment)
        # define references to selections
        self.selected_video_player_id = None
        self.selected_video_player_notes = None

        # SHOW THE MAIN WINDOW
        print('Showing window ...')
        self.window.show_all()

        # RUN THE GTK
        Gtk.main()

    def __str__(self):
        return 'VideoTagger'

    # # # # GTK EVENT HANDLERS

    # # # MAIN WINDOW

    def on_main_window_destroy(self, object, data=None):
        print('Quit with Cancel ...')
        self.window.destroy()
        Gtk.main_quit()

    # # # MENU

    def on_help_activate(self, menuitem, data=None):
        # get the object and assign to the attribute
        self.about_dialog = self.builder.get_object('aboutdialog')
        # update version number in about info
        self.about_dialog.set_version(self.app_version)
        response = self.about_dialog.run()
        self.about_dialog.hide()

    # # # BUTTONS

    def on_button_clicked(self, button):
        if button == self.start_button:
            self.player_interface(action=self.PLAY)
        if button == self.stop_button:
            self.player_interface(action=self.STOP)
        if button == self.seek_back_button:
            self.player_interface(action=self.SEEK_BACK)
        if button == self.seek_forward_button:
            self.player_interface(action=self.SEEK_FORWARD)
        if button == self.osd_button:
            self.player_interface(action=self.TOGGLE_OSD)
        if button == self.take_note_button:
            self.on_take_note_clicked()
        if button == self.select_dir_button:
            self.filechooser_dialog()

    def on_button_toggled(self, button):
        if button == self.pause_button:
            if button.get_active():
                self.player_interface(action=self.PAUSE)
            else:
                self.player_interface(action=self.RESUME)

    def on_adjustment_changed(self, widget):
        if widget == self.mpv_seek_adjustment:
            # seek to slider position if slider moved more than 5 seconds from current
            current_pos = self.player_interface(action=self.GET_POSITION)
            moved_pos = self.mpv_seek_adjustment.get_value()
            if current_pos and (moved_pos < current_pos - 5 or moved_pos > current_pos + 5):
                self.player_interface(action=self.SEEK_TO)

    # # # FILE CHOOSER WIDGET

    def filechooser_dialog(self):
        dialog = Gtk.FileChooserDialog('Select or Create Notes Directory', self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        'Select', Gtk.ResponseType.OK))
        # self.add_filters(dialog)  # just for files, not directory
        dialog.set_default_size(800, 400)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # send to the callback
            self.player_interface(action=self.SET_NOTES_DIR, notes_directory=dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print('CANCEL CLICKED!')
        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("YAML Files")
        filter_text.add_pattern('*.yaml')
        dialog.add_filter(filter_text)

    # # # NOTE TAKER DIALOG

    def on_take_note_clicked(self):
        if self.selected_video_player_id:
            # pause the vid
            self.player_interface(action=self.PAUSE)
            # raise dialog
            dialog = Gtk.Dialog("Note Taker", self.window, 0,
                                (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                 'Save Note', Gtk.ResponseType.OK))
            dialog.set_default_size(800, 600)
            dialog.set_modal(True)
            # get widget references
            notes_dir_field = self.builder.get_object('notes_dir_field')
            notes_video_source_field = self.builder.get_object('video_source_field')
            notes_video_title_field = self.builder.get_object('video_title_field')
            timestamp_field = self.builder.get_object('timestamp_field')
            note_data_box = self.builder.get_object('note_data_box')
            # set the notes dir
            if not self.player_interface(action=self.GET_NOTES_DIR):
                self.filechooser_dialog()
            notes_dir = self.player_interface(action=self.GET_NOTES_DIR)
            if notes_dir:
                # get the existing note data
                note_data = self.player_interface(action=self.GEN_NOTE)  # dict returned
                # set fields
                notes_dir_field.set_text(notes_dir)
                notes_video_title_field.set_text(note_data.get('Video Title') or '')
                # note: below creates a new list to pop, therefore leaving original intact for later
                notes_video_source_field.set_text(note_data.get('Video Source') or '')
                timestamp_field.set_text(note_data.get('Timestamp') or '')
                note_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
                note_tv = Gtk.TextView()
                note_tv.set_right_margin(11)
                note_tv.set_left_margin(11)
                note_tv.set_top_margin(11)
                note_tv.set_bottom_margin(11)
                note_tv.set_pixels_above_lines(3)
                note_tv.set_pixels_below_lines(3)
                note_tv.set_pixels_inside_wrap(3)
                note_tv.set_wrap_mode(Gtk.WrapMode.WORD)
                note_tv.set_editable(True)
                note_tv.set_halign(Gtk.Align.START)
                note_tv_buff = note_tv.get_buffer()
                note_tv_buff.set_text(note_data.get('Note') or '')
                note_box.pack_start(note_tv, True, True, 0)
                note_data_box.pack_start(note_box, True, True, 0)
                # get ref to dialog's content area
                content_area_box = dialog.get_content_area()
                # add content grid to content area
                content_area_box.pack_start(self.note_dialog_grid, True, True, 0)
                # show content
                dialog.show_all()
                # run dialog
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    # save the note
                    start, end = note_tv_buff.get_bounds()
                    note = {'timestamp': note_data.get('Timestamp'),
                            'video_title': note_data.get('Video Title'),
                            'video_source': note_data.get('Video Source'),
                            'note_data': note_tv_buff.get_text(start, end, False)}
                    self.player_interface(action=self.TAKE_NOTE, note=note)
                elif response == Gtk.ResponseType.CANCEL:
                    pass
                # cleanup
                notes_dir_field.set_text('')
                notes_video_source_field.set_text('')
                notes_video_title_field.set_text('')
                note_data_box.remove(note_box)
                # remove the grid so not destroyed (can be referenced again in new dialog)
                content_area_box.remove(self.note_dialog_grid)
            dialog.destroy()
            self.player_interface(action=self.RESUME)
            # gets / sets pause state
            self.player_interface(self.GET_PAUSE_BUTTON_STATE)
        else:
            print("No, it ain't a player!")

    # # # SET SELECTED VIDEO PLAYER ID (& PAUSE BUTTON STATE)

    def on_treeview_row_activated(self, widget, row, col):
        # sets the player ID when a treerow is clicked on
        model = widget.get_model()  # model is the treestore
        # print(model.get_value(model.get_iter(row), 0))  # prints all the rows when clicked
        # get value for player id
        player_id_treepath = Gtk.TreePath(row[0])  # Gtk.TreePath([row[0], 3])  # row, child
        self.selected_video_player_id = model.get_value(model.get_iter(player_id_treepath), 1)
        # get pause button state
        self.player_interface(action=self.GET_PAUSE_BUTTON_STATE)
        # set progress slider state to the selected video
        self.player_interface(action=self.GET_PROGRESS_SLIDER_STATE)

    # # # PLAYER INTERFACE

    '''
    This interfaces with a VideoPlayer instance, instigates actions & exchanges
    data with the player
    '''

    def player_interface(self, action=None, **kwargs):
        # set existing player instance (if any)
        player_instance = self.video_players.get_player(self.selected_video_player_id)
        if action is self.PLAY:
            # restrict to one video at a time until refactor for better multi solution
            if player_instance:
                player_instance.stop()
            if self.video_source.get_text():
                # create a new player
                new_player_instance = VideoPlayer(source=engine_room.source_filter(
                    self.video_source.get_text()),
                    video_players_group=self.video_players)
                # register the player
                self.video_players.register_player(video_player=new_player_instance)
                # play
                new_player_instance.play()
                # clear the url field for next one ..
                self.video_source.set_text('')
                # set current active player id to the newly created
                self.selected_video_player_id = new_player_instance.get_player_id()
        else:
            if player_instance:
                if action is self.STOP:
                    player_instance.stop()
                    self.selected_video_player_id = None
                elif action is self.PAUSE:
                    player_instance.pause(paused=True)
                elif action is self.RESUME:
                    player_instance.pause(paused=False)
                elif action is self.SEEK_BACK:
                    # seek back
                    player_instance.seek(dir=player_instance.REWIND)
                    # set pause button active (video paused by default when stepped back)
                    self.pause_button.set_active(True)
                elif action is self.SEEK_FORWARD:
                    # seek forward
                    player_instance.seek(dir=player_instance.FORWARD)
                    # set pause button active (video paused by default when stepped back)
                    self.pause_button.set_active(True)
                elif action is self.TOGGLE_OSD:
                    player_instance.toggle_osd()
                elif action is self.TAKE_NOTE:
                    player_instance.save_note(note=kwargs.get('note', None))
                elif action is self.GET_PAUSE_BUTTON_STATE:
                    # set the current pause button toggle status for selected id
                    if player_instance.get_player_state() is player_instance.PAUSED:
                        self.pause_button.set_active(True)
                    else:
                        self.pause_button.set_active(False)
                elif action is self.GET_NOTES_DIR:
                    return player_instance.get_notes_dir()
                elif action is self.SET_NOTES_DIR:
                    player_instance.set_notes_dir_callback(notes_directory=kwargs.get('notes_directory'))
                elif action is self.GEN_NOTE:
                    return player_instance.gen_note()
                elif action is self.GET_PROGRESS_SLIDER_STATE:
                    player_instance.get_progress_slider_state()
                elif action is self.SEEK_TO:
                    player_instance.change_video_position(self.mpv_seek_adjustment.get_value())
                elif action is self.GET_POSITION:
                    return player_instance.get_video_position()
            else:
                print("It ain't a player!")


if __name__ == '__main__':
    Main()
