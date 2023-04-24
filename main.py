#!/usr/bin/python3

from tkinter import Tk, filedialog, END
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askokcancel, showwarning

import re
import webbrowser
import os
import logging
import requests

logging.basicConfig(level=logging.INFO)

class App(Tk):

    "The wizard html editor app."

    def __init__(self):

        "Initialize the app."

        super().__init__()

        self.geometry("750x500")
        self.title("Wizard HTML Editor")

        self.font = ("Liberation Mono", 9)
        self.bold_font = ("Liberation Mono", 9, "bold")

        self.read_only = False

        self.inside_script_tag = False
        self.inside_style_tag = False

        self.editor = ScrolledText(self, undo=True)
        self.editor.pack(fill="both", expand=True)

        self.editor.config(tabs=16)

        self.editor.config(font=("Liberation Mono", 9))

        self.editor.tag_configure("tag", foreground="DarkBlue", font=self.bold_font)
        self.editor.tag_configure("doctype", foreground="Blue3", font=self.bold_font)
        self.editor.tag_configure("comment", foreground="Gray64", font=self.font)

        self.editor.tag_configure("str", foreground="Green", font=self.bold_font)

        self.editor.tag_configure("sel", background="Gray88")

        self.editor.bind("<KeyPress>", self.keydown)
        self.editor.bind("<<Modified>>", self.highlight)
        self.editor.bind("<F5>", self.run)
        self.editor.bind("<Control-s>", self.save)
        self.editor.bind("<Control-o>", self.load_file)

        self.unclosed = []

        self.path = None
        self.saved = False

    def highlight(self, _):

        "Highlight all code in the editor."

        self.inside_script_tag = False
        self.inside_style_tag = False

        self.saved = False

        for tag in self.editor.tag_names():
            self.editor.tag_remove(tag, 1.0, END)

        index = [1, 0]

        text = self.editor.get(1.0, END)

        while True:
            try:
                match = re.match("<.*?>", text)
                string_match = re.match("\".*?\"|\'.*?\'", text)

                if match:
                    if not self.inside_style_tag and not self.inside_script_tag:
                        start = str(index[0]) + "." + str(index[1])
                        end = str(index[0]) + "." + str(index[1] + len(match.group(0)))

                        if re.match("<!--.*-->", text):
                            self.editor.tag_add("comment", start, end)
                        elif re.match("<!doctype.*>", text, flags=re.IGNORECASE):
                            self.editor.tag_add("doctype", start, end)
                        elif re.match("</.*>", text):
                            self.editor.tag_add("tag", start, end)
                        else:
                            self.editor.tag_add("tag", start, end)

                    start = str(index[0]) + "." + str(index[1])
                    end = str(index[0]) + "." + str(index[1] + len(match.group(0)))

                    if re.match("<style.*>", match.group(0)):
                        self.inside_style_tag = True
                    elif re.match("<script.*>", match.group(0)):
                        self.inside_script_tag = True
                    elif re.match("</script.*>", match.group(0)):
                        self.inside_script_tag = False
                        self.editor.tag_add("tag", start, end)
                    elif re.match("</style.*>", match.group(0)):
                        self.inside_style_tag = False
                        self.editor.tag_add("tag", start, end)

                    index[1] += 1
                    text = text[1:]
                elif string_match:
                    if not self.inside_style_tag and not self.inside_script_tag:
                        start = str(index[0]) + "." + str(index[1])
                        end = str(index[0]) + "." + str(index[1] + len(string_match.group(0)))

                        self.editor.tag_add("str", start, end)

                        index[1] += len(string_match.group(0))
                        text = text[len(string_match.group(0)):]
                elif text[0] == "\n":
                    index[0] += 1
                    index[1] = 0
                    text = text[1:]
                else:
                    index[1] += 1
                    text = text[1:]
            except IndexError:
                break

        self.editor.edit_modified(0)

    def run(self, _):

        "Ask to save and run the file."

        if not self.read_only:
            if not self.saved:
                if askokcancel("Run?", "To run this, you must first save the file."):
                    while not self.saved:
                        self.save(0)

                    logging.info("File saved.")
                else:
                    logging.warning("File run canceled.")

            webbrowser.open(f'file:///{self.path}')

            logging.info("File run.")
        else:
            self.show_ro_error()

    def save(self, _):

        "Save the file."

        if not self.read_only:
            logging.info("File saved.")

            filetypes = (("HTML files", "*.html"),
                ("PHP files", "*.php"),
                ("Javascript files", "*.js"),
                ("CSS files", "*.css"),
                ("Text files", "*.txt"),
            )

            home = os.environ['HOME']

            if not self.path:
                self.path = filedialog.asksaveasfile(title="Save File", initialdir=home, filetypes=filetypes).name

            try:
                file = open(self.path, "w+")
            except (OSError, IOError):
                file = open(self.path, "x+")

            file.write(self.editor.get(1.0, END))
            file.close()

            self.saved = True

        else:
            self.show_ro_error()

    def load_file_from_external_source(self, url):

        "Open a file from a website."

        self.editor.config(state="normal")

        site = url

        try:
            root.editor.insert(1.0, requests.get(site).text)

            logging.info(f"File loaded from {site}.")
        except requests.exceptions.ConnectionError:
            logging.warning("File loading failed.")

        self.editor.config(state="disabled")

        self.read_only = True

    def load_file(self, _):

        "Load a file from the user's disk."

        filetypes = (
            ("HTML files", "*.html"),
            ("PHP files", "*.php"),
            ("Javascript files", "*.js"),
            ("CSS files", "*.css"),
            ("Text files", "*.txt"),
        )

        home = os.environ['HOME']

        file = None

        while not file:
            file = filedialog.askopenfile(title="Load File", initialdir=home, filetypes=filetypes)

        self.path = file.name

        if file:
            title = "Load File"
            desc = "Are you sure you want to replace the contents of the editor?"
            if askokcancel(title, desc):
                self.editor.config(state="normal")

                logging.info("File loaded.")

                self.editor.delete(1.0, END)
                self.editor.insert(1.0, file.read())

                self.read_only = False
            else:
                logging.warning("File load canceled.")

    def keydown(self, event):

        "If it is read only, no keys can be typed."

        if not event.keysym.startswith("Control"):
            if self.read_only:
                self.show_ro_error()

    def show_ro_error(self):

        "Show warning that you cannot edit or use the document."

        logging.warning("Attempt to edit read only file blocked.")

        title = "Read Only Document"
        message = "This document is read only."

        showwarning(title, message)

root = App()

root.editor.focus_set()

root.mainloop()
