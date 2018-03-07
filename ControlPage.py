#
# Author: vvlachoudis@gmail.com
# Date: 18-Jun-2015
#
__author__ = "Vasilis Vlachoudis"
__email__  = "vvlachoudis@gmail.com"

import math
import tkinter as tk
import tkinter.messagebox as tkMessageBox

import Utils
import Ribbon
import Sender
import tkExtra
import Unicode
import CNCRibbon
from CNC import CNC, WCS, DISTANCE_MODE, FEED_MODE, UNITS, PLANE

_LOWSTEP   = 0.0001
_HIGHSTEP  = 1000.0
_HIGHZSTEP = 10.0

OVERRIDES = ["Feed", "Rapid", "Spindle"]

#===============================================================================
# Connection Group
#===============================================================================
class ConnectionGroup(CNCRibbon.ButtonMenuGroup):
	def __init__(self, master, app):
		super().__init__(master, N_("Connection"), app,
			[(_("Hard Reset"),  "reset",     app.hardReset) ])
		self.grid2rows()

		# ---
		col,row=0,0
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["home32"],
				text=_("Home"),
				compound=tk.TOP,
				anchor=tk.W,
				command=app.home,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, rowspan=3, padx=0, pady=0, sticky=tk.NSEW)
		tkExtra.Balloon.set(b, _("Perform a homing cycle [$H]"))
		self.addWidget(b)

		# ---
		col,row=1,0
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["unlock"],
				text=_("Unlock"),
				compound=tk.LEFT,
				anchor=tk.W,
				command=app.unlock,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, padx=0, pady=0, sticky=tk.NSEW)
		tkExtra.Balloon.set(b, _("Unlock controller [$X]"))
		self.addWidget(b)

		row += 1
		b = Ribbon.LabelButton(self.frame,
				image=Utils.icons["reset"],
				text=_("Reset"),
				compound=tk.LEFT,
				anchor=tk.W,
				command=app.softReset,
				background=Ribbon._BACKGROUND)
		b.grid(row=row, column=col, padx=0, pady=0, sticky=tk.NSEW)
		tkExtra.Balloon.set(b, _("Software reset of controller [ctrl-x]"))
		self.addWidget(b)

#===============================================================================
# User Group
#===============================================================================
class UserGroup(CNCRibbon.ButtonGroup):
	def __init__(self, master, app):
		super().__init__(master, "User", app)
		self.grid3rows()

		n = Utils.getInt("Buttons","n",6)
		for i in range(1,n):
			b = Utils.UserButton(self.frame, self.app, i,
					anchor=tk.W,
					background=Ribbon._BACKGROUND)
			col,row = divmod(i-1,3)
			b.grid(row=row, column=col, sticky=tk.NSEW)
			self.addWidget(b)

#===============================================================================
# Run Group
#===============================================================================
class RunGroup(CNCRibbon.ButtonGroup):
	def __init__(self, master, app):
		super().__init__(master, "Run", app)

		b = Ribbon.LabelButton(self.frame, self, "<<Run>>",
				image=Utils.icons["start32"],
				text=_("Start"),
				compound=tk.TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=tk.LEFT, fill=tk.BOTH)
		tkExtra.Balloon.set(b, _("Run g-code commands from editor to controller"))
		self.addWidget(b)

		b = Ribbon.LabelButton(self.frame, self, "<<Pause>>",
				image=Utils.icons["pause32"],
				text=_("Pause"),
				compound=tk.TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=tk.LEFT, fill=tk.BOTH)
		tkExtra.Balloon.set(b, _("Pause running program. Sends either FEED_HOLD ! or CYCLE_START ~"))

		b = Ribbon.LabelButton(self.frame, self, "<<Stop>>",
				image=Utils.icons["stop32"],
				text=_("Stop"),
				compound=tk.TOP,
				background=Ribbon._BACKGROUND)
		b.pack(side=tk.LEFT, fill=tk.BOTH)
		tkExtra.Balloon.set(b, _("Pause running program and soft reset controller to empty the buffer."))

