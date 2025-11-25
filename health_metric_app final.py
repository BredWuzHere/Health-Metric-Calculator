import os
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, date
import calendar

#importing matplotlib for graphs
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

DB_FILENAME = "profiles.db"

BMI_CATEGORIES = [
    (0, 18.5, "Underweight"),
    (18.5, 24.9, "Normal"),
    (25.0, 29.9, "Overweight"),
    (30.0, 1000, "Obese"),
]

#  color & anim util
def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def interp(a, b, t):
    ra, ga, ba = hex_to_rgb(a)
    rb, gb, bb = hex_to_rgb(b)
    return rgb_to_hex((int(ra + (rb - ra) * t), int(ga + (gb - ga) * t), int(ba + (bb - ba) * t)))

# calculation helpers 
def calculate_bmi(weight_kg, height_cm):
    try:
        h_m = height_cm / 100.0
        bmi = weight_kg / (h_m * h_m)
        return round(bmi, 2)
    except Exception:
        return None

def bmi_category(bmi):
    for low, high, label in BMI_CATEGORIES:
        if bmi >= low and bmi <= high:
            return label
    return "Unknown"

def recommend_water_liters(bmi):
    if bmi is None: return 2.0
    cat = bmi_category(bmi)
    return {"Underweight":2.5,"Normal":3.0,"Overweight":3.5,"Obese":4.0}.get(cat,3.0)

def recommend_step_goal(bmi):
    if bmi is None: return 10000
    cat = bmi_category(bmi)
    return {"Underweight":11000,"Normal":10000,"Overweight":8000,"Obese":6000}.get(cat,10000)

