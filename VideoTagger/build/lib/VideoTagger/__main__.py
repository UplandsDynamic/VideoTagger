import gi
import os

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import VideoTagger.src.run_gui as main

if __name__ == '__main__':
    vt = main.VideoTagger()
    Gtk.main()
