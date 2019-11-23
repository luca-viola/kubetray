#!/usr/bin/env python3
import os
import sys
import wx
import wx.adv
from functools import partial
from kubernetes import client, config
from kubernetes.client import configuration
import urllib3

urllib3.disable_warnings()

PATH = os.path.dirname(os.path.realpath(__file__))
ICON = PATH+'/icon.png'
VERSION = PATH+'/VERSION'

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame
        self.toggle = 0
        wx.adv.TaskBarIcon.__init__(self)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=wx.ID_EXIT)
        self.OnSetIcon(ICON)

    def OnContextSelection(self, number, event):
        global active_index

        id_selected = event.GetId()
        active_index = id_selected 
        obj = event.GetEventObject()
        context = obj.GetLabel(id_selected)
        config.load_kube_config(context=context)
        os.system("kubectl config use-context "+context+" >/dev/null")

    def CreatePopupMenu(self):
        global context_names,active_index

        contexts, active_context = config.list_kube_config_contexts()
        if not contexts:
          print("Cannot find any context in kube-config file.")
          sys.exit(-1)
        context_names = [context['name'] for context in contexts]
        active_index = context_names.index(active_context['name'])
        
        menu = wx.Menu()
        index = 0
        for name in context_names:
            item=menu.AppendRadioItem(index,name)
            menu.Bind(wx.EVT_MENU, partial(self.OnContextSelection, index), item)
            index = index + 1
        menu.AppendSeparator()
        aboutm = wx.MenuItem(menu, wx.ID_ABOUT, 'About..')
        menu.Bind(wx.EVT_MENU, self.OnAbout, id=aboutm.GetId())
        menu.Append(aboutm)

        menu.AppendSeparator()
        quitm = wx.MenuItem(menu, wx.ID_EXIT, 'Quit')
        menu.Bind(wx.EVT_MENU, self.OnQuit, id=quitm.GetId())
        menu.Append(quitm)
        menu.Check(active_index,True)
        return menu

    def OnAbout(self,event):
        info = wx.adv.AboutDialogInfo()

        description = "Kubetray is a Desktop Gui utility to change k8s contexts"
        licence = """
Kubetray is distributed under the terms of GPL V3.

Please refer to the page below to get a copy of the licence.

https://www.gnu.org/licenses/gpl-3.0.en.html"""
        with open(VERSION, 'r') as version_file:
            version = version_file.read()
        info.SetIcon(wx.Icon(ICON, wx.BITMAP_TYPE_PNG))
        info.SetName('Kubetray')
        info.SetVersion(version)
        info.SetDescription(description)
        info.SetCopyright('(C) 2019 Luca Viola')
        info.SetWebSite('https://github.com/luca-viola/kubetray')
        info.SetLicence(licence)
        info.AddDeveloper('Luca Viola')
        info.AddDocWriter('Luca Viola')
        info.AddArtist('3AM')
        info.AddTranslator('Luca Viola')
        wx.adv.AboutBox(info)

    def OnSetIcon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, path)

    def OnQuit(self, event):
        self.RemoveIcon()
        wx.CallAfter(self.Destroy)
        self.frame.Close()

def nohup(func):
  try:
    pid = os.fork()
    if pid > 0:
      return
  except OSError as e:
    sys.stderr.write("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
    sys.exit(1)

  os.setsid()

  try:
    pid = os.fork()
    if pid > 0:
      sys.exit(0)
  except OSError as e:
    sys.stderr.write("fork #2 failed: %d (%s)" % (e.errno, e.strerror))
    sys.exit(1)

  func()

  os._exit(os.EX_OK)

def main():
    app = wx.App()
    frame=wx.Frame(None)
    TaskBarIcon(frame)
    app.MainLoop()

if __name__ == '__main__':
    nohup(main)
