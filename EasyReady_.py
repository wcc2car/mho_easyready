#!/usr/bin/python3
"""
W.C.C.

.

UI source file: EasyReady.ui
"""
import tkinter as tk
import tkinter.ttk as ttk
import EasyReady_ui as baseui


class AppUI(baseui.AppUIUI):
    def __init__(self, master=None):
        super().__init__(master)

    def check_mode(self):
        pass

    def on_go_clicked(self):
        pass

    def on_a1_clicked(self):
        pass

    def on_a2_clicked(self):
        pass

    def on_b1_clicked(self):
        pass

    def on_b2_re_clicked(self):
        pass

    def on_b2_clicked(self):
        pass

    def on_c1_clicked(self):
        pass


if __name__ == "__main__":
    app = AppUI()
    app.run()
