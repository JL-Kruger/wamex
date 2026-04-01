#!/usr/bin/env python3
"""
wa_extractor.py — WhatsApp Pending Requests → wa.me Link Generator
Paste raw HTML from the pending requests div, extract all phone numbers,
output batched wa.me links ready for community admin invites.
"""

import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

# ── Optional: use BeautifulSoup if available, else fall back to raw regex ──
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


# ─────────────────────────────────────────────
#  CORE EXTRACTION LOGIC
# ─────────────────────────────────────────────

# Matches international phone numbers: optional +, country code, digits/spaces/hyphens
# Handles formats like: +27821234567  +27 82 123 4567  +1-800-555-0199  0027821234567
PHONE_REGEX = re.compile(
    r'(?<!\d)'                          # not preceded by a digit
    r'(\+|00)'                          # starts with + or 00
    r'([1-9]\d{0,3})'                   # country code (1–4 digits)
    r'[\s\-\.]?'                        # optional separator
    r'(\d[\d\s\-\.]{6,13}\d)'          # subscriber number (7–14 digits with separators)
    r'(?!\d)',                           # not followed by a digit
    re.MULTILINE
)


def strip_non_digits(s: str) -> str:
    return re.sub(r'\D', '', s)


def extract_numbers_from_html(html: str) -> list[str]:
    """Extract and normalise phone numbers from raw HTML."""
    candidates = []

    if HAS_BS4:
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ')
        # Also check all attribute values (title, aria-label, data-*)
        for tag in soup.find_all(True):
            for attr_val in tag.attrs.values():
                if isinstance(attr_val, str):
                    text += ' ' + attr_val
                elif isinstance(attr_val, list):
                    text += ' ' + ' '.join(attr_val)
    else:
        # Strip HTML tags with regex if bs4 not available
        text = re.sub(r'<[^>]+>', ' ', html)

    seen = set()
    for match in PHONE_REGEX.finditer(text):
        raw = match.group(0)
        digits = strip_non_digits(raw)
        # Normalise 00XX → +XX
        if digits.startswith('00'):
            digits = digits[2:]
        # Sanity check: 7–15 digits (E.164 range)
        if 7 <= len(digits) <= 15:
            key = digits
            if key not in seen:
                seen.add(key)
                candidates.append('+' + digits)

    return candidates


def format_output(numbers: list[str], batch_size: int = 20) -> str:
    """Format numbers as wa.me links, with a separator every batch_size entries."""
    lines = []
    for i, num in enumerate(numbers):
        lines.append(f"https://wa.me/{num}")
        if (i + 1) % batch_size == 0 and i + 1 < len(numbers):
            lines.append('')
            lines.append('─' * 40)
            lines.append('')
    return '\n'.join(lines)


# ─────────────────────────────────────────────
#  TKINTER UI
# ─────────────────────────────────────────────

