#!/usr/bin/python
# -*- coding: utf-8 -*-
'''Módulo de interface gráfica do d10r

Este módulo concentra(rá) todas as classes e funções relacionadas a GUI.
'''
#
#import Tkinter as tk
#
#class CronometroFrame(tk.Frame):
#    '''Janela que exibe o nome de uma atividade, o tempo decorrido, o saldo e
#    botões para que o usuário pause ou pare o cronometro.'''
#    def __init__(self, master=None):
#        tk.Frame.__init__(self, master)
#        self.pack()
#
#cronometro = CronometroFrame()

import Tkinter
from Tkconstants import *
tk = Tkinter.Tk()
frame = Tkinter.Frame(tk)
frame.pack(expand=1)
label = Tkinter.Label(frame, text="Hello, World")
label.pack()
button = Tkinter.Button(frame,text="Exit",command=tk.destroy)
button.pack(side=BOTTOM)
tk.mainloop()

#root = Tk()
#clock = Label(root, font=('times', 20, 'bold'), bg='green')
#clock.pack(fill=BOTH, expand=1)
#c = Cronometro(20)
#
#def tick():
#    #global time1
#    ## get the current local time from the PC
#    #time2 = time.strftime('%H:%M:%S')
#    ## if time string has changed, update it
#    #if time2 != time1:
#    #    time1 = time2
#    #    clock.config(text=time2)
#    ## calls itself every 200 milliseconds
#    ## to update the time display as needed
#    ## could use >200 ms, but display gets jerky
#    clock.config(text=c.decorrido)
#    clock.after(200, tick)
#
#c.start()
#tick()
#root.mainloop()

from Tkinter import *

class Application(Frame):
    def say_hi(self):
        print "hi there, everyone!"

    def createWidgets(self):
        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["fg"]   = "red"
        self.QUIT["command"] =  self.quit

        self.QUIT.pack({"side": "left"})

        self.hi_there = Button(self)
        self.hi_there["text"] = "Hello",
        self.hi_there["command"] = self.say_hi

        self.hi_there.pack({"side": "left"})

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.createWidgets()

root = Tk()
app = Application(master=root)
app.mainloop()
root.destroy()
