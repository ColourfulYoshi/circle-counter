import time
import sys
import os
import math
import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
import pathlib
from tkinter import font as tkfont
from tkinter import filedialog as fd
from PIL import Image, ImageTk, ImageGrab, ImageColor
from datetime import datetime
import inspect
import keyword

import configs
import config_themes
import formula
import usersettings

AREA_TYPES = ("square", "4 points", "8 points")
AREA_TYPE = 1
AREA_STATE = 0

PICKER_VALUE = None
PICKER_COLOR = (0, 0, 0)

CANVAS_MOUSE_POS = (0, 0)

usettings = usersettings.UserSettings()
usettings.load()
usettings.autosave = True

Eval = formula.Evaluator(
    {}, {
        "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
        "min": lambda *x: min(list(x)),
        "max": lambda *x: max(list(x)),
        "avg": lambda *x: sum(list(x)) / len(list(x)),
        "sum": lambda *x: sum(list(x)),
        "int": int, "float": float
    }
)
CURRENT_FORMULA = usettings.formula

try:
    colorpicker_icon = Image.open("colorpicker.png")
except FileNotFoundError:
    colorpicker_icon = Image.open(os.path.join(sys._MEIPASS, "files/colorpicker.png"))
colorpicker_icon = colorpicker_icon.convert("RGBA")
new_icon = []
for item in colorpicker_icon.get_flattened_data():
    if all([item[i] < 25 for i in range(3)]):
        new_icon.append((0, 0, 0, 0))
    else:
        new_icon.append(item)
colorpicker_icon.putdata(new_icon)
del new_icon

class MainConfig:
    def __init__(self, theme="Dark"):
        self.theme = theme

    def __getattr__(self, attr):
        theme_dict = configs.MAIN_STYLE[self.theme]
        return theme_dict.get(attr, configs.__dict__.get(attr))

    def get(self, attr):
        return self.__getattr__(attr)

    def set_theme(self, new_theme):
        theme_dict = configs.MAIN_STYLE.get(new_theme)
        if theme_dict is None:
            return False
        self.theme = new_theme
        return True

    def get_theme_array(self):
        _ = self.theme
        return config_themes.theme_order
cfgs = MainConfig(usettings.theme)

window = tk.Tk()
window.wm_geometry(f"{int(cfgs.DEFAULT_WINDOW_WIDTH)}x{int(cfgs.DEFAULT_WINDOW_HEIGHT)}")
window.title("Nine Circles")
window.config(bg=cfgs.BACKGROUND_COLOR)
window.resizable(True, True)
if getattr(sys, 'frozen', False):
    try:
        icon = tk.PhotoImage(file="icon.png")
    except tk.TclError:
        icon = tk.PhotoImage(file=os.path.join(sys._MEIPASS, "files/icon.png"))
    window.iconphoto(True, icon)
else:
    try:
        icon = tk.PhotoImage(file="icon.png")
        window.iconphoto(True, icon)
    except tk.TclError:
        print("NO ICON FOUND")

content = tk.Frame(master=window)
content.cfg = dict(bg="BACKGROUND_COLOR")
content.config(bg=cfgs.BACKGROUND_COLOR)
content.place(relwidth=1, relheight=1, height=-25, relx=0.5, rely=1, anchor="s")

topbar = tk.Frame(master=window)
topbar.cfg = dict(bg="MIDLIGHT_BACKGROUND_COLOR")
topbar.config(bg=cfgs.MIDLIGHT_BACKGROUND_COLOR)
topbar.place(relwidth=1, height=cfgs.TOPBAR_SIZE, x=0, y=0)

canvas = tk.Canvas(master=content)
canvas.cfg = dict(
    bg="CANVAS_BACKGROUND_COLOR", highlightcolor="CANVAS_HIGHLIGHT_COLOR",
    highlightthickness="CANVAS_HIGHLIGHT_THICKNESS", highlightbackground="CANVAS_HIGHLIGHT_COLOR"
)
canvas.config(
    bg=cfgs.CANVAS_BACKGROUND_COLOR, highlightcolor=cfgs.CANVAS_HIGHLIGHT_COLOR,
    highlightthickness=cfgs.CANVAS_HIGHLIGHT_THICKNESS, highlightbackground=cfgs.CANVAS_HIGHLIGHT_COLOR
)
canvas.place(relx=0, rely=0, relwidth=0.8, relheight=0.8)

TEXT_ELEMENTS = []
TEXT_RESIZE = []
PARAM_ENTRIES = []

topbar_menus = []
def add_topbar_menu(label, font, size, commands):
    relx = sum(a[0] for a in (topbar_menus or [[0]]))

    menu_btn = tk.Button(master=topbar, text=("" if font == 0 else label))
    menu_btn.base_font = font
    menu_btn.cfg = dict(
        bg="MIDLIGHT_BACKGROUND_COLOR", fg="TEXT_COLOR",
        activebackground="LIGHT_BACKGROUND_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR",
    )
    menu_btn.config(
        bg=cfgs.MIDLIGHT_BACKGROUND_COLOR, font=(cfgs.DEFAULT_FONT, font),
        fg=cfgs.TEXT_COLOR, activebackground=cfgs.LIGHT_BACKGROUND_COLOR,
        activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR,
        borderwidth=0, relief=tk.FLAT, highlightthickness=0
    )
    menu_btn.place(relx=relx, rely=0, relwidth=size, relheight=1)
    TEXT_ELEMENTS.append(menu_btn)
    TEXT_RESIZE.append(menu_btn)

    menu_frame = tk.Frame(master=window)
    menu_frame.config(background=cfgs.MIDLIGHT_BACKGROUND_COLOR)

    menu_btns = []

    def forget_placement():
        for p in topbar_menus:
            p[2].place_forget()
            p[2].placed = False

    if isinstance(commands, list):
        for cmd_label, cmd_func in commands:
            def cmd(c):
                forget_placement()
                if c is not None:
                    c()
            cmd_btn = tk.Button(master=menu_frame, text=cmd_label, command=lambda c=cmd_func: cmd(c))
            cmd_btn.base_font = (font or 10) - 1
            cmd_btn.cfg = dict(
                bg="MIDLIGHT_BACKGROUND_COLOR", fg="TEXT_COLOR",
                activebackground="LIGHT_BACKGROUND_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR",
            )
            cmd_btn.config(
                bg=cfgs.MIDLIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, font=(cfgs.DEFAULT_FONT, font - 1),
                activebackground=cfgs.LIGHT_BACKGROUND_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR,
                borderwidth=0, relief=tk.FLAT, highlightthickness=0
            )
            cmd_btn.place(x=0, y=len(menu_btns) * cfgs.TOPBAR_MENU_BUTTON_SIZE, height=cfgs.TOPBAR_MENU_BUTTON_SIZE, relwidth=1)
            TEXT_ELEMENTS.append(cmd_btn)
            TEXT_RESIZE.append(cmd_btn)
            menu_btns.append(cmd_btn)

    menu_frame.place_dict = dict(
        relx=relx, x=3, y=cfgs.TOPBAR_SIZE + 3, relwidth=0.06, width=cfgs.TOPBAR_SIZE * 2,
        height=len(menu_btns) * cfgs.TOPBAR_MENU_BUTTON_SIZE
    )
    menu_frame.placed = False

    def btn_press():
        if inspect.isfunction(commands):
            forget_placement()
            commands()
            return

        pressed = ([1 if p[2].placed else 0 for i, p in enumerate(topbar_menus)] + [1]).index(1)
        if pressed != len(topbar_menus):
            topbar_menus[pressed][2].place_forget()
            topbar_menus[pressed][2].placed = False
        own_ind = [p[2] for p in topbar_menus].index(menu_frame)
        if pressed == own_ind:
            return
        menu_frame.place(**menu_frame.place_dict)
        menu_frame.placed = True
        menu_frame.update()
        [fit_element(i) for i in menu_btns]
    menu_btn.config(command=btn_press)

    topbar_menus.append([size, menu_btn, menu_frame, menu_btns])

def invert_hex_color(hex_color):
    hex_str = hex_color.lstrip('#')
    inverted_int = int(hex_str, 16) ^ 0xFFFFFF
    return f"#{inverted_int:06x}"

def hex2rgb(hex_color):
    return ImageColor.getrgb(hex_color)
def rgb2hex(rgb):
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

def sum_rgb(rgb, s):
    return tuple(max(min(rgb[i] + s[i], 255), 0) for i in range(len(rgb)))

def valid_variable_name(string):
    return string.isidentifier() and (not keyword.iskeyword(string))

def rgb_distance(rgb1, rgb2):
    r_diff = (rgb1[0] - rgb2[0]) * 0.299
    g_diff = (rgb1[1] - rgb2[1]) * 0.587
    b_diff = (rgb1[2] - rgb2[2]) * 0.114

    return math.sqrt((r_diff ** 2) + (g_diff ** 2) + (b_diff ** 2))