def kg_to_lb(kg): return kg * 2.2046226218
def lb_to_kg(lb): return lb / 2.2046226218
def cm_to_inches(cm): return cm / 2.54
def inches_to_cm(inches): return inches * 2.54
def cm_to_ft_in(cm):
    total_inches = cm_to_inches(cm)
    ft = int(total_inches // 12)
    inches = round(total_inches - ft*12, 2)
    return ft, inches
def ft_in_to_cm(ft, inches): return inches_to_cm(ft*12 + inches)

# custom widgets

class CalendarPopup(tk.Toplevel):
    """A simple calendar widget that returns YYYY-MM-DD via callback(date_iso)."""
    def __init__(self, master, year=None, month=None, callback=None, theme_colors=None):
        super().__init__(master)
        self.transient(master); self.grab_set()
        self.callback = callback
        self.title("Select date"); self.resizable(False, False)

        today = date.today()
        self.year = year if year is not None else today.year
        self.month = month if month is not None else today.month

        self.theme = theme_colors or {}
        bg = self.theme.get('bg', '#f6f7fb')
        fg = self.theme.get('fg', '#000000')
        btn_bg = self.theme.get('btn_bg', '#ffffff')
        
        self.configure(bg=bg)

        hdr = ttk.Frame(self); hdr.pack(fill='x', padx=6, pady=6)
        prev = tk.Button(hdr, text='<', width=3, command=self._prev_month, bg=btn_bg, fg=fg, relief='flat')
        prev.pack(side='left')
        
        self.lbl_month = tk.Label(hdr, text='', anchor='center', width=18, bg=bg, fg=fg, font=('Helvetica', 10, 'bold'))
        self.lbl_month.pack(side='left', padx=6)
        
        nxt = tk.Button(hdr, text='>', width=3, command=self._next_month, bg=btn_bg, fg=fg, relief='flat')
        nxt.pack(side='left')

        self.body = tk.Frame(self, bg=bg); self.body.pack(padx=6, pady=(0,8))
        self._draw_calendar(fg, btn_bg)

    def _draw_calendar(self, fg_color, btn_bg):
        for w in self.body.winfo_children(): w.destroy()
        cal = calendar.monthcalendar(self.year, self.month)
        days = ['Mo','Tu','We','Th','Fr','Sa','Su']
        for c, d in enumerate(days):
            lbl = tk.Label(self.body, text=d, width=4, anchor='center', bg=self.body.cget('bg'), fg=fg_color)
            lbl.grid(row=0, column=c, padx=2, pady=2)
        for r, week in enumerate(cal, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    lbl = tk.Label(self.body, text='', width=4, bg=self.body.cget('bg'))
                    lbl.grid(row=r, column=c, padx=2, pady=2)
                else:
                    b = tk.Button(self.body, text=str(day), width=4, command=lambda d=day: self._select_day(d), 
                                  bg=btn_bg, fg=fg_color, relief='flat')
                    b.grid(row=r, column=c, padx=2, pady=2)
        self.lbl_month.config(text=f"{calendar.month_name[self.month]} {self.year}")

    def _prev_month(self):
        if self.month == 1:
            self.month = 12; self.year -= 1
        else:
            self.month -= 1
        self._draw_calendar(self.theme.get('fg', 'black'), self.theme.get('btn_bg', 'white'))

    def _next_month(self):
        if self.month == 12:
            self.month = 1; self.year += 1
        else:
            self.month += 1
        self._draw_calendar(self.theme.get('fg', 'black'), self.theme.get('btn_bg', 'white'))

    def _select_day(self, day):
        d = date(self.year, self.month, day).isoformat()
        if callable(self.callback):
            try: self.callback(d)
            except Exception: pass
        self.destroy()

class AnimatedToggle(ttk.Frame):
    def __init__(self, master, width=56, height=30, padding=3,
                 on_color='#4cd964', off_color='#e5e5ea', knob_color='#ffffff',
                 initial=False, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.width = width; self.height = height; self.padding = padding
        self.radius = (height - padding*2) // 2
        self.on_color = on_color; self.off_color = off_color; self.knob_color = knob_color
        self.state = initial; self.command = command
        try:
            master_bg = self.master.cget('background')
        except Exception:
            try: master_bg = self.master.winfo_toplevel().cget('bg')
            except Exception: master_bg = '#f6f7fb'
            
        self.canvas = tk.Canvas(self, width=width, height=height, highlightthickness=0, bg=master_bg)
        self.canvas.pack()
        self._draw_static()
        self.canvas.bind('<Button-1>', self.toggle)
        self.animating = False

    def _draw_static(self):
        self.canvas.delete('all')
        x0, y0 = 0, 0; x1, y1 = self.width, self.height
        r = self.radius + self.padding
        track_color = self._current_track_color()
        self.left_oval = self.canvas.create_oval(x0, y0, x0 + 2*r, y1, outline='', fill=track_color)
        self.right_oval = self.canvas.create_oval(x1 - 2*r, y0, x1, y1, outline='', fill=track_color)
        self.center_rect = self.canvas.create_rectangle(x0 + r, y0, x1 - r, y1, outline='', fill=track_color)
        knob_x = (self.width - self.height + 2*self.padding) if self.state else self.padding
        self.knob = self.canvas.create_oval(knob_x, self.padding, knob_x + self.height - 2*self.padding, self.height - self.padding, outline='', fill=self.knob_color)

    def _current_track_color(self):
        return self.on_color if self.state else self.off_color

    def toggle(self, event=None):
        self.set(not self.state)

    def set(self, value, animate=True):
        if self.animating: return
        old = self.state; self.state = bool(value)
        if animate:
            self.animating = True
            steps = 18
            start_t = 1.0 if old else 0.0
            end_t = 1.0 if self.state else 0.0
            def step(i):
                t = i / steps
                pos_t = start_t + (end_t - start_t) * t
                color = interp(self.off_color, self.on_color, pos_t)
                try:
                    self.canvas.itemconfig(self.left_oval, fill=color)
                    self.canvas.itemconfig(self.right_oval, fill=color)
                    self.canvas.itemconfig(self.center_rect, fill=color)
                except Exception: pass
                min_x = self.padding; max_x = self.width - self.height + self.padding
                x = int(min_x + (max_x - min_x) * pos_t)
                self.canvas.coords(self.knob, x, self.padding, x + self.height - 2*self.padding, self.height - self.padding)
                if i < steps:
                    self.after(12, lambda: step(i+1))
                else:
                    self.animating = False
                    if callable(self.command):
                        try: self.command(self.state)
                        except Exception: pass
            step(0)
        else:
            color = self._current_track_color()
            try:
                self.canvas.itemconfig(self.left_oval, fill=color)
                self.canvas.itemconfig(self.right_oval, fill=color)
                self.canvas.itemconfig(self.center_rect, fill=color)
            except Exception: pass
            min_x = self.padding; max_x = self.width - self.height + self.padding
            x = int(min_x if not self.state else max_x)
            self.canvas.coords(self.knob, x, self.padding, x + self.height - 2*self.padding, self.height - self.padding)
            if callable(self.command):
                try: self.command(self.state)
                except Exception: pass

    def update_colors(self, on_color=None, off_color=None, knob_color=None, canvas_bg=None):
        if on_color is not None: self.on_color = on_color
        if off_color is not None: self.off_color = off_color
        if knob_color is not None: self.knob_color = knob_color
        if canvas_bg is not None:
            try: self.canvas.configure(bg=canvas_bg)
            except Exception: pass
        try:
            current_track = self._current_track_color()
            self.canvas.itemconfig(self.left_oval, fill=current_track)
            self.canvas.itemconfig(self.right_oval, fill=current_track)
            self.canvas.itemconfig(self.center_rect, fill=current_track)
            self.canvas.itemconfig(self.knob, fill=self.knob_color)
        except Exception: pass

# main app
class HealthApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Health Metric Calculator 1.0.1")
        self.geometry("980x640"); self.minsize(900,600)
        self.folder = None; self.db_path = None; self.conn = None; self.current_profile_id = None
        self.unit_mode = tk.StringVar(value="Metric"); self.dark_mode = False

        self.light_theme = {
            'bg': '#f6f7fb',
            'panel': '#ffffff',
            'muted': '#6b7280',
            'accent': '#007aff',
            'button_bg': '#ffffff',
            'button_fg': '#111827',
            'tree_bg': '#ffffff',
            'border': '#e6e7eb',
            'entry_bg': '#ffffff',
            'entry_fg': '#111827'
        }
        self.dark_theme = {
            'bg': '#101827',
            'panel': '#1f2937', 
            'muted': '#9aa4b2',
            'accent': '#39a0a0',
            'button_bg': '#374151',
            'button_fg': '#f3f4f6',
            'tree_bg': '#111827',
            'border': '#374151',
            'entry_bg': '#374151', 
            'entry_fg': '#f3f4f6'
        }
        self.theme_t = 0.0

        self.style = ttk.Style(self)
        try: self.style.theme_use('clam')
        except Exception: pass

        self._setup_styles()
        self._build_ui()
        self.after(80, self._entrance_animation)

    def _setup_styles(self):
        default_font = ('Helvetica', 11)
        heading_font = ('Helvetica', 13, 'bold')
        big_font = ('Helvetica', 20, 'bold')

        self.style.configure('.', font=default_font, background=self.light_theme['bg'])
        self.style.configure('Secondary.TLabel', foreground=self.light_theme['muted'])
        self.style.configure('Header.TLabel', font=heading_font, background=self.light_theme['bg'])
        self.style.configure('Big.TLabel', font=big_font, background=self.light_theme['panel'])

        self.style.configure('Accent.TButton', relief='flat', padding=8, background=self.light_theme['accent'], foreground='#ffffff', font=('Helvetica', 10, 'bold'))
        self.style.map('Accent.TButton', background=[('active', self.light_theme['accent'])])

        self.style.configure('Ghost.TButton', relief='flat', padding=6, background=self.light_theme['button_bg'], foreground=self.light_theme['button_fg'])
        self.style.map('Ghost.TButton', background=[('active', self.light_theme['border'])])

        self.style.configure('Treeview', rowheight=28, background=self.light_theme['tree_bg'], fieldbackground=self.light_theme['tree_bg'])
        self.style.configure('Treeview.Heading', font=('Helvetica', 10, 'bold'))
        self.style.configure('Card.TFrame', background=self.light_theme['panel'], relief='flat')
        self.style.configure('TNotebook', background=self.light_theme['bg'])
        self.style.configure('TNotebook.Tab', padding=(12, 8), background=self.light_theme['panel'])

        self.configure(bg=self.light_theme['bg'])

    def _get_current_colors(self):
        """Helper to get current exact color codes based on theme_t"""
        t = self.theme_t
        def lerp(key): return interp(self.light_theme[key], self.dark_theme[key], t)
        return {k: lerp(k) for k in self.light_theme}

    def _apply_theme(self, t):
        colors = self._get_current_colors()
        bg = colors['bg']; panel = colors['panel']; muted = colors['muted']
        accent = colors['accent']; btn_bg = colors['button_bg']; btn_fg = colors['button_fg']
        tree_bg = colors['tree_bg']; border = colors['border']

        self.style.configure('.', background=bg)
        self.style.configure('Header.TLabel', background=bg, foreground=muted)
        self.style.configure('Secondary.TLabel', background=bg, foreground=muted)
        self.style.configure('Big.TLabel', background=panel, foreground=btn_fg)
        self.style.configure('Card.TFrame', background=panel)
        self.style.configure('Accent.TButton', background=accent, foreground='#ffffff')
        self.style.map('Accent.TButton', background=[('active', accent)])
        self.style.configure('Ghost.TButton', background=btn_bg, foreground=btn_fg)
        self.style.map('Ghost.TButton', background=[('active', border)])
        self.style.configure('Treeview', background=tree_bg, fieldbackground=tree_bg, foreground=btn_fg)
        self.style.configure('TNotebook.Tab', background=panel, foreground=btn_fg)
        self.style.configure('TNotebook', background=bg)

        self.configure(bg=bg)
        try: self.style.configure('.', foreground=btn_fg)
        except Exception: pass

        # Recursively apply colors to standard tk widgets (Entries, Text, Listbox)
        self._apply_widget_colors(self, colors)

        try:
            off_track = interp('#cfd1d5', '#374151', t)
            if hasattr(self, 'dm_toggle') and isinstance(self.dm_toggle, AnimatedToggle):
                self.dm_toggle.update_colors(on_color=accent, off_color=off_track, knob_color=btn_bg, canvas_bg=panel)
        except Exception: pass

    def _apply_widget_colors(self, widget, colors):
        """Recursively update standard TK widgets that don't respect TTK styles well."""
        panel = colors['panel']
        btn_fg = colors['button_fg']
        accent = colors['accent']
        border = colors['border']
        entry_bg = colors['entry_bg']
        entry_fg = colors['entry_fg']

        for child in widget.winfo_children():
            try: cname = child.winfo_class()
            except Exception: cname = ''
            
            try:
                # listboxes hndler
                if isinstance(child, tk.Listbox):
                    child.configure(bg=panel, fg=btn_fg, highlightbackground=border, 
                                    selectbackground=accent, selectforeground='#ffffff')
                
                # Text widgets hndler
                elif isinstance(child, tk.Text):
                    child.configure(bg=panel, fg=btn_fg, insertbackground=btn_fg)
                
                # standard entry widgets hndler
                elif isinstance(child, tk.Entry):
                    child.configure(bg=entry_bg, fg=entry_fg, 
                                    insertbackground=entry_fg, # Cursor color
                                    highlightthickness=1,
                                    highlightbackground=border,
                                    disabledbackground=panel,
                                    disabledforeground=colors['muted'])
                
                # handle labels that are not TTK
                elif isinstance(child, tk.Label):
                    child.configure(bg=panel, fg=btn_fg)

                # handle standard buttons
                elif isinstance(child, tk.Button):
                    child.configure(bg=colors['button_bg'], fg=colors['button_fg'])

                # handle canvas
                elif isinstance(child, tk.Canvas) and not isinstance(child.master, AnimatedToggle):
                    try: child.configure(bg=panel)
                    except Exception: pass

            except Exception: pass
            
            # recurse line (dont remove bruh)
            self._apply_widget_colors(child, colors)

    def toggle_dark_mode(self, state):
        target = 1.0 if state else 0.0; steps = 18; start = self.theme_t
        def step(i):
            nonlocal start
            t = start + (target - start) * (i/steps)
            self.theme_t = t; self._apply_theme(t)
            if i < steps: self.after(14, lambda: step(i+1))
            else: self.theme_t = target
        step(0)

    #  ui build
    def _build_ui(self):
        frm_top = ttk.Frame(self, padding=(12,10), style='Card.TFrame'); frm_top.pack(side="top", fill="x", padx=12, pady=12)

        left_ctrl = ttk.Frame(frm_top, style='Card.TFrame'); left_ctrl.pack(side='left', anchor='w')
        self.btn_open = ttk.Button(left_ctrl, text="Open Directory", command=self.open_directory, style='Accent.TButton')
        self.btn_open.pack(side='left', padx=(0,8))
        self.btn_load = ttk.Button(left_ctrl, text="Load Profile", command=self.load_profile, state="disabled", style='Ghost.TButton'); self.btn_load.pack(side='left', padx=4)
        self.btn_new = ttk.Button(left_ctrl, text="New Profile", command=self.new_profile, state="disabled", style='Ghost.TButton'); self.btn_new.pack(side='left', padx=4)
        self.btn_delete = ttk.Button(left_ctrl, text="Delete Profile", command=self.delete_profile, state="disabled", style='Ghost.TButton'); self.btn_delete.pack(side='left', padx=4)

        ttk.Label(frm_top, text='').pack(side='left', expand=True)

        right_ctrl = ttk.Frame(frm_top, style='Card.TFrame'); right_ctrl.pack(side='right')
        ttk.Label(right_ctrl, text="Units:").pack(side='left', padx=(0,6))
        units_combo = ttk.Combobox(right_ctrl, textvariable=self.unit_mode, values=["Metric","Imperial"], state="readonly", width=9); units_combo.pack(side='left')
        units_combo.bind("<<ComboboxSelected>>", lambda e: self.on_unit_change())

        dmfrm = ttk.Frame(right_ctrl); dmfrm.pack(side='left', padx=(12,0))
        ttk.Label(dmfrm, text='Dark').pack(side='left', padx=(0,6))
        self.dm_toggle = AnimatedToggle(dmfrm, initial=False, command=self.toggle_dark_mode); self.dm_toggle.pack(side='left')

        self.lbl_dir = ttk.Label(self, text="No directory selected", style='Secondary.TLabel'); self.lbl_dir.pack(side='top', anchor='w', padx=20)

        content = ttk.Frame(self, padding=12, style='Card.TFrame'); content.pack(fill='both', expand=True, padx=12, pady=(8,12))
        left = ttk.Frame(content, width=280, style='Card.TFrame'); left.pack(side='left', fill='y', padx=(0,12))
        ttk.Label(left, text="Profiles", style='Header.TLabel').pack(anchor='nw')
        self.profile_list = tk.Listbox(left, height=28, bd=0, highlightthickness=0, activestyle='none'); self.profile_list.pack(fill='y', expand=True, pady=8)
        self.profile_list.bind("<<ListboxSelect>>", self.on_profile_select)

        btn_frame = ttk.Frame(left, style='Card.TFrame'); btn_frame.pack(fill='x', pady=6)

        right = ttk.Frame(content, style='Card.TFrame'); right.pack(side='left', fill='both', expand=True)
        self.notebook = ttk.Notebook(right); self.notebook.pack(fill='both', expand=True)

        # BMI tab
        self.tab_bmi = ttk.Frame(self.notebook, padding=12, style='Card.TFrame'); self.notebook.add(self.tab_bmi, text='BMI')
        self.bmi_value_var = tk.StringVar(value="—"); self.bmi_cat_var = tk.StringVar(value="—")
        ttk.Label(self.tab_bmi, text="BMI:", style='Header.TLabel').pack(anchor='nw')
        ttk.Label(self.tab_bmi, textvariable=self.bmi_value_var, style='Big.TLabel').pack(anchor='nw', pady=(6,0))
        ttk.Label(self.tab_bmi, text="Category:", style='Header.TLabel').pack(anchor='nw', pady=(10,0))
        ttk.Label(self.tab_bmi, textvariable=self.bmi_cat_var).pack(anchor='nw')
        ttk.Separator(self.tab_bmi, orient='horizontal').pack(fill='x', pady=10)
        frm_bmi_actions = ttk.Frame(self.tab_bmi); frm_bmi_actions.pack(anchor='nw', pady=5)
        ttk.Button(frm_bmi_actions, text="Edit BMI / Update Profile", command=self.edit_bmi, style='Accent.TButton').pack(side='left', padx=5)
        ttk.Button(frm_bmi_actions, text="Recalculate (from stored height/weight)", command=self.recalculate_bmi, style='Ghost.TButton').pack(side='left', padx=5)

        # steps tab
        self.tab_steps = ttk.Frame(self.notebook, padding=10, style='Card.TFrame'); self.notebook.add(self.tab_steps, text='Steps Tracker')
        self.step_goal_var = tk.StringVar(value='—')
        ttk.Label(self.tab_steps, text='Recommended daily step goal:').pack(anchor='nw')
        ttk.Label(self.tab_steps, textvariable=self.step_goal_var, font=('Helvetica', 16, 'bold')).pack(anchor='nw')
        frm_steps_log = ttk.Frame(self.tab_steps); frm_steps_log.pack(anchor='nw', pady=6)
        ttk.Label(frm_steps_log, text='Date (YYYY-MM-DD):').grid(row=0, column=0, sticky='w')
        self.steps_date_entry = tk.Entry(frm_steps_log, width=15, relief='flat'); self.steps_date_entry.grid(row=0, column=1, padx=5, ipady=3)
        self.steps_date_entry.insert(0, date.today().isoformat())
        cal_btn = ttk.Button(frm_steps_log, text='📅', width=3, command=lambda e=self.steps_date_entry: self.open_calendar_for(e), style='Ghost.TButton'); cal_btn.grid(row=0, column=2, padx=(4,0))
        ttk.Label(frm_steps_log, text='Steps:').grid(row=1, column=0, sticky='w')
        self.steps_entry = tk.Entry(frm_steps_log, width=15, relief='flat'); self.steps_entry.grid(row=1, column=1, padx=5, ipady=3)
        ttk.Button(frm_steps_log, text='Add / Update', command=self.save_steps, style='Accent.TButton').grid(row=2, column=0, columnspan=3, pady=8)
        frm_steps_actions = ttk.Frame(self.tab_steps); frm_steps_actions.pack(anchor='nw', pady=5)
        ttk.Button(frm_steps_actions, text='Show Steps Graph', command=self.plot_steps, style='Ghost.TButton').pack(side='left', padx=5)
        self.steps_tree = ttk.Treeview(self.tab_steps, columns=("date","steps"), show='headings', height=12)
        self.steps_tree.heading('date', text='Date'); self.steps_tree.heading('steps', text='Steps')
        self.steps_tree.column('date', width=150, anchor='center'); self.steps_tree.column('steps', width=120, anchor='center')
        self.steps_tree.pack(fill='both', expand=True, pady=6)

        # water tab
        self.tab_water = ttk.Frame(self.notebook, padding=10, style='Card.TFrame'); self.notebook.add(self.tab_water, text='Water Intake')
        self.water_rec_var = tk.StringVar(value='—')
        ttk.Label(self.tab_water, text='Recommended daily water intake:').pack(anchor='nw')
        ttk.Label(self.tab_water, textvariable=self.water_rec_var, font=('Helvetica', 16, 'bold')).pack(anchor='nw')
        frm_water_log = ttk.Frame(self.tab_water); frm_water_log.pack(anchor='nw', pady=6)
        ttk.Label(frm_water_log, text='Date (YYYY-MM-DD):').grid(row=0, column=0, sticky='w')
        self.water_date_entry = tk.Entry(frm_water_log, width=15, relief='flat'); self.water_date_entry.grid(row=0, column=1, padx=5, ipady=3)
        self.water_date_entry.insert(0, date.today().isoformat())
        wcal_btn = ttk.Button(frm_water_log, text='📅', width=3, command=lambda e=self.water_date_entry: self.open_calendar_for(e), style='Ghost.TButton'); wcal_btn.grid(row=0, column=2, padx=(4,0))
        ttk.Label(frm_water_log, text='Amount (ml):').grid(row=1, column=0, sticky='w')
        self.water_entry = tk.Entry(frm_water_log, width=15, relief='flat'); self.water_entry.grid(row=1, column=1, padx=5, ipady=3)
        ttk.Button(frm_water_log, text='Add / Update', command=self.save_water, style='Accent.TButton').grid(row=2, column=0, columnspan=3, pady=8)
        frm_water_actions = ttk.Frame(self.tab_water); frm_water_actions.pack(anchor='nw', pady=5)
        ttk.Button(frm_water_actions, text='Show Water Graph', command=self.plot_water, style='Ghost.TButton').pack(side='left', padx=5)
        self.water_tree = ttk.Treeview(self.tab_water, columns=("date","ml"), show='headings', height=12)
        self.water_tree.heading('date', text='Date'); self.water_tree.heading('ml', text='Amount (ml)')
        self.water_tree.column('date', width=150, anchor='center'); self.water_tree.column('ml', width=120, anchor='center')
        self.water_tree.pack(fill='both', expand=True, pady=6)

        # insights / reco tab
        self.tab_recs = ttk.Frame(self.notebook, padding=12, style='Card.TFrame')
        self.notebook.add(self.tab_recs, text='Insights')
        ttk.Label(self.tab_recs, text="Health Insights & Recommendations", style='Header.TLabel').pack(anchor='nw', pady=(0, 10))
        self.txt_recs = tk.Text(self.tab_recs, height=18, width=50, bd=0, highlightthickness=0, font=('Helvetica', 11), wrap='word')
        self.txt_recs.pack(fill='both', expand=True, padx=5, pady=5)
        self.txt_recs.config(state='disabled')

        # abt tab
        self.tab_about = ttk.Frame(self.notebook, padding=12, style='Card.TFrame')
        self.notebook.add(self.tab_about, text='About')
        about_inner = ttk.Frame(self.tab_about, style='Card.TFrame')
        about_inner.pack(expand=True, fill='both', padx=20, pady=40)
        ttk.Label(about_inner, text="CS121 Advanced Computer Programming", style='Header.TLabel').pack(anchor='center', pady=(10, 5))
        ttk.Label(about_inner, text="BSU Project", style='Big.TLabel').pack(anchor='center', pady=(0, 20))
        about_text = ("This is a project for CS121 advanced computer programming in BSU,\n"
                      "made using Python and the Tkinter.\n\n"
                      "It also includes SQLite integration that supports\n"
                      "CRUD operations (Create, Read, Update, Delete).")
        ttk.Label(about_inner, text=about_text, justify='center', font=('Helvetica', 11)).pack(anchor='center')


        # How to use
        self.tab_how = ttk.Frame(self.notebook, padding=12, style='Card.TFrame')
        self.notebook.add(self.tab_how, text='How to use') 
        how_inner = ttk.Frame(self.tab_how, style='Card.TFrame')
        how_inner.pack(expand=True, fill='both', padx=20, pady=40)
        ttk.Label(how_inner, text="Getting Started with the App", style='Header.TLabel').pack(anchor='center', pady=(10, 5))
        ttk.Label(how_inner, text="Simple, Effective Health Tracking", style='Big.TLabel').pack(anchor='center', pady=(0, 20))
        how_to_use_text = (
            "1. Click \"Open Directory\" to select a folder where your data will be saved (profiles.db).\n\n"
            "2. Click \"New Profile\" to create your user entry, calculating your BMI and setting goals.\n\n"
            "3. Select and \"Load Profile\" from the list.\n\n"
            "4. Navigate to the Steps Tracker and Water Intake tabs and enter your daily data.\n\n"
            "It's that simple! You can also delete, update, and share your profile data."
        )
        ttk.Label(how_inner, text=how_to_use_text, justify='left', font=('Helvetica', 11)).pack(anchor='center')
        
        # apply theme
        self._apply_theme(self.theme_t)

    # calendar helper
    def open_calendar_for(self, entry_widget):
        txt = entry_widget.get().strip()
        try:
            d = datetime.fromisoformat(txt).date()
            year, month = d.year, d.month
        except Exception:
            today = date.today(); year, month = today.year, today.month
        
        # pass current theme colors to calendar
        colors = self._get_current_colors()
        theme_args = {'bg': colors['panel'], 'fg': colors['button_fg'], 'btn_bg': colors['button_bg']}
        
        CalendarPopup(self, year=year, month=month, callback=lambda iso: (entry_widget.delete(0, tk.END), entry_widget.insert(0, iso)), theme_colors=theme_args)

    # entrance anim
    def _entrance_animation(self):
        x = self.winfo_x(); y = max(100, self.winfo_y() + 50); target_y = self.winfo_y(); steps = 12
        def step(i):
            if i > steps: return
            new_y = int(target_y + (50 * (1 - i/steps)))
            self.geometry(f"+{x}+{new_y}")
            self.after(10, lambda: step(i+1))
        step(0)

    # DB management
    def open_directory(self):
        folder = filedialog.askdirectory(title="Select folder to store profiles")
        if not folder: return
        self.folder = folder; self.db_path = os.path.join(self.folder, DB_FILENAME)
        first_time = not os.path.exists(self.db_path)
        self.lbl_dir.config(text=self.folder)
        self._init_db()
        self.btn_load.config(state="normal"); self.btn_new.config(state="normal"); self.btn_delete.config(state="normal")
        self.refresh_profiles_list()
        if first_time:
            messagebox.showinfo("New directory", "No database found in the chosen folder. A new database was created. Please create a new profile now.")
            self.new_profile()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                height_cm REAL,
                weight_kg REAL,
                bmi REAL,
                category TEXT,
                water_l REAL,
                step_goal INTEGER,
                created_at TEXT
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER,
                date TEXT,
                steps INTEGER,
                UNIQUE(profile_id, date)
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS water_logs (
                id INTEGER PRIMARY KEY,
                profile_id INTEGER,
                date TEXT,
                ml INTEGER,
                UNIQUE(profile_id, date)
            );
        """)
        self.conn.commit()

    # profiles CRUD
    def refresh_profiles_list(self):
        if not self.conn: return
        cur = self.conn.cursor(); cur.execute("SELECT id, name FROM profiles ORDER BY name;"); rows = cur.fetchall()
        self.profile_list.delete(0, tk.END)
        for r in rows: self.profile_list.insert(tk.END, f"{r[0]}: {r[1]}")

    def new_profile(self):
        if not self.conn: messagebox.showwarning("No directory", "Please select a directory first."); return
        
        popup = tk.Toplevel(self); popup.title("Create New Profile"); popup.transient(self); popup.grab_set()
        
        colors = self._get_current_colors()
        popup.configure(bg=colors['panel'])
        
        pf = tk.Frame(popup, bg=colors['panel'])
        pf.pack(fill='both', expand=True, padx=20, pady=20)
        
        lbl_style = {'bg': colors['panel'], 'fg': colors['button_fg']}
        ent_config = {'bg': colors['entry_bg'], 'fg': colors['entry_fg'], 'insertbackground': colors['entry_fg'], 'relief': 'flat'}

        tk.Label(pf, text="Name:", **lbl_style).grid(row=0, column=0, sticky="w", padx=8, pady=8)
        name_ent = tk.Entry(pf, **ent_config); name_ent.grid(row=0, column=1, padx=8, pady=8, ipady=3)
        
        unit = self.unit_mode.get()
        if unit == "Metric":
            tk.Label(pf, text="Height (cm):", **lbl_style).grid(row=1, column=0, sticky="w", padx=8, pady=8)
            height_ent = tk.Entry(pf, **ent_config); height_ent.grid(row=1, column=1, padx=8, pady=8, ipady=3)
            
            tk.Label(pf, text="Weight (kg):", **lbl_style).grid(row=2, column=0, sticky="w", padx=8, pady=8)
            weight_ent = tk.Entry(pf, **ent_config); weight_ent.grid(row=2, column=1, padx=8, pady=8, ipady=3)
        else:
            tk.Label(pf, text="Height - ft:in (eg '5 11')", **lbl_style).grid(row=1, column=0, sticky="w", padx=8, pady=8)
            height_ft = tk.Entry(pf, **ent_config); height_ft.grid(row=1, column=1, padx=8, pady=8, ipady=3)
            
            tk.Label(pf, text="Weight (lb):", **lbl_style).grid(row=2, column=0, sticky="w", padx=8, pady=8)
            weight_ent = tk.Entry(pf, **ent_config); weight_ent.grid(row=2, column=1, padx=8, pady=8, ipady=3)

        def create_and_close():
            name = name_ent.get().strip()
            if not name: messagebox.showerror("Missing name", "Please enter a name for the profile."); return
            try:
                if unit == "Metric":
                    height_cm = float(height_ent.get()); weight_kg = float(weight_ent.get())
                else:
                    parts = str(height_ft.get()).strip().split()
                    if len(parts) >= 2: ft = float(parts[0]); inches = float(parts[1])
                    elif len(parts) == 1 and parts[0] != "": ft = float(parts[0]); inches = 0.0
                    else: ft = 0.0; inches = 0.0
                    height_cm = ft_in_to_cm(ft, inches); weight_kg = lb_to_kg(float(weight_ent.get()))
            except Exception:
                messagebox.showerror("Invalid input", "Please enter valid numeric values for height and weight."); return
            bmi = calculate_bmi(weight_kg, height_cm); cat = bmi_category(bmi); water_l = recommend_water_liters(bmi); step_goal = recommend_step_goal(bmi)
            cur = self.conn.cursor(); cur.execute("""INSERT OR REPLACE INTO profiles (name, height_cm, weight_kg, bmi, category, water_l, step_goal, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?);""", (name, height_cm, weight_kg, bmi, cat, water_l, step_goal, datetime.now().isoformat()))
            self.conn.commit(); popup.destroy(); self.refresh_profiles_list(); cur.execute("SELECT id FROM profiles WHERE name=?;", (name,)); row = cur.fetchone()
            if row: self.load_profile(profile_id=row[0])

        ttk.Button(pf, text="Create", command=create_and_close, style='Accent.TButton').grid(row=3, column=0, columnspan=2, pady=12)

    def on_profile_select(self, event):
        if not self.conn: return
        sel = self.profile_list.curselection(); 
        if not sel: return
        text = self.profile_list.get(sel[0]); pid = int(text.split(":",1)[0]); self.load_profile(profile_id=pid)

    def load_profile(self, profile_id=None):
        if not self.conn: messagebox.showwarning("No directory", "Please select a directory first."); return
        
        if profile_id is None:
            sel = self.profile_list.curselection()
            if not sel:
                rows = self.conn.execute("SELECT id, name FROM profiles ORDER BY name;").fetchall()
                if not rows: messagebox.showinfo("No profiles", "No profiles available. Create a new profile first."); return
                
                popup = tk.Toplevel(self); popup.title("Load Profile"); popup.transient(self); popup.grab_set()
                colors = self._get_current_colors()
                popup.configure(bg=colors['panel'])
                
                lb = tk.Listbox(popup, bg=colors['panel'], fg=colors['button_fg'], highlightbackground=colors['border'])
                lb.pack(fill='both', expand=True, padx=10, pady=10)
                for r in rows: lb.insert(tk.END, f"{r[0]}: {r[1]}")
                
                def on_choose():
                    s = lb.curselection()
                    if not s: return
                    txt = lb.get(s[0])
                    pid = int(txt.split(":",1)[0])
                    popup.destroy()
                    self.load_profile(profile_id=pid)
                    
                ttk.Button(popup, text="Load", command=on_choose, style='Accent.TButton').pack(pady=(0,10))
                self.wait_window(popup)
                return
            else:
                text = self.profile_list.get(sel[0]); profile_id = int(text.split(":",1)[0])
        
        if not profile_id: return 

        cur = self.conn.cursor()
        cur.execute("SELECT id, name, height_cm, weight_kg, bmi, category, water_l, step_goal FROM profiles WHERE id=?;", (profile_id,))
        row = cur.fetchone()
        if not row: messagebox.showerror("Not found", "Profile not found."); return
        self.current_profile_id = row[0]; self.title(f"Health Metric Calculator — {row[1]}")
        self.bmi_value_var.set(str(row[4])); self.bmi_cat_var.set(row[5]); self.step_goal_var.set(f"{row[7]} steps"); self.water_rec_var.set(f"{row[6]} L")
        self.refresh_steps_view(); self.refresh_water_view(); self.refresh_recommendations()

    def delete_profile(self):
        if not self.conn: return
        sel = self.profile_list.curselection(); 
        if not sel: messagebox.showinfo("Select profile", "Please select a profile from the list to delete."); return
        text = self.profile_list.get(sel[0]); pid = int(text.split(":",1)[0])
        confirm = messagebox.askyesno("Confirm delete", "Delete profile and all associated logs? This cannot be undone.")
        if not confirm: return
        cur = self.conn.cursor(); cur.execute("DELETE FROM steps WHERE profile_id=?;", (pid,)); cur.execute("DELETE FROM water_logs WHERE profile_id=?;", (pid,)); cur.execute("DELETE FROM profiles WHERE id=?;", (pid,))
        self.conn.commit(); self.current_profile_id = None; self.title("Health Metric Calculator"); self.refresh_profiles_list(); self.bmi_value_var.set("—"); self.bmi_cat_var.set("—"); self.step_goal_var.set("—"); self.water_rec_var.set("—")
        for t in self.steps_tree.get_children(): self.steps_tree.delete(t)
        for t in self.water_tree.get_children(): self.water_tree.delete(t)
        self.txt_recs.config(state='normal'); self.txt_recs.delete("1.0", tk.END); self.txt_recs.config(state='disabled')

    def edit_bmi(self):
        if not self.conn: messagebox.showwarning("No directory", "Please select a directory first."); return
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load or create a profile first."); return
        cur = self.conn.cursor(); cur.execute("SELECT name, height_cm, weight_kg FROM profiles WHERE id=?;", (self.current_profile_id,)); row = cur.fetchone()
        if not row: messagebox.showerror("Not found", "Profile not found."); return
        
        popup = tk.Toplevel(self); popup.title("Edit BMI / Profile Data"); popup.transient(self); popup.grab_set()
        colors = self._get_current_colors()
        popup.configure(bg=colors['panel'])
        pf = tk.Frame(popup, bg=colors['panel'])
        pf.pack(fill='both', expand=True, padx=20, pady=20)
        
        lbl_style = {'bg': colors['panel'], 'fg': colors['button_fg']}
        ent_config = {'bg': colors['entry_bg'], 'fg': colors['entry_fg'], 'insertbackground': colors['entry_fg'], 'relief': 'flat'}

        tk.Label(pf, text=f"Name: {row[0]}", **lbl_style).grid(row=0, column=0, columnspan=2, sticky="w", padx=8, pady=8)
        
        unit = self.unit_mode.get()
        if unit == "Metric":
            tk.Label(pf, text="Height (cm):", **lbl_style).grid(row=1, column=0, sticky="w", padx=8, pady=8)
            h_ent = tk.Entry(pf, **ent_config); h_ent.grid(row=1, column=1, padx=8, pady=8, ipady=3); h_ent.insert(0, str(row[1]))
            
            tk.Label(pf, text="Weight (kg):", **lbl_style).grid(row=2, column=0, sticky="w", padx=8, pady=8)
            w_ent = tk.Entry(pf, **ent_config); w_ent.grid(row=2, column=1, padx=8, pady=8, ipady=3); w_ent.insert(0, str(row[2]))
        else:
            ft, inches = cm_to_ft_in(row[1])
            tk.Label(pf, text="Height - ft:in (enter as 'ft inches')", **lbl_style).grid(row=1, column=0, sticky="w", padx=8, pady=8)
            h_ent = tk.Entry(pf, **ent_config); h_ent.grid(row=1, column=1, padx=8, pady=8, ipady=3); h_ent.insert(0, f"{ft} {inches}")
            
            tk.Label(pf, text="Weight (lb):", **lbl_style).grid(row=2, column=0, sticky="w", padx=8, pady=8)
            w_ent = tk.Entry(pf, **ent_config); w_ent.grid(row=2, column=1, padx=8, pady=8, ipady=3); w_ent.insert(0, f"{round(kg_to_lb(row[2]),2)}")

        def save_changes():
            try:
                if unit == "Metric": h = float(h_ent.get()); w = float(w_ent.get())
                else:
                    parts = str(h_ent.get()).strip().split()
                    if len(parts) >= 2: ft = float(parts[0]); inches = float(parts[1])
                    elif len(parts) == 1: ft = float(parts[0]); inches = 0.0
                    else: ft = 0.0; inches = 0.0
                    h = ft_in_to_cm(ft, inches); w = lb_to_kg(float(w_ent.get()))
            except Exception:
                messagebox.showerror("Invalid", "Enter numeric values for height and weight."); return
            bmi = calculate_bmi(w, h); cat = bmi_category(bmi); water_l = recommend_water_liters(bmi); step_goal = recommend_step_goal(bmi)
            cur.execute("UPDATE profiles SET height_cm=?, weight_kg=?, bmi=?, category=?, water_l=?, step_goal=? WHERE id=?;", (h, w, bmi, cat, water_l, step_goal, self.current_profile_id))
            self.conn.commit(); popup.destroy(); self.load_profile(profile_id=self.current_profile_id)

        ttk.Button(pf, text="Save", command=save_changes, style='Accent.TButton').grid(row=3, column=0, columnspan=2, pady=12)

    def recalculate_bmi(self):
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load a profile first."); return
        cur = self.conn.cursor(); cur.execute("SELECT height_cm, weight_kg FROM profiles WHERE id=?;", (self.current_profile_id,)); row = cur.fetchone()
        if not row: return
        bmi = calculate_bmi(row[1], row[0]); cat = bmi_category(bmi); water_l = recommend_water_liters(bmi); step_goal = recommend_step_goal(bmi)
        cur.execute("UPDATE profiles SET bmi=?, category=?, water_l=?, step_goal=? WHERE id=?;", (bmi, cat, water_l, step_goal, self.current_profile_id))
        self.conn.commit(); self.load_profile(profile_id=self.current_profile_id)

    # steps & water logging
    def save_steps(self):
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load or create a profile first."); return
        try: d = datetime.fromisoformat(self.steps_date_entry.get()).date().isoformat()
        except Exception: messagebox.showerror("Invalid date", "Please enter date in YYYY-MM-DD format."); return
        try: steps = int(self.steps_entry.get())
        except Exception: messagebox.showerror("Invalid steps", "Enter a whole number for steps."); return
        cur = self.conn.cursor(); cur.execute("INSERT INTO steps (profile_id, date, steps) VALUES (?, ?, ?) ON CONFLICT(profile_id, date) DO UPDATE SET steps=excluded.steps;", (self.current_profile_id, d, steps)); self.conn.commit(); messagebox.showinfo("Saved", "Steps saved."); self.refresh_steps_view(); self.refresh_recommendations()

    def refresh_steps_view(self):
        for r in self.steps_tree.get_children(): self.steps_tree.delete(r)
        if not self.current_profile_id: return
        cur = self.conn.cursor(); rows = cur.execute("SELECT date, steps FROM steps WHERE profile_id=? ORDER BY date DESC LIMIT 100;", (self.current_profile_id,)).fetchall()
        for r in rows: self.steps_tree.insert("", "end", values=(r[0], r[1]))

    def save_water(self):
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load or create a profile first."); return
        try: d = datetime.fromisoformat(self.water_date_entry.get()).date().isoformat()
        except Exception: messagebox.showerror("Invalid date", "Please enter date in YYYY-MM-DD format."); return
        try: ml = int(self.water_entry.get())
        except Exception: messagebox.showerror("Invalid amount", "Enter a whole number for ml."); return
        cur = self.conn.cursor(); cur.execute("INSERT INTO water_logs (profile_id, date, ml) VALUES (?, ?, ?) ON CONFLICT(profile_id, date) DO UPDATE SET ml=excluded.ml;", (self.current_profile_id, d, ml)); self.conn.commit(); messagebox.showinfo("Saved", "Water log saved."); self.refresh_water_view(); self.refresh_recommendations()

    def refresh_water_view(self):
        for r in self.water_tree.get_children(): self.water_tree.delete(r)
        if not self.current_profile_id: return
        cur = self.conn.cursor(); rows = cur.execute("SELECT date, ml FROM water_logs WHERE profile_id=? ORDER BY date DESC LIMIT 100;", (self.current_profile_id,)).fetchall()
        for r in rows: self.water_tree.insert("", "end", values=(r[0], r[1]))

    def refresh_recommendations(self):
        if not self.current_profile_id or not self.conn:
            self._update_rec_text("Please load a profile to see recommendations.")
            return

        cur = self.conn.cursor()

        #  analyze BMI
        cur.execute("SELECT bmi, category, step_goal, water_l FROM profiles WHERE id=?", (self.current_profile_id,))
        p_row = cur.fetchone()
        if not p_row: return
        bmi, cat, s_goal, w_goal_l = p_row
        
        lines = []
        lines.append(f"• BMI Status: {cat} ({bmi})")
        if cat == "Overweight" or cat == "Obese":
            lines.append("  Tip: Focus on a slight caloric deficit and consistent cardio.")
        elif cat == "Underweight":
            lines.append("  Tip: Ensure you are eating enough nutrient-dense foods.")
        else:
            lines.append("  Tip: Maintain your current routine!")
        lines.append("-" * 40)

        # analyze Steps
        cur.execute("SELECT count(*), avg(steps) FROM steps WHERE profile_id=?", (self.current_profile_id,))
        s_count, s_avg = cur.fetchone()
        s_avg = int(s_avg) if s_avg else 0

        lines.append(f"• Steps Analysis ({s_count} entries)")
        if s_count < 5:
            lines.append(f"  Result: Lacking Data (Need {5 - s_count} more entries)")
            lines.append("  Advice: Log your steps daily to get a personalized analysis.")
        else:
            diff = s_avg - s_goal
            if diff >= 0:
                lines.append(f"  Result: Excellent! Averaging {s_avg} steps.")
                lines.append("  Advice: You are consistently beating your goal. Consider raising it!")
            else:
                lines.append(f"  Result: Averaging {s_avg} steps (Goal: {s_goal})")
                lines.append(f"  Advice: You are under by ~{abs(diff)} steps. Try a 10-minute walk after dinner.")
        lines.append("-" * 40)

        #  analyze water (Convert L to ml for comparison)
        w_goal_ml = w_goal_l * 1000
        cur.execute("SELECT count(*), avg(ml) FROM water_logs WHERE profile_id=?", (self.current_profile_id,))
        w_count, w_avg = cur.fetchone()
        w_avg = int(w_avg) if w_avg else 0

        lines.append(f"• Hydration Analysis ({w_count} entries)")
        if w_count < 5:
            lines.append(f"  Result: Lacking Data (Need {5 - w_count} more entries)")
            lines.append("  Advice: Track your water intake for a few more days.")
        else:
            if w_avg >= (w_goal_ml * 0.9):
                lines.append(f"  Result: Great hydration! Averaging {w_avg} ml.")
                lines.append("  Advice: Keep it up. Clear skin and energy come from water.")
            else:
                lines.append(f"  Result: Averaging {w_avg} ml (Goal: {int(w_goal_ml)} ml)")
                lines.append("  Advice: Try carrying a water bottle with you to meet your target.")

        final_text = "\n".join(lines)
        self._update_rec_text(final_text)

    def _update_rec_text(self, text):
        self.txt_recs.config(state='normal')
        self.txt_recs.delete("1.0", tk.END)
        self.txt_recs.insert("1.0", text)
        self.txt_recs.config(state='disabled')

    # plotting
    def plot_steps(self):
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load a profile first."); return
        if plt is None: messagebox.showerror("Plotting unavailable", "matplotlib not installed. Install with: pip install matplotlib"); return
        
        cur = self.conn.cursor(); rows = cur.execute("SELECT date, steps FROM steps WHERE profile_id=? ORDER BY date ASC;", (self.current_profile_id,)).fetchall()
        if not rows: messagebox.showinfo("No data", "No steps data to plot."); return
        
        dates = [r[0] for r in rows]; values = [r[1] for r in rows]
        
        # Get current theme colors
        c = self._get_current_colors()
        
        with plt.rc_context({
            'axes.facecolor': c['panel'],
            'figure.facecolor': c['bg'],
            'text.color': c['button_fg'],
            'xtick.color': c['button_fg'],
            'ytick.color': c['button_fg'],
            'axes.labelcolor': c['button_fg'],
            'axes.edgecolor': c['border'],
            'axes.titlecolor': c['button_fg']
        }):
            plt.figure(figsize=(8,4))
            plt.plot(dates, values, marker='o', color=c['accent'], linewidth=2)
            plt.xticks(rotation=45)
            plt.xlabel("Date")
            plt.ylabel("Steps")
            plt.title("Steps over time")
            plt.tight_layout()
            plt.show()

    def plot_water(self):
        if not self.current_profile_id: messagebox.showinfo("No profile", "Load a profile first."); return
        if plt is None: messagebox.showerror("Plotting unavailable", "matplotlib not installed. Install with: pip install matplotlib cuh just do it its a requirement for the graph"); return
        
        cur = self.conn.cursor(); rows = cur.execute("SELECT date, ml FROM water_logs WHERE profile_id=? ORDER BY date ASC;", (self.current_profile_id,)).fetchall()
        if not rows: messagebox.showinfo("No data", "No water data to plot."); return
        
        dates = [r[0] for r in rows]; values = [r[1] for r in rows]
        
        c = self._get_current_colors()
        
        with plt.rc_context({
            'axes.facecolor': c['panel'],
            'figure.facecolor': c['bg'],
            'text.color': c['button_fg'],
            'xtick.color': c['button_fg'],
            'ytick.color': c['button_fg'],
            'axes.labelcolor': c['button_fg'],
            'axes.edgecolor': c['border'],
            'axes.titlecolor': c['button_fg']
        }):
            plt.figure(figsize=(8,4))
            plt.plot(dates, values, marker='o', color=c['accent'], linewidth=2)
            plt.xticks(rotation=45)
            plt.xlabel("Date")
            plt.ylabel("Water (ml)")
            plt.title("Water intake over time")
            plt.tight_layout()
            plt.show()

    def on_unit_change(self):
        if self.current_profile_id: self.load_profile(profile_id=self.current_profile_id)

if __name__ == '__main__':
    app = HealthApp()
    app.mainloop()