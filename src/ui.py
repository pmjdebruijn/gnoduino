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
import glib
import gobject
import gtk
import subprocess
import select
import shutil
import signal
import time

import gettext
_ = gettext.gettext

import board
import config
import compiler
import programmer
import misc
import prefs
import uploader
import serialio
import srcview
import gnoduino

import gtksourceview2
font = "Monospace 10"

def setupPage(w, page, p):
	misc.set_widget_font(getCurrentView(), config.cur_editor_font)
	getCurrentPage().queue_resize()
	pg = w.get_nth_page(p)
	cl = pg.get_data("close");
	if cl == None: return
	accel = gtk.AccelGroup()
	cl.add_accelerator("activate", accel, ord("w"), gtk.gdk.CONTROL_MASK, 0)
	mainwin.add_accel_group(accel)
	srcview.updatePos(pg.get_data("buffer"), sb2)

def replacePage(page):
	nb.remove_page(nb.page_num(page))

def destroyPage(w, b):
	f = b.get_data("file")
	buf = b.get_data("buffer")
	if misc.bufferModified(buf, f) is True:
		if f is None: f= "Untitled"
		save = misc.createPopup(_("Save document"), mainwin, \
			_("Save changes to document \"%s\"\n before closing?" % os.path.basename(f)))
		if save == gtk.RESPONSE_YES:
			if csave(None, False) is False:
				return False
		if save == gtk.RESPONSE_CANCEL or save == gtk.RESPONSE_DELETE_EVENT:
			return False
	nb.remove_page(nb.page_num(b))
	if nb.get_n_pages() < 1:
		createPage(nb)
	return True

def updatePageTitle(w, status):
	page = getCurrentPage()
	f = page.get_data("file")
	l = page.get_data("label")
	if f != None:
		name = os.path.basename(f)
	else:
		fh = 0
		name = "Untitled"

	if (misc.bufferModified(w, f)):
		l.set_text("*"+name)
	else:
		l.set_text(name)
	srcview.updatePos(w, status)

def switchPage(page, a, b, c):
	nb.set_current_page(int(chr(b-1)))

