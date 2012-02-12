#!/usr/bin/python
#
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

import glob
import os
import re
import logging
import subprocess
from distutils.core import setup
from distutils import cmd
import distutils.command
from distutils.command.install import install as _install
import sys

def runProg(cmdline):
	sout = ""
	serr = ""
	logging.debug("CMD:-%s", cmdline)
	try:
		p = subprocess.Popen(cmdline,
			stdout = subprocess.PIPE,
			stderr = subprocess.STDOUT,
			stdin = subprocess.PIPE,
			close_fds = True)
		poll = select.poll()
		poll.register(p.stdout, select.POLLIN)
		(sout,serr) = p.communicate()
		if p.poll()==1: raise
	except:
		logging.debug("ERR:%s", sout)
		return (False, sout)
	return (True, sout)

def get_gnoduino_version():
	"""Get version from src/__init__.py."""
	text = open(os.path.join("src", "__init__.py"), "r").read()
	return re.search(r"__version__ *= *['\"](.*?)['\"]", text).group(1)

class installSchema(_install):
	def run(self):
		try:
			os.system('GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source` gconftool-2 --makefile-install-rule data/gnoduino.schemas')
		except Exception, e:
			print "Installing schema has failed."
			print "%s: %s" % (type(e), e)
			sys.exit(1)
		_install.run(self)

class Pixmaps(cmd.Command):
	"""Command to build pixmaps from svg sources."""
	description = "build png files from svg sources"
	user_options = []

	def initialize_options(self):
		"""Initialize default values for options."""
		pass

	def finalize_options(self):
		"""Ensure that options have valid values."""
		pass

	def run(self):
		"""Build pixmap from svg sources."""
		if not self.dry_run:
			subprocess.call("scripts/gen-pixmaps.sh")

compline = "scripts/gen_boards.py"
(run, sout) = runProg(compline)
compline = "scripts/gen_programmers.py"
(run, sout) = runProg(compline)
compline = "scripts/gitlog.sh"
(run, sout) = runProg(compline)

class install(_install):
	def run(self):
		if len(glob.glob('pixmaps/*.png')) == 0:
			print "Couldn't find pixmaps files."
			print "Please run 'python setup.py pixmaps' to build pixmap files."
			sys.exit(1)
		# Run all sub-commands (at least those that need to be run)
		_install.run(self)

def get_data_files():
    data_files = [
        ('share/gnoduino/ui', ['ui/main.ui', 'ui/arduino.xml']),
        ('share/gnoduino/', ['BOARDS', 'ChangeLog', 'NEWS', 'PROGRAMMERS', 'preferences.txt']),
        ('share/gnoduino/pixmaps', glob.glob('pixmaps/*.png')),
        ('share/gnoduino/scripts', ['scripts/gen_boards.py', 'scripts/gen_programmers.py']),
        ('share/man/man1', ['data/gnoduino.1']),
        ('share/applications', ['data/gnoduino.desktop']),
        ('share/pixmaps', ['pixmaps/gnoduino.png']),
    ]
    for subdir in ("hardware", "libraries", "reference"):
        # We ship hardware/libraries/reference modules if not already installed
        if not os.path.exists(os.path.join(sys.prefix, "share", "arduino", subdir)) or 1:
            for dirpath, dirnames, filenames in os.walk(subdir):
                if ".git" not in dirpath and filenames:
                    data_files.append([os.path.join("share", "gnoduino", dirpath),
                                       [os.path.join(dirpath,i) for i in filenames]])
    return data_files

setup(name='gnoduino',
	version=get_gnoduino_version(),
	description='Gnome Arduino IDE implementation',
	package_dir={'gnoduino': 'src'},
	packages = ['gnoduino'],
	scripts = ['gnoduino'],

	author='Lucian Langa',
	author_email='lucilanga@gnome.org',
	url='http://gnome.eu.org/evo/index.php/Gnoduino',
	license='GPL',
	platforms='linux',
	data_files = get_data_files(),
	cmdclass={
		"pixmaps": Pixmaps,
		"install": install,
		"install": installSchema
	}
)