def render_dot(this_canvas, center_point, size, **kwargs):
    if center_point is None:
        return
    canvas_size = [this_canvas.winfo_width(), this_canvas.winfo_height()]
    this_canvas.create_rectangle(
        max(0, center_point[0] - (size // 2)), max(0, center_point[1] - (size // 2)),
        min(canvas_size[0], center_point[0] + (size // 2)), min(canvas_size[1], center_point[1] + (size // 2)),
        fill=kwargs.get("fill") or "#ffffff", outline=kwargs.get("outline") or "#000000",
        width=kwargs.get("width") or 1, tags=tuple(kwargs.get("tags", []))
    )
def render_line(this_canvas, p1, p2, width, **kwargs):
    if p1 is None:
        return
    if p2 is None:
        return
    this_canvas.create_line(
        p1[0], p1[1], p2[0], p2[1], fill=kwargs.get("fill", "#ffffff"), width=width,
        tags=tuple(kwargs.get("tags", []))
    )
def render_text(this_canvas, pos, text, **kwargs):
    this_canvas.create_text(
        pos[0], pos[1], anchor=kwargs.get("anchor", "center"), text=text,
        fill=kwargs.get("fill") or "#ffffff", font=kwargs.get("font") or (cfgs.DEFAULT_FONT, 16),
        tags=tuple(kwargs.get("tags", []))
    )
def render_oval(this_canvas, x0, y0, x1, y1, **kwargs):
    this_canvas.create_oval(
        x0, y0, x1, y1,
        fill=kwargs.get("fill", "#000000"), outline=kwargs.get("outline", "#ffffff"),
        width=kwargs.get("width", 0), tags=tuple(kwargs.get("tags", []))
    )
def render_circle(this_canvas, center, radius, **kwargs):
    render_oval(
        this_canvas,
        center[0] - radius, center[1] - radius,
        center[0] + radius, center[1] + radius,
        **kwargs
    )

def fit_element(el):
    new_size = (el.base_font / cfgs.DEFAULT_WINDOW_HEIGHT) * window.winfo_height()
    new_size = min(new_size, el.winfo_height())
    new_size = int(new_size)
    font_object = tkfont.Font(family=cfgs.DEFAULT_FONT, size=new_size)
    text_width = font_object.measure(el["text"])
    if text_width > el.winfo_width():
        new_size /= text_width / el.winfo_width()
    el.config(font=(cfgs.DEFAULT_FONT, int(new_size)))

def rescale_text_fits():
    for el in TEXT_ELEMENTS:
        if el.__dict__.get("img"):
            new_size = int(max(min(el.winfo_height(), el.winfo_width()) - 5, 1))
            del el.img
            el.img = ImageTk.PhotoImage(el.base_img.resize((new_size, new_size)))
            el.config(image=el.img)
        else:
            new_size = (el.base_font / cfgs.DEFAULT_WINDOW_HEIGHT) * window.winfo_height()
            el.config(font=(cfgs.DEFAULT_FONT, int(new_size)))

    for el in TEXT_RESIZE:
        fit_element(el)

def button_base(btn, font, text):
    if isinstance(text, str):
        btn.base_font = font
        btn.cfg = dict(
            bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
            fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
        )
        btn.config(
            text=text, bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
            fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR, font=(cfgs.DEFAULT_FONT, btn.base_font)
        )
        TEXT_ELEMENTS.append(btn)
    else:
        btn.base_base_img = text
        btn.base_img = text.copy()
        btn.img = ImageTk.PhotoImage(text)
        btn.cfg = dict(
            bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
            fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
        )
        btn.config(
            text="", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
            fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR, image=btn.img
        )
        TEXT_ELEMENTS.append(btn)

def label_base(label, font, text):
    label.base_font = font
    label.config(text=text, fg=cfgs.TEXT_COLOR, bg=cfgs.BACKGROUND_COLOR, font=(cfgs.DEFAULT_FONT, label.base_font))
    TEXT_ELEMENTS.append(label)
    TEXT_RESIZE.append(label)

def toggle_colorpicker_offset(state, initial=None):
    if not state:
        new_offset = colorpicker_entry_elements[0].get()
        if new_offset in ["", "-"]:
            new_offset = 0
        new_offset = int(new_offset)
        for p in PARAM_ENTRIES:
            if p[1] == PICKER_VALUE:
                p[0].val_offset = new_offset
                break
        for el in colorpicker_entry_elements:
            if el is None:
                continue
            el.place_forget()
    else:
        for el in colorpicker_entry_elements:
            if el is None:
                continue
            el.place(**el.place_dict)
            el.lift()
        colorpicker_entry_elements[0].delete(0, tk.END)
        colorpicker_entry_elements[0].insert(0, str(initial))

def labeled_entry(text, font, lfont, relx, rely, relwidth, relheight, param=False, anchor="nw", picker=False, ret_all=False, master=content):
    global PARAM_ENTRIES
    picker_size = 0.03

    entry = tk.Entry(master=master)
    entry.base_font = font
    entry.config(
        bg=cfgs.LIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, highlightthickness=0,
        font=(cfgs.DEFAULT_FONT, entry.base_font)
    )
    TEXT_ELEMENTS.append(entry)
    if param:
        PARAM_ENTRIES.append([entry, param])
    entry.place_dict = dict(
        relx=relx, relwidth=relwidth - (picker_size if picker else 0), rely=rely, relheight=relheight,
        anchor=anchor
    )
    entry.place(**entry.place_dict)

    label = tk.Label(master=master)
    label.config(anchor="sw")
    label_base(label, lfont, text)
    label.place_dict = dict(
        relx=relx, relwidth=relwidth, rely=rely, relheight=relheight, anchor="sw" if "w" in anchor else "se",
        x=2, y=-1, width=-4 if "w" in anchor else 4, height=-3
    )
    label.place(**label.place_dict)

    picker_btn = None
    if picker:
        def picker_func():
            global PICKER_VALUE
            if CURRENT_IMAGE is None:
                toggle_colorpicker_offset(False)
                PICKER_VALUE = None
                set_status(level="warninfo", text=f"no image loaded to pick value")
                return
            if CURRENT_AREA is not None:
                if "select" in CURRENT_AREA:
                    toggle_colorpicker_offset(False)
                    PICKER_VALUE = None
                    set_status(level="warninfo", text=f"currently picking area. cannot use value picker")
                    return
                if None in CURRENT_AREA:
                    toggle_colorpicker_offset(False)
                    PICKER_VALUE = None
                    set_status(level="warninfo", text=f"currently picking area. cannot use value picker")
                    return
            if PICKER_VALUE is not None:
                if PICKER_VALUE == param:
                    set_status(level="info", text=f"cancelled picking for {PICKER_VALUE}")
                    toggle_colorpicker_offset(False)
                    PICKER_VALUE = None
                    return
                set_status(level="info", text=f"cancelled picking for {PICKER_VALUE}, picking for {param}")
                toggle_colorpicker_offset(False)
                PICKER_VALUE = None
            PICKER_VALUE = param
            toggle_colorpicker_offset(True, entry.val_offset)
            set_status(level="info", text=f"picking value for {param} (current: {entry.get()})")
            set_status(level="prompt", text=f"click on the spot on the image to pick a value for {param}. click the same button to cancel. current: {entry.get()}")
        picker_btn = tk.Button(master=master)
        button_base(picker_btn, "IMAGE", colorpicker_icon)
        picker_btn.config(command=picker_func)
        picker_btn.base_font = 1
        picker_btn.place_dict = dict(
            relx=(relx + relwidth) if "w" in anchor else (relx - relwidth), relwidth=picker_size, rely=rely,
            relheight=relheight, anchor="ne" if "w" in anchor else "nw"
        )
        picker_btn.place(**picker_btn.place_dict)
        entry.val_offset = 0

    return [entry, label, picker_btn] if ret_all else entry

def checkmark_base(checkbtn, val, font, text):
    var = tk.BooleanVar()
    var.set(val)
    checkbtn.base_font = font
    checkbtn.config(
        text=text, bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR,
        activebackground=cfgs.BACKGROUND_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR,
        selectcolor=cfgs.BACKGROUND_COLOR, font=(cfgs.DEFAULT_FONT, checkbtn.base_font),
        variable=var, onvalue=True, offvalue=False, anchor="w"
    )
    TEXT_ELEMENTS.append(checkbtn)
    TEXT_RESIZE.append(checkbtn)
    return var

image_label = tk.Label(master=content)
label_base(image_label, 12, "Image")
image_label.place(relx=0.975, rely=0.01, relwidth=0.15, relheight=0.03, anchor="ne")

openfile_btn = tk.Button(master=content)
button_base(openfile_btn, 14, "Open")
openfile_btn.place(relx=0.825, rely=0.05, relwidth=0.07, relheight=0.04, anchor="nw")

pastefile_btn = tk.Button(master=content)
button_base(pastefile_btn, 14, "Paste")
pastefile_btn.place(relx=0.825, rely=0.1, relwidth=0.07, relheight=0.04, anchor="nw")

clearfile_btn = tk.Button(master=content)
button_base(clearfile_btn, 14, "Clear")
clearfile_btn.place(relx=0.975, rely=0.1, relwidth=0.07, relheight=0.04, anchor="ne")

dimensions_label = tk.Label(master=content)
label_base(dimensions_label, 12, "0x0")
dimensions_label.place(relx=0.975, rely=0.05, relwidth=0.07, relheight=0.05, anchor="ne")

detect_label = tk.Label(master=content)
label_base(detect_label, 12, "Detection Config")
detect_label.place(relx=0.975, rely=0.155, relwidth=0.15, relheight=0.03, anchor="ne")

# =============================================== config entries

minarea_entry = labeled_entry("min area", 13, 8, 0.825, 0.22, 0.07, 0.03, "min_area")
minarea_entry.insert(0, str(cfgs.DEFAULT_AREA_MIN))
maxarea_entry = labeled_entry("max area", 13, 8, 0.975, 0.22, 0.07, 0.03, "max_area", "ne")
maxarea_entry.insert(0, str(cfgs.DEFAULT_AREA_MAX))

areabase_entry = labeled_entry("base area", 13, 8, 0.825, 0.285, 0.07, 0.03, "!areabase")
areabase_entry.insert(0, str(cfgs.DEFAULT_AREA_BASE))
arearatio_entry = labeled_entry("base ratio", 13, 8, 0.975, 0.285, 0.07, 0.03, "!arearatio", "ne")
arearatio_entry.insert(0, str(cfgs.DEFAULT_AREA_RATIO))

minthresh_entry = labeled_entry("min thresh", 13, 8, 0.825, 0.35, 0.07, 0.03, "minval", picker=True)
minthresh_entry.insert(0, str(cfgs.DEFAULT_THRESHOLD_MIN))
minthresh_entry.val_offset = -10
maxthresh_entry = labeled_entry("max thresh", 13, 8, 0.975, 0.35, 0.07, 0.03, "maxval", "ne", picker=True)
maxthresh_entry.insert(0, str(cfgs.DEFAULT_THRESHOLD_MAX))
maxthresh_entry.val_offset = 0
glarethresh_entry = labeled_entry("glare val", 13, 8, 0.825, 0.415, 0.07, 0.03, "glareval", picker=True)
glarethresh_entry.insert(0, str(cfgs.DEFAULT_GLARE_BARRIER))
glarethresh_entry.val_offset = -2
glaremax_entry = labeled_entry("glare max", 13, 8, 0.975, 0.415, 0.07, 0.03, "glaremax", "ne", picker=True)
glaremax_entry.insert(0, str(cfgs.DEFAULT_GLARE_CEILING))
glaremax_entry.val_offset = 2

basescale_entry = labeled_entry("prop size", 13, 10, 0.825, 0.48, 0.15, 0.03, "!propsize")
basescale_entry.insert(0, str(cfgs.DEFAULT_PROP_SIZE))
areasize_entry = labeled_entry("area size", 13, 10, 0.825, 0.545, 0.15, 0.03, "!areasize")
areasize_entry.insert(0, str(cfgs.DEFAULT_AREA_SIZE))

ksize_entry = labeled_entry("blur ksize", 13, 8, 0.825, 0.61, 0.07, 0.03, "ksize")
ksize_entry.insert(0, str(cfgs.DEFAULT_KSIZE))
glareblur_entry = labeled_entry("glare blur", 13, 8, 0.975, 0.61, 0.07, 0.03, "glareblur", "ne")
glareblur_entry.insert(0, str(cfgs.DEFAULT_GLARE_BLUR))

colorpicker_entry_elements = labeled_entry("picker offset", 13, 10, 0.03, 0.94, 0.2, 0.04, ret_all=True)
def validate_int(P):
    if P in ["", "-"]:
        return True
    try:
        _ = int(P)
        return True
    except ValueError:
        return False
def validate_float(P):
    if P in ["", "-", "."]:
        return True
    try:
        _ = float(P)
        return True
    except ValueError:
        return False
valid_int_cmd = window.register(validate_int)
colorpicker_entry_elements[0].config(validate="key", validatecommand=(valid_int_cmd, "%P"))

# =============================================== config entry end

selectarea_btn = tk.Button(master=content)
button_base(selectarea_btn, 16, "Area")
selectarea_btn.place(relx=0.825, rely=0.66, relwidth=0.073, relheight=0.05, anchor="nw")

cleararea_btn = tk.Button(master=content)
button_base(cleararea_btn, 16, "Clear")
cleararea_btn.place(relx=0.975, rely=0.66, relwidth=0.073, relheight=0.05, anchor="ne")

areatype_btn = tk.Button(master=content)
button_base(areatype_btn, 10, f"Type: {AREA_TYPES[AREA_TYPE]}")
areatype_btn.place(relx=0.825, rely=0.715, relwidth=0.15, relheight=0.03, anchor="nw")

detect_btn = tk.Button(master=content)
button_base(detect_btn, 18, "Detect")
detect_btn.place(relx=0.975, rely=0.8, relwidth=0.15, relheight=0.05, anchor="se")

status_label = tk.Label(master=content)
label_base(status_label, 16, "")
status_label.config(fg=cfgs.STATUS_LABEL_COLOR)
status_label.config(anchor="w")
status_label.place(relx=0.01, rely=0.81, relwidth=0.88, relheight=0.04, anchor="nw")

journal_btn = tk.Button(master=content)
button_base(journal_btn, 14, "Journal")
journal_btn.place(relx=0.99, rely=0.81, relwidth=0.09, relheight=0.04, anchor="ne")

possible_stats = {}
STATUS_JOURNAL = []
def set_possible_stats():
    global possible_stats
    possible_stats = cfgs.STATUSES.copy()
def journal_add(timestamp, level, text):
    STATUS_JOURNAL.append((timestamp, level, text))
def set_status(level="status", text="None"):
    status = possible_stats.get(level, possible_stats["status"])
    status_label.config(bg=status[0], text=f"[{status[1]}] {text}")
    fit_element(status_label)
    if level != "prompt":
        journal_add(time.time(), level, text)
set_possible_stats()
set_status(text="Launched")

JOURNAL_TOPLEVEL:tk.Toplevel = None
def view_journal():
    global JOURNAL_TOPLEVEL
    if JOURNAL_TOPLEVEL is not None:
        JOURNAL_TOPLEVEL.destroy()

    JOURNAL_TOPLEVEL = tk.Toplevel(master=window, width=cfgs.DEFAULT_JOURNAL_WIDTH, height=cfgs.DEFAULT_JOURNAL_HEIGHT)
    JOURNAL_TOPLEVEL.non_instant = True
    JOURNAL_TOPLEVEL.title("Status Journal")
    JOURNAL_TOPLEVEL.config(bg=cfgs.BACKGROUND_COLOR)

    style = ttk.Style(master=JOURNAL_TOPLEVEL)
    style.theme_use("alt")
    style.configure(
        "Vertical.TScrollbar",
        troughcolor=cfgs.BACKGROUND_COLOR, background=cfgs.LIGHT_BACKGROUND_COLOR,
        arrowcolor=cfgs.LIGHT_BACKGROUND_COLOR
    )
    style.map(
        "Vertical.TScrollbar",
        troughcolor=[("disabled", cfgs.BACKGROUND_COLOR)], background=[("disabled", cfgs.BACKGROUND_COLOR)],
        arrowcolor=[("disabled", cfgs.BACKGROUND_COLOR)]
    )

    TL_TEXT_ELEMENTS = []
    def top_level_rescale_text_fits(*_):
        for el in TL_TEXT_ELEMENTS:
            new_size = (el.base_font / cfgs.DEFAULT_JOURNAL_HEIGHT) * JOURNAL_TOPLEVEL.winfo_height()
            el.config(font=(cfgs.DEFAULT_FONT, int(new_size), el.font_type))

    journal_title = tk.Label(master=JOURNAL_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, text="Journal")
    journal_title.base_font = 16
    journal_title.font_type = "bold"
    journal_title.config(font=(cfgs.DEFAULT_FONT, journal_title.base_font, journal_title.font_type))
    journal_title.place(relx=0.5, rely=0, relwidth=0.9, relheight=0.1, anchor="n")
    TL_TEXT_ELEMENTS.append(journal_title)

    text_frame = tk.Frame(master=JOURNAL_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR)
    text_frame.place(relx=0, rely=1, relwidth=1, relheight=0.9, anchor="sw")

    text_scroll = ttk.Scrollbar(master=text_frame, orient=tk.VERTICAL)
    text_scroll.place(relx=1, rely=0, width=20, relheight=1, anchor="ne")

    text_box = tk.Text(master=text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
    text_box.config(bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, font=(cfgs.DEFAULT_FONT, 16))
    text_box.place(relx=0, rely=0, width=-20, relwidth=1, relheight=1)

    for level in possible_stats:
        status = possible_stats[level]
        text_box.tag_configure(level, background=status[0], foreground=status_label["foreground"])
        text_box.tag_configure(f"{level}_timestamp", background=status[0], foreground=status_label["foreground"], font=(cfgs.DEFAULT_FONT, 10))

    for stat in STATUS_JOURNAL:
        status = possible_stats.get(stat[1], possible_stats["status"])
        timestamp = datetime.fromtimestamp(stat[0]).strftime("%d/%m/%Y %H:%M:%S")
        text_box.insert(tk.END, f"[{timestamp}] ", f"{stat[1]}_timestamp")
        text_box.insert(tk.END, f"[{status[1]}] {stat[2]}\n", stat[1])

    text_box.config(state=tk.DISABLED)

    JOURNAL_TOPLEVEL.bind("<Configure>", top_level_rescale_text_fits)
    def on_close():
        global JOURNAL_TOPLEVEL
        JOURNAL_TOPLEVEL.destroy()
        JOURNAL_TOPLEVEL = None
    JOURNAL_TOPLEVEL.protocol("WM_DELETE_WINDOW", on_close)
    JOURNAL_TOPLEVEL.focus_force()
journal_btn.config(command=view_journal)

def set_formula(new_formula):
    global CURRENT_FORMULA
    if new_formula == CURRENT_FORMULA:
        return
    old = CURRENT_FORMULA
    CURRENT_FORMULA = new_formula
    set_status(level="info", text=f"set new formula: \"{CURRENT_FORMULA}\" (old: \"{old}\")")
    usettings.formula = new_formula

FORMULA_TOPLEVEL:tk.Toplevel = None
def formula_input():
    global FORMULA_TOPLEVEL
    if FORMULA_TOPLEVEL is not None:
        FORMULA_TOPLEVEL.destroy()

    FORMULA_TOPLEVEL = tk.Toplevel(master=window, width=cfgs.DEFAULT_FORMULA_INPUT_WIDTH, height=cfgs.DEFAULT_FORMULA_INPUT_HEIGHT)
    FORMULA_TOPLEVEL.non_instant = True
    FORMULA_TOPLEVEL.title("Set formula")
    FORMULA_TOPLEVEL.config(bg=cfgs.BACKGROUND_COLOR)

    TL_TEXT_ELEMENTS = []
    def top_level_rescale_text_fits(*_):
        for el in TL_TEXT_ELEMENTS:
            new_size = (el.base_font / cfgs.DEFAULT_FORMULA_INPUT_HEIGHT) * FORMULA_TOPLEVEL.winfo_height()
            el.config(font=(cfgs.DEFAULT_FONT, int(new_size), el.__dict__.get("font_type", "normal")))

    formula_title = tk.Label(master=FORMULA_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, text="Formula")
    formula_title.base_font = 22
    formula_title.font_type = "bold"
    formula_title.config(font=(cfgs.DEFAULT_FONT, formula_title.base_font, formula_title.font_type))
    formula_title.place(relx=0.5, rely=0.05, relwidth=0.9, relheight=0.25, anchor="n")
    TL_TEXT_ELEMENTS.append(formula_title)

    formula_entry = tk.Entry(master=FORMULA_TOPLEVEL)
    formula_entry.base_font = 14
    formula_entry.cfg = dict(
        bg="LIGHT_BACKGROUND_COLOR", fg="TEXT_COLOR",
    )
    formula_entry.config(
        bg=cfgs.LIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, highlightthickness=0,
        font=(cfgs.DEFAULT_FONT, formula_entry.base_font)
    )
    formula_entry.place(relx=0.5, rely=0.325, relwidth=0.9, relheight=0.2, anchor="n")
    formula_entry.insert(0, CURRENT_FORMULA)
    TL_TEXT_ELEMENTS.append(formula_entry)

    def reset():
        formula_entry.delete(0, tk.END)
        formula_entry.insert(0, formula.BASE_FORMULA)

    reset_btn = tk.Button(master=FORMULA_TOPLEVEL)
    reset_btn.base_font = 12
    reset_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    reset_btn.config(
        text="Reset", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR, command=reset
    )
    reset_btn.place(relx=0.5, rely=0.725, relwidth=0.4, relheight=0.15, anchor="s")
    TL_TEXT_ELEMENTS.append(reset_btn)

    set_btn = tk.Button(master=FORMULA_TOPLEVEL)
    set_btn.base_font = 16
    set_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    set_btn.config(
        text="Set", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    set_btn.place(relx=0.475, rely=0.85, relwidth=0.4, relheight=0.2, anchor="e")
    TL_TEXT_ELEMENTS.append(set_btn)

    cancel_btn = tk.Button(master=FORMULA_TOPLEVEL)
    cancel_btn.base_font = 16
    cancel_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    cancel_btn.config(
        text="Cancel", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    cancel_btn.place(relx=0.525, rely=0.85, relwidth=0.4, relheight=0.2, anchor="w")
    TL_TEXT_ELEMENTS.append(cancel_btn)

    top_level_rescale_text_fits(None)

    FORMULA_TOPLEVEL.bind("<Configure>", top_level_rescale_text_fits)
    def on_close():
        global FORMULA_TOPLEVEL
        FORMULA_TOPLEVEL.destroy()
        FORMULA_TOPLEVEL = None
    set_btn.config(command=lambda: set_formula(formula_entry.get()))
    cancel_btn.config(command=on_close)
    FORMULA_TOPLEVEL.protocol("WM_DELETE_WINDOW", on_close)
    FORMULA_TOPLEVEL.focus_force()

BINDER_TOPLEVEL:tk.Toplevel = None
def binder_toplevel():
    global BINDER_TOPLEVEL
    if BINDER_TOPLEVEL is not None:
        BINDER_TOPLEVEL.destroy()

    BINDER_TOPLEVEL = tk.Toplevel(master=window, width=cfgs.DEFAULT_BINDERS_WIDTH, height=cfgs.DEFAULT_BINDERS_HEIGHT)
    BINDER_TOPLEVEL.non_instant = True
    BINDER_TOPLEVEL.title("Set binders")
    BINDER_TOPLEVEL.config(bg=cfgs.BACKGROUND_COLOR)

    TL_TEXT_ELEMENTS = []

    def top_level_rescale_text_fits(*_):
        for el in TL_TEXT_ELEMENTS:
            new_size = (el.base_font / cfgs.DEFAULT_BINDERS_HEIGHT) * BINDER_TOPLEVEL.winfo_height()
            el.config(font=(cfgs.DEFAULT_FONT, int(new_size), el.__dict__.get("font_type", "normal")))

    theme_title = tk.Label(master=BINDER_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, text="Binders")
    theme_title.base_font = 18
    theme_title.font_type = "bold"
    theme_title.config(font=(cfgs.DEFAULT_FONT, theme_title.base_font, theme_title.font_type))
    theme_title.place(relx=0.5, rely=0.02, relwidth=0.9, relheight=0.2, anchor="n")
    TL_TEXT_ELEMENTS.append(theme_title)

    style = ttk.Style()
    style.theme_use("clam")
    style.layout("TCombobox", [
        ('Combobox.field', {
            'sticky': 'nswe',
            'children': [
                ('Combobox.downarrow', {'side': 'right', 'sticky': 'ns'}),
                ('Combobox.padding', {
                    'sticky': 'nswe',
                    'children': [
                        ('Combobox.textarea', {'sticky': 'nswe'})
                    ]
                })
            ]
        })
    ])

    style.configure(
        "Vertical.TScrollbar",
        troughcolor=cfgs.BACKGROUND_COLOR,
        background=cfgs.LIGHT_BACKGROUND_COLOR,
        arrowcolor=cfgs.LIGHT_BACKGROUND_COLOR
    )
    style.configure(
        "TCombobox",
        arrowcolor=cfgs.LIGHTER_BACKGROUND_COLOR,
        background=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        bordercolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        lightcolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        darkcolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        fieldbackground=cfgs.INTERACT_COLOR,
        foreground=cfgs.TEXT_COLOR,
        padding=2,
        relief=tk.FLAT,
        selectbackground=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        selectforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", cfgs.INTERACT_COLOR)],
        foreground=[("readonly", cfgs.TEXT_COLOR)],
        background=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        bordercolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        lightcolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        darkcolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)]
    )
    style.map(
        "Vertical.TScrollbar",
        troughcolor=[("disabled", cfgs.BACKGROUND_COLOR)],
        background=[("disabled", cfgs.BACKGROUND_COLOR)],
        arrowcolor=[("disabled", cfgs.BACKGROUND_COLOR)]
    )
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.background", cfgs.LIGHT_BACKGROUND_COLOR)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.foreground", cfgs.TEXT_COLOR)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.selectBackground", cfgs.LIGHTER_BACKGROUND_COLOR)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.selectForeground", cfgs.HIGHLIGHT_TEXT_COLOR)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.font", cfgs.DEFAULT_FONT)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.relief", "flat")
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.borderWidth", 0)
    BINDER_TOPLEVEL.option_add("*TCombobox*Listbox.highlightThickness", 0)

    binder_list = ttk.Combobox(master=BINDER_TOPLEVEL, values=[], style="TCombobox", state="readonly")
    binder_list.base_font = 16
    binder_list.place(relx=0.5, rely=0.25, relwidth=0.9, relheight=0.2, anchor="n")
    TL_TEXT_ELEMENTS.append(binder_list)

    binder_name_entry = tk.Entry(master=BINDER_TOPLEVEL)
    binder_name_entry.base_font = 13
    binder_name_entry.config(
        bg=cfgs.LIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, highlightthickness=0,
        font=(cfgs.DEFAULT_FONT, binder_name_entry.base_font)
    )
    binder_name_entry.place(relx=0.05, rely=0.47, relwidth=0.435, relheight=0.15, anchor="nw")
    TL_TEXT_ELEMENTS.append(binder_name_entry)

    binder_value_entry = tk.Entry(master=BINDER_TOPLEVEL)
    binder_value_entry.base_font = 13
    binder_value_entry.config(
        bg=cfgs.LIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, highlightthickness=0,
        font=(cfgs.DEFAULT_FONT, binder_value_entry.base_font)
    )
    binder_value_entry.place(relx=0.95, rely=0.47, relwidth=0.435, relheight=0.15, anchor="ne")
    TL_TEXT_ELEMENTS.append(binder_value_entry)

    add_btn = tk.Button(master=BINDER_TOPLEVEL)
    add_btn.base_font = 14
    add_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    add_btn.config(
        text="Add", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    add_btn.place(relx=0.1, rely=0.65, relwidth=0.35, relheight=0.15, anchor="nw")
    TL_TEXT_ELEMENTS.append(add_btn)

    remove_btn = tk.Button(master=BINDER_TOPLEVEL)
    remove_btn.base_font = 14
    remove_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    remove_btn.config(
        text="Remove", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    remove_btn.place(relx=0.9, rely=0.65, relwidth=0.35, relheight=0.15, anchor="ne")
    TL_TEXT_ELEMENTS.append(remove_btn)

    set_btn = tk.Button(master=BINDER_TOPLEVEL)
    set_btn.base_font = 14
    set_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    set_btn.config(
        text="Set", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    set_btn.place(relx=0.5, rely=0.98, relwidth=0.8, relheight=0.15, anchor="s")
    TL_TEXT_ELEMENTS.append(set_btn)

    top_level_rescale_text_fits(None)

    BINDER_TOPLEVEL.bind("<Configure>", top_level_rescale_text_fits)

    def on_close():
        global BINDER_TOPLEVEL
        BINDER_TOPLEVEL.destroy()
        BINDER_TOPLEVEL = None

    def select_binder(_):
        current = binder_list.current()
        binder_name_entry.delete(0, tk.END)
        binder_value_entry.delete(0, tk.END)
        if current == -1:
            return
        name = binder_list.get()
        binder_name_entry.insert(0, name)
        binder_value_entry.insert(0, usettings.binders.get(name, 0))

    def add_binder():
        name = binder_name_entry.get()
        if not valid_variable_name(name):
            set_status(level="warning", text=f"\"{name}\" is an invalid variable name for a binder")
            return
        if name in usettings.binders.keys():
            set_status(level="warninfo", text=f"binder with name \"{name}\" already exists")
            return
        if name in ["t", "a", "p"]:
            set_status(level="warninfo", text=f"\"{name}\" is already in use by the default formula inputs (t, a, p)")
            return
        usettings.binders[name] = 0
        binder_list.config(values=list(usettings.binders.keys()))
        binder_list.current(list(usettings.binders.keys()).index(name))
        select_binder(None)
        set_status(level="info", text=f"created binder \"{name}\"")

    def remove_binder():
        name = binder_name_entry.get()
        if name not in usettings.binders.keys():
            set_status(level="warning", text=f"no binder with name \"{name}\" exists")
            return
        prev_val = usettings.binders[name]
        del usettings.binders[name]
        binder_list.config(values=list(usettings.binders.keys()))
        if len(list(usettings.binders.keys())) > 0:
            binder_list.current(0)
        else:
            binder_list.set("")
        set_status(level="warninfo", text=f"deleted binder \"{name}\" (had a value of: {prev_val})")
        select_binder(None)

    def set_binder():
        name = binder_name_entry.get()
        if name not in usettings.binders.keys():
            set_status(level="warning", text=f"no binder with name \"{name}\" exists, add it first")
            return
        value = binder_value_entry.get()
        if not validate_float(value):
            set_status(level="warning", text=f"binders have to be strictly numeric (\"{value}\" is an invalid number)")
            return
        prev_val = usettings.binders[name]
        if value in ["", "-", "."]:
            value = 0
        usettings.binders[name] = float(value)
        set_status(level="info", text=f"set binder \"{name}\" (new: {float(value)}; old: {prev_val})")

    binder_list.bind("<<ComboboxSelected>>", select_binder)
    binder_list.config(values=list(usettings.binders.keys()))
    if len(list(usettings.binders.keys())) > 0:
        binder_list.current(0)
    select_binder(None)

    add_btn.config(command=add_binder)
    remove_btn.config(command=remove_binder)
    set_btn.config(command=set_binder)

    BINDER_TOPLEVEL.protocol("WM_DELETE_WINDOW", on_close)
    BINDER_TOPLEVEL.focus_force()

result_canvas = tk.Canvas(master=content)
result_canvas.cfg = dict(
    bg="RESULT_CANVAS_BACKGROUND_COLOR", highlightcolor="RESULT_CANVAS_HIGHLIGHT_COLOR",
    highlightthickness="RESULT_CANVAS_HIGHLIGHT_THICKNESS", highlightbackground="RESULT_CANVAS_HIGHLIGHT_COLOR"
)
result_canvas.config(
    bg=cfgs.RESULT_CANVAS_BACKGROUND_COLOR, highlightcolor=cfgs.RESULT_CANVAS_HIGHLIGHT_COLOR,
    highlightthickness=cfgs.RESULT_CANVAS_HIGHLIGHT_THICKNESS, highlightbackground=cfgs.RESULT_CANVAS_HIGHLIGHT_COLOR
)
result_canvas.place(relx=0, rely=1, relwidth=0.7, relheight=0.14, anchor="sw")

debug_checkbtn = tk.Checkbutton(master=content)
debug_var = checkmark_base(debug_checkbtn, cfgs.SHOW_DEBUG_IMAGES, 8, "debug images")
debug_checkbtn.place(relx=0.71, rely=0.87, relwidth=0.13, relheight=0.02, anchor="nw")

filterglare_checkbtn = tk.Checkbutton(master=content)
glare_var = checkmark_base(filterglare_checkbtn, cfgs.FILTER_GLARE, 8, "filter glare")
filterglare_checkbtn.place(relx=0.71, rely=0.9, relwidth=0.13, relheight=0.02, anchor="nw")

glarerange_checkbtn = tk.Checkbutton(master=content)
glare_range = checkmark_base(glarerange_checkbtn, cfgs.GLARE_RANGE, 8, "glare range")
glarerange_checkbtn.place(relx=0.71, rely=0.93, relwidth=0.13, relheight=0.02, anchor="nw")

glarefill_checkbtn = tk.Checkbutton(master=content)
glare_fill = checkmark_base(glarefill_checkbtn, cfgs.GLARE_FILL, 8, "glare fill")
glarefill_checkbtn.place(relx=0.85, rely=0.87, relwidth=0.13, relheight=0.02, anchor="nw")

bgrconvert_checkbtn = tk.Checkbutton(master=content)
rgb2bgr_var = checkmark_base(bgrconvert_checkbtn, cfgs.RGB_CONVERT, 8, "RGB to BGR")
bgrconvert_checkbtn.place(relx=0.85, rely=0.9, relwidth=0.13, relheight=0.02, anchor="nw")

hsvglare_checkbtn = tk.Checkbutton(master=content)
glarehsv_var = checkmark_base(hsvglare_checkbtn, cfgs.HSV_OVER_GRAY, 8, "glare HSV mask")
hsvglare_checkbtn.place(relx=0.85, rely=0.93, relwidth=0.13, relheight=0.02, anchor="nw")

destroywins_checkbtn = tk.Checkbutton(master=content)
destroywins_var = checkmark_base(destroywins_checkbtn, False, 8, "clear cv2 windows")
def destroywins():
    cv2.destroyAllWindows()
    destroywins_var.set(False)
destroywins_checkbtn.config(command=destroywins)
destroywins_checkbtn.place(relx=0.71, rely=0.96, relwidth=0.28, relheight=0.02, anchor="nw")

def show_result(result):
    if result == "clear":
        result_canvas.delete("all")
        return
    if result.get("text"):
        result_canvas.delete("all")
        render_text(
            result_canvas, [2, 2], result.get("text"),
            anchor="nw", fill=result.get("fill") or "#ffffff", font=result.get("font") or (cfgs.DEFAULT_FONT, 14)
        )
        return

    result_canvas.delete("all")
    render_text(result_canvas, [3, 3], "Result", anchor="nw", font=(cfgs.DEFAULT_FONT, 16))
    render_text(
        result_canvas, [9, 22], f"Detections: {result.get('total', 'nil')}",
        anchor="nw", fill="#aaaaff", font=(cfgs.DEFAULT_FONT, 14)
    )
    render_text(
        result_canvas, [9, 40], f"Whole area: {result.get('whole', 'nil')}",
        anchor="nw", fill="#aaffbb", font=(cfgs.DEFAULT_FONT, 14)
    )
show_result("clear")

CURRENT_IMAGE:Image = None
IMAGE_RATIO = 1
CURRENT_AREA:list = None

def refresh_canvas():
    global CURRENT_IMAGE, CURRENT_AREA

    canvas.delete("area")
    canvas.delete("picker")

    if PICKER_VALUE is not None:
        # def render_oval(this_canvas, x0, y0, x1, y1, **kwargs):
        #     this_canvas.create_oval(
        #         x0, y0, x1, y1,
        #         fill=kwargs.get("fill", "#000000"), outline=kwargs.get("outline", "#ffffff"),
        #         width=kwargs.get("width", 0), tags=tuple(kwargs.get("tags", []))
        #     )
        radius = cfgs.COLOR_PICKER_RADIUS
        width = cfgs.COLOR_PICKER_WIDTH
        color = PICKER_COLOR
        if isinstance(PICKER_COLOR, tuple) or isinstance(PICKER_COLOR, list):
            color = f"#{PICKER_COLOR[0]:02x}{PICKER_COLOR[1]:02x}{PICKER_COLOR[2]:02x}"
        render_oval(
            canvas, CANVAS_MOUSE_POS[0] - radius, CANVAS_MOUSE_POS[1] - radius,
                    CANVAS_MOUSE_POS[0] + radius, CANVAS_MOUSE_POS[1] + radius,
            fill=None, outline=f"#{(0xFFFFFF ^ int(color.lstrip('#'), 16)):06x}",
            width=width + 4, tags=["picker"]
        )
        render_oval(
            canvas, CANVAS_MOUSE_POS[0] - radius, CANVAS_MOUSE_POS[1] - radius,
            CANVAS_MOUSE_POS[0] + radius, CANVAS_MOUSE_POS[1] + radius,
            fill=None, outline=color, width=width, tags=["picker"]
        )

    if isinstance(CURRENT_AREA, list):
        if len(CURRENT_AREA) == 1:
            render_dot(canvas, CURRENT_AREA[0][0], 5, fill="#0000ff", width=1, outline="#ffffff", tags=["area"])
        else:
            if len(CURRENT_AREA) >= 4:
                first_point = CURRENT_AREA[0][0]
                prev_point = first_point
                render_dots = []
                for i, l in enumerate(CURRENT_AREA):
                    if not isinstance(l, list):
                        continue
                    if i == 0:
                        this_size = cfgs.CANVAS_AREA_END_SIZE
                        this_fill = cfgs.CANVAS_AREA_END_FILL
                        this_outline = cfgs.CANVAS_AREA_END_OUTLINE
                        this_width = cfgs.CANVAS_AREA_END_WIDTH
                    elif i == len(CURRENT_AREA) - 1:
                        this_size = cfgs.CANVAS_AREA_START_SIZE
                        this_fill = cfgs.CANVAS_AREA_START_FILL
                        this_outline = cfgs.CANVAS_AREA_START_OUTLINE
                        this_width = cfgs.CANVAS_AREA_START_WIDTH
                    else:
                        this_size = cfgs.CANVAS_AREA_MIDPOINT_SIZE
                        this_fill = cfgs.CANVAS_AREA_MIDPOINT_FILL
                        this_outline = cfgs.CANVAS_AREA_MIDPOINT_OUTLINE
                        this_width = cfgs.CANVAS_AREA_MIDPOINT_WIDTH
                    if l != prev_point:
                        render_line(canvas, prev_point, l[0], 2, tags=["area"])
                        prev_point = l[0]
                    render_dots.append({
                        "center_point": l[0],
                        "size": this_size,
                        "fill": this_fill,
                        "width": this_width,
                        "outline": this_outline
                    })
                if first_point != prev_point:
                    render_line(canvas, prev_point, first_point, 2, tags=["area"])
                for dot in render_dots:
                    render_dot(canvas, **dot, tags=["area"])
            else:
                tl = CURRENT_AREA[0][0]
                br = CURRENT_AREA[1][0]
                tr = [br[0], tl[1]]
                bl = [tl[0], br[1]]
                render_line(canvas, tl, tr, 2, tags=["area"])
                render_line(canvas, bl, br, 2, tags=["area"])
                render_line(canvas, tl, bl, 2, tags=["area"])
                render_line(canvas, tr, br, 2, tags=["area"])
                render_dot(
                    canvas, tl, cfgs.CANVAS_AREA_START_SIZE,
                    fill=cfgs.CANVAS_AREA_START_FILL, width=cfgs.CANVAS_AREA_START_WIDTH,
                    outline=cfgs.CANVAS_AREA_START_OUTLINE, tags=["area"]
                )
                render_dot(
                    canvas, tr, cfgs.CANVAS_AREA_MIDPOINT_SIZE,
                    fill=cfgs.CANVAS_AREA_MIDPOINT_FILL, width=cfgs.CANVAS_AREA_MIDPOINT_WIDTH,
                    outline=cfgs.CANVAS_AREA_MIDPOINT_OUTLINE, tags=["area"]
                )
                render_dot(
                    canvas, bl, cfgs.CANVAS_AREA_MIDPOINT_SIZE,
                    fill=cfgs.CANVAS_AREA_MIDPOINT_FILL, width=cfgs.CANVAS_AREA_MIDPOINT_WIDTH,
                    outline=cfgs.CANVAS_AREA_MIDPOINT_OUTLINE, tags=["area"]
                )
                render_dot(
                    canvas, br, cfgs.CANVAS_AREA_END_SIZE,
                    fill=cfgs.CANVAS_AREA_END_FILL, width=cfgs.CANVAS_AREA_END_WIDTH,
                    outline=cfgs.CANVAS_AREA_END_OUTLINE, tags=["area"]
                )

def refresh_image():
    global CURRENT_IMAGE, CURRENT_AREA, IMAGE_RATIO
    if CURRENT_IMAGE is None:
        return

    CURRENT_AREA = None

    width_ratio = canvas.winfo_width() / CURRENT_IMAGE.width
    height_ratio = canvas.winfo_height() / CURRENT_IMAGE.height
    using_ratio = min(width_ratio, height_ratio)
    IMAGE_RATIO = using_ratio

    dimensions_label.config(text=f"{CURRENT_IMAGE.width}x{CURRENT_IMAGE.height}")

    img = CURRENT_IMAGE.resize((
        max(1, int(using_ratio * CURRENT_IMAGE.width)),
        max(1, int(using_ratio * CURRENT_IMAGE.height))
    ), Image.Resampling.LANCZOS)
    tk_img = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    canvas.image = tk_img

    refresh_canvas()

def erase_image():
    global CURRENT_IMAGE, CURRENT_AREA
    if CURRENT_IMAGE is None:
        set_status(level="warninfo", text=f"no file selected to clear")
        return

    canvas.delete("all")
    set_status(level="warninfo", text=f"file deselected")
    dimensions_label.config(text=f"0x0")
    rescale_text_fits()
    CURRENT_IMAGE = None
    CURRENT_AREA = None
    refresh_canvas()

def new_image(path, image=None):
    global CURRENT_IMAGE

    erase_image()
    if path is None:
        CURRENT_IMAGE = image
        set_status(level="success", text=f"inserted file from buffer")
    else:
        CURRENT_IMAGE = Image.open(path)
        set_status(level="success", text=f"opened file: {path}")
    try:
        CURRENT_IMAGE = CURRENT_IMAGE.convert("RGB")
    except Exception as e:
        set_status(level="criterror", text="error while trying to convert image to RGB. see error in journal.")
        journal_add(time.time(), "criterror", str(e))
        return
    refresh_image()
    rescale_text_fits()

def open_new_image():
    filepath = fd.askopenfilename(filetypes=(
        ("Image files", tuple([f"*.{x}" for x in cfgs.ALLOWED_EXTENSIONS])),
        ("All files", "*.*")
    ))
    if filepath:
        path = pathlib.Path(filepath)
        if path.suffix[1:].lower() in cfgs.ALLOWED_EXTENSIONS:
            new_image(filepath)
        else:
            set_status(level="warning", text=f"\"{path.suffix[1:]}\" files aren't supported")

def paste_new_image():
    img = ImageGrab.grabclipboard()
    if img:
        if isinstance(img, list):
            new_image(img[0], None)
        else:
            new_image(None, img)
    else:
        set_status(level="warning", text=f"no image found in buffer")

def change_area_type():
    global AREA_TYPE
    AREA_TYPE = (AREA_TYPE + 1) if AREA_TYPE < (len(AREA_TYPES) - 1) else 0
    areatype_btn.config(text=f"Type: {AREA_TYPES[AREA_TYPE]}")

def select_area():
    global CURRENT_AREA, AREA_STATE

    if PICKER_VALUE is not None:
        set_status(level="warninfo", text=f"currently picking a color. cannot select an area")
        return

    if CURRENT_AREA is not None:
        if "select" in CURRENT_AREA:
            if isinstance(CURRENT_AREA, list):
                set_status(level="info", text="area selection canceled (" +
                                              (f"{CURRENT_AREA[0][0]} {CURRENT_AREA[1][0]}" if AREA_TYPE == 0 else f"{len(CURRENT_AREA) - 1}pts") + ")")
                CURRENT_AREA.remove("select")
            else:
                set_status(level="info", text=f"area selection canceled (previously none)")
                CURRENT_AREA = None
            return

    set_status(level="info", text=f"selecting area. type: {AREA_TYPES[AREA_TYPE]}")
    if AREA_TYPE == 0:
        set_status(level="prompt", text="select area by clicking and dragging. you can cancel by pressing the button again")
    elif AREA_TYPE in [1, 2]:
        AREA_STATE = 0
        set_status(level="prompt", text="place the first point of the area by clicking. you can cancel by pressing the button again")

    if isinstance(CURRENT_AREA, list):
        CURRENT_AREA.append("select")
    else:
        CURRENT_AREA = "select"

def clear_area():
    global CURRENT_AREA
    CURRENT_AREA = None
    refresh_canvas()

    set_status(level="info", text="area cleared")

def detect(image, ksize=15, minval=cfgs.DEFAULT_THRESHOLD_MIN, maxval=cfgs.DEFAULT_THRESHOLD_MAX, min_area=0, max_area=10**10, glareval=None, glaremax=None, glarerange=True, glareblur=cfgs.DEFAULT_GLARE_BLUR):
    if ksize % 2 == 0:
        set_status(level="error", text=f"ksize has to be an odd number. current: {ksize}")
        return None
    output = image.copy()

    if glareval is not None:
        glare_img = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
        if glarehsv_var.get():
            glare_img = cv2.cvtColor(output, cv2.COLOR_BGR2HSV)[:, :, 2]
            # glare_mask = cv2.threshold(hsv[:, :, 2], glareval, maxval, cv2.THRESH_BINARY)[1]
        glare_mask = cv2.inRange(glare_img, glareval, glaremax)
        if debug_var.get():
            cv2.imshow("glare inrange", glare_mask)
        glare_mask = cv2.dilate(glare_mask, np.ones((glareblur, glareblur), np.uint8), iterations=2)
        if glare_fill.get():
            output = cv2.inpaint(output, glare_mask, glareblur, cv2.INPAINT_TELEA)
        else:
            glare_mask = cv2.bitwise_not(glare_mask)
            output = cv2.bitwise_and(output, output, mask=glare_mask)
        if debug_var.get():
            cv2.imshow("filtered glare", output)

    gray = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (ksize, ksize), 0)
    if (glareval is not None) and glarerange:
        thresh1 = cv2.inRange(blurred, minval, glareval)
        thresh2 = cv2.inRange(blurred, glaremax, maxval)
        thresh = cv2.bitwise_or(thresh1, thresh2)
    else:
        thresh = cv2.inRange(blurred, minval, maxval)
    thresh = cv2.erode(thresh, None, iterations=1)
    thresh = cv2.dilate(thresh, None, iterations=2)

    if debug_var.get():
        cv2.imshow("thresh test", thresh)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    points = []
    for i, c in enumerate(contours):
        area = cv2.contourArea(c)
        if not (min_area < area < max_area):
            continue
        moments = cv2.moments(c)
        cx = int(moments["m10"] / moments["m00"])
        cy = int(moments["m01"] / moments["m00"])
        points.append([[cx, cy], area])
        cv2.circle(output, (cx, cy), 7, (255, 0, 0), 1)
        cv2.putText(output, str(area), (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    if debug_var.get():
        cv2.imshow("test", output)

    return points

def detection_command():
    if CURRENT_IMAGE is None:
        set_status(level="warning", text="no image loaded for detection")
        return

    prop_size = cfgs.DEFAULT_PROP_SIZE
    area_size = cfgs.DEFAULT_AREA_SIZE
    area_base = cfgs.DEFAULT_AREA_BASE
    area_ratio = cfgs.DEFAULT_AREA_RATIO

    set_status(level="info", text="compiling parameters...")
    kwargs = {}
    for entry, param in PARAM_ENTRIES:
        val = entry.get()
        try:
            val = float(val)
        except ValueError:
            set_status(level="warning", text=f"config \"{param}\" is not a number")
            return

        if param[0] != "!":
            if (param == "glareval") and (not glare_var.get()):
                val = None
            else:
                val = int(val)
            kwargs[param] = val
        else:
            param = param[1:]
            if param == "propsize":
                prop_size = val
            elif param == "areasize":
                area_size = val
            elif param == "areabase":
                area_base = val
            elif param == "arearatio":
                area_ratio = val

    if area_base == 0:
        area_ratio = 0
        area_base = 1

    kwargs["glarerange"] = glare_range.get()

    set_status(level="info", text="compiling image...")
    # try:
    #     canvas_image = canvas.image
    # except AttributeError:
    #     set_status(level="error", text="no image is associated with the canvas")
    #     return
    image = np.array(CURRENT_IMAGE, dtype=np.uint8)
    if rgb2bgr_var.get():
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    shape = list(reversed(image.shape[0:2]))
    ratio = IMAGE_RATIO

    area_coef = ((shape[0] * shape[1]) / (area_base ** 2)) * area_ratio
    if area_coef != 0:
        kwargs["min_area"] *= area_coef
        kwargs["max_area"] *= area_coef

    area = [[0, 0], [shape[0], shape[1]]]
    if isinstance(CURRENT_AREA, list):
        if len(CURRENT_AREA) >= 4:
            area = [CURRENT_AREA[i][0].copy() for i in range(len(CURRENT_AREA))]
        else:
            area = [CURRENT_AREA[0][0].copy(), CURRENT_AREA[1][0].copy()]
            area[0][0], area[0][1], area[1][0], area[1][1] = (
                min(area[0][0], area[1][0]), min(area[0][1], area[1][1]),
                max(area[0][0], area[1][0]), max(area[0][1], area[1][1])
            )
        for i in range(len(area)):
            for o in range(len(area[i])):
                area[i][o] = int(area[i][o] / ratio)
    if len(area) == 2:
        image = image[area[0][1]:(area[0][1] + abs(area[1][1] - area[0][1])), area[0][0]:(area[0][0] + abs(area[1][0] - area[0][0]))]
    else:
        pts = np.array(area, dtype=np.int32)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        region = cv2.bitwise_and(image, image, mask=mask)
        x, y, w, h = cv2.boundingRect(pts)
        image = region[y:y+h, x:x+w]
        area[0] = [x, y]

    set_status(level="info", text="calculating...")
    start_time = time.time()
    try:
        points = detect(image, **kwargs)
        if points is None:
            return
    except Exception as e:
        set_status(level="criterror", text=f"error while calculating. see result log below")
        journal_add(time.time(), "criterror", str(e))
        show_result({
            "text": str(e),
            "fill": "#ff3367",
            "font": (cfgs.DEFAULT_FONT, 13)
        })
        return
    end_time = time.time()
    total = len(points)
    Eval.set_vars(usettings.binders | {
        "t": total,
        "a": area_size,
        "p": prop_size
    })
    success = True
    whole = Eval.eval(CURRENT_FORMULA) # round(total * ((prop_size ** 2) / (area_size ** 2)))
    if isinstance(whole, str):
        set_status(level="error", text=f"error while computing with formula. falling back to default. see error in journal.")
        journal_add(time.time(), level="error", text=whole)
        whole = Eval.eval(formula.BASE_FORMULA)
        success = False

    if success:
        set_status(level="success", text=f"detection complete (timestamp: {start_time}; {end_time - start_time})")
    else:
        set_status(level="warning", text=f"detection complete (timestamp: {start_time}; {end_time - start_time}), "
                                         f"however an exception was handled during it. check journal.")
    show_result({
        "total": total,
        "whole": whole
    })

    canvas.delete("detect")
    for i, pa in enumerate(points):
        p, a = pa
        center = [(area[0][0] + p[0]) * ratio, (area[0][1] + p[1]) * ratio]
        render_circle(
            canvas, center, math.sqrt(a / math.pi), tags=["detect"], fill=None,
            outline=cfgs.CANVAS_DETECTION_COLOR, width=cfgs.CANVAS_DETECTION_WIDTH
        )
        render_text(
            canvas, center, str(i + 1), tags=["detect"], fill=cfgs.CANVAS_DETECTION_TEXT_COLOR,
            font=(cfgs.DEFAULT_FONT, cfgs.CANVAS_DETECTION_TEXT_SIZE, "bold"), anchor="center"
        )

def on_canvas_click(event):
    global CURRENT_AREA, AREA_STATE, PICKER_VALUE, PICKER_COLOR

    ev_x, ev_y = event.x, event.y
    rel_x = ev_x / canvas.winfo_width()
    rel_y = ev_y / canvas.winfo_height()
    click_list = [[ev_x, ev_y], [rel_x, rel_y]]

    valid_area_pick = True
    if CURRENT_AREA is None:
        valid_area_pick = False
    elif ("select" not in CURRENT_AREA) and (AREA_TYPE not in [1, 2]):
        valid_area_pick = False
    elif isinstance(CURRENT_AREA, list):
        if (None not in CURRENT_AREA) and ("select" not in CURRENT_AREA):
            valid_area_pick = False

    if not valid_area_pick:
        if PICKER_VALUE is not None:
            if CURRENT_IMAGE is None:
                toggle_colorpicker_offset(False)
                PICKER_VALUE = None
                refresh_canvas()
                return
            try:
                color = np.array(CURRENT_IMAGE)
                if not rgb2bgr_var.get():
                    color = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
                else:
                    color = cv2.cvtColor(color, cv2.COLOR_RGB2GRAY)
                color = int(color[int(ev_y / IMAGE_RATIO), int(ev_x / IMAGE_RATIO)])
            except IndexError:
                set_status(
                    level="error",
                    text=f"error when picking pixel: [{ev_x}, {ev_y}] "
                         f"(ratio: {IMAGE_RATIO}). outside of image boundary."
                )
            except Exception as e:
                set_status(
                    level="criterror",
                    text=f"error when picking pixel: [{ev_x}, {ev_y}] "
                         f"(ratio: {IMAGE_RATIO}). unhandled exception: {str(e)}"
                )
            else:
                PICKER_COLOR = None
                applied_offset = 0
                for p in PARAM_ENTRIES:
                    if p[1] == PICKER_VALUE:
                        applied_offset = colorpicker_entry_elements[0].get()
                        if applied_offset in ["", "-"]:
                            applied_offset = 0
                        p[0].val_offset = int(applied_offset)
                        color += p[0].val_offset
                        p[0].delete(0, tk.END)
                        p[0].insert(0, str(int(color)))
                        break
                set_status(level="info", text=f"pixel: [{ev_x}, {ev_y}] (ratio: {IMAGE_RATIO}). grayscale color: {color} "
                                              f"(after applying offset {int(applied_offset)}, original: {color - int(applied_offset)})")
                toggle_colorpicker_offset(False)
                PICKER_VALUE = None
                refresh_canvas()
        return

    if AREA_TYPE == 0:
        CURRENT_AREA = [click_list, click_list, None]
    elif AREA_TYPE in [1, 2]:
        if "select" in CURRENT_AREA:
            AREA_STATE = 0
            CURRENT_AREA = [click_list, *[None for _ in range({1: 4, 2: 8}.get(AREA_TYPE, 4))]]
        elif None in CURRENT_AREA:
            CURRENT_AREA[AREA_STATE] = click_list
        AREA_STATE += 1
        set_status(level="info", text=f"point {AREA_STATE} placed ({click_list[0][0]} {click_list[0][1]})")
        if AREA_STATE > (3 if AREA_TYPE == 1 else 7):
            AREA_STATE = 0
            set_status(level="info", text=f"last point placed, area selected ({click_list[0][0]} {click_list[0][1]})")
            del CURRENT_AREA[-1]
    refresh_canvas()

def on_canvas_motion(event):
    global CURRENT_AREA

    ev_x, ev_y = event.x, event.y
    rel_x = ev_x / canvas.winfo_width()
    rel_y = ev_y / canvas.winfo_height()
    click_list = [[ev_x, ev_y], [rel_x, rel_y]]

    if CURRENT_AREA is None:
        return
    elif len(CURRENT_AREA) != 3:
        return

    CURRENT_AREA[1] = click_list

    set_status(level="prompt", text=f"drag end point ({CURRENT_AREA[0][0]} {CURRENT_AREA[1][0]})")
    refresh_canvas()

def on_canvas_hover(event):
    global CURRENT_AREA, AREA_STATE, PICKER_VALUE, PICKER_COLOR, CANVAS_MOUSE_POS

    ev_x, ev_y = event.x, event.y
    CANVAS_MOUSE_POS = (ev_x, ev_y)
    rel_x = ev_x / canvas.winfo_width()
    rel_y = ev_y / canvas.winfo_height()
    click_list = [[ev_x, ev_y], [rel_x, rel_y]]

    valid_area_picking = True
    if (CURRENT_AREA is None) or isinstance(CURRENT_AREA, str):
        valid_area_picking = False
    elif len(CURRENT_AREA) < 5:
        valid_area_picking = False
    elif isinstance(CURRENT_AREA, list):
        if None not in CURRENT_AREA:
            valid_area_picking = False

    if not valid_area_picking:
        if PICKER_VALUE is not None:
            try:
                color = CURRENT_IMAGE.resize((canvas.image.width(), canvas.image.height())).getpixel((ev_x, ev_y))
            except IndexError:
                color = cfgs.CANVAS_BACKGROUND_COLOR
            PICKER_COLOR = color
        refresh_canvas()
        return

    CURRENT_AREA[AREA_STATE] = click_list

    set_status(level="prompt", text=f"place end point {AREA_STATE + 1} ({click_list[0][0]} {click_list[0][1]})")
    refresh_canvas()

def on_canvas_release(event):
    global CURRENT_AREA, AREA_STATE
    if CURRENT_AREA is None:
        return
    if len(CURRENT_AREA) == 3:
        del CURRENT_AREA[2]
    else:
        return

    # 00 has to be the min point, 10 - max
    CURRENT_AREA[0][0][0], CURRENT_AREA[0][0][1], CURRENT_AREA[1][0][0], CURRENT_AREA[1][0][1] = (
        min(CURRENT_AREA[0][0][0], CURRENT_AREA[1][0][0]), min(CURRENT_AREA[0][0][1], CURRENT_AREA[1][0][1]),
        max(CURRENT_AREA[0][0][0], CURRENT_AREA[1][0][0]), max(CURRENT_AREA[0][0][1], CURRENT_AREA[1][0][1])
    )

    refresh_canvas()
    set_status(level="info", text=f"area selected ({CURRENT_AREA[0][0]} {CURRENT_AREA[1][0]})")

def on_canvas_resize(*_):
    refresh_image()
    rescale_text_fits()

openfile_btn.config(command=open_new_image)
pastefile_btn.config(command=paste_new_image)
clearfile_btn.config(command=erase_image)

selectarea_btn.config(command=select_area)
cleararea_btn.config(command=clear_area)
areatype_btn.config(command=change_area_type)
detect_btn.config(command=detection_command)

canvas.bind("<Configure>", on_canvas_resize)
canvas.bind("<Button-1>", on_canvas_click)
canvas.bind("<B1-Motion>", on_canvas_motion)
canvas.bind("<Motion>", on_canvas_hover)
canvas.bind("<ButtonRelease-1>", on_canvas_release)

def theme_change_widget(widget):
    if widget == status_label:
        return

    widget_dict = widget.__dict__.get("cfg", {})
    base_dict = {}
    if isinstance(widget, tk.Frame) or isinstance(widget, tk.Canvas) or isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
        base_dict = dict(bg=cfgs.BACKGROUND_COLOR)
    elif isinstance(widget, tk.Label):
        base_dict = dict(bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, font=(cfgs.DEFAULT_FONT, widget.base_font))
    elif isinstance(widget, tk.Button):
        base_dict = dict(
            bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
            fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR, font=(cfgs.DEFAULT_FONT, widget.base_font)
        )
    elif isinstance(widget, tk.Entry):
        base_dict = dict(
            bg=cfgs.LIGHT_BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, highlightthickness=0,
            font=(cfgs.DEFAULT_FONT, widget.base_font)
        )
    elif isinstance(widget, tk.Checkbutton):
        base_dict = dict(
            bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR,
            activebackground=cfgs.BACKGROUND_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR,
            selectcolor=cfgs.BACKGROUND_COLOR, font=(cfgs.DEFAULT_FONT, widget.base_font),
        )
    if widget.__dict__.get("base_base_img"):
        new_data = []
        for pixel in widget.base_base_img.get_flattened_data():
            if all([pixel[i] > 200 for i in range(3)]):
                new_data.append(hex2rgb(cfgs.TEXT_COLOR) + (255,))
            else:
                new_data.append(pixel)
        base_dict["base_img"] = widget.base_img.putdata(new_data)
    for k in widget_dict:
        base_dict[k] = cfgs.get(widget_dict[k])
    widget.config(**base_dict)
def theme_process_widget(widget):
    if widget.__dict__.get("non_instant"):
        return
    theme_change_widget(widget)
    for w in widget.winfo_children():
        theme_process_widget(w)
def theme_change(theme_name):
    exists = cfgs.set_theme(theme_name)
    if not exists:
        set_status(level="error", text=f"theme with name \"{theme_name}\" does not exist")
        return
    theme_process_widget(window)
    rescale_text_fits()
    usettings.theme = theme_name

THEME_TOPLEVEL:tk.Toplevel = None
def theme_toplevel():
    global THEME_TOPLEVEL
    if THEME_TOPLEVEL is not None:
        THEME_TOPLEVEL.destroy()

    THEME_TOPLEVEL = tk.Toplevel(master=window, width=cfgs.DEFAULT_THEME_SELECT_WIDTH, height=cfgs.DEFAULT_THEME_SELECT_HEIGHT)
    THEME_TOPLEVEL.non_instant = True
    THEME_TOPLEVEL.title("Set theme")
    THEME_TOPLEVEL.config(bg=cfgs.BACKGROUND_COLOR)

    TL_TEXT_ELEMENTS = []

    def top_level_rescale_text_fits(*_):
        for el in TL_TEXT_ELEMENTS:
            new_size = (el.base_font / cfgs.DEFAULT_THEME_SELECT_HEIGHT) * THEME_TOPLEVEL.winfo_height()
            el.config(font=(cfgs.DEFAULT_FONT, int(new_size), el.__dict__.get("font_type", "normal")))

    theme_title = tk.Label(master=THEME_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, text="Theme")
    theme_title.base_font = 18
    theme_title.font_type = "bold"
    theme_title.config(font=(cfgs.DEFAULT_FONT, theme_title.base_font, theme_title.font_type))
    theme_title.place(relx=0.5, rely=0.02, relwidth=0.9, relheight=0.08, anchor="n")
    TL_TEXT_ELEMENTS.append(theme_title)

    style = ttk.Style()
    style.theme_use("clam")
    style.layout("TCombobox", [
        ('Combobox.field', {
            'sticky': 'nswe',
            'children': [
                ('Combobox.downarrow', {'side': 'right', 'sticky': 'ns'}),
                ('Combobox.padding', {
                    'sticky': 'nswe',
                    'children': [
                        ('Combobox.textarea', {'sticky': 'nswe'})
                    ]
                })
            ]
        })
    ])

    style.configure(
        "Vertical.TScrollbar",
        troughcolor=cfgs.BACKGROUND_COLOR,
        background=cfgs.LIGHT_BACKGROUND_COLOR,
        arrowcolor=cfgs.LIGHT_BACKGROUND_COLOR
    )
    style.configure(
        "TCombobox",
        arrowcolor=cfgs.LIGHTER_BACKGROUND_COLOR,
        background=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        bordercolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        lightcolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        darkcolor=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        fieldbackground=cfgs.INTERACT_COLOR,
        foreground=cfgs.TEXT_COLOR,
        padding=2,
        relief=tk.FLAT,
        selectbackground=cfgs.MIDLIGHT_BACKGROUND_COLOR,
        selectforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", cfgs.INTERACT_COLOR)],
        foreground=[("readonly", cfgs.TEXT_COLOR)],
        background=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        bordercolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        lightcolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)],
        darkcolor=[("focus", cfgs.MIDLIGHT_BACKGROUND_COLOR)]
    )
    style.map(
        "Vertical.TScrollbar",
        troughcolor=[("disabled", cfgs.BACKGROUND_COLOR)],
        background=[("disabled", cfgs.BACKGROUND_COLOR)],
        arrowcolor=[("disabled", cfgs.BACKGROUND_COLOR)]
    )
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.background", cfgs.LIGHT_BACKGROUND_COLOR)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.foreground", cfgs.TEXT_COLOR)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.selectBackground", cfgs.LIGHTER_BACKGROUND_COLOR)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.selectForeground", cfgs.HIGHLIGHT_TEXT_COLOR)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.font", cfgs.DEFAULT_FONT)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.relief", "flat")
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.borderWidth", 0)
    THEME_TOPLEVEL.option_add("*TCombobox*Listbox.highlightThickness", 0)

    using_collection = 0
    using_theme = 0
    theme_options = []
    for i, c in enumerate(cfgs.STYLES):
        theme_options.append(c[0])
        if cfgs.theme in c[1]:
            using_collection = i
            using_theme = c[1].index(cfgs.theme)

    coll_list = ttk.Combobox(THEME_TOPLEVEL, values=theme_options, style="TCombobox", state="readonly")
    coll_list.base_font = 16
    coll_list.current(using_collection)
    coll_list.place(relx=0.5, rely=0.12, relwidth=0.9, relheight=0.1, anchor="n")
    TL_TEXT_ELEMENTS.append(coll_list)

    theme_list = ttk.Combobox(master=THEME_TOPLEVEL, values=cfgs.STYLES[using_collection][1], style="TCombobox", state="readonly")
    theme_list.base_font = 16
    theme_list.current(using_theme)
    theme_list.place(relx=0.5, rely=0.24, relwidth=0.9, relheight=0.1, anchor="n")
    TL_TEXT_ELEMENTS.append(theme_list)

    text_frame = tk.Frame(master=THEME_TOPLEVEL, bg=cfgs.BACKGROUND_COLOR)
    text_frame.place(relx=0.5, rely=0.36, relwidth=0.95, relheight=0.49, anchor="n")

    text_scroll = ttk.Scrollbar(master=text_frame, orient=tk.VERTICAL)
    text_scroll.place(relx=1, rely=0, width=20, relheight=1, anchor="ne")

    text_box = tk.Text(master=text_frame, wrap=tk.WORD, yscrollcommand=text_scroll.set)
    text_box.config(bg=cfgs.BACKGROUND_COLOR, fg=cfgs.TEXT_COLOR, font=(cfgs.DEFAULT_FONT, 15))
    text_box.place(relx=0, rely=0, width=-20, relwidth=1, relheight=1)

    set_btn = tk.Button(master=THEME_TOPLEVEL)
    set_btn.base_font = 16
    set_btn.cfg = dict(
        bg="INTERACT_COLOR", activebackground="INTERACT_HIGHLIGHT_COLOR",
        fg="TEXT_COLOR", activeforeground="HIGHLIGHT_TEXT_COLOR"
    )
    set_btn.config(
        text="Select", bg=cfgs.INTERACT_COLOR, activebackground=cfgs.INTERACT_HIGHLIGHT_COLOR,
        fg=cfgs.TEXT_COLOR, activeforeground=cfgs.HIGHLIGHT_TEXT_COLOR
    )
    set_btn.place(relx=0.5, rely=0.98, relwidth=0.8, relheight=0.1, anchor="s")
    TL_TEXT_ELEMENTS.append(set_btn)

    # def dropdown_borders(event):
    #     print(event)
    #     path = str(event.widget)
    #
    #     popdown = f"{path}.popdown"
    #     listbox = f"{path}.popdown.f.l"
    #
    #     theme_list.tk.call(listbox, "configure", "-borderwidth", 0)
    #     theme_list.tk.call(listbox, "configure", "-highlightthickness", 0)
    #     theme_list.tk.call(listbox, "configure", "-relief", "flat")
    #
    #     theme_list.tk.call(popdown, "configure", "-padx", 0, "-pady", 0)
    #     theme_list.tk.call(popdown, "configure", "-borderwidth", 0)
    #     theme_list.tk.call(popdown, "configure", "-relief", "flat")
    #
    # theme_list.bind("<Button-1>", dropdown_borders)

    top_level_rescale_text_fits(None)

    THEME_TOPLEVEL.bind("<Configure>", top_level_rescale_text_fits)

    def on_close():
        global THEME_TOPLEVEL
        THEME_TOPLEVEL.destroy()
        THEME_TOPLEVEL = None

    def set_preview(_):
        # collection = coll_list.current()
        # theme = theme_list.current()
        theme_name = theme_list.get()
        text_box.configure(state="normal")
        text_box.delete("1.0", tk.END)
        style_dict = cfgs.MAIN_STYLE.get(theme_name)
        if style_dict is None:
            set_status(level="error", text=f"theme with name \"{theme_name}\" does not exist; cannot load data")
            return
        for o, k in enumerate(style_dict):
            v = style_dict[k]
            if isinstance(v, str):
                inv = invert_hex_color(v)
                if rgb_distance(hex2rgb(v), hex2rgb(inv)) < 60:
                    inv = rgb2hex(sum_rgb(hex2rgb(inv), (100, 100, 100)))
                text_box.tag_configure(k, background=v, foreground=inv)
            else:
                text_box.tag_configure(k, background=style_dict["BACKGROUND_COLOR"], foreground=style_dict["TEXT_COLOR"])
            text_box.insert(tk.END, f"{k} = {v}{cfgs.NL if o != len(style_dict) else ''}", k)
        text_box.configure(state="disabled")

    def refresh_themes(_):
        selected = coll_list.current()
        theme_list.config(values=cfgs.STYLES[selected][1])
        theme_list.current(0)
        set_preview(_)

    coll_list.bind("<<ComboboxSelected>>", refresh_themes)
    theme_list.bind("<<ComboboxSelected>>", set_preview)
    set_preview(None)

    def select():
        theme_change(theme_list.get())
        on_close()

    set_btn.config(command=select)

    THEME_TOPLEVEL.protocol("WM_DELETE_WINDOW", on_close)
    THEME_TOPLEVEL.focus_force()

add_topbar_menu(
    "File", 10, 0.05,
    [
        ("Open", open_new_image),
        ("Paste", paste_new_image),
        ("Close", erase_image)
    ]
)
add_topbar_menu(
    "Theme", 10, 0.06, [("[Advanced]", theme_toplevel)] +
    [(title, lambda t=title: theme_change(t)) for title in configs.MAIN_STYLE]
)
add_topbar_menu(
    "Settings", 10, 0.08,
    [
        ("Formula", formula_input),
        ("Binders", binder_toplevel),
        ("Reset Window", lambda: window.wm_geometry(f"{cfgs.DEFAULT_WINDOW_WIDTH}x{cfgs.DEFAULT_WINDOW_HEIGHT}"))
    ]
)
theme_change(cfgs.theme)

# img = cv2.imread("img_1.png")
# detect(img)
# cv2.waitKey(0)

journal_add(time.time(), "info", usettings.get_full_filepath())

tk.mainloop()