#===============================================================================
# DRO Frame
#===============================================================================
class DROFrame(CNCRibbon.PageFrame):
	dro_status = ('Helvetica',12,'bold')
	dro_wpos   = ('Helvetica',12,'bold')
	dro_mpos   = ('Helvetica',12)

	def __init__(self, master, app):
		super().__init__(master, "DRO", app)

		DROFrame.dro_status = Utils.getFont("dro.status", DROFrame.dro_status)
		DROFrame.dro_wpos   = Utils.getFont("dro.wpos",   DROFrame.dro_wpos)
		DROFrame.dro_mpos   = Utils.getFont("dro.mpos",   DROFrame.dro_mpos)

		row = 0
		col = 0
		tk.Label(self,text=_("Status:")).grid(row=row,column=col,sticky=tk.E)
		col += 1
		self.state = tk.Button(self,
				text=Sender.NOT_CONNECTED,
				font=DROFrame.dro_status,
				command=self.showState,
				cursor="hand1",
				background=Sender.STATECOLOR[Sender.NOT_CONNECTED],
				activebackground="LightYellow")
		self.state.grid(row=row,column=col, columnspan=3, sticky=tk.EW)
		tkExtra.Balloon.set(self.state,
				_("Show current state of the machine\n"
				  "Click to see details\n"
				  "Right-Click to clear alarm/errors"))
		#self.state.bind("<Button-3>", lambda e,s=self : s.event_generate("<<AlarmClear>>"))
		self.state.bind("<Button-3>", self.stateMenu)

		row += 1
		col = 0
		tk.Label(self,text=_("WPos:")).grid(row=row,column=col,sticky=tk.E)

		# work
		col += 1
		self.xwork = tk.Entry(self, font=DROFrame.dro_wpos,
					background="White",
					relief=tk.FLAT,
					borderwidth=0,
					justify=tk.RIGHT)
		self.xwork.grid(row=row,column=col,padx=1,sticky=tk.EW)
		tkExtra.Balloon.set(self.xwork, _("X work position (click to set)"))
		self.xwork.bind('<FocusIn>',  self.workFocus)
		self.xwork.bind('<Return>',   self.setX)
		self.xwork.bind('<KP_Enter>', self.setX)

		# ---
		col += 1
		self.ywork = tk.Entry(self, font=DROFrame.dro_wpos,
					background="White",
					relief=tk.FLAT,
					borderwidth=0,
					justify=tk.RIGHT)
		self.ywork.grid(row=row,column=col,padx=1,sticky=tk.EW)
		tkExtra.Balloon.set(self.ywork, _("Y work position (click to set)"))
		self.ywork.bind('<FocusIn>',  self.workFocus)
		self.ywork.bind('<Return>',   self.setY)
		self.ywork.bind('<KP_Enter>', self.setY)

		# ---
		col += 1
		self.zwork = tk.Entry(self, font=DROFrame.dro_wpos,
					background="White",
					relief=tk.FLAT,
					borderwidth=0,
					justify=tk.RIGHT)
		self.zwork.grid(row=row,column=col,padx=1,sticky=tk.EW)
		tkExtra.Balloon.set(self.zwork, _("Z work position (click to set)"))
		self.zwork.bind('<FocusIn>',  self.workFocus)
		self.zwork.bind('<Return>',   self.setZ)
		self.zwork.bind('<KP_Enter>', self.setZ)

		# Machine
		row += 1
		col = 0
		tk.Label(self,text=_("MPos:")).grid(row=row,column=col,sticky=tk.E)

		col += 1
		self.xmachine = tk.Label(self, font=DROFrame.dro_mpos, background="White",anchor=tk.E)
		self.xmachine.grid(row=row,column=col,padx=1,sticky=tk.EW)

		col += 1
		self.ymachine = tk.Label(self, font=DROFrame.dro_mpos, background="White",anchor=tk.E)
		self.ymachine.grid(row=row,column=col,padx=1,sticky=tk.EW)

		col += 1
		self.zmachine = tk.Label(self, font=DROFrame.dro_mpos, background="White", anchor=tk.E)
		self.zmachine.grid(row=row,column=col,padx=1,sticky=tk.EW)

		# Set buttons
		row += 1
		col = 1

		self.xzero = tk.Button(self, text=_("X=0"),
				command=self.setX0,
				activebackground="LightYellow",
				padx=2, pady=1)
		self.xzero.grid(row=row, column=col, pady=0, sticky=tk.EW)
		tkExtra.Balloon.set(self.xzero, _("Set X coordinate to zero (or to typed coordinate in WPos)"))
		self.addWidget(self.xzero)

		col += 1
		self.yzero = tk.Button(self, text=_("Y=0"),
				command=self.setY0,
				activebackground="LightYellow",
				padx=2, pady=1)
		self.yzero.grid(row=row, column=col, pady=0, sticky=tk.EW)
		tkExtra.Balloon.set(self.yzero, _("Set Y coordinate to zero (or to typed coordinate in WPos)"))
		self.addWidget(self.yzero)

		col += 1
		self.zzero = tk.Button(self, text=_("Z=0"),
				command=self.setZ0,
				activebackground="LightYellow",
				padx=2, pady=1)
		self.zzero.grid(row=row, column=col, pady=0, sticky=tk.EW)
		tkExtra.Balloon.set(self.zzero, _("Set Z coordinate to zero (or to typed coordinate in WPos)"))
		self.addWidget(self.zzero)

		# Set buttons
		row += 1
		col = 1
		f = tk.Frame(self)
		f.grid(row=row, column=col, columnspan=3, pady=0, sticky=tk.EW)

		b = tk.Button(f, text=_("Set WPOS"),
				image=Utils.icons["origin"],
				compound=tk.LEFT,
				activebackground="LightYellow",
				command=lambda s=self: s.event_generate("<<SetWPOS>>"),
				padx=2, pady=1)
		b.pack(side=tk.LEFT,fill=tk.X,expand=tk.YES)
		tkExtra.Balloon.set(b, _("Set WPOS to mouse location"))
		self.addWidget(b)

		#col += 2
		b = tk.Button(f, text=_("Move Gantry"),
				image=Utils.icons["gantry"],
				compound=tk.LEFT,
				activebackground="LightYellow",
				command=lambda s=self: s.event_generate("<<MoveGantry>>"),
				padx=2, pady=1)
		#b.grid(row=row, column=col, pady=0, sticky=tk.EW)
		b.pack(side=tk.RIGHT,fill=tk.X,expand=tk.YES)
		tkExtra.Balloon.set(b, _("Move gantry to mouse location [g]"))
		self.addWidget(b)

		self.grid_columnconfigure(1, weight=1)
		self.grid_columnconfigure(2, weight=1)
		self.grid_columnconfigure(3, weight=1)

	#----------------------------------------------------------------------
	def stateMenu(self, event=None):
		menu = tk.Menu(self, tearoff=0)

		menu.add_command(label=_("Show Info"), image=Utils.icons["info"], compound=tk.LEFT,
					command=self.showState)
		menu.add_command(label=_("Clear Message"), image=Utils.icons["clear"], compound=tk.LEFT,
					command=lambda s=self: s.event_generate("<<AlarmClear>>"))
		menu.add_separator()

		menu.add_command(label=_("Feed hold"), image=Utils.icons["pause"], compound=tk.LEFT,
					command=lambda s=self: s.event_generate("<<FeedHold>>"))
		menu.add_command(label=_("Resume"), image=Utils.icons["start"], compound=tk.LEFT,
					command=lambda s=self: s.event_generate("<<Resume>>"))

		menu.tk_popup(event.x_root, event.y_root)

	#----------------------------------------------------------------------
	def updateState(self):
		msg = self.app._msg or CNC.vars["state"]
		self.state.config(text=msg, background=CNC.vars["color"])

	#----------------------------------------------------------------------
	def updateCoords(self):
		try:
			focus = self.focus_get()
		except:
			focus = None
		if focus is not self.xwork:
			self.xwork.delete(0,tk.END)
			self.xwork.insert(0,self.padFloat(CNC.drozeropad,CNC.vars["wx"]))
		if focus is not self.ywork:
			self.ywork.delete(0,tk.END)
			self.ywork.insert(0,self.padFloat(CNC.drozeropad,CNC.vars["wy"]))
		if focus is not self.zwork:
			self.zwork.delete(0,tk.END)
			self.zwork.insert(0,self.padFloat(CNC.drozeropad,CNC.vars["wz"]))

		self.xmachine["text"] = self.padFloat(CNC.drozeropad,CNC.vars["mx"])
		self.ymachine["text"] = self.padFloat(CNC.drozeropad,CNC.vars["my"])
		self.zmachine["text"] = self.padFloat(CNC.drozeropad,CNC.vars["mz"])

	#----------------------------------------------------------------------
	def padFloat(self, decimals, value):
		if decimals>0:
			return "%0.*f"%(decimals, value)
		else:
			return value

	#----------------------------------------------------------------------
	# Do not give the focus while we are running
	#----------------------------------------------------------------------
	def workFocus(self, event=None):
		if self.app.running:
			self.app.focus_set()

	#----------------------------------------------------------------------
	def setX0(self, event=None):
		self._wcsSet("0",None,None)

	#----------------------------------------------------------------------
	def setY0(self, event=None):
		self._wcsSet(None,"0",None)

	#----------------------------------------------------------------------
	def setZ0(self, event=None):
		self._wcsSet(None,None,"0")

	#----------------------------------------------------------------------
	def setX(self, event=None):
		if self.app.running: return
		try:
			value = float(eval(self.xwork.get(),CNC.vars,self.app.gcode.vars))
			self._wcsSet(value,None,None)
		except:
			pass

	#----------------------------------------------------------------------
	def setY(self, event=None):
		if self.app.running: return
		try:
			value = float(eval(self.ywork.get(),CNC.vars,self.app.gcode.vars))
			self._wcsSet(None,value,None)
		except:
			pass

	#----------------------------------------------------------------------
	def setZ(self, event=None):
		if self.app.running: return
		try:
			value = float(eval(self.zwork.get(),CNC.vars,self.app.gcode.vars))
			self._wcsSet(None,None,value)
		except:
			pass

	#----------------------------------------------------------------------
	def wcsSet(self, x, y, z):
		self._wcsSet(x, y, z)

	#----------------------------------------------------------------------
	def _wcsSet(self, x, y, z):
		global wcsvar
		p = wcsvar.get()
		if p<6:
			cmd = "G10L20P%d"%(p+1)
		elif p==6:
			cmd = "G28.1"
		elif p==7:
			cmd = "G30.1"
		elif p==8:
			cmd = "G92"

		pos = ""
		if x is not None: pos += "X"+str(x)
		if y is not None: pos += "Y"+str(y)
		if z is not None: pos += "Z"+str(z)
		cmd += pos
		self.sendGCode(cmd)
		self.sendGCode("$#")
		self.event_generate("<<Status>>",
			data=(_("Set workspace %s to %s")%(WCS[p],pos)))
		self.event_generate("<<CanvasFocus>>")

	#----------------------------------------------------------------------
	def showState(self):
		err = CNC.vars["errline"]
		if err:
			msg  = _("Last error: %s\n")%(CNC.vars["errline"])
		else:
			msg = ""

		state = CNC.vars["state"]
		msg += Sender.ERROR_CODES.get(state,
				_("No info available.\nPlease contact the author."))
		tkMessageBox.showinfo(_("State: %s")%(state), msg, parent=self)

