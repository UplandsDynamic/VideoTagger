#!/usr/bin/env python3
import os
import gi
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Pango
from .video_players import VideoPlayer, VideoPlayers
from . import machine
from VideoTagger.__init__ import PROJECT_ROOT


class VideoTagger:
    PROJECT_ROOT = PROJECT_ROOT
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
    SEEK_TO = 'Seeks to position in video stream'
    GET_POSITION = 'Gets current video position in stream'
    READ_EDIT_NOTE = 'Opens note editor'

    def __init__(self):

        # if MAKE_CONFIG_DIR set, make the config directory if does not exist
        if self.MAKE_CONFIG_DIR:
            user_home = os.getenv('USERPROFILE') or os.getenv('HOME')
            machine.Setup.make_config_dir(path='{}/.config/video_tagger'.format(user_home))

        # set version number from file
        with open('{}VideoTagger/VERSION.rst'.format(self.PROJECT_ROOT)) as in_file:
            self.app_version = machine.sanitize_filter(in_file.read())[0:7]

        # set license from file
        with open('{}VideoTagger/LICENSE.txt'.format(self.PROJECT_ROOT)) as in_file:
            self.license_text = in_file.read()

        # set short description from file
        with open('{}VideoTagger/SHORT_DESCRIPTION.txt'.format(self.PROJECT_ROOT)) as in_file:
            self.short_desc = in_file.read()

        # set manual from file
        with open('{}VideoTagger/MANUAL.txt'.format(self.PROJECT_ROOT)) as in_file:
            self.manual = in_file.read()

        # set custom css styling
        self.style_provider = Gtk.CssProvider()
        self.style_provider.load_from_path('{}VideoTagger/resources/videotagger.css'.format(
            self.PROJECT_ROOT))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            self.style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        ''' GLADE '''
        # # # # # # # TOP LEVEL GLADE SETUP
        self.glade_file = '{}/VideoTagger/resources/videotagger.glade'.format(self.PROJECT_ROOT)
        # create builder and add the glade file
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.glade_file)
        # connect the signals
        self.builder.connect_signals(self)
        # get the top level glade object
        self.window = self.builder.get_object('main_window')
        self.window.set_wmclass("VideoTagger", "VideoTagger")
        self.window.set_title("VideoTagger")

        # # # CREATE INSTANCE REFERENCES TO WIDGETS
        # buttons
        self.start_button = self.builder.get_object('start_button')
        self.stop_button = self.builder.get_object('stop_button')
        self.pause_button = self.builder.get_object('pause_button')
        self.seek_back_button = self.builder.get_object('seek_back_button')
        self.seek_forward_button = self.builder.get_object('seek_forward_button')
        self.osd_button = self.builder.get_object('toggle_osd')
        self.take_note_button = self.builder.get_object('take_note_button')
        self.select_dir_button = self.builder.get_object('notes_dir_button')
        self.about_blurb_button = self.builder.get_object('about_blurb_button')
        self.usage_button = self.builder.get_object('usage_button')
        self.edit_notes_button = self.builder.get_object('edit_notes_button')
        # edit texts
        self.video_source = self.builder.get_object('video_source')
        # grids
        self.note_dialog_grid = self.builder.get_object('note_dialog_grid')
        self.mpv_seek_adjustment = self.builder.get_object('mpv_seek_adjustment')
        # menus
        self.about_menu_item = self.builder.get_object('menu_about')
        self.usage_menu_item = self.builder.get_object('menu_usage')
        # dialogs
        self.about_dialog = self.builder.get_object('aboutdialog')
        self.info_dialog = self.builder.get_object('info_dialog')
        # textviews
        self.info_textview = self.builder.get_object('info_textview')
        # textview buffers
        self.info_textview_buffer = self.builder.get_object('info_textview_buffer')
        # boxes
        self.video_player_list_container = self.builder.get_object('video_player_list_container')

        # # # CREATE TREEVIEW / TREESTORE
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
        self.tvcol = Gtk.TreeViewColumn()
        self.tvcol_cell = Gtk.CellRendererText()
        self.tvcol_cell.set_fixed_size(250, -1)
        self.tvcol.pack_start(self.tvcol_cell, expand=False)
        self.tvcol.add_attribute(self.tvcol_cell, 'text', 0)
        # self.tvcol.set_sort_column_id(0)  # uncomment to make sortable (but then references to rows will break)
        # define action column
        self.tv_action_col = Gtk.TreeViewColumn('Video Details')
        self.tv_action_cell = Gtk.CellRendererText()
        self.tv_action_cell.set_fixed_size(-1, -1)
        self.tv_action_col.pack_start(self.tv_action_cell, expand=True)
        self.tv_action_col.add_attribute(self.tv_action_cell, 'text', 1)
        # add the columns to the treeview
        self.treeview.append_column(self.tvcol)
        self.treeview.append_column(self.tv_action_col)
        # add the treeview to the container
        self.video_player_list_container.pack_start(self.treeview, True, True, 0)
        # get reference to video players group
        self.video_players = VideoPlayers(treestore=self.treestore, slider=self.mpv_seek_adjustment)

        # # # SELECTION REFERENCES
        self.selected_video_player_id = None
        self.selected_video_player_notes = None
        self.notes_file = None
        self.selected_note_row = None

        # # # NOTE EDIT DIALOG TEXTVIEW
        self.note_edit_panel = Gtk.TextView()
        self.note_edit_panel.set_left_margin(7)
        self.note_edit_panel.set_right_margin(7)
        self.note_edit_panel.set_top_margin(7)
        self.note_edit_panel.set_bottom_margin(7)

        # # # # # # # SHOW THE MAIN WINDOW
        print('Showing window ...')
        self.window.show_all()

        # RUN THE GTK
        # Gtk.main()

    def __str__(self):
        return 'VideoTagger'

    # # # # GTK EVENT HANDLERS

    # # # MAIN WINDOW

    def on_main_window_destroy(self, object, data=None):
        print('Quit with Cancel ...')
        self.window.destroy()
        Gtk.main_quit()

    # # # MENU

    def on_menu_activate(self, menuitem, data=None):
        if menuitem == self.about_menu_item:
            # get the object and assign to the attribute
            self.about_dialog = self.builder.get_object('aboutdialog')
            # update version number in about info
            self.about_dialog.set_version(self.app_version)
            self.about_dialog.set_license(self.license_text)
            response = self.about_dialog.run()
            self.about_dialog.hide()
        elif menuitem == self.usage_menu_item:
            self.info_textview.set_editable(False)
            self.info_textview.set_cursor_visible(False)
            self.info_textview_buffer.set_text(self.manual)
            response = self.info_dialog.run()
            self.info_dialog.hide()

    # # # BUTTONS

    def on_button_clicked(self, button, note_data=None):
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
        if button == self.about_blurb_button:
            self.info_dialog_show(self.short_desc)
        if button == self.usage_button:
            self.info_dialog_show(self.manual)
        if button == self.edit_notes_button:
            self.on_edit_notes_clicked()
        if button.get_name() == 'edit_play_button':
            self.on_edit_play(note_data=note_data)

    def on_button_toggled(self, button):
        if button == self.pause_button:
            if button.get_active():
                self.player_interface(action=self.PAUSE)
            else:
                self.player_interface(action=self.RESUME)

    def on_adjustment_changed(self, widget):
        if widget == self.mpv_seek_adjustment:
            # seek to slider position if slider moved more than n seconds from current
            current_pos = self.player_interface(action=self.GET_POSITION)
            moved_pos = self.mpv_seek_adjustment.get_value()
            if current_pos and (moved_pos < current_pos - 0.1 or moved_pos > current_pos + 0.1):
                self.player_interface(action=self.SEEK_TO)

    # # # FILE CHOOSER WIDGETS

    def filechooser_dialog(self, attach=None):
        attach = attach or self.window
        dialog = Gtk.FileChooserDialog('Select or Create Notes Directory', attach,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        'Select', Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # send to the callback
            self.player_interface(action=self.SET_NOTES_DIR, notes_directory=dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print('CANCEL CLICKED!')
        dialog.destroy()

    def notes_filechooser_dialog(self, attach=None):
        attach = attach or self.window
        dialog = Gtk.FileChooserDialog('Select a notes file to read or edit', attach,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        'Select', Gtk.ResponseType.OK))
        self.notes_filechooser_dialog_add_filters(dialog)  # just for files, not directory
        dialog.set_default_size(800, 400)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # send to the callback
            self.notes_file = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            print('CANCEL CLICKED!')
        dialog.destroy()

    def notes_filechooser_dialog_add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("YAML Files")
        filter_text.add_pattern('*.yaml')
        dialog.add_filter(filter_text)

    # # # INFO DIALOG

    def info_dialog_show(self, blurb):
        self.info_textview.set_cursor_visible(False)
        self.info_textview_buffer.set_text(blurb)
        response = self.info_dialog.run()
        self.info_dialog.hide()

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
                # get the pre-populated note data
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
                note_tv.set_hexpand(True)
                note_tv_buff = note_tv.get_buffer()
                note_tv_buff.set_text(note_data.get('Note') or '')
                start, end = note_tv_buff.get_bounds()
                note_tv_buff.place_cursor(end)
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

    # # # NOTE READER & EDITOR DIALOG

    def on_edit_notes_clicked(self):
        if self.selected_video_player_id:
            # pause the vid
            self.player_interface(action=self.PAUSE)
        # raise dialog
        dialog = Gtk.Dialog("Note Editor", self.window, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             'Save Note', Gtk.ResponseType.OK))
        dialog.set_default_size(800, 600)
        dialog.set_modal(False)
        # select the notes file
        self.notes_filechooser_dialog(attach=dialog)
        if self.notes_file:
            note_data = machine.NoteMachine.edit_notes(notes_file=self.notes_file)
            notes_dir = '/'.join(self.notes_file.split('/')[0:-1])  # gets path minus filename
            notes_filename = self.notes_file.split('/')[-1]
            main_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
            main_container.set_homogeneous(False)
            current_notes_container = Gtk.ScrolledWindow()
            current_notes_container.set_size_request(400, 0)
            # create treestore
            ts = Gtk.TreeStore(str)
            # define field column
            tv_value_col = Gtk.TreeViewColumn()
            # set tooltipped title
            tv_value_col_header = Gtk.Label()
            tv_value_col_header.show()
            tv_value_col.set_widget(tv_value_col_header)
            # tv_value_col_header.set_tooltip_text()
            # define cell renderer
            tv_value_cell = Gtk.CellRendererText()
            tv_value_cell.set_fixed_size(-1, -1)
            tv_value_col.pack_start(tv_value_cell, expand=True)
            tv_value_col.add_attribute(tv_value_cell, 'text', 0)
            # define holding variables
            timestamp_field = None
            note_position_marker = {}
            # iterate note_data & extract values
            for note_pos, n in enumerate(note_data):
                for item_pos, item in enumerate(n['Note']):
                    if 'Timestamp' in item:
                        timestamp_field = ts.append(None, ['Timestamp: {}'.format(item['Timestamp'])])
                    if 'Note' in item:
                        note_field = ts.append(timestamp_field, [item['Note']])
                        ''' create dict with note_pos as key & item_pos as value.
                        note_pos will be same as treestore row, retrieved when selected later.
                        This is used to reconile selected note with it's position in the
                        note_data dict, as is being iterated here, in order to overwrite
                        that note in note_data dict '''
                        note_position_marker[note_pos] = item_pos
                    if 'Video Title' in item:
                        tv_value_col_header.set_text('Notes For: {}'.format(item['Video Title']))
            # create treeview (adding the now-sorted treestore)
            tv = Gtk.TreeView(ts)
            # add the columns to the treeview
            tv.append_column(tv_value_col)
            # define treeview properties
            tv.set_reorderable(False)
            tv.set_activate_on_single_click(True)
            tv.set_grid_lines(True)
            # connect action, when treeview row selected
            tv.connect('row-activated', self.on_note_tv_activated)
            # expand all by default
            tv.expand_all()
            # add treeview to the container
            current_notes_container.add(tv)
            # add notes container to main container
            main_container.pack_start(current_notes_container, False, False, 3)
            # add note_textview to main container
            main_container.pack_start(self.note_edit_panel, True, True, 3)
            # get ref to dialog's content area
            content_area_box = dialog.get_content_area()
            # add content grid to content area
            content_area_box.pack_start(main_container, True, True, 3)
            # add view video button to panel
            video_button = Gtk.Button('Play Video')
            video_button.set_name('edit_play_button')
            action_area = dialog.get_action_area()
            action_area.pack_start(video_button, False, False, 3)
            action_area.reorder_child(video_button, 0)
            # add video view button action
            video_button.connect('clicked', self.on_button_clicked, note_data)
            # show content
            dialog.show_all()
            # run dialog
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                buffer = self.note_edit_panel.get_buffer()
                # save the note
                edited_text = buffer.get_text(*buffer.get_bounds(), False)
                note_pos = self.selected_note_row
                if note_pos:
                    item_pos = note_position_marker[note_pos]
                    note_data[note_pos]['Note'][item_pos]['Note'] = edited_text
                    machine.NoteMachine.save_edit(notes_dir=notes_dir,
                                                  notes_filename=notes_filename,
                                                  note_data=note_data)
            elif response == Gtk.ResponseType.CANCEL:
                pass
            # cleanup
            self.selected_note_row = None
            self.note_edit_panel.get_buffer().set_text('')
            self.notes_file = None
            # cleanup (remove inst var from box to stop it being destroyed with dialog (causing crash)
            main_container.remove(self.note_edit_panel)
            dialog.destroy()
        if self.selected_video_player_id:
            self.player_interface(action=self.RESUME)
            # gets / sets pause state
            self.player_interface(self.GET_PAUSE_BUTTON_STATE)

    def on_note_tv_activated(self, widget, row, col):
        # opens an edit dialog
        model = widget.get_model()
        # get value for note
        note_path = str(Gtk.TreePath(row))
        # if timestamp row clicked, display following note row in edit pane - not the timestamp
        if ':0' not in note_path:
            note_path += ':0'
        # get the data to display in the pane from the note_path
        display_data = model.get_value(model.get_iter(note_path), 0)
        # set the selected row param
        self.selected_note_row = int(str(row)[0])
        buffer = self.note_edit_panel.get_buffer()
        # set the note text in the edit panel buffer
        buffer.set_text(display_data.strip())

    def on_edit_play(self, note_data):
        timestamp = None
        # close existing player, if any
        if self.selected_video_player_id:
            self.player_interface(action=self.STOP)
        if note_data and self.selected_note_row is not None:
            for d in note_data[self.selected_note_row]['Note']:
                if 'Video Source' in d:
                    self.video_source.set_text(d['Video Source'])
                if 'Timestamp' in d:
                    timestamp = d['Timestamp']
            # start the player at the designated position
            self.player_interface(action=self.PLAY,
                                  start_position=machine.minsec_to_sec(timestamp))

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

    # # # PLAYER INTERFACE

    '''
    This interfaces with a VideoPlayer instance, instigates actions & exchanges
    data with the player
    '''

    def player_interface(self, action=None, **kwargs):
        # check for existing player instances (and close if close_existing kwarg passed)
        existing_player_ids = self.video_players.get_all_ids()
        if not existing_player_ids:  # restrict to one player at a time (for now ...)
            # set existing player instance (if any)
            if action is self.PLAY:
                if self.video_source.get_text():
                    # get/set start position
                    start_position = kwargs.get('start_position') or None
                    # create a new player
                    new_player_instance = VideoPlayer(source=machine.source_filter(
                        self.video_source.get_text()),
                        video_players_group=self.video_players)
                    # register the player
                    self.video_players.register_player(video_player=new_player_instance)
                    # play
                    new_player_instance.play(start_position=start_position)
                    # set current active player id to the newly created
                    self.selected_video_player_id = new_player_instance.get_player_id()
        else:
            player_instance = self.video_players.get_player(self.selected_video_player_id)
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
                elif action is self.SEEK_TO:
                    pass  # define later as necessary ...
                elif action is self.GET_POSITION:
                    return player_instance.get_video_position()
            else:
                print("It ain't a player!")
        # clear the url field for next one ..
        self.video_source.set_text('')
