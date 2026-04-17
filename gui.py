"""
gui.py — Premium Tkinter GUI for Universal Dev Environment Manager.

Layout:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  ⚡ Universal Dev Environment Manager                   OS: Windows │
  │  One-click install for 50+ developer tools                         │
  ├─────────────────────────────────────────────────────────────────────┤
  │  🔍 Search tools…                      Category: [All ▾]           │
  ├─────────────────────────────────────────────────────────────────────┤
  │  ■  Python          General-purpose programming language   Language │
  │  □  Node.js         JavaScript runtime                    Language │
  │  □  Docker          Container platform                    DevOps   │
  │  □  …               …                                    …        │
  ├─────────────────────────────────────────────────────────────────────┤
  │  [⚡ Install Selected] [☑ Select All] [☐ Clear] [↻ Refresh] [✕]   │
  ├─────────────────────────────────────────────────────────────────────┤
  │  ▓▓▓▓░░░░░░░░░░░░░░░░  35%   Installing Node.js…                  │
  ├─────────────────────────────────────────────────────────────────────┤
  │  > log output …                                                     │
  └─────────────────────────────────────────────────────────────────────┘

Features:
  • Dark premium theme with vibrant accent colours
  • Custom Canvas-drawn checkboxes — fully visible on dark background
  • Animated hover effects on rows and buttons
  • Selected rows glow with accent border
  • Instant search filtering + category dropdown
  • Scrollable checkbox list with descriptions
  • Install button disabled until ≥1 item selected
  • Threaded installation (GUI never freezes)
  • Live progress bar + status label + scrolling log
  • Success / error popup dialogs
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import threading
import sys

from utils import (
    logger,
    load_tools,
    get_categories,
    check_internet,
    os_label,
    is_admin,
)
from installer import (
    install_selected,
    set_progress_callback,
    set_log_callback,
)

# ═══════════════════════════════════════════════════════════════════════════
#  Theme Palette  — Deep space dark with electric purple accents
# ═══════════════════════════════════════════════════════════════════════════
BG             = "#0b0e14"
BG_SECONDARY   = "#10141c"
BG_CARD        = "#131824"
BG_INPUT       = "#181e2e"
BG_ITEM        = "#141a28"
BG_ITEM_HOVER  = "#1a2236"
BG_ITEM_SEL    = "#1c1f3a"
FG             = "#e8eaef"
FG_DIM         = "#8891a5"
FG_MUTED       = "#5c647a"
FG_DESC        = "#727d94"
ACCENT         = "#8b5cf6"
ACCENT_LIGHT   = "#a78bfa"
ACCENT_GLOW    = "#7c3aed"
ACCENT_DARK    = "#6d28d9"
ACCENT_SUBTLE  = "#1e1544"
GREEN          = "#34d399"
GREEN_DIM      = "#0d3f2f"
RED            = "#f87171"
RED_DIM        = "#3f1515"
ORANGE         = "#fbbf24"
CYAN           = "#22d3ee"
BORDER         = "#1e2538"
BORDER_ACCENT  = "#2d2466"
SCROLLBAR_BG   = "#1a1f30"
SCROLLBAR_FG   = "#2a3352"

# Checkbox colours
CB_BOX         = "#2a3352"
CB_BOX_HOVER   = "#3b4670"
CB_CHECK       = "#a78bfa"
CB_CHECK_GLOW  = "#8b5cf6"

WIN_W, WIN_H   = 960, 720


# ═══════════════════════════════════════════════════════════════════════════
#  Custom Canvas Checkbox — fully visible on dark backgrounds
# ═══════════════════════════════════════════════════════════════════════════
class CanvasCheckbox(tk.Canvas):
    """A custom-drawn checkbox using a Canvas widget.
    Draws a rounded-rectangle box with a bold checkmark when selected.
    """

    SIZE = 20
    PAD  = 2

    def __init__(self, master, variable: tk.BooleanVar, bg=BG_ITEM, **kw):
        super().__init__(
            master, width=self.SIZE, height=self.SIZE,
            bg=bg, highlightthickness=0, bd=0, cursor="hand2", **kw,
        )
        self._var = variable
        self._bg = bg
        self._hovered = False

        # Draw initial state
        self._draw()

        # Bindings
        self.bind("<Button-1>", self._toggle)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._var.trace_add("write", lambda *_: self._draw())

    def _toggle(self, _event=None):
        self._var.set(not self._var.get())

    def _on_enter(self, _event=None):
        self._hovered = True
        self._draw()

    def _on_leave(self, _event=None):
        self._hovered = False
        self._draw()

    def update_bg(self, new_bg):
        self._bg = new_bg
        self.configure(bg=new_bg)
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self.SIZE
        p = self.PAD
        checked = self._var.get()

        # Box fill
        if checked:
            box_fill = ACCENT_GLOW
            box_outline = ACCENT_LIGHT
        elif self._hovered:
            box_fill = CB_BOX_HOVER
            box_outline = ACCENT_LIGHT
        else:
            box_fill = CB_BOX
            box_outline = "#3b4670"

        # Draw rounded rect (simulated with oval corners)
        r = 4  # corner radius
        self.create_rectangle(
            p, p, s - p, s - p,
            fill=box_fill, outline=box_outline, width=1.5,
        )

        # Draw checkmark if checked
        if checked:
            # Bold white checkmark
            cx, cy = s // 2, s // 2
            self.create_line(
                cx - 4, cy,
                cx - 1, cy + 4,
                cx + 5, cy - 4,
                fill="#ffffff", width=2.5,
                capstyle="round", joinstyle="round",
            )


# ═══════════════════════════════════════════════════════════════════════════
#  App
# ═══════════════════════════════════════════════════════════════════════════
class ManagerApp:
    """Main GUI application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Universal Dev Environment Manager")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)
        self.root.minsize(800, 600)

        # Centre on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - WIN_W) // 2
        y = (self.root.winfo_screenheight() - WIN_H) // 2
        self.root.geometry(f"+{x}+{y}")

        # ── Fonts ──────────────────────────────────────────────────────
        self._f_title   = tkfont.Font(family="Segoe UI", size=22, weight="bold")
        self._f_subtitle = tkfont.Font(family="Segoe UI", size=10)
        self._f_sub     = tkfont.Font(family="Segoe UI", size=10)
        self._f_label   = tkfont.Font(family="Segoe UI", size=11)
        self._f_btn     = tkfont.Font(family="Segoe UI", size=10, weight="bold")
        self._f_item    = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self._f_desc    = tkfont.Font(family="Segoe UI", size=9)
        self._f_cat_tag = tkfont.Font(family="Segoe UI", size=8)
        self._f_log     = tkfont.Font(family="Consolas", size=9)
        self._f_search  = tkfont.Font(family="Segoe UI", size=11)
        self._f_status  = tkfont.Font(family="Segoe UI", size=9, slant="italic")
        self._f_count   = tkfont.Font(family="Segoe UI", size=10, weight="bold")

        # ── TTK styles ────────────────────────────────────────────────
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=BG_INPUT,
            background=ACCENT,
            darkcolor=ACCENT_DARK,
            lightcolor=ACCENT_LIGHT,
            bordercolor=BORDER,
            thickness=16,
        )
        style.configure(
            "Cat.TCombobox",
            fieldbackground=BG_INPUT,
            background=BG_INPUT,
            foreground=FG,
            arrowcolor=FG_DIM,
            bordercolor=BORDER,
            selectbackground=ACCENT,
            selectforeground=FG,
        )
        style.map("Cat.TCombobox", fieldbackground=[("readonly", BG_INPUT)])
        self.root.option_add("*TCombobox*Listbox.background", BG_CARD)
        self.root.option_add("*TCombobox*Listbox.foreground", FG)
        self.root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

        # ── Data ──────────────────────────────────────────────────────
        self._all_tools: list[dict] = load_tools()
        self._categories = ["All"] + get_categories(self._all_tools)
        self._tool_vars: dict[str, tk.BooleanVar] = {}  # key → BooleanVar
        self._item_widgets: dict[str, dict] = {}         # key → widget refs
        self._installing = False

        # ── Build UI ──────────────────────────────────────────────────
        self._build_header()
        self._build_divider(self.root)
        self._build_search_bar()
        self._build_tool_list()
        self._build_buttons()
        self._build_progress()
        self._build_log()

        # ── Installer callbacks ───────────────────────────────────────
        set_progress_callback(self._on_progress)
        set_log_callback(self._on_log)

    # ──────────────────────────────────────────────────────────────────
    #  Divider helper
    # ──────────────────────────────────────────────────────────────────
    @staticmethod
    def _build_divider(parent, padx=28, pady=(0, 0)):
        tk.Frame(parent, bg=BORDER, height=1).pack(
            fill="x", padx=padx, pady=pady,
        )

    # ──────────────────────────────────────────────────────────────────
    #  Header
    # ──────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=28, pady=(18, 0))

        # Left side — title + subtitle
        left = tk.Frame(hdr, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left, text="⚡  Universal Dev Manager",
            font=self._f_title, fg=FG, bg=BG, anchor="w",
        ).pack(anchor="w")

        tk.Label(
            left, text="One-click install for 50+ essential developer tools",
            font=self._f_subtitle, fg=FG_MUTED, bg=BG, anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Right side — status badge
        right = tk.Frame(hdr, bg=BG)
        right.pack(side="right")

        admin_text = "🔓 Admin" if is_admin() else "🔒 User"
        admin_fg = GREEN if is_admin() else ORANGE

        badge = tk.Frame(right, bg=ACCENT_SUBTLE, padx=12, pady=4)
        badge.pack(pady=(4, 0))

        tk.Label(
            badge, text=f"{os_label()}  •  {admin_text}",
            font=self._f_sub, fg=admin_fg, bg=ACCENT_SUBTLE,
        ).pack()

    # ──────────────────────────────────────────────────────────────────
    #  Search + Category filter
    # ──────────────────────────────────────────────────────────────────
    def _build_search_bar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=28, pady=(14, 0))

        # Initialize variables FIRST before any traces
        self._search_var = tk.StringVar()
        self._cat_var = tk.StringVar(value="All")

        # Now add trace (safe because _cat_var exists)
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        search_frame = tk.Frame(
            bar, bg=BG_INPUT,
            highlightbackground=BORDER, highlightthickness=1,
            highlightcolor=ACCENT,
        )
        search_frame.pack(side="left", fill="x", expand=True, ipady=5)

        tk.Label(
            search_frame, text="  🔍 ", bg=BG_INPUT, fg=FG_DIM,
            font=self._f_search,
        ).pack(side="left")

        self._search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            font=self._f_search, fg=FG, bg=BG_INPUT,
            insertbackground=ACCENT_LIGHT, relief="flat", bd=0,
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Placeholder text
        self._search_entry.insert(0, "Search tools…")
        self._search_entry.config(fg=FG_MUTED)
        self._search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self._search_entry.bind("<FocusOut>", self._on_search_focus_out)

        # Category dropdown
        cat_frame = tk.Frame(bar, bg=BG)
        cat_frame.pack(side="right", padx=(14, 0))

        tk.Label(
            cat_frame, text="Category:", font=self._f_sub, fg=FG_DIM, bg=BG,
        ).pack(side="left", padx=(0, 6))

        self._cat_combo = ttk.Combobox(
            cat_frame, textvariable=self._cat_var,
            values=self._categories, state="readonly",
            width=18, style="Cat.TCombobox", font=self._f_sub,
        )
        self._cat_combo.pack(side="left")
        self._cat_combo.bind("<<ComboboxSelected>>", lambda _: self._apply_filter())

        # Selection counter badge
        self._sel_count_var = tk.StringVar(value="0 selected")
        count_badge = tk.Frame(bar, bg=ACCENT_SUBTLE, padx=8, pady=2)
        count_badge.pack(side="right", padx=(0, 14))
        self._sel_count_label = tk.Label(
            count_badge, textvariable=self._sel_count_var,
            font=self._f_count, fg=ACCENT_LIGHT, bg=ACCENT_SUBTLE,
        )
        self._sel_count_label.pack()

    def _on_search_focus_in(self, _event):
        if self._search_entry.get() == "Search tools…":
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=FG)

    def _on_search_focus_out(self, _event):
        if not self._search_entry.get():
            self._search_entry.insert(0, "Search tools…")
            self._search_entry.config(fg=FG_MUTED)

    # ──────────────────────────────────────────────────────────────────
    #  Scrollable Tool List
    # ──────────────────────────────────────────────────────────────────
    def _build_tool_list(self):
        # Outer container with subtle border
        container = tk.Frame(
            self.root, bg=BG_CARD,
            highlightbackground=BORDER, highlightthickness=1,
        )
        container.pack(fill="both", expand=True, padx=28, pady=(12, 0))

        # Canvas + custom-styled Scrollbar for scrolling
        self._canvas = tk.Canvas(
            container, bg=BG_CARD, highlightthickness=0, bd=0,
        )
        self._scrollbar = tk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview,
            bg=SCROLLBAR_FG, troughcolor=SCROLLBAR_BG,
            activebackground=ACCENT, width=10, bd=0,
            relief="flat",
        )
        self._inner_frame = tk.Frame(self._canvas, bg=BG_CARD)

        self._inner_frame.bind(
            "<Configure>",
            lambda _: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner_frame, anchor="nw",
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Make inner frame fill canvas width
        self._canvas.bind("<Configure>", self._on_canvas_resize)

        # Mouse wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Populate
        self._populate_items()

    def _on_canvas_resize(self, event):
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _populate_items(self):
        """Create a premium styled row for every tool."""
        for idx, tool in enumerate(self._all_tools):
            key = tool.get("key", tool["name"])
            var = tk.BooleanVar(value=False)
            var.trace_add("write", lambda *_, k=key: self._on_item_toggle(k))
            self._tool_vars[key] = var

            # ── Row container ──
            row = tk.Frame(self._inner_frame, bg=BG_ITEM, pady=6, padx=10)
            row.pack(fill="x", padx=8, pady=(4, 0) if idx > 0 else (8, 0))

            # Left accent bar (hidden by default, shown on selection)
            accent_bar = tk.Frame(row, bg=BG_ITEM, width=3)
            accent_bar.pack(side="left", fill="y", padx=(0, 8))

            # Custom Canvas checkbox — clearly visible!
            cb = CanvasCheckbox(row, variable=var, bg=BG_ITEM)
            cb.pack(side="left", padx=(0, 10), pady=2)

            # Tool name
            name_lbl = tk.Label(
                row, text=tool["name"], font=self._f_item,
                fg=FG, bg=BG_ITEM, anchor="w", width=20,
            )
            name_lbl.pack(side="left", padx=(0, 6))

            # Description
            desc_lbl = tk.Label(
                row, text=tool.get("description", ""),
                font=self._f_desc, fg=FG_DESC, bg=BG_ITEM, anchor="w",
            )
            desc_lbl.pack(side="left", fill="x", expand=True)

            # Category tag badge
            cat_text = tool.get("category", "")
            cat_badge = tk.Frame(row, bg=ACCENT_SUBTLE, padx=8, pady=2)
            cat_badge.pack(side="right", padx=(6, 4))

            cat_lbl = tk.Label(
                cat_badge, text=cat_text,
                font=self._f_cat_tag, fg=ACCENT_LIGHT, bg=ACCENT_SUBTLE,
            )
            cat_lbl.pack()

            # ── Hover effects ──
            all_widgets = [row, name_lbl, desc_lbl]

            def _enter(e, r=row, widgets=all_widgets, ab=accent_bar,
                       cb_ref=cb, cframe=cat_badge, clbl=cat_lbl, v=var):
                if not v.get():
                    r.configure(bg=BG_ITEM_HOVER)
                    ab.configure(bg=ACCENT)
                    for w in widgets:
                        try:
                            w.configure(bg=BG_ITEM_HOVER)
                        except Exception:
                            pass
                    cb_ref.update_bg(BG_ITEM_HOVER)

            def _leave(e, r=row, widgets=all_widgets, ab=accent_bar,
                       cb_ref=cb, cframe=cat_badge, clbl=cat_lbl, v=var):
                if not v.get():
                    r.configure(bg=BG_ITEM)
                    ab.configure(bg=BG_ITEM)
                    for w in widgets:
                        try:
                            w.configure(bg=BG_ITEM)
                        except Exception:
                            pass
                    cb_ref.update_bg(BG_ITEM)

            row.bind("<Enter>", _enter)
            row.bind("<Leave>", _leave)

            # Click anywhere on row to toggle
            for widget in [name_lbl, desc_lbl, row]:
                widget.bind("<Button-1>", lambda e, v=var: v.set(not v.get()))
                widget.configure(cursor="hand2")

            self._item_widgets[key] = {
                "row": row, "cb": cb, "name": name_lbl,
                "desc": desc_lbl, "cat_badge": cat_badge, "cat": cat_lbl,
                "accent_bar": accent_bar, "tool": tool,
            }

        # Bottom padding
        tk.Frame(self._inner_frame, bg=BG_CARD, height=8).pack(fill="x")

    def _on_item_toggle(self, key: str):
        """Update visual state when an item is toggled."""
        self._update_install_btn()
        w = self._item_widgets.get(key)
        if not w:
            return
        var = self._tool_vars[key]
        checked = var.get()

        if checked:
            bg = BG_ITEM_SEL
            w["accent_bar"].configure(bg=ACCENT)
            w["name"].configure(fg=ACCENT_LIGHT)
        else:
            bg = BG_ITEM
            w["accent_bar"].configure(bg=BG_ITEM)
            w["name"].configure(fg=FG)

        w["row"].configure(bg=bg)
        w["name"].configure(bg=bg)
        w["desc"].configure(bg=bg)
        w["cb"].update_bg(bg)

    # ──────────────────────────────────────────────────────────────────
    #  Filtering
    # ──────────────────────────────────────────────────────────────────
    def _apply_filter(self):
        if not hasattr(self, '_item_widgets') or not self._item_widgets:
            return
        query = self._search_var.get().lower().strip()
        if query == "search tools…":
            query = ""
        cat = self._cat_var.get()

        for key, w in self._item_widgets.items():
            tool = w["tool"]
            name_match = (
                query in tool["name"].lower()
                or query in tool.get("description", "").lower()
                or query in key.lower()
            )
            cat_match = cat == "All" or tool.get("category", "") == cat
            if name_match and cat_match:
                w["row"].pack(fill="x", padx=8, pady=(4, 0))
            else:
                w["row"].pack_forget()

    # ──────────────────────────────────────────────────────────────────
    #  Buttons
    # ──────────────────────────────────────────────────────────────────
    def _build_buttons(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=28, pady=(12, 0))

        # Install button (initially disabled) — prominent accent style
        self._install_btn = tk.Button(
            bar, text="⚡  Install Selected", font=self._f_btn,
            fg="#555", bg="#1a1f30", activebackground=ACCENT_LIGHT,
            activeforeground=FG, bd=0, padx=20, pady=9,
            cursor="arrow", state="disabled",
            command=self._on_install,
        )
        self._install_btn.pack(side="left", padx=(0, 8))

        # Other action buttons
        buttons = [
            ("☑  Select All",  BG_INPUT, self._on_select_all),
            ("☐  Clear",       BG_INPUT, self._on_clear),
            ("↻  Refresh",     BG_INPUT, self._on_refresh),
        ]
        for text, bg_color, cmd in buttons:
            b = tk.Button(
                bar, text=text, font=self._f_btn, fg=FG, bg=bg_color,
                activebackground=ACCENT, activeforeground=FG,
                bd=0, padx=14, pady=9, cursor="hand2", command=cmd,
            )
            b.pack(side="left", padx=(0, 6))
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=ACCENT_SUBTLE, fg=ACCENT_LIGHT))
            b.bind("<Leave>", lambda e, btn=b, c=bg_color: btn.config(bg=c, fg=FG))

        # Exit button — right-aligned, subtle red
        exit_btn = tk.Button(
            bar, text="✕  Exit", font=self._f_btn,
            fg=RED, bg=RED_DIM, activebackground=RED, activeforeground=FG,
            bd=0, padx=14, pady=9, cursor="hand2", command=self._on_exit,
        )
        exit_btn.pack(side="right")
        exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg=RED, fg=FG))
        exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg=RED_DIM, fg=RED))

    def _update_install_btn(self):
        """Enable install button iff ≥ 1 tool is selected."""
        count = sum(1 for v in self._tool_vars.values() if v.get())
        self._sel_count_var.set(f"{count} selected")

        if count > 0:
            self._install_btn.configure(
                state="normal", bg=ACCENT, fg=FG, cursor="hand2",
            )
            self._sel_count_label.configure(fg=ACCENT_LIGHT)
            # Add hover to install btn
            self._install_btn.bind(
                "<Enter>", lambda e: self._install_btn.config(bg=ACCENT_LIGHT),
            )
            self._install_btn.bind(
                "<Leave>", lambda e: self._install_btn.config(bg=ACCENT),
            )
        else:
            self._install_btn.configure(
                state="disabled", bg="#1a1f30", fg="#555", cursor="arrow",
            )
            self._sel_count_label.configure(fg=FG_MUTED)
            self._install_btn.unbind("<Enter>")
            self._install_btn.unbind("<Leave>")

    # ──────────────────────────────────────────────────────────────────
    #  Progress & Log
    # ──────────────────────────────────────────────────────────────────
    def _build_progress(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="x", padx=28, pady=(12, 0))

        self._status_var = tk.StringVar(value="Ready — select tools to install")
        tk.Label(
            frame, textvariable=self._status_var, font=self._f_label,
            fg=FG_DIM, bg=BG, anchor="w",
        ).pack(fill="x")

        self._pct_var = tk.IntVar(value=0)
        self._pbar = ttk.Progressbar(
            frame, variable=self._pct_var, maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self._pbar.pack(fill="x", pady=(4, 0))

    def _build_log(self):
        frame = tk.Frame(self.root, bg=BG)
        frame.pack(fill="both", expand=False, padx=28, pady=(10, 18))

        # Log header
        log_header = tk.Frame(frame, bg=BG)
        log_header.pack(fill="x", pady=(0, 4))
        tk.Label(
            log_header, text="📋  Output Log",
            font=self._f_sub, fg=FG_MUTED, bg=BG, anchor="w",
        ).pack(side="left")

        self._log_text = tk.Text(
            frame, font=self._f_log, fg=FG_DIM, bg=BG_INPUT,
            insertbackground=FG, selectbackground=ACCENT,
            relief="flat", bd=0, wrap="word", height=6, state="disabled",
            padx=12, pady=8,
        )
        sb = tk.Scrollbar(
            frame, command=self._log_text.yview,
            bg=SCROLLBAR_FG, troughcolor=SCROLLBAR_BG,
            activebackground=ACCENT, width=8, bd=0, relief="flat",
        )
        self._log_text.configure(yscrollcommand=sb.set)

        # Tag colours for log lines
        self._log_text.tag_configure("success", foreground=GREEN)
        self._log_text.tag_configure("error", foreground=RED)
        self._log_text.tag_configure("warn", foreground=ORANGE)
        self._log_text.tag_configure("info", foreground=FG_DIM)
        self._log_text.tag_configure("accent", foreground=ACCENT_LIGHT)

        sb.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True)

    # ──────────────────────────────────────────────────────────────────
    #  Callbacks from installer (worker thread → GUI)
    # ──────────────────────────────────────────────────────────────────
    def _on_progress(self, tool: str, status: str, pct: int):
        self.root.after(0, self._set_progress, tool, status, pct)

    def _on_log(self, msg: str):
        self.root.after(0, self._append_log, msg)

    def _set_progress(self, tool, status, pct):
        self._status_var.set(f"{tool}  ·  {status}")
        self._pct_var.set(pct)

    def _append_log(self, msg: str):
        tag = "info"
        ml = msg.lower()
        if "✓" in msg or "success" in ml or "installed" in ml:
            tag = "success"
        elif "✗" in msg or "fail" in ml or "error" in ml:
            tag = "error"
        elif "⚠" in msg or "warning" in ml or "skip" in ml:
            tag = "warn"
        elif "═" in msg:
            tag = "accent"

        self._log_text.configure(state="normal")
        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # ──────────────────────────────────────────────────────────────────
    #  Button Handlers
    # ──────────────────────────────────────────────────────────────────
    def _selected_tools(self) -> list[dict]:
        return [
            self._item_widgets[k]["tool"]
            for k, v in self._tool_vars.items()
            if v.get()
        ]

    def _on_select_all(self):
        for key, w in self._item_widgets.items():
            # Only select visible (filtered) items
            if w["row"].winfo_manager():
                self._tool_vars[key].set(True)

    def _on_clear(self):
        for v in self._tool_vars.values():
            v.set(False)

    def _on_refresh(self):
        """Reload tools.json and rebuild the list."""
        for w in self._item_widgets.values():
            w["row"].destroy()
        self._item_widgets.clear()
        self._tool_vars.clear()
        self._all_tools = load_tools()
        self._categories = ["All"] + get_categories(self._all_tools)
        self._cat_combo.configure(values=self._categories)
        self._populate_items()
        self._apply_filter()
        self._update_install_btn()
        self._append_log("↻  Tool list refreshed from tools.json")

    def _on_exit(self):
        if self._installing:
            if not messagebox.askyesno("Confirm", "Installation in progress. Force exit?"):
                return
        self.root.destroy()
        sys.exit(0)

    def _on_install(self):
        tools = self._selected_tools()
        if not tools:
            messagebox.showwarning("Nothing selected", "Select at least one tool first.")
            return
        if self._installing:
            messagebox.showinfo("Busy", "An installation is already running.")
            return

        # Internet check
        self._append_log("Checking internet connection…")
        if not check_internet():
            messagebox.showerror("No Internet", "Please connect to the internet and try again.")
            self._append_log("✗ No internet — aborted.")
            return

        self._installing = True
        self._pct_var.set(0)
        self._status_var.set("Starting installation…")

        names = ", ".join(t["name"] for t in tools)
        self._append_log(f"Selected: {names}")

        def worker():
            try:
                results = install_selected(tools)
            except Exception as ex:
                logger.exception("Unhandled error during installation")
                self.root.after(0, lambda: messagebox.showerror("Error", str(ex)))
                results = {}
            finally:
                self._installing = False
                self.root.after(0, self._show_results, results)

        threading.Thread(target=worker, daemon=True).start()

    def _show_results(self, results: dict[str, str]):
        self._pct_var.set(100)
        installed = sum(1 for v in results.values() if v == "installed")
        skipped = sum(1 for v in results.values() if v == "already_installed")
        failed = sum(1 for v in results.values() if v == "failed")

        summary = (
            f"Installation Complete\n\n"
            f"   Newly installed:   {installed}\n"
            f"   Already present:   {skipped}\n"
            f"   Failed:            {failed}\n"
        )

        if failed:
            self._status_var.set("Completed with errors")
            failed_names = [
                k for k, v in results.items() if v == "failed"
            ]
            summary += f"\nFailed: {', '.join(failed_names)}"
            messagebox.showwarning("Completed with errors", summary)
        else:
            self._status_var.set("All done — happy coding! 🎉")
            messagebox.showinfo("Success ✓", summary)

    # ──────────────────────────────────────────────────────────────────
    #  Run
    # ──────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()