#===============================================================================
# ControlFrame
#===============================================================================
class ControlFrame(CNCRibbon.PageLabelFrame):
	def __init__(self, master, app):
		super().__init__(master, "Control", app)

		row,col = 0,0
		tk.Label(self, text=_("Z")).grid(row=row, column=col)

		col += 3
		tk.Label(self, text=_("Y")).grid(row=row, column=col)

		# ---
		row += 1
		col = 0

		width=3
		height=2

		b = tk.Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
					command=self.moveZup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move +Z"))
		self.addWidget(b)

		col += 2
		b = tk.Button(self, text=Unicode.UPPER_LEFT_TRIANGLE,
					command=self.moveXdownYup,
					width=width, height=height,
					activebackground="LightYellow")

		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move -X +Y"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=Unicode.BLACK_UP_POINTING_TRIANGLE,
					command=self.moveYup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move +Y"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=Unicode.UPPER_RIGHT_TRIANGLE,
					command=self.moveXupYup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move +X +Y"))
		self.addWidget(b)

		col += 2
		b = tk.Button(self, text=u"\u00D710",
				command=self.mulStep,
				width=3,
				padx=1, pady=1)
		b.grid(row=row, column=col, sticky=tk.EW+tk.S)
		tkExtra.Balloon.set(b, _("Multiply step by 10"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=_("+"),
				command=self.incStep,
				width=3,
				padx=1, pady=1)
		b.grid(row=row, column=col, sticky=tk.EW+tk.S)
		tkExtra.Balloon.set(b, _("Increase step by 1 unit"))
		self.addWidget(b)

		# ---
		row += 1

		col = 1
		tk.Label(self, text=_("X"), width=3, anchor=tk.E).grid(row=row, column=col, sticky=tk.E)

		col += 1
		b = tk.Button(self, text=Unicode.BLACK_LEFT_POINTING_TRIANGLE,
					command=self.moveXdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move -X"))
		self.addWidget(b)

		col += 1
		b = Utils.UserButton(self, self.app, 0, text=Unicode.LARGE_CIRCLE,
					command=self.go2origin,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move to Origin.\nUser configurable button.\nRight click to configure."))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=Unicode.BLACK_RIGHT_POINTING_TRIANGLE,
					command=self.moveXup,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move +X"))
		self.addWidget(b)

		# --
		col += 1
		tk.Label(self,"",width=2).grid(row=row,column=col)

		col += 1
		self.step = tkExtra.Combobox(self, width=6, background="White")
		self.step.grid(row=row, column=col, columnspan=2, sticky=tk.EW)
		self.step.set(Utils.config.get("Control","step"))
		self.step.fill(map(float, Utils.config.get("Control","steplist").split()))
		tkExtra.Balloon.set(self.step, _("Step for every move operation"))
		self.addWidget(self.step)

		# -- Separate zstep --
		try:
			zstep = Utils.config.get("Control","zstep")
			self.zstep = tkExtra.Combobox(self, width=4, background="White")
			self.zstep.grid(row=row, column=0, columnspan=1, sticky=tk.EW)
			self.zstep.set(zstep)
			self.zstep.fill(map(float, Utils.config.get("Control","zsteplist").split()))
			tkExtra.Balloon.set(self.zstep, _("Step for Z move operation"))
			self.addWidget(self.zstep)
		except:
			self.zstep = self.step

		# Default steppings
		try:
			self.step1 = Utils.getFloat("Control","step1")
		except:
			self.step1 = 0.1

		try:
			self.step2 = Utils.getFloat("Control","step2")
		except:
			self.step2 = 1

		try:
			self.step3 = Utils.getFloat("Control","step3")
		except:
			self.step3 = 10

		# ---
		row += 1
		col = 0

		b = tk.Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
					command=self.moveZdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move -Z"))
		self.addWidget(b)

		col += 2
		b = tk.Button(self, text=Unicode.LOWER_LEFT_TRIANGLE,
					command=self.moveXdownYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move -X -Y"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=Unicode.BLACK_DOWN_POINTING_TRIANGLE,
					command=self.moveYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move -Y"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=Unicode.LOWER_RIGHT_TRIANGLE,
					command=self.moveXupYdown,
					width=width, height=height,
					activebackground="LightYellow")
		b.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(b, _("Move +X -Y"))
		self.addWidget(b)

		col += 2
		b = tk.Button(self, text=u"\u00F710",
					command=self.divStep,
					padx=1, pady=1)
		b.grid(row=row, column=col, sticky=tk.EW+tk.N)
		tkExtra.Balloon.set(b, _("Divide step by 10"))
		self.addWidget(b)

		col += 1
		b = tk.Button(self, text=_("-"),
					command=self.decStep,
					padx=1, pady=1)
		b.grid(row=row, column=col, sticky=tk.EW+tk.N)
		tkExtra.Balloon.set(b, _("Decrease step by 1 unit"))
		self.addWidget(b)

		#self.grid_columnconfigure(6,weight=1)
		try:
#			self.grid_anchor(tk.CENTER)
			self.tk.call("grid","anchor",self,tk.CENTER)
		except tk.TclError:
			pass

	#----------------------------------------------------------------------
	def saveConfig(self):
		Utils.setFloat("Control", "step", self.step.get())
		if self.zstep is not self.step:
			Utils.setFloat("Control", "zstep", self.zstep.get())

	#----------------------------------------------------------------------
	# Jogging
	#----------------------------------------------------------------------
	def moveXup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X%s"%(self.step.get()))
		self.sendGCode("G90")

	def moveXdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X-%s"%(self.step.get()))
		self.sendGCode("G90")

	def moveYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0Y%s"%(self.step.get()))
		self.sendGCode("G90")

	def moveYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0Y-%s"%(self.step.get()))
		self.sendGCode("G90")

	def moveXdownYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X-%sY%s"%(self.step.get(),self.step.get()))
		self.sendGCode("G90")

	def moveXupYup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X%sY%s"%(self.step.get(),self.step.get()))
		self.sendGCode("G90")

	def moveXdownYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X-%sY-%s"%(self.step.get(),self.step.get()))
		self.sendGCode("G90")

	def moveXupYdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0X%sY-%s"%(self.step.get(),self.step.get()))
		self.sendGCode("G90")

	def moveZup(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0Z%s"%(self.zstep.get()))
		self.sendGCode("G90")

	def moveZdown(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.sendGCode("G91G0Z-%s"%(self.zstep.get()))
		self.sendGCode("G90")

	def go2origin(self, event=None):
		self.sendGCode("G90G0X0Y0Z0")

	#----------------------------------------------------------------------
	def setStep(self, s, zs=None):
		self.step.set("%.4g"%(s))
		if self.zstep is self.step or zs is None:
			self.event_generate("<<Status>>",
				data=_("Step: %g")%(s))
		else:
			self.zstep.set("%.4g"%(zs))
			self.event_generate("<<Status>>",
				data=_("Step: %g    Zstep:%g ")%(s,zs))

	#----------------------------------------------------------------------
	@staticmethod
	def _stepPower(step):
		try:
			step = float(step)
			if step <= 0.0: step = 1.0
		except:
			step = 1.0
		power = math.pow(10.0,math.floor(math.log10(step)))
		return round(step/power)*power, power

	#----------------------------------------------------------------------
	def incStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step+power
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step+power
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def decStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step-power
		if s<=0.0: s = step-power/10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step-power
			if zs<=0.0: zs = step-power/10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def mulStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step*10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step*10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def divStep(self, event=None):
		if event is not None and not self.acceptKey(): return
		step, power = ControlFrame._stepPower(self.step.get())
		s = step/10.0
		if s<_LOWSTEP: s = _LOWSTEP
		elif s>_HIGHSTEP: s = _HIGHSTEP
		if self.zstep is not self.step:
			step, power = ControlFrame._stepPower(self.zstep.get())
			zs = step/10.0
			if zs<_LOWSTEP: zs = _LOWSTEP
			elif zs>_HIGHZSTEP: zs = _HIGHZSTEP
		else:
			zs=None
		self.setStep(s, zs)

	#----------------------------------------------------------------------
	def setStep1(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step1, self.step1)

	#----------------------------------------------------------------------
	def setStep2(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step2, self.step2)

	#----------------------------------------------------------------------
	def setStep3(self, event=None):
		if event is not None and not self.acceptKey(): return
		self.setStep(self.step3, self.step2)

#===============================================================================
# StateFrame
#===============================================================================
class StateFrame(CNCRibbon.PageExLabelFrame):
	def __init__(self, master, app):
		global wcsvar
		super().__init__(master, "State", app)
		self._gUpdate = False

		# State
		f = tk.Frame(self())
		f.pack(side=tk.TOP, fill=tk.X)

		# ===
		col,row=0,0
		f2 = tk.Frame(f)
		f2.grid(row=row, column=col, columnspan=5,sticky=tk.EW)
		for p,w in enumerate(WCS):
			col += 1
			b = tk.Radiobutton(f2, text=w,
					foreground="DarkRed",
					font = "Helvetica,14",
					padx=1, pady=1,
					variable=wcsvar,
					value=p,
					indicatoron=tk.FALSE,
					activebackground="LightYellow",
					command=self.wcsChange)
			b.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
			tkExtra.Balloon.set(b, _("Switch to workspace %s")%(w))
			self.addWidget(b)

		# Absolute or relative mode
		row += 1
		col = 0
		tk.Label(f, text=_("Distance:")).grid(row=row, column=col, sticky=tk.E)
		col += 1
		self.distance = tkExtra.Combobox(f, True,
					command=self.distanceChange,
					width=5,
					background="White")
		self.distance.fill(sorted(DISTANCE_MODE.values()))
		self.distance.grid(row=row, column=col, columnspan=2, sticky=tk.EW)
		tkExtra.Balloon.set(self.distance, _("Distance Mode [G90,G91]"))
		self.addWidget(self.distance)

		# populate gstate dictionary
		self.gstate = {}	# $G state results widget dictionary
		for k,v in DISTANCE_MODE.items():
			self.gstate[k] = (self.distance, v)

		# Units mode
		col += 2
		tk.Label(f, text=_("Units:")).grid(row=row, column=col, sticky=tk.E)
		col += 1
		self.units = tkExtra.Combobox(f, True,
					command=self.unitsChange,
					width=5,
					background="White")
		self.units.fill(sorted(UNITS.values()))
		self.units.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(self.units, _("Units [G20, G21]"))
		for k,v in UNITS.items(): self.gstate[k] = (self.units, v)
		self.addWidget(self.units)

		# Tool
		row += 1
		col = 0
		tk.Label(f, text=_("Tool:")).grid(row=row, column=col, sticky=tk.E)

		col += 1
		self.toolEntry = tkExtra.IntegerEntry(f, background="White", width=5)
		self.toolEntry.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(self.toolEntry, _("Tool number [T#]"))
		self.addWidget(self.toolEntry)

		col += 1
		b = tk.Button(f, text=_("set"),
				command=self.setTool,
				padx=1, pady=1)
		b.grid(row=row, column=col, sticky=tk.W)
		self.addWidget(b)

		# Plane
		col += 1
		tk.Label(f, text=_("Plane:")).grid(row=row, column=col, sticky=tk.E)
		col += 1
		self.plane = tkExtra.Combobox(f, True,
					command=self.planeChange,
					width=5,
					background="White")
		self.plane.fill(sorted(PLANE.values()))
		self.plane.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(self.plane, _("Plane [G17,G18,G19]"))
		self.addWidget(self.plane)

		for k,v in PLANE.items(): self.gstate[k] = (self.plane, v)

		# Feed mode
		row += 1
		col = 0
		tk.Label(f, text=_("Feed:")).grid(row=row, column=col, sticky=tk.E)

		col += 1
		self.feedRate = tkExtra.FloatEntry(f, background="White", disabledforeground="Black", width=5)
		self.feedRate.grid(row=row, column=col, sticky=tk.EW)
		self.feedRate.bind('<Return>',   self.setFeedRate)
		self.feedRate.bind('<KP_Enter>', self.setFeedRate)
		tkExtra.Balloon.set(self.feedRate, _("Feed Rate [F#]"))
		self.addWidget(self.feedRate)

		col += 1
		b = tk.Button(f, text=_("set"),
				command=self.setFeedRate,
				padx=1, pady=1)
		b.grid(row=row, column=col, columnspan=2, sticky=tk.W)
		self.addWidget(b)

		col += 1
		tk.Label(f, text=_("Mode:")).grid(row=row, column=col, sticky=tk.E)

		col += 1
		self.feedMode = tkExtra.Combobox(f, True,
					command=self.feedModeChange,
					width=5,
					background="White")
		self.feedMode.fill(sorted(FEED_MODE.values()))
		self.feedMode.grid(row=row, column=col, sticky=tk.EW)
		tkExtra.Balloon.set(self.feedMode, _("Feed Mode [G93, G94, G95]"))
		for k,v in FEED_MODE.items(): self.gstate[k] = (self.feedMode, v)
		self.addWidget(self.feedMode)

		# ---
		f.grid_columnconfigure(1, weight=1)
		f.grid_columnconfigure(4, weight=1)

		# Spindle
		f = tk.Frame(self())
		f.pack(side=tk.BOTTOM, fill=tk.X)

		self.override = tk.IntVar()
		self.override.set(100)
		self.spindle = tk.BooleanVar()
		self.spindleSpeed = tk.IntVar()

		col,row=0,0
		self.overrideCombo = tkExtra.Combobox(f, width=8, command=self.overrideComboChange)
		self.overrideCombo.fill(OVERRIDES)
		self.overrideCombo.grid(row=row, column=col, pady=0, sticky=tk.EW)
		tkExtra.Balloon.set(self.overrideCombo, _("Select override type."))

		b = tk.Button(f, text=_("Reset"), pady=0, command=self.resetOverride)
		b.grid(row=row+1, column=col, pady=0, sticky=tk.NSEW)
		tkExtra.Balloon.set(b, _("Reset override to 100%"))

		col += 1
		self.overrideScale = tk.Scale(f,
				command=self.overrideChange,
				variable=self.override,
				showvalue=True,
				orient=tk.HORIZONTAL,
				from_=25,
				to_=200,
				resolution=1)
		self.overrideScale.bind("<Double-1>", self.resetOverride)
		self.overrideScale.bind("<Button-3>", self.resetOverride)
		self.overrideScale.grid(row=row, column=col, rowspan=2, columnspan=4, sticky=tk.EW)
		tkExtra.Balloon.set(self.overrideScale,
			_("Set Feed/Rapid/Spindle Override. Right or Double click to reset."))

		self.overrideCombo.set(OVERRIDES[0])

		# ---
		row += 2
		col = 0
		b = tk.Checkbutton(f, text=_("Spindle"),
				image=Utils.icons["spinningtop"],
				command=self.spindleControl,
				compound=tk.LEFT,
				indicatoron=False,
				variable=self.spindle,
				padx=1,
				pady=0)
		tkExtra.Balloon.set(b, _("Start/Stop spindle (M3/M5)"))
		b.grid(row=row, column=col, pady=0, sticky=tk.NSEW)
		self.addWidget(b)

		col += 1
		b = tk.Scale(f,	variable=self.spindleSpeed,
				command=self.spindleControl,
				showvalue=True,
				orient=tk.HORIZONTAL,
				from_=Utils.config.get("CNC","spindlemin"),
				to_=Utils.config.get("CNC","spindlemax"))
		tkExtra.Balloon.set(b, _("Set spindle RPM"))
		b.grid(row=row, column=col, sticky=tk.EW, columnspan=3)
		self.addWidget(b)

		f.grid_columnconfigure(1, weight=1)

		# Coolant control

		self.coolant = tk.BooleanVar()
		self.mist = tk.BooleanVar()
		self.flood = tk.BooleanVar()


		row += 1
		col = 0
		tk.Label(f, text=_("Coolant:")).grid(row=row, column=col, sticky=tk.E)
		col += 1

		coolantDisable = tk.Checkbutton(f, text=_("OFF"),
				command=self.coolantOff,
				indicatoron=False,
				variable=self.coolant,
				padx=1,
				pady=0)
		tkExtra.Balloon.set(coolantDisable, _("Stop cooling (M9)"))
		coolantDisable.grid(row=row, column=col, pady=0, sticky=tk.NSEW)
		self.addWidget(coolantDisable)

		col += 1
		floodEnable = tk.Checkbutton(f, text=_("Flood"),
				command=self.coolantFlood,
				indicatoron=False,
				variable=self.flood,
				padx=1,
				pady=0)
		tkExtra.Balloon.set(floodEnable, _("Start flood (M8)"))
		floodEnable.grid(row=row, column=col, pady=0, sticky=tk.NSEW)
		self.addWidget(floodEnable)

		col += 1
		mistEnable = tk.Checkbutton(f, text=_("Mist"),
				command=self.coolantMist,
				indicatoron=False,
				variable=self.mist,
				padx=1,
				pady=0)
		tkExtra.Balloon.set(mistEnable, _("Start mist (M7)"))
		mistEnable.grid(row=row, column=col, pady=0, sticky=tk.NSEW)
		self.addWidget(mistEnable)
		f.grid_columnconfigure(1, weight=1)

	#----------------------------------------------------------------------
	def overrideChange(self, event=None):
		n = self.overrideCombo.get()
		c = self.override.get()
		CNC.vars["_Ov"+n] = c
		CNC.vars["_OvChanged"] = True

	#----------------------------------------------------------------------
	def resetOverride(self, event=None):
		self.override.set(100)
		self.overrideChange()

	#----------------------------------------------------------------------
	def overrideComboChange(self):
		n = self.overrideCombo.get()
		if n=="Rapid":
			self.overrideScale.config(to_=100, resolution=25)
		else:
			self.overrideScale.config(to_=200, resolution=1)
		self.override.set(CNC.vars["_Ov"+n])

	#----------------------------------------------------------------------
	def _gChange(self, value, dictionary):
		for k,v in dictionary.items():
			if v==value:
				self.sendGCode(k)
				return

	#----------------------------------------------------------------------
	def distanceChange(self):
		if self._gUpdate: return
		self._gChange(self.distance.get(), DISTANCE_MODE)

	#----------------------------------------------------------------------
	def unitsChange(self):
		if self._gUpdate: return
		self._gChange(self.units.get(), UNITS)

	#----------------------------------------------------------------------
	def feedModeChange(self):
		if self._gUpdate: return
		self._gChange(self.feedMode.get(), FEED_MODE)

	#----------------------------------------------------------------------
	def planeChange(self):
		if self._gUpdate: return
		self._gChange(self.plane.get(), PLANE)

	#----------------------------------------------------------------------
	def setFeedRate(self, event=None):
		if self._gUpdate: return
		try:
			feed = float(self.feedRate.get())
			self.sendGCode("F%g"%(feed))
			self.event_generate("<<CanvasFocus>>")
		except ValueError:
			pass

	#----------------------------------------------------------------------
	def setTool(self, event=None):
		pass

	#----------------------------------------------------------------------
	def spindleControl(self, event=None):
		if self._gUpdate: return
		# Avoid sending commands before unlocking
		if CNC.vars["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED): return
		if self.spindle.get():
			self.sendGCode("M3 S%d"%(self.spindleSpeed.get()))
		else:
			self.sendGCode("M5")

	#----------------------------------------------------------------------
	def coolantMist(self, event=None):
		if self._gUpdate: return
		# Avoid sending commands before unlocking
		if CNC.vars["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
			self.mist.set(tk.FALSE)
			return
		self.coolant.set(tk.FALSE)
		self.mist.set(tk.TRUE)
		self.sendGCode("M7")

	#----------------------------------------------------------------------
	def coolantFlood(self, event=None):
		if self._gUpdate: return
		# Avoid sending commands before unlocking
		if CNC.vars["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
			self.flood.set(tk.FALSE)
			return
		self.coolant.set(tk.FALSE)
		self.flood.set(tk.TRUE)
		self.sendGCode("M8")

	#----------------------------------------------------------------------
	def coolantOff(self, event=None):
		if self._gUpdate: return
		# Avoid sending commands before unlocking
		if CNC.vars["state"] in (Sender.CONNECTED, Sender.NOT_CONNECTED):
			self.coolant.set(tk.FALSE)
			return
		self.flood.set(tk.FALSE)
		self.mist.set(tk.FALSE)
		self.coolant.set(tk.TRUE)
		self.sendGCode("M9")

	#----------------------------------------------------------------------
	def updateG(self):
		global wcsvar
		self._gUpdate = True
		wcsvar.set(WCS.index(CNC.vars["WCS"]))
		self.feedRate.set(str(CNC.vars["feed"]))
		self.feedMode.set(FEED_MODE[CNC.vars["feedmode"]])
		self.spindle.set(CNC.vars["spindle"]=="M3")
		self.spindleSpeed.set(int(CNC.vars["rpm"]))
		self.toolEntry.set(CNC.vars["tool"])
		self.units.set(UNITS[CNC.vars["units"]])
		self.distance.set(DISTANCE_MODE[CNC.vars["distance"]])
		self.plane.set(PLANE[CNC.vars["plane"]])

		self._gUpdate = False

	#----------------------------------------------------------------------
	def updateFeed(self):
		if self.feedRate.cget("state") == tk.DISABLED:
			self.feedRate.config(state=tk.NORMAL)
			self.feedRate.delete(0,tk.END)
			self.feedRate.insert(0, CNC.vars["curfeed"])
			self.feedRate.config(state=tk.DISABLED)

	#----------------------------------------------------------------------
	def wcsChange(self):
		global wcsvar
		self.sendGCode(WCS[wcsvar.get()])
		self.app.viewState()
		#self.sendGCode("$G")

#===============================================================================
# Control Page
#===============================================================================
class ControlPage(CNCRibbon.Page):
	__doc__ = _("CNC communication and control")
	_name_  = N_("Control")
	_icon_  = "control"

	#----------------------------------------------------------------------
	# Add a widget in the widgets list to enable disable during the run
	#----------------------------------------------------------------------
	def register(self):
		global wcsvar
		wcsvar = tk.IntVar()
		wcsvar.set(0)

		self._register((ConnectionGroup, UserGroup, RunGroup),
			(DROFrame, ControlFrame, StateFrame))
