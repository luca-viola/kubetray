#!/usr/bin/env python3
import os
import sys
import signal
from kubernetes import config
import urllib3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3

urllib3.disable_warnings()

APPINDICATOR_ID = 'kubetray'
ICON_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'icon.png')
VERSION_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'VERSION')


class Kubetray:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            APPINDICATOR_ID,
            ICON_PATH,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()

        # Load kube contexts
        contexts, active_context = config.list_kube_config_contexts()
        if not contexts:
            print("No Kubernetes contexts found.")
            sys.exit(1)

        self.context_names = [ctx['name'] for ctx in contexts]
        self.active_index = self.context_names.index(active_context['name'])

        group = None
        for i, name in enumerate(self.context_names):
            item = Gtk.RadioMenuItem.new_with_label(group or [], name)
            if group is None:
                group = item.get_group()
            item.connect("toggled", self.on_context_selected, name)
            if i == self.active_index:
                item.set_active(True)
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        about_item = Gtk.MenuItem(label='About...')
        about_item.connect("activate", self.on_about)
        menu.append(about_item)

        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def on_context_selected(self, widget, context_name):
        if widget.get_active():
            config.load_kube_config(context=context_name)
            os.system(f"kubectl config use-context {context_name} >/dev/null")

    def on_about(self, _):
        version = "unknown"
        if os.path.exists(VERSION_PATH):
            with open(VERSION_PATH, 'r') as vf:
                version = vf.read().strip()

        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Kubetray - Kubernetes context switcher",
        )
        dialog.format_secondary_text(f"Version: {version}\n© 2019 Luca Viola\nGPL v3 Licensed")
        dialog.run()
        dialog.destroy()

    def quit(self, _):
        Gtk.main_quit()


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # Proper Ctrl+C handling
    Kubetray()
    Gtk.main()


if __name__ == '__main__':
    main()