BG        = '#0e0e0e'
BG_PANEL  = '#161616'
BG_INPUT  = '#1a1a1a'
ACCENT    = '#25d366'   # WhatsApp green
ACCENT2   = '#128c7e'
TEXT      = '#e8e8e8'
TEXT_DIM  = '#666666'
BORDER    = '#2a2a2a'
FONT_MONO = ('JetBrains Mono', 10) if True else ('Courier New', 10)
FONT_UI   = ('JetBrains Mono', 10)
FONT_TITLE = ('JetBrains Mono', 15, 'bold')
FONT_SMALL = ('JetBrains Mono', 8)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('wa.me Extractor')
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(740, 600)

        self._html_path: Path | None = None
        self._numbers: list[str] = []

        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 860, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

    # ── Layout ──────────────────────────────
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Header ──
        hdr = tk.Frame(self, bg=BG, pady=18)
        hdr.grid(row=0, column=0, sticky='ew', padx=28)

        tk.Label(hdr, text='⬡  wa.me extractor', font=FONT_TITLE,
                 fg=ACCENT, bg=BG).pack(side='left')
        self._bs4_badge(hdr)

        # ── Controls row ──
        ctrl = tk.Frame(self, bg=BG_PANEL, pady=14, padx=20)
        ctrl.grid(row=1, column=0, sticky='ew', padx=0)
        ctrl.columnconfigure(1, weight=1)

        tk.Label(ctrl, text='HTML source:', font=FONT_UI,
                 fg=TEXT_DIM, bg=BG_PANEL).grid(row=0, column=0, sticky='w', padx=(0,10))

        self._path_var = tk.StringVar(value='no file selected')
        tk.Label(ctrl, textvariable=self._path_var, font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG_PANEL, anchor='w').grid(row=0, column=1, sticky='ew')

        btn_open = self._btn(ctrl, '📂  open .txt', self._open_file)
        btn_open.grid(row=0, column=2, padx=(12,6))

        btn_run = self._btn(ctrl, '⚡  extract', self._run, primary=True)
        btn_run.grid(row=0, column=3, padx=(0,0))

        # Batch size
        tk.Label(ctrl, text='  batch size:', font=FONT_UI,
                 fg=TEXT_DIM, bg=BG_PANEL).grid(row=0, column=4, padx=(18,6))
        self._batch_var = tk.StringVar(value='20')
        batch_spin = tk.Spinbox(ctrl, from_=5, to=50, increment=5,
                                textvariable=self._batch_var,
                                width=4, font=FONT_UI,
                                bg=BG_INPUT, fg=ACCENT, insertbackground=ACCENT,
                                buttonbackground=BG_INPUT, relief='flat',
                                highlightthickness=1, highlightcolor=BORDER,
                                highlightbackground=BORDER)
        batch_spin.grid(row=0, column=5, padx=(0,2))

        # ── Main panes ──
        panes = tk.Frame(self, bg=BG)
        panes.grid(row=2, column=0, sticky='nsew', padx=20, pady=(0,12))
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(2, weight=1)
        panes.rowconfigure(1, weight=1)

        # Left — raw HTML input
        self._label(panes, 'paste html  /  or open file above', 0, 0)
        self._html_box = self._text_area(panes, 1, 0)

        # Divider
        div = tk.Frame(panes, bg=BORDER, width=1)
        div.grid(row=0, column=1, rowspan=2, sticky='ns', padx=10)

        # Right — output
        self._out_label_var = tk.StringVar(value='wa.me links')
        self._label_var(panes, self._out_label_var, 0, 2)
        self._out_box = self._text_area(panes, 1, 2, editable=False)

        # ── Footer ──
        foot = tk.Frame(self, bg=BG, pady=8)
        foot.grid(row=3, column=0, sticky='ew', padx=20)
        foot.columnconfigure(0, weight=1)

        self._status_var = tk.StringVar(value='ready — open an HTML dump or paste below')
        tk.Label(foot, textvariable=self._status_var, font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG, anchor='w').grid(row=0, column=0, sticky='w')

        btn_copy = self._btn(foot, '⎘  copy all', self._copy_output)
        btn_copy.grid(row=0, column=1, padx=(6,4))

        btn_save = self._btn(foot, '💾  save .txt', self._save_output, primary=True)
        btn_save.grid(row=0, column=2)

    # ── Helpers ─────────────────────────────
    def _btn(self, parent, text, cmd, primary=False):
        fg   = BG       if primary else TEXT
        bg   = ACCENT   if primary else BG_INPUT
        abg  = ACCENT2  if primary else BORDER
        b = tk.Button(parent, text=text, command=cmd,
                      font=FONT_UI, fg=fg, bg=bg,
                      activeforeground=fg, activebackground=abg,
                      relief='flat', padx=12, pady=5,
                      cursor='hand2', bd=0)
        return b

    def _label(self, parent, text, row, col):
        tk.Label(parent, text=text.upper(), font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG, anchor='w'
                 ).grid(row=row, column=col, sticky='w', pady=(0,4))

    def _label_var(self, parent, var, row, col):
        tk.Label(parent, textvariable=var, font=FONT_SMALL,
                 fg=TEXT_DIM, bg=BG, anchor='w'
                 ).grid(row=row, column=col, sticky='w', pady=(0,4))

    def _text_area(self, parent, row, col, editable=True):
        frame = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        frame.grid(row=row, column=col, sticky='nsew')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        t = scrolledtext.ScrolledText(
            frame,
            font=FONT_MONO,
            bg=BG_INPUT, fg=TEXT,
            insertbackground=ACCENT,
            selectbackground=ACCENT2,
            relief='flat', bd=0,
            padx=10, pady=10,
            wrap='none',
            state='normal' if editable else 'disabled'
        )
        t.grid(row=0, column=0, sticky='nsew')
        return t

    def _bs4_badge(self, parent):
        colour = ACCENT if HAS_BS4 else '#e05252'
        label  = 'bs4 ✓' if HAS_BS4 else 'bs4 ✗ (regex fallback)'
        tk.Label(parent, text=label, font=FONT_SMALL,
                 fg=colour, bg=BG).pack(side='right', padx=4)

    # ── Actions ─────────────────────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            title='Select HTML dump (.txt)',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        if not path:
            return
        self._html_path = Path(path)
        self._path_var.set(str(self._html_path))
        content = self._html_path.read_text(encoding='utf-8', errors='replace')
        self._html_box.delete('1.0', tk.END)
        self._html_box.insert('1.0', content)
        self._status_var.set(f'loaded {len(content):,} chars — hit ⚡ extract')

    def _run(self):
        html = self._html_box.get('1.0', tk.END).strip()
        if not html:
            messagebox.showwarning('Nothing to parse',
                                   'Paste HTML or open a .txt file first.')
            return

        try:
            batch = int(self._batch_var.get())
        except ValueError:
            batch = 20

        self._numbers = extract_numbers_from_html(html)
        count = len(self._numbers)

        if count == 0:
            self._status_var.set('⚠  no phone numbers found — check your HTML')
            messagebox.showinfo('No numbers found',
                                'Could not find any international phone numbers.\n'
                                'Make sure the HTML includes the +XX prefixed numbers.')
            return

        output = format_output(self._numbers, batch_size=batch)
        batches = (count + batch - 1) // batch

        self._out_box.config(state='normal')
        self._out_box.delete('1.0', tk.END)
        self._out_box.insert('1.0', output)
        self._out_box.config(state='disabled')

        self._out_label_var.set(f'wa.me links  [{count} numbers · {batches} batches]')
        self._status_var.set(
            f'✓  extracted {count} numbers → {batches} batches of ≤{batch}'
        )

    def _copy_output(self):
        text = self._out_box.get('1.0', tk.END).strip()
        if not text:
            self._status_var.set('nothing to copy yet')
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._status_var.set('✓  copied to clipboard')

    def _save_output(self):
        text = self._out_box.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning('Nothing to save', 'Run extraction first.')
            return
        path = filedialog.asksaveasfilename(
            title='Save wa.me links',
            defaultextension='.txt',
            initialfile='wame_links.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')]
        )
        if not path:
            return
        Path(path).write_text(text, encoding='utf-8')
        self._status_var.set(f'✓  saved → {path}')


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    app = App()
    app.mainloop()
