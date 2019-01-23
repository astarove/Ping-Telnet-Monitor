#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import subprocess
import re
import time

from telnetlib import Telnet
from tkinter import *
from tkinter.ttk import Frame, Style, Notebook, Treeview


class PMFileUtils:
    """docstring"""

    def __init__(self):
#        self.textfield = textfield
        pass

    def get_host(self):

        with open("hosts.json", "r") as read_file:
            data = json.load(read_file)
            for host in data:
                yield[host, data[host]]

class PMUtils:
    """docstring"""

    def __init__(self, textfield):
        self.textfield = textfield
        pass

    def ping(self, addr):
        args = ["ping", addr, "-n", "6"]
        process = subprocess.Popen(args, stdout=subprocess.PIPE)
        line = ' '
        result = "OK"
        while( line ):
            line = process.stdout.readline().decode("ascii")
            if line:
                self.textfield.insert(END, line)
                self.textfield.update()
                self.textfield.see(END)
                if re.search('\(100% loss\),', line):
                    result = "FAIL"
        return result

    def telnet(self, addr, port, timeout=5):
        result = "OK"

        try:
            Telnet(addr, port, timeout).interact()
        except ConnectionRefusedError:
            self.textfield.insert(END, "Connection error to %s:%s\n" %
                                 (addr, port))
            result = "FALSE"
        else:
            self.textfield.insert(END, "Connection established to %s:%s\n" %
                                 (addr, port))
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

    def get_data(self):
        iids = self.table.get_children()
        with( open("export.csv", "w")) as fh:
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
#        a = self.frame1.get_data()
#        pass

    def _get_telnet(self):
        for host in PMFileUtils.get_host(PMFileUtils):
            if len(host[1]):
                for port in host[1]:
                    result = self.Utils.telnet(host[0], port)
                    self.frame_log.insert(END, "============================\n")
                    self.frame_log.see(END)
                    self.frame2.add_data_telnet(host[0], port, result)
#        a = self.frame2.get_data()
#        pass

    def _menu(self):
        menubar = Menu(self.parent)
        filemenu = Menu(menubar, tearoff=0)
#        filemenu.add_command(label="Load", command=self.quit)

        filemenu.add_separator()

        filemenu.add_command(label="Export Ping to CSV",
                             command=self.frame1.get_data)
        filemenu.add_command(label="Export Telnet to CSV",
                             command=self.frame2.get_data)

        filemenu.add_separator()

        filemenu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        editmenu = Menu(menubar, tearoff=0)

#        editmenu.add_command(label="Properties", command=self.quit)

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


def main():
    root = Tk()
    root.geometry("650x350+300+300")
    app = PMGUI(root)
    util = PMUtils(app.get_textfield())

    root.mainloop()

if __name__ == '__main__':
    main()