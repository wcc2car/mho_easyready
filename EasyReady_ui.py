#!/usr/bin/python3
"""
W.C.C.

.

UI source file: EasyReady.ui
"""
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.pathchooserinput import PathChooserButton


def safe_i18n_translator(value):
    """i18n - Setup translator in derived class file"""
    return value


def safe_fo_callback(widget):
    """on first objec callback - Setup callback in derived class file."""
    pass


def safe_image_loader(master, image_name: str):
    """Image loader - Setup image_loader in derived class file."""
    img = None
    try:
        img = tk.PhotoImage(file=image_name, master=master)
    except tk.TclError:
        pass
    return img


class AppUIUI:
    def __init__(
        self,
        master=None,
        *,
        translator=None,
        on_first_object_cb=None,
        data_pool=None,
        image_loader=None
    ):
        if translator is None:
            translator = safe_i18n_translator
        _ = translator  # i18n string marker.
        if image_loader is None:
            image_loader = safe_image_loader
        if on_first_object_cb is None:
            on_first_object_cb = safe_fo_callback
        # build ui
        self.tk01 = tk.Tk(master)
        self.tk01.configure(height=700, width=1024)
        # First object created
        on_first_object_cb(self.tk01)

        self.frame_lu = ttk.Labelframe(self.tk01, name="frame_lu")
        self.frame_lu.configure(
            height=140,
            takefocus=True,
            text=_('TITLE_MENU'),
            width=380)
        self.radio_bt1 = ttk.Radiobutton(self.frame_lu, name="radio_bt1")
        self.v_selected = tk.StringVar(value=_('online'))
        self.radio_bt1.configure(
            takefocus=True,
            text=_('RB_ONLINE'),
            value="online",
            variable=self.v_selected)
        self.radio_bt1.grid(column=0, padx="30 0", pady=6, row=0, sticky="w")
        self.radio_bt1.configure(command=self.check_mode)
        self.radio_bt2 = ttk.Radiobutton(self.frame_lu, name="radio_bt2")
        self.radio_bt2.configure(
            takefocus=True,
            text=_('RB_OFFLINE'),
            value="offline",
            variable=self.v_selected)
        self.radio_bt2.grid(column=0, padx="30 0", pady=6, row=1, sticky="w")
        self.radio_bt2.configure(command=self.check_mode)
        self.radio_bt3 = ttk.Radiobutton(self.frame_lu, name="radio_bt3")
        self.radio_bt3.configure(
            takefocus=True,
            text=_('RB_LAN_SERVER'),
            value="lanhost",
            variable=self.v_selected)
        self.radio_bt3.grid(column=0, padx="30 0", pady=6, row=2, sticky="w")
        self.radio_bt3.configure(command=self.check_mode)
        self.cbox_lang = ttk.Combobox(self.frame_lu, name="cbox_lang")
        self.lang_var = tk.StringVar()
        self.cbox_lang.configure(
            state="readonly",
            takefocus=True,
            textvariable=self.lang_var,
            values='MENU_ZH_TW MENU_EN_US',
            width=12)
        self.cbox_lang.grid(column=1, row=0, sticky="e")
        self.button_1 = ttk.Button(self.frame_lu, name="button_1")
        self.button_1.configure(takefocus=True, text=_('BTN_GO'), width=12)
        self.button_1.grid(column=1, row=2, sticky="e")
        self.button_1.configure(command=self.on_go_clicked)
        self.frame_lu.grid(column=0, row=0, sticky="nw")
        self.frame_lu.grid_propagate(0)
        self.frame_lu.grid_anchor("w")
        self.frame_lu.rowconfigure(3, weight=1)
        self.frame_lu.columnconfigure(0, weight=1)
        self.frame_ld = ttk.Labelframe(self.tk01, name="frame_ld")
        self.frame_ld.configure(height=560, text=_('TITLE_STEP'), width=380)
        self.frame_a1 = ttk.Frame(self.frame_ld, name="frame_a1")
        self.frame_a1.configure(height=67, width=380)
        self.lab_icon_a1 = ttk.Label(self.frame_a1, name="lab_icon_a1")
        self.img_null_30 = image_loader(self.tk01, "null_30.png")
        self.lab_icon_a1.configure(image=self.img_null_30)
        self.lab_icon_a1.grid(column=0, row=0, rowspan=2, sticky="w")
        self.lab_txt_a1 = ttk.Label(self.frame_a1, name="lab_txt_a1")
        self.lab_txt_a1.configure(text=_('LAB_A1'))
        self.lab_txt_a1.grid(column=1, row=0, rowspan=2, sticky="w")
        self.path_btn_a1 = PathChooserButton(self.frame_a1, name="path_btn_a1")
        self.path_btn_a1.configure(
            mustexist=True,
            path="path_var",
            takefocus=True,
            text=_('PATH_BTN'),
            type="directory",
            width=9)
        self.path_btn_a1.grid(column=2, row=0, sticky="e")
        self.btn_a1 = ttk.Button(self.frame_a1, name="btn_a1")
        self.btn_a1.configure(takefocus=True, text=_('BTN_NEXT'), width=9)
        self.btn_a1.grid(column=2, row=1, sticky="e")
        self.btn_a1.configure(command=self.on_a1_clicked)
        self.frame_a1.grid(sticky="ew")
        self.frame_a1.grid_propagate(0)
        self.frame_a1.columnconfigure(1, weight=1)
        self.frame_a2 = ttk.Frame(self.frame_ld, name="frame_a2")
        self.frame_a2.configure(height=67, width=380)
        self.lab_icon_a2 = ttk.Label(self.frame_a2, name="lab_icon_a2")
        self.lab_icon_a2.configure(image=self.img_null_30)
        self.lab_icon_a2.grid(column=0, row=0, sticky="w")
        self.lab_txt_a2 = ttk.Label(self.frame_a2, name="lab_txt_a2")
        self.lab_txt_a2.configure(text=_('LAB_A2'))
        self.lab_txt_a2.grid(column=1, row=0, sticky="w")
        self.btn_a2 = ttk.Button(self.frame_a2, name="btn_a2")
        self.btn_a2.configure(takefocus=True, text=_('BTN_NEXT'), width=9)
        self.btn_a2.grid(column=2, row=0, sticky="e")
        self.btn_a2.configure(command=self.on_a2_clicked)
        self.frame_a2.grid(row=1, sticky="ew")
        self.frame_a2.grid_propagate(0)
        self.frame_a2.grid_anchor("w")
        self.frame_a2.columnconfigure(1, weight=1)
        self.frame_a3 = ttk.Frame(self.frame_ld, name="frame_a3")
        self.frame_a3.configure(height=67, width=380)
        self.lab_icon_a3 = ttk.Label(self.frame_a3, name="lab_icon_a3")
        self.lab_icon_a3.configure(image=self.img_null_30)
        self.lab_icon_a3.grid(column=0, row=0, sticky="w")
        self.lab_txt_a3 = ttk.Label(self.frame_a3, name="lab_txt_a3")
        self.lab_txt_a3.configure(text=_('LAB_A3'))
        self.lab_txt_a3.grid(column=1, row=0, sticky="w")
        self.frame_a3.grid(row=2, sticky="ew")
        self.frame_a3.grid_propagate(0)
        self.frame_a3.grid_anchor("w")
        self.frame_a3.columnconfigure(1, weight=1)
        self.frame_b1 = ttk.Frame(self.frame_ld, name="frame_b1")
        self.frame_b1.configure(height=67, width=380)
        self.lab_icon_b1 = ttk.Label(self.frame_b1, name="lab_icon_b1")
        self.lab_icon_b1.configure(image=self.img_null_30)
        self.lab_icon_b1.grid(column=0, row=0, sticky="w")
        self.lab_txt_b1 = ttk.Label(self.frame_b1, name="lab_txt_b1")
        self.lab_txt_b1.configure(text=_('LAB_B1'))
        self.lab_txt_b1.grid(column=1, row=0, sticky="w")
        self.btn_b1 = ttk.Button(self.frame_b1, name="btn_b1")
        self.btn_b1.configure(takefocus=True, text=_('BTN_NEXT'), width=9)
        self.btn_b1.grid(column=2, row=0, sticky="e")
        self.btn_b1.configure(command=self.on_b1_clicked)
        self.frame_b1.grid(row=3, sticky="ew")
        self.frame_b1.grid_propagate(0)
        self.frame_b1.grid_anchor("w")
        self.frame_b1.columnconfigure(1, weight=1)
        self.frame_b2 = ttk.Frame(self.frame_ld, name="frame_b2")
        self.frame_b2.configure(height=67, width=380)
        self.lab_icon_b2 = ttk.Label(self.frame_b2, name="lab_icon_b2")
        self.lab_icon_b2.configure(image=self.img_null_30)
        self.lab_icon_b2.grid(column=0, row=0, rowspan=2, sticky="w")
        self.lab_txt_b2 = ttk.Label(self.frame_b2, name="lab_txt_b2")
        self.lab_txt_b2.configure(text=_('LAB_B2'))
        self.lab_txt_b2.grid(column=1, row=0, rowspan=2, sticky="w")
        self.btn_b2_re = ttk.Button(self.frame_b2, name="btn_b2_re")
        self.btn_b2_re.configure(takefocus=True, text=_('BTN_RE'), width=9)
        self.btn_b2_re.grid(column=2, row=0, sticky="e")
        self.btn_b2_re.configure(command=self.on_b2_re_clicked)
        self.btn_b2 = ttk.Button(self.frame_b2, name="btn_b2")
        self.btn_b2.configure(takefocus=True, text=_('BTN_NEXT'), width=9)
        self.btn_b2.grid(column=2, row=1, sticky="e")
        self.btn_b2.configure(command=self.on_b2_clicked)
        self.frame_b2.grid(row=4, sticky="ew")
        self.frame_b2.grid_propagate(0)
        self.frame_b2.grid_anchor("w")
        self.frame_b2.columnconfigure(1, weight=1)
        self.frame_b3 = ttk.Frame(self.frame_ld, name="frame_b3")
        self.frame_b3.configure(height=67, width=380)
        self.lab_icon_b3 = ttk.Label(self.frame_b3, name="lab_icon_b3")
        self.lab_icon_b3.configure(image=self.img_null_30)
        self.lab_icon_b3.grid(column=0, row=0, sticky="w")
        self.lab_txt_b3 = ttk.Label(self.frame_b3, name="lab_txt_b3")
        self.lab_txt_b3.configure(text=_('LAB_B3'))
        self.lab_txt_b3.grid(column=1, row=0, sticky="w")
        self.frame_b3.grid(row=5, sticky="ew")
        self.frame_b3.grid_propagate(0)
        self.frame_b3.grid_anchor("w")
        self.frame_b3.columnconfigure(1, weight=1)
        self.frame_c1 = ttk.Frame(self.frame_ld, name="frame_c1")
        self.frame_c1.configure(height=67, width=380)
        self.lab_icon_c1 = ttk.Label(self.frame_c1, name="lab_icon_c1")
        self.lab_icon_c1.configure(image=self.img_null_30)
        self.lab_icon_c1.grid(column=0, row=0, rowspan=2, sticky="w")
        self.lab_txt_c1 = ttk.Label(self.frame_c1, name="lab_txt_c1")
        self.lab_txt_c1.configure(text=_('LAB_C1'))
        self.lab_txt_c1.grid(column=1, row=0, rowspan=2, sticky="w")
        self.cbox_c1 = ttk.Combobox(self.frame_c1, name="cbox_c1")
        self.selected_ip = tk.StringVar()
        self.cbox_c1.configure(
            state="readonly",
            takefocus=True,
            textvariable=self.selected_ip,
            width=14)
        self.cbox_c1.grid(column=2, pady="0 1", row=0, sticky="e")
        self.btn_c1 = ttk.Button(self.frame_c1, name="btn_c1")
        self.btn_c1.configure(takefocus=True, text=_('BTN_NEXT'), width=9)
        self.btn_c1.grid(column=2, row=1, sticky="e")
        self.btn_c1.configure(command=self.on_c1_clicked)
        self.frame_c1.grid(row=6, sticky="ew")
        self.frame_c1.grid_propagate(0)
        self.frame_c1.grid_anchor("w")
        self.frame_c1.columnconfigure(1, weight=1)
        self.frame_c2 = ttk.Frame(self.frame_ld, name="frame_c2")
        self.frame_c2.configure(height=67, width=380)
        self.lab_icon_c2 = ttk.Label(self.frame_c2, name="lab_icon_c2")
        self.lab_icon_c2.configure(image=self.img_null_30)
        self.lab_icon_c2.grid(column=0, row=0, sticky="w")
        self.lab_txt_c2 = ttk.Label(self.frame_c2, name="lab_txt_c2")
        self.lab_txt_c2.configure(text=_('LAB_C2'))
        self.lab_txt_c2.grid(column=1, row=0, sticky="w")
        self.frame_c2.grid(row=7, sticky="ew")
        self.frame_c2.grid_propagate(0)
        self.frame_c2.grid_anchor("w")
        self.frame_c2.columnconfigure(1, weight=1)
        self.frame_ld.grid(column=0, row=1, sticky="nw")
        self.frame_ld.grid_anchor("nw")
        self.frame_r = ttk.Labelframe(self.tk01, name="frame_r")
        self.frame_r.configure(height=700, text=_('TITLE_NOTE'), width=640)
        self.text_r = tk.Text(self.frame_r, name="text_r")
        self.text_r.configure(height=24, padx=6, pady=6, width=63)
        self.text_r.grid(column=0, row=0, sticky="nsew")
        self.scrollbar_1 = ttk.Scrollbar(self.frame_r, name="scrollbar_1")
        self.scrollbar_1.configure(orient="vertical")
        self.scrollbar_1.grid(column=1, row=0, sticky="nsew")
        self.frame_r.grid(column=1, row=0, rowspan=2, sticky="nsew")
        self.frame_r.grid_propagate(0)
        self.frame_r.rowconfigure(0, weight=1)
        self.frame_r.columnconfigure(0, weight=1)
        self.tk01.rowconfigure(1, minsize=560, weight=1)
        self.tk01.columnconfigure(1, weight=1)

        # Main widget
        self.mainwindow = self.tk01

    def run(self):
        self.mainwindow.mainloop()

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
    app = AppUIUI()
    app.run()
