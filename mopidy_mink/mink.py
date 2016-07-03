from __future__ import absolute_import, unicode_literals

import logging
import pykka
import requests
import signal
import sys
import threading
import time

from .lcd import LCD
from mopidy import core

log = logging.getLogger(__name__)

class Mink(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        log.debug("Mink is loading.")
        super(Mink, self).__init__()
        self.config = config
        self.core = core
        self.ui = LCD()
        self.tracks = []
        self.mode = None
        self.selected_track_index = 0
        signal.signal(signal.SIGINT, self.stop)

    def on_start(self):
        """ Starts the application. """
        log.debug("Mink is starting.")
        self._initialize_ui()
        self._load_playlist()
        if len(self.tracks) > 0:
            self._select_track()

    def on_stop(self):
        """ Stops the application. """
        log.debug("Mink is stopping.")
        self.ui.stop()

    def _initialize_ui(self):
        colour = self.config["mink"]["colour"]
        log.debug("Colour is " + colour)
        self.ui.colour(colour)
        self.ui.start()

    def _load_playlist(self):
        name = self.config["mink"]["playlist"]
        log.debug("Playlist is " + name)
        all = self.core.playlists.as_list().get()
        playlist = [i for i in all if i.name == name]
        if len(playlist) == 0:
            log.error("The playlist '{0}' does not exist.".format(name))
        log.debug("Uri is " + playlist[0].uri)
        streams = self.core.playlists.lookup(playlist[0].uri).get()
        self.tracks = streams.tracks
        log.info("There are {0} streams.".format(len(self.tracks)))

    def _select_track(self):
        count = len(self.tracks)
        dial = ""
        for i in xrange(1, count + 1):
            dial += "{0} ".format(i)
        self.ui.echo(1, dial)
        self._update_selection()
        self.ui.pressed = self._select_pressed
        
    def _update_selection(self):
        self.ui.echo(2, self.tracks[self.selected_track_index].name)
        log.info("Selected index {0}: {1}".format(self.selected_track_index, self.tracks[self.selected_track_index].name))
        x = self.selected_track_index * 2
        self.ui.cursor(x, 1)

    def _select_pressed(self, button):
        if button == LCD.left and not self._is_playing() and self.selected_track_index > 0:
            self.selected_track_index -= 1
            log.info("Previous")
            self._update_selection()
        elif button == LCD.right and not self._is_playing() and self.selected_track_index < len(self.tracks)-1:
            self.selected_track_index += 1
            log.info("Next")
            self._update_selection()
        elif button == LCD.select and not self._is_playing():
            self._play()
        elif button == LCD.select and self._is_playing():
            log.info("Stopping")
            self._stop()
            self._select_track()
        elif button == LCD.up:
            self._select_track()
        elif button == LCD.down and self._is_playing():
            log.info("Pausing")
            self._pause()
        elif button == LCD.down and not self._is_playing():
            log.info("Playing")
            self._resume()

    def _play(self):
        track = self.tracks[self.selected_track_index]
        log.info("Playing stream: " + track.uri)
        self.core.playback.stop()
        self.core.tracklist.clear()
        self.core.tracklist.add([track])
        self.ui.echo(2, "Starting...")
        self.core.playback.play()

    def _pause(self):
        self.core.playback.pause()

    def _resume(self):
        self.core.playback.resume()

    def _stop(self):
        self.core.playback.stop()

    def _is_playing(self):
        return self.core.playback.get_state().get() == "playing"

    def _update_status(self):
        track = self.tracks[self.selected_track_index]
        state = self.core.playback.get_state().get()
        if state != 'stopped':
            self.ui.cursor(None)
            self.ui.echo(1, track.name)
        self.ui.echo(2, state)
        
    def playback_state_changed(self, old_state, new_state):
        self._update_status()

    def stream_title_changed(self, title):
        print "Stream: " + title
        self.ui.echo(2, title)
