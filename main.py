#!/usr/bin/python
# -*- coding:utf-8 -*-

import argparse
import json
import os
import subprocess
import sys
import re
import time


from telnetlib import Telnet
from threading import Timer
from tkinter import *
from tkinter.ttk import Frame, Style, Notebook, Treeview


class PMFileUtils:
    """docstring"""

    def __init__(self):
        pass

    def get_host(self):

        with open("hosts.json", "r") as read_file:
            data = json.load(read_file)
            for host in data:
                yield[host, data[host]]


class PMUtils:
    """docstring"""

    def __init__(self, textfield, cmd=False):
        self.textfield = textfield
        self.cmd = cmd
        pass

    def ping(self, addr):
        args = ["ping", addr, "-n", "6"]
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        line = ' '
        result = "FAIL"
        while line:
            line = process.stdout.readline().decode("cp1251")
            if line:
                if self.cmd:
                    print(line.rstrip())
                else:
                    self.textfield.insert(END, line)
                    self.textfield.update()
                    self.textfield.see(END)
                if re.search('\(\d{1,2}%\s', line) and not re.search('TTL=', line):
                    result = "OK"
        return result

    def telnet(self, addr, port, timeout=5):
        result = "OK"

        if self.cmd:
            try:
                Telnet(addr, port, timeout).interact()
            except ConnectionRefusedError:
                print("Connection error to %s:%s" % (addr, port))
                result = "FALSE"
            else:
                print("Connection established to %s:%s" % (addr, port))
                result = "OK"
            finally:
                return result
        else:
            try:
                Telnet(addr, port, timeout).interact()
            except ConnectionRefusedError:
                self.textfield.insert(END, "Connection error to %s:%s" % (addr, port))
                result = "FALSE"
            else:
                self.textfield.insert(END, "Connection established to %s:%s" % (addr, port))
                result = "OK"
            finally:
                self.textfield.update()
                return result


class Table(Frame):
    def __init__(self, parent=None, headings=tuple(), rows=tuple()):
        super().__init__(parent)

        self.table = Treeview(self, show="headings", selectmode="browse")
        self.table["columns"]=headings
        self.table["displaycolumns"]=headings

        for head in headings:
            self.table.heading(head, text=head, anchor=CENTER)
            self.table.column(head, anchor=CENTER)

        for row in rows:
            self.table.insert('', END, values=tuple(row))

        scrolltable = Scrollbar(self, command=self.table.yview)
        self.table.configure(yscrollcommand=scrolltable.set)
        scrolltable.pack(side=RIGHT, fill=Y)
        self.table.pack(expand=YES, fill=BOTH)

    def add_data_ping(self, col1, col2):
        self.table.insert('', END, values=(col1, col2))
        self.table.update()

    def add_data_telnet(self, col1, col2, col3):
        self.table.insert('', END, values=(col1, col2, col3))
        self.table.update()

    def export_data(self, auto=False):
        iids = self.table.get_children()
        access_type = "w"
        if auto:
            access_type = "a"
        with( open("export.csv", access_type)) as fh:
            for iid in iids:
                fh.write(','.join(str(i) for i in
                                  self.table.item(iid)["values"]))
                fh.write('\n')


