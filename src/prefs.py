# gnoduino - Python Arduino IDE implementation
# Copyright (C) 2010  Lucian Langa
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import os
import sys
import gconf
import glib

import gettext
_ = gettext.gettext

import misc

defaultFile = "preferences.txt"
defaultPath = os.path.expanduser('~/.arduino/preferences.txt')

"""gconf/preferences.txt keys"""
config_keys = [
[ "default.window.width",  "/apps/gnoduino/width", "int", 800],
[ "default.window.height", "/apps/gnoduino/height", "int", 600], #mh
[ "console.height", "/apps/gnoduino/conspos", "int", 100], #CPOS
[ "user.library", "/apps/gnoduino/user_library", "string", "" ], #user_library_key
[ "serial.port", "/apps/gnoduino/serial_port", "string", "/dev/ttyS0" ], #serial_port_key
[ "serial.debug_rate", "/apps/gnoduino/serial_baud_rate", "string", "9600" ], #serial_baud_rate_key
[ "board", "/apps/gnoduino/board", "string", "atmega168" ], #board
[ "editor.font", "/apps/gnoduino/editor_font", "string", "Monospace,10" ],
[ "console.font", "/apps/gnoduino/console_font", "string", "Monospace,10" ],
[ "build.verbose", "/apps/gnoduino/build_verbose", "string", "false" ],
[ "show.numbers", "/apps/gnoduino/show_numbers", "string", "false" ]]

class preferences(object):

	def __init__(self):
		"""default backend is preferences.txt"""
		self.backend = 0
		self.defaults = []
		self.mapping = []
		if os.path.exists(defaultPath):
			"""raise SystemExit(_("Cannot find %s") % defaultFile)"""
			for i in open(defaultPath):
				self.defaults.append(i.replace(" ", "").rstrip("\n").split("="))
			return None
		else:
			"""use gconf as backend"""
			self.backend = 1
			client = gconf.client_get_default()
			for i in config_keys:
				val = None
				self.mapping.append([i[0], i[1]])
				if i[2] is 'int':
					val = client.get_int(i[1])
				if i[2] is 'string':
					try:
						val = client.get_string(i[1])
					except glib.GError: None
				if val is not None and val is not 0:
					self.defaults.append([i[0], val])

	def getType(self, key):
		for i in config_keys:
			if i[0] == key:
				return i[2]
		return 'string'

	def getMap(self, key):
		for i in config_keys:
			if i[0] == key:
				return i[1]
		return None

	def getValue(self, value):
		for i in self.defaults:
			if i[0] == value:
				return i[1]
		return None

	def getBoolValue(self, value):
		for i in self.defaults:
			if i[0] == value:
				if i[1] == 'true':
					return True
				if i[1] == 'false':
					return False
		return None

	def getDefaultValue(self, value):
		for i in config_keys:
			if i[0] == value:
				return i[3]
		return fail

	def getSafeValue(self, value, fail):
		for i in self.defaults:
			if i[0] == value:
				return i[1]
		return fail

	def setValue(self, key, value):
		update = False
		for i in self.defaults:
			if i[0] == key:
				i[1] = str(value)
				update = True

		self.defaults.append([key, str(value)]) if update is not True else ""

	def saveValues(self):
		if self.backend is 0:
			#fixme add backup copy in case things go wrong
			w = open(defaultPath, "w")
			for i in self.defaults:
				if len(i)>1:
					w.write(i[0]+" = "+i[1]+"\n")
				else:
					w.write(i[0]+"\n")
			w.close()
		else:
			client = gconf.client_get_default()
			for i in self.defaults:
				if len(i)>1:
					if self.getType(i[0]) == 'string':
						client.set_string(self.getMap(i[0]), i[1])
					if self.getType(i[0]) == 'int':
						client.set_int(self.getMap(i[0]), int(i[1]))
