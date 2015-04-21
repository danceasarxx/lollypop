#!/usr/bin/python
# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GLib

import os
from _thread import start_new_thread
from gettext import gettext as _

from lollypop.view import View
from lollypop.devicemanager import DeviceManagerWidget


# Playlist synchronisation view
class DeviceView(View):
    """
        @param device as Device
        @param progress as Gtk.ProgressBar
        @param width as int
    """
    def __init__(self, device, progress, width):
        View.__init__(self)
        self._device = device
        self._progress = progress
        builder = Gtk.Builder()
        builder.add_from_resource('/org/gnome/Lollypop/DeviceManagerView.ui')
        self._memory_combo = builder.get_object('memory_combo')
        self._syncing_btn = builder.get_object('sync_btn')
        self._syncing_btn.set_label(_("Synchronize %s") % device.name)
        builder.connect_signals(self)
        grid = builder.get_object('widget')
        self.add(grid)
        self._device_widget = DeviceManagerWidget(device, progress, self)
        self._device_widget.connect('sync-finished', self._on_sync_finished)
        self._device_widget.show()
        self._scrolledWindow.set_property('halign', Gtk.Align.CENTER)
        self._scrolledWindow.set_property('width-request', width)
        self._viewport.add(self._device_widget)
        self.add(self._scrolledWindow)

    def populate(self):
        files = os.listdir(self._device.path)
        GLib.idle_add(self._set_combo_text, files)

    def is_syncing(self):
        return self._device_widget.is_syncing()

#######################
# PRIVATE             #
#######################
    """
        Start synchronisation
        @param widget as Gtk.Button
    """
    def _on_sync_clicked(self, widget):
        if self._device_widget.is_syncing():
            self._device_widget.cancel_sync()
            self._on_sync_finished(None)
        elif not self._progress.is_visible():
            self._memory_combo.hide()
            self._syncing_btn.set_label(_("Cancel synchronization"))
            self._device_widget.sync()

    """
        Restore widgets state
        @param device widget as DeviceManager
    """
    def _on_sync_finished(self, device_widget):
        self._memory_combo.show()
        self._syncing_btn.set_label(_("Synchronize %s") %
                                    self._device.name)
    """
        Update path
        @param combo as Gtk.ComboxText
    """
    def _on_memory_combo_changed(self, combo):
        text = combo.get_active_text()
        path = "%s/%s/Music/%s" % (self._device.path, text, "lollypop")
        try:
            if not os.path.exists(path+"/tracks"):
                self._mkdir(path+"/tracks")
            on_disk_playlists = os.listdir(path)
        except Exception as e:
            print("DeviceManagerWidget::_on_memory_combo_changed: %s" % e)
            on_disk_playlists = []
        self._device_widget.set_playlists(on_disk_playlists, path)
        start_new_thread(self._device_widget.populate, ())

    """
        Set combobox text
        @param text list as [str]
    """
    def _set_combo_text(self, text_list):
        for text in text_list:
            self._memory_combo.append_text(text)
        self._memory_combo.set_active(0)