class PMGUI(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.text = Text(self.parent)
        self.notebook = Notebook(self.parent)
        self.frame1 = Table(self.parent, headings=('Host', 'Status'), rows=())
        self.frame_log = Text(self.parent)
        self.frame_log.pack(expand=YES, fill=BOTH)
        self.frame2 = Table(self.parent, headings=('Host', 'Port', 'Status'),
                            rows=())
        self.Utils = PMUtils(self.frame_log)
        self.initUI()


    def _get_ping(self):
        for host in PMFileUtils.get_host(PMFileUtils):
            result = self.Utils.ping(host[0])
            self.frame_log.insert(END, "============================\n")
            self.frame_log.see(END)
            self.frame1.add_data_ping(host[0], result)
#        a = self.frame1.export_data()
#        pass

    def _get_telnet(self):
        for host in PMFileUtils.get_host(PMFileUtils):
            if len(host[1]):
                for port in host[1]:
                    result = self.Utils.telnet(host[0], port)
                    self.frame_log.insert(END, "============================\n")
                    self.frame_log.see(END)
                    self.frame2.add_data_telnet(host[0], port, result)
#        a = self.frame2.export_data()
#        pass

    def _auto_scan(self):
        self._get_ping()
        self._get_telnet()

    def _start_timer(self):
        pass

    def _stop_timer(self):
        pass

    def _menu(self):
        menubar = Menu(self.parent)
        filemenu = Menu(menubar, tearoff=0)
#        filemenu.add_command(label="Load", command=self.quit)

        filemenu.add_separator()

        filemenu.add_command(label="Export Ping to CSV",
                             command=self.frame1.export_data)
        filemenu.add_command(label="Export Telnet to CSV",
                             command=self.frame2.export_data)

        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        editmenu = Menu(menubar, tearoff=0)

#        editmenu.add_command(label="Properties", command=self.quit)
        editmenu.add_command(label="Start autoscan", command=self._start_timer)
        editmenu.add_command(label="Stop autoscan", command=self._stop_timer)

        editmenu.add_separator()

        editmenu.add_command(label="Ping", command=self._get_ping)
        editmenu.add_command(label="Telnet", command=self._get_telnet)

        menubar.add_cascade(label="Scan...", menu=editmenu)
        helpmenu = Menu(menubar, tearoff=0)
#        helpmenu.add_command(label="Help Index", command=self.quit)
#        helpmenu.add_command(label="About...", command=self.quit)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.parent.config(menu=menubar)

    def _textBox(self):
        self.text.pack()

    def _notebook(self):
        self.notebook.pack(fill='both', expand='yes')

        self.notebook.add(self.frame1, text='Ping stat')
        self.notebook.add(self.frame2, text='Telnet stat')
        self.notebook.add(self.frame_log, text='Log')

    def get_textfield(self):
        return self.frame1

    def initUI(self):
        self.parent.title("Ping monitor")
        self.style = Style()
        self.style.theme_use("default")

        self.pack(fill=BOTH, expand=1)

        self._menu()
        self._notebook()


def _output(host, data, target, port=False):
    print(data)
    if target:
        access_type = "a"
        with(open(target, access_type)) as fh:
            if port and data in ['OK', 'FALSE']:
                fh.write('telnet, %s:%s,%s,' % (host[0], port, data))
                fh.write('\n')
            elif data in ['OK', 'FAIL']:
                    fh.write('ping, %s,%s,' % (host[0], data))
                    fh.write('\n')
    pass


def main_gui():
    root = Tk()
    root.geometry("650x350+300+300")
    app = PMGUI(root)
    PMUtils(app.get_textfield())

    root.mainloop()


def main_cli(args):
    utils = PMUtils('', True)
    hosts = PMFileUtils()
    if args.ping:
        for host in hosts.get_host():
            _output(host, utils.ping(host[0]), args.export)
    elif args.telnet:
        for host in hosts.get_host():
            if len(host[1]):
                for port in host[1]:
                    _output(host, utils.telnet(host[0], port), args.export, port)
    elif args.all:
        for host in hosts.get_host():
            _output(host, utils.ping(host[0]), args.export)
            if len(host[1]):
                for port in host[1]:
                    _output(host, utils.telnet(host[0], port), args.export, port)
    else:
        parser.print_help()
        main_gui()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='main', usage='python %(prog)s [options] <-e filename.csv> <-d S> <-r N>')

    parser.add_argument('-p', '--ping', help='Launch pinging addresses',
                        action='store_const', const=True, default=False)
    parser.add_argument('-t', '--telnet', help='Check specified ports from file',
                        action='store_const', const=True, default=False)
    parser.add_argument('-a', '--all', help='Launch both Ping and Telnet',
                        action='store_const', const=True, default=False)
    parser.add_argument('-e', '--export', help='File name to export in CSV format', default=False)
    parser.add_argument('-d', '--delay', type=int, help='Enable timer with delay, in seconds', default=False)
    parser.add_argument('-r', '--repeat', type=int, help='Repeat N launches (with timer only).'
                                                         ' If not set, repeats will be infinite (not recommended)',
                        default=False)

    args = parser.parse_args()

    if args.export:
        try:
            os.remove(args.export)
        except OSError:
            pass

    if args.delay:
        if args.repeat:
            for n in range(int(args.repeat)):
                main_cli(args)
                time.sleep(int(args.delay))
        else:
            while 1:
                main_cli(args)
                time.sleep(int(args.delay))
    else:
        main_cli(args)
