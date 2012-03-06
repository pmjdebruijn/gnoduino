# Arduino python implementation
# Copyright (C) 2010  Lucian Langa <cooly@gnome.eu.org>
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
#

import os
import sys
import ConfigParser
import misc
import config
import prefs

import gettext
_ = gettext.gettext

class mydict(dict):
	def __missing__(self, key):
		return 0

class Programmer(object):
	def __init__(self):
		self.programmers = []
		self.defaults = []
		conf = ConfigParser.RawConfigParser()
		path = misc.getArduinoFile("PROGRAMMERS")
		if path is None: raise SystemExit(_("Cannot find PROGRAMMERS"))
		conf.read(path)
		if not len(conf.sections()):
			raise SystemExit(_("Error reading %s file. File is corrupt. Installation problem.") % path)
		c = 1
		for i in conf.sections():
			v = mydict(conf.items(i))
			v['id'] = c
			v['desc'] = i
			self.programmers.append(v)
			c = c + 1

	def getProgrammers(self):
		return self.programmers

	def getCommunication(self, id):
		return self.programmers[id-1]['communication']

	def getProtocol(self, id):
		return self.programmers[id-1]['protocol']

	def getSpeed(self, id):
		return self.programmers[id-1]['speed']

	def getForce(self, id):
		return  self.programmers[id-1]['force']
