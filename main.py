#!/usr/bin/python3

from tkinter import Tk, END
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askokcancel
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
        self.inside_script_tag = False
        self.inside_style_tag = False
        self.editor = ScrolledText(self, undo=True)
        self.editor.pack(fill="both", expand=True)
        self.editor.config(font=("Liberation Mono", 9))
        self.editor.tag_configure("tag", foreground="DarkBlue", font=self.bold_font)
        self.editor.tag_configure("doctype", foreground="Blue2", font=self.bold_font)
        self.editor.tag_configure("comment", foreground="Gray64", font=self.font)
        self.editor.tag_configure("sel", background="Gray98")
        self.editor.bind("<<Modified>>", self.highlight)
        self.editor.bind("<F5>", self.run)
        self.editor.bind("<Control-s>", self.save)
        self.unclosed = []
        self.file_name = "index.html"

    def highlight(self, _):
        "Highlight all code in the editor."
        self.inside_script_tag = False
        self.inside_style_tag = False
        for tag in self.editor.tag_names():
            self.editor.tag_remove(tag, 1.0, END)
        index = [1, 0]
        text = self.editor.get(1.0, END)
        while True:
            try:
                match = re.match("<.*?>", text)
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
                    index[1] += len(match.group(0))
                    text = text[len(match.group(0)):]
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
        if askokcancel("Run?", "To run this, you must first save the file."):
            logging.info("File saved.")
            folder = os.environ['HOME']
            try:
                file = open(f"{folder}/{self.file_name}", "w+")
            except (OSError, IOError):
                file = open(f"{folder}/{self.file_name}", "x+")
            file.write(self.editor.get(1.0, END))
            file.close()
            logging.info("File run.")
            webbrowser.open(f'file:///{folder}/{self.file_name}')
        else:
            logging.warning("File run canceled.")

    def save(self, _):
        "Save the file."
        logging.info("File saved.")
        folder = os.environ['HOME']
        try:
            file = open(f"{folder}/{self.file_name}", "w+")
        except (OSError, IOError):
            file = open(f"{folder}/{self.file_name}", "x+")
        file.write(self.editor.get(1.0, END))
        file.close()

root = App()
try:
    root.editor.insert(1.0, requests.get("https://example.com").text)
    logging.info("File loaded from external source.")
except requests.exceptions.ConnectionError:
    logging.warning("File loading failed.")
root.editor.focus_set()
root.mainloop()
