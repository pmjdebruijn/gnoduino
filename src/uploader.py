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
import gettext
_ = gettext.gettext
import misc
import sys
import time

import board
import config
import programmer
import misc
import prefs
import serialio

avr = [
	"avrdude",
#	"-Chardware/tools/avrdude.conf",
	"-v",
	"-v",
	"-v",
	"-F",	#force write to ignore signature check
	"-D"
]

avr_bl = [
	"avrdude",
#	"-Chardware/tools/avrdude.conf",
#	"-v",
]


def burnBootloader(serial, output, notify, id):
	p = prefs.preferences()
	misc.clearConsole(output)
	context = notify.get_context_id("main")
	notify.pop(context)
	notify.push(context, _("Burning bootloader..."))
	b = board.Board()
	port = serial.getConfigSerialPort(notify, output)
	if port != -1:
		serial.resetBoard()
	pgm = programmer.Programmer()
	"""De-fuse and erase board"""
	compline=[i for i in avr_bl]
	compline.append("-c" + pgm.getProtocol(id))
	compline.append("-p" + b.getBoardMCU(b.getBoard()))
	compline.append("-e")
	if pgm.getForce(id) == 'true':
		compline.append("-F")
	compline.append("-Ulock:w:" + b.getFuseUnlock(b.getBoard()) + ":m")
	compline.append("-Uefuse:w:" + b.getFuseExtended(b.getBoard()) + ":m")
	compline.append("-Uhfuse:w:" + b.getFuseHigh(b.getBoard()) + ":m")
	compline.append("-Ulfuse:w:" + b.getFuseLow(b.getBoard()) + ":m")
	misc.printMessageLn(output, ' '.join(compline))
	try:
		(run, sout) = misc.runProg(compline)
		if run == False:
			if p.getBoolValue("build.verbose"):
				misc.printErrorLn(notify, output, _("Burn Error"), sout)
			raise
	except:
		misc.printErrorLn(notify, output, _("Burn Error"), _("Burn ERROR."))
		return
	"""Burn and fuse board"""
	compline=[i for i in avr_bl]
	compline.append("-c" + pgm.getProtocol(id))
	compline.append("-p" + b.getBoardMCU(b.getBoard()))
	compline.append("-e")
	if pgm.getForce(id) == 'true':
		compline.append("-F")
	compline.append("-Uflash:w:" + findBootLoader() + ":i")
	compline.append("-Ulock:w:" + b.getFuseLock(b.getBoard()) + ":m")
	if p.getBoolValue("build.verbose"): print compline
	try:
		run = misc.runProgOutput(output, compline)
		if run == False:
			if p.getBoolValue("build.verbose"):
				misc.printErrorLn(notify, output, _("Burn Error"), sout)
			raise
	except:
		misc.printErrorLn(notify, output, _("Burn Error"), _("Burn ERROR."))
		return
	notify.pop(context)
	notify.push(context, _("Burn complete."))
	misc.printMessageLn(output, \
		"Burn OK.");

def upload(obj, serial, output, notify):
	p = prefs.preferences()
	context = notify.get_context_id("main")
	notify.pop(context)
	notify.push(context, _("Flashing..."))
	b = board.Board()
	port = serial.getConfigSerialPort(notify, output)
	if port == -1:
		notify.pop(context)
		notify.push(context, _("Flashing error."))
		return
	serial.resetBoard()
	compline=[i for i in avr]
	# avrdude wants "stk500v1" to distinguish it from stk500v2
	protocol = b.getPGM(b.getBoard())
	if protocol == "stk500": protocol = "stk500v1"
	compline.append("-c" + protocol)
	compline.append("-P" + port)
	compline.append("-b" + b.getPGMSpeed(b.getBoard()))
	compline.append("-p" + b.getBoardMCU(b.getBoard()))
	compline.append("-Uflash:w:"+obj+".hex:i")
	try:
		if p.getBoolValue("build.verbose"):
			sys.stderr.write(' '.join(compline)+"\n")
			misc.printMessageLn(output, ' '.join(compline))
		(run, sout) = misc.runProg(compline)
		misc.printMessageLn(output, sout, p.getBoolValue("build.verbose"), 'false')
		if run == False: raise
	except:
		misc.printErrorLn(notify, output, _("Flashing Error"), _("Flash ERROR.\n"))
		return
	notify.pop(context)
	notify.push(context, _("Flashing complete."))
	misc.printMessageLn(output, \
		"Flash OK.");

def findBootLoader():
	b = board.Board()
	return os.path.join(misc.getArduinoBootPath(), b.getPath(b.getBoard()), \
		b.getBootloader(b.getBoard())+".hex")

