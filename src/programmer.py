# Arduino python implementation
# Copyright (C) 2010,2012  Lucian Langa <cooly@gnome.eu.org>
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

		try:
			self.programmers.extend(self.readCustomProgrammers())
		except: pass
		try:
			self.programmers.extend(self.readArduinoProgrammers())
		except:	self.programmers.extend(misc.readGnoduinoConfFile("PROGRAMMERS"))

		#renumber ids in case we grown with customs
		for i in range(len(self.programmers)): self.programmers[i]['id'] = i+1

		self.p = prefs.preferences()
		if config.cur_programmer == -1:
			try:
				config.cur_programmer = self.getProgrammerIdByName(self.p.getSafeValue("programmer", "arduino:avrispmkii")) - 1
			except:
				config.cur_programmer = self.getProgrammerIdByName("arduino:avrispmkii") - 1

	def readArduinoProgrammers(self):
		return misc.readArduinoConfFile(misc.getArduinoFile("hardware/arduino/programmers.txt"))

	def readCustomProgrammers(self):
		custom = []
		p = prefs.preferences()
		d = os.path.join(p.getValue("sketchbook.path"), "hardware")
		try:
			for i in os.listdir(d):
				if os.path.exists(os.path.join(d, i, "programmers.txt")):
					custom.extend(misc.readArduinoConfFile(os.path.join(d, i, "programmers.txt")))
			return custom
		except: return None

	def getProgrammers(self):
		return self.programmers

	def getProgrammer(self):
		return config.cur_programmer

	def getCommunication(self, id):
		try:
			return self.programmers[id]['communication']
		except KeyError: return ""

	def getProtocol(self, id):
		return self.programmers[id]['protocol']

	def getSpeed(self, id):
		try:
			return self.programmers[id]['speed']
		except KeyError: return 0

	def getForce(self, id):
		try:
			return self.programmers[id]['force']
		except KeyError: return "false"

	def setProgrammer(self, id):
		config.cur_programmer = (id - 1)
		self.p.setValue("programmer",
			self.getProgrammerPlatform(config.cur_programmer)+
			":"+
			self.programmers[config.cur_programmer]['name'])
		self.p.saveValues()

	def getProgrammerPlatform(self, id):
		return os.path.basename(
				os.path.dirname(self.programmers[id]['hwpath']))

	def getProgrammerIdByName(self, name):
		if name == None: return 1
		for i in self.programmers:
			if self.getProgrammerPlatform(i['id']-1)+":"+i['name'] == name:
				return i['id']