def createPage(nb, f=None):
	hbox = gtk.HBox(False, 0)
	flabel = gtk.Label(os.path.basename(f) if f else "Untitled")
	hbox.pack_start(flabel, True, False, 3)
	b = gtk.Button()
	img = gtk.Image()
	img.set_from_icon_name(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
	img.set_pixel_size(11)
	b.set_image(img)
	b.set_relief(gtk.RELIEF_NONE)
	hbox.pack_start(b, True, True)
	hbox.show_all()
	(sbuf,sv) = srcview.createsrcview(sb2, f)
	sbuf.connect("changed", updatePageTitle, sb2)
	sw = gtk.ScrolledWindow()
	sw.add(sv)
	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	sw.set_placement(gtk.CORNER_BOTTOM_LEFT)
	sw.set_shadow_type(gtk.SHADOW_IN)
	sw.show_all()
	p = nb.append_page(sw, hbox)
	wp = nb.get_nth_page(p)
	wp.set_data("file", f)		#add file information to the page widget
	wp.set_data("buffer", sbuf)	#add buffer information to the page widget
	wp.set_data("view", sv)	#add buffer information to the page widget
	wp.set_data("label", flabel)	#add source view widget to the page widget
	wp.set_data("close", b)	#add close widget to the page widget
	nb.set_current_page(p)
	page = nb.get_nth_page(p)
	nb.set_scrollable(True);
	nb.set_tab_reorderable(page, True);
	accel = gtk.AccelGroup()
	for i in range(1, 10):
		accel.connect_group(ord(str(i)), gtk.gdk.MOD1_MASK, 0,
			switchPage)
	mainwin.add_accel_group(accel)
	sv.grab_focus()
	b.connect("clicked", destroyPage, sw)
	accel = gtk.AccelGroup()
	b.add_accelerator("activate", accel, ord("w"), gtk.gdk.CONTROL_MASK, 0)
	mainwin.add_accel_group(accel)
	srcview.updatePos(sbuf, sb2)
	return sv

def cnew(widget, data=None):
	createPage(nb, data)

def searchFile(nb, f):
	for i in range(nb.get_n_pages()):
		of = nb.get_nth_page(i).get_data("file")
		if of == f:
			nb.set_current_page(i)
			return True
	return False

def openFile(w):
	f = w.get_filename()
	if searchFile(nb, f) == True:
		w.destroy()
		return
	processFile(f)

def processFile(f):
	if not os.path.exists(f):
		return
	page = getCurrentPage()
	createPage(nb, f)
	if page.get_data("label").get_text() == "Untitled":
		replacePage(page)

def saveAs(js=False):
	page = getCurrentPage()
	buf = page.get_data("buffer")
	f = page.get_data("file")
	if misc.bufferModified(buf, f) is False and js is False:
		return
	p = gtk.FileChooserDialog("Save file", None, gtk.FILE_CHOOSER_ACTION_SAVE,
		(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
		gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
	if page.get_data("file") is not None:
		name =  os.path.basename(page.get_data("file"))
		p.set_filename(name)
	else:
		name = "Untitled"
		p.set_current_name(name)
	p.set_default_size(450, 400)
	p.show_all()
	if p.run() == gtk.RESPONSE_ACCEPT:
		f = p.get_filename()
		p.destroy()
		return f
	p.destroy()
	return None

def copen(widget, data=None):
	p = gtk.FileChooserDialog("Open file", None, gtk.FILE_CHOOSER_ACTION_OPEN,
		(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
		gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
	p.set_size_request(450, 400)
	p.show_all()
	if p.run() == gtk.RESPONSE_ACCEPT:
		openFile(p)
	p.destroy()

def csave_as(w, data=None):
	csave(w, True)

def csave(w, data=None):
	page = getCurrentPage()
	l = page.get_data("label")
	b = page.get_data("buffer")
	f = page.get_data("file")
	if f == None or data == True:
		f = saveAs(data)
		if f == None: return False
		else:
			if os.path.exists(f):
				p = misc.MessageBox()
				res = p.show("""<b>A file named %s already exists. Do you want to replace it?</b>""" % f,
				"The file already exists in \"%s\". Replacing it will overwrite its contents." % os.path.dirname(f))
				if not res: return
			l.set_text(os.path.basename(f))
			page.set_data("file", f)
	F = open(f, "w")
	F.write(b.get_text(b.get_start_iter(), b.get_end_iter()))
	F.close()
	updatePageTitle(b, sb2)
	return True

def quit(widget, data=None):
	for i in range(nb.get_n_pages()):
		if (destroyPage(None, nb.get_nth_page(0)) is False):
			return True
	shutil.rmtree(id, True)
	gtk.main_quit()

def find(widget, data=None):
	find = gui.get_object("find")
	find_text = gui.get_object("find-text")
	find_text.select_region(0, -1)
	cbs = ["checkbutton1", "checkbutton2","checkbutton3", "checkbutton4"]
	find_text.connect("key-release-event", srcview.findText, [gui.get_object(i) for i in cbs])
	find.set_default_response(gtk.RESPONSE_OK)
	r =  find.run()
	if r == 1:
		srcview.findText(find_text, -1, [gui.get_object(i) for i in cbs])
	find.hide()

def libImport(widget, data=None):
	compiler.getLibraries()

def compile(widget, data=file):
	cserial(None, 0, sctw)
	page = getCurrentPage()
	obj = compiler.compile(page.get_data("view"), id, tw, sb) #page.get_data("buffer")
	return obj

def upload(widget, serial, data=file):
	obj = compile(widget, data)
	if obj == -1: return
	while (gtk.events_pending()):
		gtk.main_iteration()
	uploader.upload(obj, serial, tw, sb)

def butSave(widget, data=None):
	b = getCurrentPage()
	f = b.get_data("file")
	buf = b.get_data("buffer")
	if misc.bufferModified(buf, f) is True:
		csave(widget, False)

def menuUpload(widget, data=None):
	upload(widget, ser, data)

def menuReference(widget, data=None):
	gtk.show_uri(None, "file:///"+os.path.join(misc.getArduinoFile("reference"), "index.html"), int(time.time()))

def about(widget, data=None):
	about = gui.get_object("about")
	about.set_version(gnoduino.__version__)
	about.run()
	about.hide()

def menuResetBoard(widget, data=None):
	ser.resetBoard()

def preferences(widget, data=None):
	pref = gui.get_object("preferences")
	fe = gui.get_object("fontbutton1")
	fc = gui.get_object("fontbutton2")
	bv = gui.get_object("build.verbose")
	sn = gui.get_object("show.numbers")
	ul = gui.get_object("user.library")
	p = prefs.preferences()
	fe.set_font_name(misc.merge_font_name(fe, config.cur_editor_font))
	fc.set_font_name(misc.merge_font_name(fc, config.cur_console_font))
	val = 0
	if config.build_verbose != -1:
		if config.build_verbose == 'true':
			val = 1
	else:
		if p.getSafeValue("build.verbose", "false") == 'true':
			val = 1
	bv.set_active(val)
	val = 0
	if config.show_numbers != -1:
		if config.show_numbers == 'true':
			val = 1
	else:
		if p.getSafeValue("show.numbers", "false") == 'true':
			val = 1
	sn.set_active(val)
	if (config.user_library != None and config.user_library != -1):
		ul.set_text(str(config.user_library))
	else:
		ul.set_text(str(p.getSafeValue("user.library", "")))
	r = pref.run()
	if r == 1:
		config.cur_editor_font = fe.get_font_name()
		p.setValue("editor.font", config.cur_editor_font.replace(" ", ","))
		config.cur_console_font = fc.get_font_name()
		p.setValue("console.font", config.cur_console_font.replace(" ", ","))
		config.user_library = ul.get_text()
		if bv.get_active() == 1:
			config.build_verbose = 'true'
		else:
			config.build_verbose = 'false'
		p.setValue("build.verbose", config.build_verbose)
		if sn.get_active() == 1:
			config.show_numbers = 'true'
		else:
			config.show_numbers = 'false'
		p.setValue("show.numbers", config.show_numbers)
		for i in range(nb.get_n_pages()):
			sv = nb.get_nth_page(i).get_data("view")
			if (config.show_numbers == 'true'):
				sv.set_show_line_numbers(True)
			else:
				sv.set_show_line_numbers(False)
		p.setValue("user.library", config.user_library)
		p.saveValues()
		misc.set_widget_font(tw, config.cur_console_font)
		misc.set_widget_font(sctw, config.cur_console_font)
		misc.set_widget_font(getCurrentView(), config.cur_editor_font)
	pref.hide()

def stop(widget, data=None):
	print "stop"

def cserial(w, st, data=None):
	global sertime
	"""inhibit function"""
	if st == 0:
		if sertime:
			glib.source_remove(sertime)
			sertime = None
			vbox.remove(scon)
			vbox.add(con)
		return
	if (sertime == None):
		if not ser.serial.isOpen():
			ser.getConfigSerialPort(sb, tw)
			return
		sertime = glib.timeout_add(1000,
			ser.updateConsole,
			data)
		vbox.remove(con)
		vbox.add(scon)
	else:
		glib.source_remove(sertime)
		sertime = None
		vbox.remove(scon)
		vbox.add(con)

def burnBootloader(w, id):
	uploader.burnBootloader(ser, tw, sb, id)

def setBaud(w, data=None):
	if ser.serial.isOpen():
		ser.resetBoard()
		ser.serial.close()
	else: return
	if config.serial_baud_rate == -1:
		config.serial_baud_rate = p.getSafeValue("serial.debug_rate", p.getDefaultValue("serial.debug_rate"))
		defbaud = config.serial_baud_rate
	else:
		if w: defbaud = ser.getBaudrates()[w.get_active()]
	ser.serial.baudrate = [i for i in ser.getBaudrates() if i == defbaud][0]
	ser.serial.open()
	p.setValue("serial.debug_rate", defbaud)
	p.saveValues()

def serSendText(w, data=None):
	ser.serial.write(w.get_text())
	w.set_text("")

def undo(w, data=None):
	page = getCurrentPage()
	b = page.get_data("buffer")
	if b.can_undo(): b.undo()

def redo(w, data=None):
	page = getCurrentPage()
	b = page.get_data("buffer")
	if b.can_redo(): b.redo()

def cut(w, data=None):
	page = getCurrentPage()
	b = page.get_data("buffer")
	display = gtk.gdk.display_manager_get().get_default_display()
	clipboard = gtk.Clipboard(display, "PRIMARY")
	b.cut_clipboard(clipboard, True)

def copy(w, data=None):
	page = getCurrentPage()
	b = page.get_data("buffer")
	display = gtk.gdk.display_manager_get().get_default_display()
	clipboard = gtk.Clipboard(display, "PRIMARY")
	b.copy_clipboard(clipboard)

def paste(w, data=None):
	page = getCurrentPage()
	b = page.get_data("buffer")
	display = gtk.gdk.display_manager_get().get_default_display()
	clipboard = gtk.Clipboard(display, "PRIMARY")
	b.paste_clipboard(clipboard, None, True)

menus = [
		("menu-new", cnew, (ord('n'), gtk.gdk.CONTROL_MASK)),
		("menu-open", copen, (ord('o'), gtk.gdk.CONTROL_MASK)),
		("menu-save", csave, (ord('s'), gtk.gdk.CONTROL_MASK)),
		("menu-save-as", csave_as, (ord('s'), gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK)),
		("menu-quit", quit, (ord('q'), gtk.gdk.CONTROL_MASK)),
		("menu-find", find, (ord('f'), gtk.gdk.CONTROL_MASK)),
		("menu-undo", undo, (ord('z'), gtk.gdk.CONTROL_MASK)),
		("menu-redo", redo, (ord('z'), gtk.gdk.CONTROL_MASK|gtk.gdk.SHIFT_MASK)),
		("menu-cut", cut, (ord('x'), gtk.gdk.CONTROL_MASK)),
		("menu-copy", copy, (ord('c'), gtk.gdk.CONTROL_MASK)),
		("menu-paste", paste, (ord('v'), gtk.gdk.CONTROL_MASK)),
		("menu-compile", compile, (ord('r'), gtk.gdk.CONTROL_MASK)),
		("menu-import", libImport, (ord('i'), gtk.gdk.CONTROL_MASK)),
		("menu-reset-board", menuResetBoard, (ord('m'), gtk.gdk.CONTROL_MASK)),
		("menu-preferences", preferences, (None, None)),
		("menu-upload", menuUpload, (ord('u'), gtk.gdk.CONTROL_MASK)),
		("menu-reference", menuReference, (None, None)),
		("menu-about", about, (None, None)),

	]

def menu(gui):
	[gui.get_object(i[0]).connect("activate", i[1]) for i in menus]
	accel = gtk.AccelGroup()
	[gui.get_object(i[0]).add_accelerator("activate", \
		accel, i[2][0], i[2][1], 0) for i in menus if i[2][0] != None]
	mainwin.add_accel_group(accel)
	gui.get_object("menu-find-next").set_sensitive(False)
	gui.get_object("menu-replace").set_sensitive(False)

def createCon():
	sw = gtk.ScrolledWindow()
	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	sw.set_shadow_type(gtk.SHADOW_IN)
	tmp = gtk.TextView()
	tmp.set_editable(False)
	twbuf = gtk.TextBuffer()
	tmp.set_buffer(twbuf)
	tmp.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
	tmp.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color("#ffffff"))
	misc.set_widget_font(tmp, config.cur_console_font)
	sw.add(tmp)
	sw.show_all()
	return (sw, tmp)

def createScon():
	global baud
	sw = gtk.ScrolledWindow()
	sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
	sw.set_shadow_type(gtk.SHADOW_IN)
	tmp = gtk.TextView()
	tmp.set_editable(False)
	tmp.set_wrap_mode(gtk.WRAP_WORD)
	twbuf = gtk.TextBuffer()
	tmp.set_buffer(twbuf)
	tmp.modify_base(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
	tmp.modify_text(gtk.STATE_NORMAL, gtk.gdk.Color("#ffffff"))
	misc.set_widget_font(tmp, config.cur_console_font)
	sw.add(tmp)
	hbox = gtk.HBox(False, 0)
	s = gtk.Button("Send")
	c = gtk.Button("Clear")
	c.connect("clicked", ser.clearConsole, tmp)
	bb = gtk.HBox(False, 0)
	gui.set_data("baudHBox", bb)
	text = gtk.Entry()
	text.connect("activate", serSendText)
	hbox.pack_start(bb, False, False, 3)
	hbox.pack_start(text, True, True, 3)
	hbox.pack_start(s, False, False, 3)
	hbox.pack_start(c, False, False, 3)
	vbox = gtk.VBox(False, 0)
	vbox.pack_start(hbox, False, False, 3)
	vbox.pack_start(sw, True, True, 3)
	vbox.show_all()
	createBaudCombo(None, config.cur_serial_port)
	return (vbox, tmp)

buttons = [
		("compile", "compile.png", compile),
		("stop", "stop.png", stop),

		("open", "open.png", copen),
		("new", "new.png", cnew),

		("save", "save.png", butSave),
		("upload", "upload.png", None),
		("serial", "serial.png", None)
	]

def createBaudCombo(w, port):
	hb = gui.get_data("baudHBox")
	if hb:
		bw = gui.get_data("baudWidget")
		if bw: bw.destroy()
		b = gtk.combo_box_new_text()
		[b.append_text(i+" baud") for i in ser.getBaudrates()]
		b.connect("changed", setBaud)
		b.set_active(ser.getBaudrates().index(config.serial_baud_rate))
		hb.pack_start(b, False, False, 3)
		gui.set_data("baudWidget", b)
		hb.show_all()

def selectBoard(w, id):
	b.setBoard(id)

def setSerial(w, id):
	createBaudCombo(w, id)
	try:
		config.cur_serial_port = id
		if ser.serial.isOpen():
			ser.resetBoard()
			ser.serial.close()
		ser.serial.port = id
		ser.serial.open()
		p.setValue("serial.port", id)
		p.saveValues()
	except Exception,e:
		misc.clearConsole(tw)
		misc.printMessage(tw, str(e))
		print(e)

def getCurrentPage():
	return nb.get_nth_page(nb.get_current_page())

def getCurrentView():
	p = nb.get_nth_page(nb.get_current_page())
	return p.get_data("view")


def getGui():
	return gui

def cb_configure_event(widget, event):
	p.setValue("default.window.width", event.width)
	p.setValue("default.window.height", event.height)
	p.saveValues()

def vbox_move_handle(widget, scrolltype):
	p.setValue("console.height", widget.get_position()+8)
	p.saveValues()
	return True

def run():
	try:
		global gui
		global mainwin
		global sb2
		global ser
		global id
		global nb
		global tw
		global sctw
		global sb
		global sertime
		global vbox
		global con
		global scon
		global p
		global b
		#perform cleanup prior to this
		signal.signal(signal.SIGINT, signal.SIG_DFL)
		id = misc.makeWorkdir()
		ser = serialio.sconsole()
		p = prefs.preferences()
		sertime = None
		gui = gtk.Builder()
		try:
			path = os.path.join(os.getcwd(), "ui", "main.ui")
			if os.path.exists(path):
				gui.add_from_file(path)
			else: raise NameError("System error")
		except:
			try:
				path = os.path.join(sys.prefix, "local", "share", "gnoduino", "ui", "main.ui")
				if os.path.exists(path):
					gui.add_from_file(path)
				else: raise NameError("System error")
			except:
				try:
					path = os.path.join(sys.prefix, "share", "gnoduino", "ui", "main.ui")
					if os.path.exists(path):
						gui.add_from_file(path)
					else: raise NameError("System error")
				except Exception,e:
					print(e)
					raise SystemExit(_("Cannot load ui file"))
		mainwin = gui.get_object("top_win")
		mainwin.set_icon_from_file(misc.getPixmapPath("gnoduino.png"))
		mw = int(p.getSafeValue("default.window.width", 640))
		mh = int(p.getSafeValue("default.window.height", 480))
		if (mw and mh):
			mainwin.set_default_size(mw, mh)
		mainwin.connect("configure-event", cb_configure_event)
		vbox = gui.get_object("vpan")
		sb = gui.get_object("statusbar1")
		sb2 = gui.get_object("statusbar2")
		config.cur_editor_font = p.getSafeValue("editor.font", p.getDefaultValue("editor.font")).replace(",", " ")
		config.cur_console_font = p.getSafeValue("console.font", p.getDefaultValue("console.font")).replace(",", " ")
		config.build_verbose = p.getSafeValue("build.verbose", p.getDefaultValue("build.verbose"))
		config.show_numbers = p.getSafeValue("show.numbers", p.getDefaultValue("show.numbers"))
		config.user_library = p.getValue("user.library")
		menu(gui)
		"""build menus"""
		sub = gtk.Menu()
		b = board.Board()
		maingroup = gtk.RadioMenuItem(None, None)
		for i in b.getBoards():
			menuItem = gtk.RadioMenuItem(maingroup, i['desc'])
			if i['id'] == b.getBoard() + 1:
				menuItem.set_active(True)
			menuItem.connect('toggled', selectBoard, i['id'])
			sub.append(menuItem)
		gui.get_object("board").set_submenu(sub)
		(con, tw) = createCon()
		misc.setConsoleTags(tw)

		"""setup default serial port"""
		sub = gtk.Menu()
		maingroup = gtk.RadioMenuItem(None, None)
		defport = p.getValue("serial.port")
		validport = False
		activePort = False
		"""validate serial ports - this should really be moved to serialio"""
		for i in ser.scan():
			if i == defport:
				validport = True

		for i in ser.scan():
			menuItem = gtk.RadioMenuItem(maingroup, i)
			if defport and validport:
				if i == defport:
					menuItem.set_active(True)
					if config.cur_serial_port == -1:
						config.cur_serial_port = i
					setSerial(None, i)
			else:
				if config.cur_serial_port == -1:
					config.cur_serial_port = i
				try:
					s = ser.tryPort(i)
					s.close()
				except: continue
				menuItem.set_active(True)
				setSerial(None, i)
			menuItem.connect('activate', setSerial, i)
			sub.append(menuItem)
			activePort = True

		if config.serial_baud_rate == -1:
			config.serial_baud_rate = p.getSafeValue("serial.debug_rate", p.getDefaultValue("serial.debug_rate"))

		gui.get_object("serial_port").set_submenu(sub)
		gui.get_object("serial_port").set_sensitive(activePort)

		sub = gtk.Menu()
		pgm = programmer.Programmer()
		for i in pgm.getProgrammers():
			menuItem = gtk.MenuItem(i['desc'])
			menuItem.connect('activate', burnBootloader, i['id'])
			sub.append(menuItem)
		gui.get_object("burn").set_submenu(sub)

		nb = gtk.Notebook()
		nb.connect("switch-page", setupPage)
		sv = createPage(nb)
		vbox.pack1(nb, shrink=True, resize=True)
		(scon,sctw) = createScon()
		vbox.pack2(con, shrink=False, resize=False)
		vbox.connect("notify::position", vbox_move_handle)
		cpos = int(p.getSafeValue("console.height", -1))
		vbox.set_position(cpos)
		mainwin.set_focus(sv)
		mainwin.show_all()
		mainwin.set_title("Gnoduino")
		mainwin.connect("delete-event", quit)
		gui.get_object("ser_monitor").connect("activate", cserial, sertime, sctw)
		gui.get_object("serial").connect("clicked", cserial, sertime, sctw)
		gui.get_object("upload").connect("clicked", upload, ser)
		for i in buttons:
			w = gtk.Image()
			w.set_from_file(misc.getPixmapPath(i[1]))
			o = gui.get_object(i[0])
			o.set_icon_widget(w)
			o.show_all()
			if i[2] != None:
				o.connect("clicked", i[2])
		if (sys.argv[1:]):
			if sys.argv[1:][0] == "--help" or sys.argv[1:][0] == "-h":
				print """--help Prints the command line options.\n--version Output version information and exit"""
				sys.exit(0)
			if sys.argv[1:][0] == "--version" or sys.argv[1:][0] == "-v":
				print "gnoduino %s" % gnoduino.__version__
				sys.exit(0)
			for f in sys.argv[1:]:
				processFile(f)
		gtk.main()
	except KeyboardInterrupt:
		print "\nExit on user cancel."
		sys.exit(1)
