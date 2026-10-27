#!/usr/bin/env python3
"""Project Nephilim - GTK4 + Libadwaita Interface."""

import json
import logging
import os
import sys
import threading
from pathlib import Path
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, Gdk, GLib, GObject, Pango

try:
    from subProjt_NEPHILIM.nephilim import parse_archive, install_files
except ImportError:
    from nephilim import parse_archive, install_files

try:
    from subProjt_NEPHILIM.languages import (
        detect_language,
        get_language,
        set_language,
        get_supported_languages,
        get_language_name,
        t,
    )
except ImportError:
    from languages import (
        detect_language,
        get_language,
        set_language,
        get_supported_languages,
        get_language_name,
        t,
    )

CONFIG_DIR = os.path.expanduser("~/.config/nephilim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

log = logging.getLogger(__name__)


def load_config():
    """Load settings from ~/.config/nephilim/config.json."""
    default_cfg = {
        "sims2_prefix": None,
        "default_install_mode": "clean",
        "color_scheme": "system",
        "ui_layout": "modern",
        "language": None,
    }
    if not os.path.exists(CONFIG_PATH):
        return default_cfg
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in default_cfg.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        log.exception("Error loading config")
        return default_cfg


def save_config(cfg):
    """Save settings atomically to ~/.config/nephilim/config.json."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        tmp_path = CONFIG_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp_path, CONFIG_PATH)
    except Exception:
        log.exception("Error saving config")


def apply_color_scheme(scheme_str):
    """Apply the selected color scheme immediately using StyleManager."""
    sm = Adw.StyleManager.get_default()
    if scheme_str == "light":
        sm.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
    elif scheme_str == "dark":
        sm.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
    else:
        sm.set_color_scheme(Adw.ColorScheme.DEFAULT)


def make_wrap_safe_label(**extra_kwargs):
    """Gtk.Label pre-configured to wrap instead of stretching its parent.
    ponytail: width_chars(1) caps the min-width request (the real fix —
    max-width-chars alone only caps natural width). WORD_CHAR wrap handles
    long tokens with no spaces (e.g. a comma-separated GameVersion string).
    """
    kwargs = {"xalign": 0, "wrap": True}
    kwargs.update(extra_kwargs)
    label = Gtk.Label(**kwargs)
    label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
    label.set_max_width_chars(80)
    label.set_width_chars(1)
    return label


class FileItem(GObject.Object):
    """Model wrapper for package entries in the classic data grid."""
    __gtype_name__ = "FileItem"
    checked = GObject.Property(type=bool, default=True)

    def __init__(self, f_dict: dict):
        super().__init__()
        self.f = f_dict
        self.checked = True


class NephilimWindow(Adw.ApplicationWindow):
    """Main window for Project Nephilim following GNOME HIG conventions."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("NINA pack installer")
        self.set_default_size(780, 560)

        self.current_file_path = None
        self.parsed_files = []
        self.pkg_type = ""
        self.game_ver = ""
        self.current_page = "empty"
        self._return_page = "empty"
        self._current_pkg_index = -1
        self.package_queue = []
        self._install_in_progress = False
        self._is_single_file_inspect = False
        self._updating_strip_chk = False
        self._updating_ui_texts = False
        self._install_token = 0

        app = self.get_application()
        self.config = app.config if app and hasattr(app, "config") and app.config else load_config()
        if self.config.get("language"):
            set_language(self.config["language"])

        # Data store for classic view
        self.classic_store = Gio.ListStore.new(FileItem)

        # Header Bar
        header_bar = Adw.HeaderBar()

        # Open Button (for empty and classic pages)
        self.open_button = Gtk.Button.new_from_icon_name("document-open-symbolic")
        self.open_button.set_tooltip_text(t("btn_open"))
        self.open_button.connect("clicked", self._on_open_clicked)
        header_bar.pack_start(self.open_button)

        # Back Button (for details / classic / preferences pages)
        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_button.set_tooltip_text(t("btn_back"))
        self.back_button.connect("clicked", self._on_back_clicked)
        header_bar.pack_start(self.back_button)

        # Settings Button (for empty / classic pages)
        self.settings_button = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
        self.settings_button.set_tooltip_text(t("btn_preferences"))
        self.settings_button.connect("clicked", self._on_settings_clicked)
        header_bar.pack_end(self.settings_button)

        # Install Button (for modern details page and queue)
        self.install_button = Gtk.Button(label=t("btn_install"))
        self.install_button.add_css_class("suggested-action")
        self.install_button.set_tooltip_text(t("btn_install_package"))
        self.install_button.connect("clicked", self._on_install_clicked)
        header_bar.pack_end(self.install_button)

        # Main Vertical Container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.append(header_bar)

        # View Stack for switching between views
        self.view_stack = Adw.ViewStack()
        self.view_stack.set_vexpand(True)
        # ponytail: safety net. Whatever page is showing, its height request can
        # never push the window taller than the user set it; the header above
        # stays fixed and an over-tall page scrolls instead.
        page_scroller = Gtk.ScrolledWindow()
        page_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        page_scroller.set_propagate_natural_height(False)
        page_scroller.set_vexpand(True)
        page_scroller.set_child(self.view_stack)
        main_box.append(page_scroller)
        self.set_content(main_box)

        # Global Drag and Drop Controller — entire window accepts drops
        # ponytail: Gdk.FileList is the type for multi-file drops from file managers.
        # Gio.File only catches single-file drops. Using FileList covers both.
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self._on_file_dropped)
        self.add_controller(drop_target)

        # --- Page 0: Welcome / Onboarding State (page "welcome") ---
        self.welcome_status_page = Adw.StatusPage(
            title=t("welcome_title"),
            description=t("welcome_subtitle"),
            icon_name="package-x-generic-symbolic",
            valign=Gtk.Align.CENTER,
            vexpand=True,
        )
        self.welcome_browse_btn = Gtk.Button(label=t("btn_browse_prefix"))
        self.welcome_browse_btn.add_css_class("suggested-action")
        self.welcome_browse_btn.add_css_class("pill")
        self.welcome_browse_btn.set_halign(Gtk.Align.CENTER)
        self.welcome_browse_btn.connect("clicked", self._on_welcome_browse_clicked)
        self.welcome_status_page.set_child(self.welcome_browse_btn)

        welcome_clamp = Adw.Clamp(maximum_size=450)
        welcome_clamp.set_child(self.welcome_status_page)
        self.view_stack.add_named(welcome_clamp, "welcome")

        # --- Page 1: Empty / Queue State (page "empty") ---
        self.empty_stack = Gtk.Stack()
        self.empty_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.empty_stack.set_vexpand(True)

        # Child 0: Status page when queue is empty
        self.status_page = Adw.StatusPage(
            title=t("no_file_title"),
            description=t("no_file_subtitle"),
            icon_name="package-x-generic-symbolic",
            valign=Gtk.Align.CENTER,
            vexpand=True,
        )
        self.choose_btn = Gtk.Button(label=t("btn_select_file"))
        self.choose_btn.add_css_class("suggested-action")
        self.choose_btn.add_css_class("pill")
        self.choose_btn.set_halign(Gtk.Align.CENTER)
        self.choose_btn.connect("clicked", self._on_open_clicked)
        self.status_page.set_child(self.choose_btn)

        status_clamp = Adw.Clamp(maximum_size=450)
        status_clamp.set_child(self.status_page)
        self.empty_stack.add_named(status_clamp, "status")

        # Child 1: Queue list when packages are pending
        queue_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        queue_box.set_margin_top(18)
        queue_box.set_margin_bottom(18)
        queue_box.set_margin_start(12)
        queue_box.set_margin_end(12)

        self.queue_listbox = Gtk.ListBox()
        self.queue_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.queue_listbox.add_css_class("boxed-list")
        # Scroll only the list; propagate_natural_height=False keeps the window
        # at its own size no matter how many rows are added. Bar shows on demand.
        queue_scroller = Gtk.ScrolledWindow()
        queue_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        queue_scroller.set_propagate_natural_height(False)
        queue_scroller.set_vexpand(True)
        queue_scroller.set_child(self.queue_listbox)
        queue_box.append(queue_scroller)

        self.queue_progress = Gtk.ProgressBar()
        self.queue_progress.set_show_text(True)
        self.queue_progress.set_text(t("status_ready"))
        self.queue_progress.set_visible(False)
        queue_box.append(self.queue_progress)

        queue_clamp = Adw.Clamp(maximum_size=600)
        queue_clamp.set_child(queue_box)
        self.empty_stack.add_named(queue_clamp, "queue")

        page_empty_clamp = Adw.Clamp(maximum_size=600)
        page_empty_clamp.set_child(self.empty_stack)
        self.view_stack.add_named(page_empty_clamp, "empty")

        # --- Page 2: Modern Details View (page "details") ---
        details_scrolled = Gtk.ScrolledWindow()

        details_clamp = Adw.Clamp(maximum_size=600)
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        details_box.set_margin_top(18)
        details_box.set_margin_bottom(18)
        details_box.set_margin_start(12)
        details_box.set_margin_end(12)

        # Preferences Group for Package Info
        self.details_pref_group = Adw.PreferencesGroup(title="Package Information")

        self.row_filename = Adw.ActionRow(title="File Name")
        self.row_size = Adw.ActionRow(title="Size")
        self.row_pkg_type = Adw.ActionRow(title="Package Type")
        self.row_file_count = Adw.ActionRow(title="Contents Summary")
        self.row_path = Adw.ActionRow(title="Full Path")

        # ponytail: some .sims2pack files carry pathological long text (e.g. a
        # comma-separated GameVersion with no spaces). Label min/natural width
        # semantics are easy to get wrong (max-width-chars only caps natural
        # width, not minimum) and it silently stretches the whole window.
        # Fix: give the label's container a hard physical size ceiling via a
        # ScrolledWindow + size_request. GTK cannot violate an explicit
        # pixel size_request the way it can ignore Clamp/Label sizing hints.
        self.row_game_ver = Adw.ExpanderRow(title="Game Version")
        self.game_ver_full_label = make_wrap_safe_label(yalign=0, selectable=True)
        self.game_ver_full_label.set_margin_top(6)
        self.game_ver_full_label.set_margin_bottom(6)
        self.game_ver_full_label.set_margin_start(12)
        self.game_ver_full_label.set_margin_end(12)

        game_ver_scroller = Gtk.ScrolledWindow()
        game_ver_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        game_ver_scroller.set_propagate_natural_width(False)
        game_ver_scroller.set_hexpand(False)
        game_ver_scroller.set_size_request(-1, 100)
        game_ver_scroller.set_child(self.game_ver_full_label)
        self.row_game_ver.add_row(game_ver_scroller)

        for row in (self.row_filename, self.row_path):
            row.set_subtitle_lines(0)  # 0 = unlimited wrapped lines (libadwaita 1.3+)

        self.details_pref_group.add(self.row_filename)
        self.details_pref_group.add(self.row_size)
        self.details_pref_group.add(self.row_pkg_type)
        self.details_pref_group.add(self.row_game_ver)
        self.details_pref_group.add(self.row_file_count)
        self.details_pref_group.add(self.row_path)

        details_box.append(self.details_pref_group)

        # Preferences Group for Installation Options
        self.details_opts_group = Adw.PreferencesGroup(title="Installation Options")
        mode_model = Gtk.StringList.new([
            t("opt_keep_cc"),
            t("opt_clean_primary"),
        ])
        self.row_mode = Adw.ComboRow(title="Install Mode", model=mode_model)
        self.row_mode.set_selected(0)
        self.row_mode.connect("notify::selected", self._on_row_mode_changed)
        self.details_opts_group.add(self.row_mode)

        details_box.append(self.details_opts_group)

        # Progress Bar for extraction/install status
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text(t("status_ready"))
        details_box.append(self.progress_bar)

        details_clamp.set_child(details_box)
        details_scrolled.set_child(details_clamp)

        self.view_stack.add_named(details_scrolled, "details")

        # --- Page 3: Classic GUI View (page "classic" - Mootilda 2014 Layout) ---
        classic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        classic_box.set_margin_top(12)
        classic_box.set_margin_bottom(12)
        classic_box.set_margin_start(14)
        classic_box.set_margin_end(14)

        # Top Header / Toolbar Area
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info_box.set_hexpand(True)
        self.classic_title_label = Gtk.Label(xalign=0, ellipsize=Pango.EllipsizeMode.END)
        self.classic_title_label.add_css_class("title-4")
        self.classic_type_label = Gtk.Label(xalign=0)
        self.classic_type_label.add_css_class("dim-label")
        info_box.append(self.classic_title_label)
        info_box.append(self.classic_type_label)
        top_bar.append(info_box)

        # Filter dropdown
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.filter_lbl = Gtk.Label(label=t("classic_filter"))
        self.filter_lbl.add_css_class("dim-label")
        filter_box.append(self.filter_lbl)

        filter_model = Gtk.StringList.new([
            t("filter_all"),
            t("filter_no_hacks"),
            t("filter_primary_only"),
            t("filter_cc_only"),
        ])
        self.classic_dropdown_filter = Gtk.DropDown(model=filter_model)
        self.classic_dropdown_filter.connect("notify::selected", self._on_classic_filter_changed)
        filter_box.append(self.classic_dropdown_filter)
        top_bar.append(filter_box)

        # Remove Custom Content Checkbox (Lot specific)
        # ponytail: named for what it does — strips all non-primary CC, not
        # just furniture. Real per-category filtering (furniture vs clothing
        # vs skins) would need DBPF resource-type data parse_archive doesn't
        # expose yet.
        self.classic_chk_remove_furniture = Gtk.CheckButton(label=t("classic_strip_cc"))
        self.classic_chk_remove_furniture.connect("toggled", self._on_classic_remove_furniture_toggled)
        top_bar.append(self.classic_chk_remove_furniture)

        # Selection Action Buttons
        self.btn_sel_all = Gtk.Button(label=t("btn_select_all"))
        self.btn_sel_all.connect("clicked", lambda _b: self._set_all_checked(True))
        top_bar.append(self.btn_sel_all)

        self.btn_desel_all = Gtk.Button(label=t("btn_deselect_all"))
        self.btn_desel_all.connect("clicked", lambda _b: self._set_all_checked(False))
        top_bar.append(self.btn_desel_all)

        classic_box.append(top_bar)

        # Center Data Grid (ColumnView)
        scrolled_grid = Gtk.ScrolledWindow(has_frame=True)
        scrolled_grid.set_vexpand(True)
        scrolled_grid.set_hexpand(True)

        self.classic_sel = Gtk.SingleSelection.new(self.classic_store)
        self.classic_sel.connect("notify::selected-item", self._on_classic_item_selected)
        self.classic_cv = Gtk.ColumnView.new(self.classic_sel)
        self.classic_cv.add_css_class("data-table")

        # Column 0: Checkbox
        f_chk = Gtk.SignalListItemFactory()
        f_chk.connect("setup", lambda f, li: li.set_child(Gtk.CheckButton()))
        f_chk.connect("bind", self._bind_col_chk)
        f_chk.connect("unbind", self._unbind_col_chk)
        self.col_chk = Gtk.ColumnViewColumn.new(t("btn_install"), f_chk)
        self.classic_cv.append_column(self.col_chk)

        # Column 1: Status / Warning
        f_status = Gtk.SignalListItemFactory()
        f_status.connect("setup", lambda f, li: li.set_child(Gtk.Label(xalign=0)))
        f_status.connect("bind", self._bind_col_status)
        self.col_status = Gtk.ColumnViewColumn.new(t("Status"), f_status)
        self.classic_cv.append_column(self.col_status)

        # Columns 2-6: plain text columns — same setup/bind shape, only the
        # extractor and label kwargs differ.
        self.col_name = self._add_text_column(
            t("Name"), lambda f: f.get("name", ""), ellipsize=Pango.EllipsizeMode.END
        )
        self.col_name.set_expand(True)

        self.col_type = self._add_text_column(t("Type"), lambda f: f.get("type", ""))

        self.col_crc = self._add_text_column(
            t("MD5 / CRC"), lambda f: f.get("crc", ""), ellipsize=Pango.EllipsizeMode.END
        )
        self.col_crc.set_fixed_width(120)

        self.col_subfolder = self._add_text_column(
            t("Subfolder"), lambda f: "Teleport" if f.get("is_primary") else "Downloads"
        )

        self.col_size = self._add_text_column(
            t("row_size"), lambda f: self._format_size(f.get("length", 0)), xalign=1
        )


        scrolled_grid.set_child(self.classic_cv)
        classic_box.append(scrolled_grid)

        # Bottom Panel: Description & Metadata + Install Action
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        # Bottom Left: Description
        desc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.desc_title = Gtk.Label(label="<b>Package Description</b>", use_markup=True, xalign=0)
        desc_box.append(self.desc_title)

        desc_scrolled = Gtk.ScrolledWindow(has_frame=True)
        self.classic_text_desc = Gtk.TextView(
            editable=False,
            cursor_visible=False,
            wrap_mode=Gtk.WrapMode.WORD,
            left_margin=6,
            right_margin=6,
            top_margin=6,
            bottom_margin=6,
        )
        desc_scrolled.set_child(self.classic_text_desc)
        desc_box.append(desc_scrolled)
        bottom_box.append(desc_box)

        # Bottom Right: Metadata, Progress & Install Action
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.meta_title = Gtk.Label(label="<b>Package Details</b>", use_markup=True, xalign=0)
        action_box.append(self.meta_title)

        self.classic_lbl_meta = make_wrap_safe_label(use_markup=True)
        action_box.append(self.classic_lbl_meta)

        self.classic_progress_bar = Gtk.ProgressBar(show_text=True, text=t("status_ready"))
        action_box.append(self.classic_progress_bar)

        self.classic_btn_install = Gtk.Button(label="Install Selected")
        self.classic_btn_install.add_css_class("suggested-action")
        self.classic_btn_install.connect("clicked", self._on_classic_install_clicked)
        action_box.append(self.classic_btn_install)

        bottom_box.append(action_box)
        classic_box.append(bottom_box)

        self.view_stack.add_named(classic_box, "classic")

        # --- Page 4: Embedded Preferences View (page "preferences") ---
        prefs_scrolled = Gtk.ScrolledWindow()

        prefs_clamp = Adw.Clamp(maximum_size=600)
        prefs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        prefs_box.set_margin_top(18)
        prefs_box.set_margin_bottom(18)
        prefs_box.set_margin_start(12)
        prefs_box.set_margin_end(12)

        # General Preferences Group
        self.group_general = Adw.PreferencesGroup(title="General")

        self.pref_row_prefix = Adw.ActionRow(title="Game wine prefix")
        self.pref_row_prefix.set_subtitle(self.config.get("sims2_prefix") or "Not configured")
        self.btn_pref_browse = Gtk.Button(label="Browse…")
        self.btn_pref_browse.set_valign(Gtk.Align.CENTER)
        self.btn_pref_browse.connect("clicked", self._on_pref_browse_prefix_clicked)
        self.pref_row_prefix.add_suffix(self.btn_pref_browse)
        self.pref_row_prefix.set_activatable_widget(self.btn_pref_browse)
        self.group_general.add(self.pref_row_prefix)

        # Language Selection Row
        self.supported_langs = get_supported_languages()
        lang_names = [get_language_name(l) for l in self.supported_langs]
        lang_model = Gtk.StringList.new(lang_names)
        self.pref_row_lang = Adw.ComboRow(title="Language", model=lang_model)
        cur_lang = get_language()
        if cur_lang in self.supported_langs:
            self.pref_row_lang.set_selected(self.supported_langs.index(cur_lang))
        self.pref_row_lang.connect("notify::selected", self._on_pref_lang_changed)
        self.group_general.add(self.pref_row_lang)

        initial_active = self.config.get("default_install_mode") == "clean"
        self.pref_row_mode = Adw.SwitchRow(
            title="Clean Install",
            subtitle="Only install primary files (strip custom content by default)",
        )
        self.pref_row_mode.set_active(initial_active)
        self.pref_row_mode.connect("notify::active", self._on_pref_mode_changed)
        self.group_general.add(self.pref_row_mode)

        # UI Layout Toggle (Hot-swappable between Modern and Classic)
        initial_classic = self.config.get("ui_layout") == "classic"
        self.pref_row_layout = Adw.SwitchRow(
            title="Classic GUI Layout",
            subtitle="Use Mootilda 2014 Clean Installer grid layout",
        )
        self.pref_row_layout.set_active(initial_classic)
        self.pref_row_layout.connect("notify::active", self._on_pref_layout_changed)
        self.group_general.add(self.pref_row_layout)

        prefs_box.append(self.group_general)

        # Color Scheme Preferences Group
        self.group_appearance = Adw.PreferencesGroup(title="Color Scheme")
        current_scheme = self.config.get("color_scheme", "system")

        self.scheme_rows = []
        radio_group = None
        for scheme_id, title, title_key in [("system", "Follow System", "opt_theme_system"), ("light", "Light", "opt_theme_light"), ("dark", "Dark", "opt_theme_dark")]:
            row = Adw.ActionRow(title=title)
            radio = Gtk.CheckButton()
            if radio_group:
                radio.set_group(radio_group)
            else:
                radio_group = radio
            radio.set_valign(Gtk.Align.CENTER)
            row.add_suffix(radio)
            row.set_activatable_widget(radio)
            self.group_appearance.add(row)
            self.scheme_rows.append((row, title_key))

            if current_scheme == scheme_id:
                radio.set_active(True)

            radio.connect("toggled", self._on_pref_scheme_changed, scheme_id)

        prefs_box.append(self.group_appearance)

        # Miscellaneous Preferences Group
        self.group_misc = Adw.PreferencesGroup(title="Miscellaneous")

        self.row_donate = Adw.ActionRow(
            title="Donate", subtitle="Support the project development (coming soon)"
        )
        self.btn_donate = Gtk.Button(label="Donate")
        self.btn_donate.set_valign(Gtk.Align.CENTER)
        self.row_donate.add_suffix(self.btn_donate)
        self.row_donate.set_activatable_widget(self.btn_donate)
        self.group_misc.add(self.row_donate)

        prefs_box.append(self.group_misc)

        prefs_clamp.set_child(prefs_box)
        prefs_scrolled.set_child(prefs_clamp)

        self.view_stack.add_named(prefs_scrolled, "preferences")

        # Sync initial UI strings with active locale
        self._update_ui_texts()

        # Determine initial view (Welcome page if prefix is missing)
        if not self.config.get("sims2_prefix"):
            self._show_page("welcome")
        else:
            self._show_page("empty")

    def _add_text_column(self, title: str, extractor, **label_kwargs):
        """Create+append a plain text ColumnViewColumn. extractor(f_dict) -> str."""
        label_kwargs.setdefault("xalign", 0)
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda f, li: li.set_child(Gtk.Label(**label_kwargs)))
        factory.connect("bind", lambda f, li: li.get_child().set_text(extractor(li.get_item().f)))
        column = Gtk.ColumnViewColumn.new(title, factory)
        self.classic_cv.append_column(column)
        return column

    def _on_item_toggled(self, item):
        self._update_classic_selection_summary()
        if not self._updating_strip_chk and item.checked and not item.f.get("is_primary", False):
            if self.classic_chk_remove_furniture.get_active():
                self._updating_strip_chk = True
                try:
                    self.classic_chk_remove_furniture.set_active(False)
                finally:
                    self._updating_strip_chk = False

    def _bind_col_chk(self, factory, list_item):
        chk = list_item.get_child()
        item = list_item.get_item()
        if item:
            binding = item.bind_property(
                "checked", chk, "active",
                GObject.BindingFlags.BIDIRECTIONAL | GObject.BindingFlags.SYNC_CREATE
            )
            toggle_id = chk.connect("toggled", lambda b: self._on_item_toggled(item))
            # ponytail: store refs on the widget so unbind can clean them up
            chk._nephilim_binding = binding
            chk._nephilim_toggle_id = toggle_id
            # Accessibility: screen readers announce the file name, not just "checkbox"
            chk.update_property(
                Gtk.AccessibleProperty.LABEL,
                f"Install {item.f.get('name', '')}"
            )

    def _unbind_col_chk(self, factory, list_item):
        chk = list_item.get_child()
        if chk:
            if hasattr(chk, "_nephilim_binding"):
                chk._nephilim_binding.unbind()
                del chk._nephilim_binding
            if hasattr(chk, "_nephilim_toggle_id"):
                chk.disconnect(chk._nephilim_toggle_id)
                del chk._nephilim_toggle_id

    def _bind_col_status(self, factory, list_item):
        lbl = list_item.get_child()
        item = list_item.get_item()
        if item:
            if item.f.get("is_hack"):
                lbl.set_markup('<span foreground="#e01b24"><b>⚠️ Mod/Hack</b></span>')
            elif item.f.get("is_primary"):
                lbl.set_markup('<span foreground="#3584e4">★ Primary</span>')
            else:
                lbl.set_markup('<span foreground="#2ec27e">● Clean</span>')

    def _update_header_bar(self):
        """Sync HeaderBar button labels and visibility across all page transitions."""
        page_name = self.current_page

        if page_name == "welcome":
            self.open_button.set_visible(False)
            self.settings_button.set_visible(False)
            self.back_button.set_visible(False)
            self.install_button.set_visible(False)
        elif page_name == "empty":
            self.open_button.set_visible(True)
            self.settings_button.set_visible(True)
            self.back_button.set_visible(False)
            has_active_batch = bool(self.package_queue) and not self._is_single_file_inspect
            if has_active_batch:
                self.install_button.set_label(t("btn_install_all"))
                self.install_button.set_visible(True)
            else:
                self.install_button.set_visible(False)
        elif page_name == "details":
            self.open_button.set_visible(False)
            self.settings_button.set_visible(False)
            self.back_button.set_visible(True)
            self.install_button.set_label(t("btn_install"))
            self.install_button.set_visible(True)
        elif page_name == "classic":
            self.open_button.set_visible(True)
            self.settings_button.set_visible(False)
            self.back_button.set_visible(True)
            self.install_button.set_visible(False)
        elif page_name == "preferences":
            self.open_button.set_visible(False)
            self.settings_button.set_visible(False)
            self.back_button.set_visible(True)
            self.install_button.set_visible(False)

    def _update_ui_texts(self):
        """Refresh all visible UI strings according to the active language."""
        self._updating_ui_texts = True
        try:
            self.open_button.set_tooltip_text(t("btn_open"))
            self.back_button.set_tooltip_text(t("btn_back"))
            self.settings_button.set_tooltip_text(t("btn_preferences"))
            self.install_button.set_tooltip_text(t("btn_install_package"))
            self._update_header_bar()

            if hasattr(self, "welcome_status_page"):
                self.welcome_status_page.set_title(t("welcome_title"))
                self.welcome_status_page.set_description(t("welcome_subtitle"))
                self.welcome_browse_btn.set_label(t("btn_browse_prefix"))

            if hasattr(self, "status_page"):
                self.status_page.set_title(t("no_file_title"))
                self.status_page.set_description(t("no_file_subtitle"))
                self.choose_btn.set_label(t("btn_select_file"))

            if hasattr(self, "details_pref_group"):
                self.details_pref_group.set_title(t("pref_group_package_info"))
                self.row_filename.set_title(t("row_filename"))
                self.row_size.set_title(t("row_size"))
                self.row_pkg_type.set_title(t("row_pkg_type"))
                self.row_file_count.set_title(t("row_contents_summary"))
                self.row_path.set_title(t("row_full_path"))
                self.row_game_ver.set_title(t("row_game_version"))
                self.details_opts_group.set_title(t("pref_group_install_opts"))
                self.row_mode.set_title(t("row_install_mode"))
                mode_sel = self.row_mode.get_selected()
                self.row_mode.set_model(Gtk.StringList.new([
                    t("opt_keep_cc"),
                    t("opt_clean_primary"),
                ]))
                self.row_mode.set_selected(mode_sel)

            if hasattr(self, "classic_chk_remove_furniture"):
                self.filter_lbl.set_label(t("classic_filter"))
                filter_sel = self.classic_dropdown_filter.get_selected()
                self.classic_dropdown_filter.set_model(Gtk.StringList.new([
                    t("filter_all"),
                    t("filter_no_hacks"),
                    t("filter_primary_only"),
                    t("filter_cc_only"),
                ]))
                self.classic_dropdown_filter.set_selected(filter_sel)
                self.classic_chk_remove_furniture.set_label(t("classic_strip_cc"))
                self.btn_sel_all.set_label(t("btn_select_all"))
                self.btn_desel_all.set_label(t("btn_deselect_all"))
                self.desc_title.set_markup(f"<b>{t('classic_pkg_desc')}</b>")
                self.meta_title.set_markup(f"<b>{t('classic_pkg_details')}</b>")
                self.classic_btn_install.set_label(t("btn_install_selected"))

            if hasattr(self, "col_chk"):
                self.col_chk.set_title(t("btn_install"))
                self.col_status.set_title(t("Status"))
                self.col_name.set_title(t("Name"))
                self.col_type.set_title(t("Type"))
                self.col_crc.set_title(t("MD5 / CRC"))
                self.col_subfolder.set_title(t("Subfolder"))
                self.col_size.set_title(t("row_size"))

            if hasattr(self, "group_general"):
                self.group_general.set_title(t("pref_group_general"))
                self.pref_row_prefix.set_title(t("row_wine_prefix"))
                self.btn_pref_browse.set_label(t("btn_browse"))
                self.pref_row_lang.set_title(t("row_language"))
                self.pref_row_mode.set_title(t("row_clean_install"))
                self.pref_row_mode.set_subtitle(t("row_clean_install_sub"))
                self.pref_row_layout.set_title(t("row_classic_layout"))
                self.pref_row_layout.set_subtitle(t("row_classic_layout_sub"))
                self.group_appearance.set_title(t("pref_group_color_scheme"))
                for row, title_key in getattr(self, "scheme_rows", []):
                    row.set_title(t(title_key))
                self.group_misc.set_title(t("pref_group_misc"))
                self.row_donate.set_title(t("btn_donate"))
                self.row_donate.set_subtitle(t("row_donate_sub"))
                self.btn_donate.set_label(t("btn_donate"))

            if self.current_file_path:
                self.classic_type_label.set_text(f"{t('Package Type:')} {t(self.pkg_type) if self.pkg_type else t('msg_unknown')}")
                self._update_classic_selection_summary()
                if self.pkg_type:
                    self.row_pkg_type.set_subtitle(t(self.pkg_type))
        finally:
            self._updating_ui_texts = False

    def _show_page(self, page_name: str):
        self.current_page = page_name
        self._update_header_bar()

        if page_name == "preferences":
            self.pref_row_prefix.set_subtitle(
                self.config.get("sims2_prefix") or "Not configured"
            )

        self.view_stack.set_visible_child_name(page_name)

    def _browse_prefix(self, navigate_to_empty: bool):
        dialog = Gtk.FileDialog()
        dialog.set_title(t("dlg_select_prefix"))
        dialog.select_folder(self, None, lambda d, r: self._on_prefix_picked(d, r, navigate_to_empty))

    def _on_prefix_picked(self, dialog, result, navigate_to_empty: bool):
        try:
            folder = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        if not folder:
            return
        path = folder.get_path()
        if not path:
            return
        real_path = os.path.realpath(path)

        # ponytail: trust boundary — the user picks any folder on disk, and
        # nephilim.py won't fail until install time (IOError deep in
        # resolve_directory). Check writability now so the failure surfaces
        # immediately, next to the picker, not mid-install with no context.
        # isdir guards against a symlink pointing at a writable regular file,
        # which os.access(W_OK) alone would accept. Resolved via realpath to
        # check the actual target directory; TOCTOU risk is accepted here as
        # this is a single-user desktop app — a real temp-file write test
        # would be the more robust upgrade if this ever needs hardening.
        if not os.path.isdir(real_path) or not os.access(real_path, os.W_OK):
            self.pref_row_prefix.set_subtitle(f"Not writable: {path}")
            return

        # ponytail: store the resolved path, not the picked one — if the user
        # picked a symlink, every later resolve_directory() call should walk
        # the real target, not the link, since that's what we just validated.
        self.config["sims2_prefix"] = real_path
        save_config(self.config)
        self.pref_row_prefix.set_subtitle(real_path)
        if navigate_to_empty:
            self._show_page("empty")

    def _on_welcome_browse_clicked(self, _button):
        self._browse_prefix(navigate_to_empty=True)

    def _on_settings_clicked(self, _button):
        self._return_page = self.view_stack.get_visible_child_name()
        self._show_page("preferences")

    def _on_back_clicked(self, _button):
        self._install_token += 1
        if self.current_page == "preferences":
            self._show_page(self._return_page)
        elif self.current_page in ("details", "classic"):
            self._current_pkg_index = -1
            if self._is_single_file_inspect:
                self.package_queue.clear()
                self._is_single_file_inspect = False
                self.empty_stack.set_visible_child_name("status")
            else:
                self._populate_queue_view()
            self._show_page("empty")

    def _apply_layout(self, mode: str):
        """Hot-swap active view based on user layout preference."""
        if self.current_page in ("details", "classic"):
            target = "classic" if mode == "classic" else "details"
            self._show_page(target)
        elif self.current_page == "preferences":
            if self._return_page in ("details", "classic"):
                self._return_page = "classic" if mode == "classic" else "details"

    def _on_pref_lang_changed(self, combo, _gparam):
        idx = combo.get_selected()
        if 0 <= idx < len(self.supported_langs):
            selected_lang = self.supported_langs[idx]
            if selected_lang != get_language():
                set_language(selected_lang)
                self.config["language"] = selected_lang
                save_config(self.config)
                self._update_ui_texts()

    def _on_pref_layout_changed(self, switch_row, _gparam):
        new_layout = "classic" if switch_row.get_active() else "modern"
        self.config["ui_layout"] = new_layout
        save_config(self.config)
        self._apply_layout(new_layout)

    def _on_pref_browse_prefix_clicked(self, _button):
        self._browse_prefix(navigate_to_empty=False)

    def _on_pref_mode_changed(self, switch_row, _gparam):
        new_mode = "clean" if switch_row.get_active() else "keep-cc"
        self.config["default_install_mode"] = new_mode
        save_config(self.config)

    def _on_row_mode_changed(self, combo_row, _gparam):
        if getattr(self, "_updating_ui_texts", False):
            return
        if 0 <= self._current_pkg_index < len(self.package_queue):
            new_mode = "keep-cc" if combo_row.get_selected() == 0 else "clean"
            self.package_queue[self._current_pkg_index]["mode"] = new_mode

    def _on_pref_scheme_changed(self, radio_btn, scheme_name):
        if radio_btn.get_active():
            self.config["color_scheme"] = scheme_name
            save_config(self.config)
            apply_color_scheme(scheme_name)

    def _reset_status_page(self):
        self.status_page.set_title(t("no_file_title"))
        self.status_page.set_description(t("no_file_subtitle"))
        self.status_page.set_icon_name("package-x-generic-symbolic")

    def _format_size(self, size_bytes: int) -> str:
        for limit, div, fmt, unit in (
            (1 << 30, 1 << 30, ".2f", "GB"),
            (1 << 20, 1 << 20, ".1f", "MB"),
            (1 << 10, 1 << 10, ".1f", "KB"),
        ):
            if size_bytes >= limit:
                return f"{size_bytes / div:{fmt}} {unit}"
        return f"{size_bytes} B"

    def _on_open_clicked(self, _button):
        self._reset_status_page()
        filter_sims2pack = Gtk.FileFilter()
        filter_sims2pack.set_name("Sims2Pack Files (*.Sims2Pack)")
        filter_sims2pack.add_pattern("*.Sims2Pack")
        filter_sims2pack.add_pattern("*.sims2pack")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_sims2pack)

        dialog = Gtk.FileDialog()
        dialog.set_title(t("dlg_select_packs"))
        dialog.set_filters(filters)
        dialog.set_default_filter(filter_sims2pack)
        dialog.open_multiple(self, None, self._on_file_dialog_finish)

    def _on_file_dialog_finish(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            if files:
                paths = []
                for i in range(files.get_n_items()):
                    f = files.get_item(i)
                    path = f.get_path()
                    if path is None:
                        self._show_status_error(
                            "Remote File Not Supported",
                            "Please select local files only."
                        )
                        return
                    paths.append(path)
                self._handle_selected_files(paths)
        except GLib.Error:
            pass

    def _on_file_dropped(self, _target, value, _x, _y):
        paths = []
        if isinstance(value, Gdk.FileList):
            paths.extend(f.get_path() for f in value if f.get_path())

        if not paths:
            return False
        self._handle_selected_files(paths)
        return True

    def _populate_classic_view(self):
        """Populate Mootilda 2014 classic grid layout with parsed files."""
        self.classic_store.remove_all()
        # ponytail: stale snapshot from a previous package would corrupt
        # selection state if the strip checkbox toggles off after remove_all.
        if hasattr(self, "_pre_strip_selection"):
            del self._pre_strip_selection
        for f in self.parsed_files:
            self.classic_store.append(FileItem(f))

        # ponytail: SingleSelection keeps its selected index across
        # remove_all()/append(), so opening a second package can leave the
        # description panel showing an item from the previous package until
        # the user clicks something. Force it back to a known state.
        if self.classic_store.get_n_items() > 0:
            self.classic_sel.set_selected(0)

        file_name = os.path.basename(self.current_file_path) if self.current_file_path else ""
        self.classic_title_label.set_text(file_name)
        self.classic_type_label.set_text(f"{t('Package Type:')} {t(self.pkg_type) if self.pkg_type else t('msg_unknown')}")

        has_primary = any(f.get("is_primary") for f in self.parsed_files)
        self.classic_chk_remove_furniture.set_visible(has_primary)
        self.classic_chk_remove_furniture.set_active(False)

        self.classic_dropdown_filter.set_selected(0)

        # Set initial package description
        initial_desc = t("No description available.")
        if self.parsed_files and self.parsed_files[0].get("desc"):
            initial_desc = self.parsed_files[0]["desc"]
        self.classic_text_desc.get_buffer().set_text(initial_desc)

        self.classic_progress_bar.set_fraction(0.0)
        self.classic_progress_bar.set_text(t("status_ready_install"))
        self.classic_btn_install.set_sensitive(True)

        self._update_classic_selection_summary()

    def _update_classic_selection_summary(self):
        total = self.classic_store.get_n_items()
        selected = sum(item.checked for item in self.classic_store)
        safe_ver = GLib.markup_escape_text(t(self.game_ver) if self.game_ver else t("msg_unknown"))
        self.classic_lbl_meta.set_markup(
            f"<b>{t('Game Version:')}</b> {safe_ver}\n"
            f"<b>{t('Selected: {selected} / {total} files', selected=selected, total=total)}</b>"
        )

    def _on_classic_item_selected(self, sel, _gparam):
        item = sel.get_selected_item()
        if item and item.f.get("desc"):
            self.classic_text_desc.get_buffer().set_text(item.f["desc"])
        elif self.parsed_files and self.parsed_files[0].get("desc"):
            self.classic_text_desc.get_buffer().set_text(self.parsed_files[0]["desc"])
        else:
            self.classic_text_desc.get_buffer().set_text(t("No description available."))

    def _on_classic_filter_changed(self, dropdown, _gparam):
        if getattr(self, "_updating_ui_texts", False):
            return
        # ponytail: changing the filter invalidates the strip snapshot —
        # restoring a snapshot taken before the filter change would leave the
        # selection in a state that doesn't match any visible control combo.
        if hasattr(self, "_pre_strip_selection"):
            del self._pre_strip_selection
        idx = dropdown.get_selected()
        for item in self.classic_store:
            if idx == 0:  # Everything
                item.checked = True
            elif idx == 1:  # No Hacks/Mods
                item.checked = not item.f.get("is_hack", False)
            elif idx == 2:  # Primary Only
                item.checked = bool(item.f.get("is_primary", False))
            elif idx == 3:  # Custom Content Only
                item.checked = not bool(item.f.get("is_primary", False))
        self._update_classic_selection_summary()

    def _on_classic_remove_furniture_toggled(self, chk):
        if chk.get_active():
            # ponytail: snapshot current selection so we can restore it later
            self._pre_strip_selection = [item.checked for item in self.classic_store]
            self._updating_strip_chk = True
            try:
                for item in self.classic_store:
                    if not item.f.get("is_primary", False):
                        item.checked = False
            finally:
                self._updating_strip_chk = False
        else:
            if not self._updating_strip_chk:
                if hasattr(self, "_pre_strip_selection"):
                    for item, checked in zip(self.classic_store, self._pre_strip_selection):
                        item.checked = checked
                    del self._pre_strip_selection
                else:
                    self._on_classic_filter_changed(self.classic_dropdown_filter, None)
            else:
                if hasattr(self, "_pre_strip_selection"):
                    del self._pre_strip_selection
        self._update_classic_selection_summary()

    def _set_all_checked(self, value: bool):
        for item in self.classic_store:
            item.checked = value
        self._update_classic_selection_summary()

    def _show_status_error(self, title: str, description: str, icon_name: str = "dialog-error-symbolic"):
        self.status_page.set_title(t(title))
        self.status_page.set_description(t(description))
        self.status_page.set_icon_name(icon_name)
        self.empty_stack.set_visible_child_name("status")
        self._show_page("empty")

    def _mode_display_name(self, mode: str) -> str:
        """Return human-readable install mode for UI display."""
        return t("opt_keep_cc") if mode == "keep-cc" else t("opt_clean_primary")

    def _try_parse_package(self, file_path: str):
        """Parse and validate a single package. Returns pkg dict or raises."""
        if not file_path or not os.path.isfile(file_path):
            raise ValueError(f"File not found or is a directory: {file_path}")

        file_name = os.path.basename(file_path)
        size_bytes = os.path.getsize(file_path)
        formatted_size = self._format_size(size_bytes)

        pkg_type, game_ver, files = parse_archive(file_path)

        for f in files:
            name = f.get("name", "")
            if any(part == ".." for part in Path(name.replace("\\", "/")).parts) or os.path.isabs(name):
                raise ValueError(f"Unsafe path: {name}")

        primary_count = sum(1 for f in files if f.get("is_primary"))
        cc_count = len(files) - primary_count

        default_mode = self.config.get("default_install_mode", "clean")

        return {
            "file_path": file_path,
            "file_name": file_name,
            "pkg_type": pkg_type,
            "game_ver": game_ver,
            "files": files,
            "mode": default_mode,
            "size_bytes": size_bytes,
            "formatted_size": formatted_size,
            "primary_count": primary_count,
            "cc_count": cc_count,
        }

    def _handle_selected_files(self, paths: list):
        """Batch handler: parse multiple files and add to queue."""
        # Hide progress bar when adding new files
        self.queue_progress.set_visible(False)

        old_title = self.status_page.get_title()
        old_desc = self.status_page.get_description()
        self.status_page.set_title("Analyzing...")
        self.status_page.set_description("Please wait while packages are parsed")
        self.empty_stack.set_visible_child_name("status")
        self.choose_btn.set_sensitive(False)
        self.open_button.set_sensitive(False)

        def worker():
            is_batch = (len(paths) > 1) or (bool(self.package_queue) and not self._is_single_file_inspect)
            already_queued = {pkg["file_path"] for pkg in self.package_queue}
            new_pkgs = []
            errors = []
            
            for path in paths:
                if path in already_queued:
                    continue
                try:
                    pkg = self._try_parse_package(path)
                    new_pkgs.append(pkg)
                except Exception as err:
                    errors.append(f"{os.path.basename(path)}: {err}")
                    
            GLib.idle_add(update_ui, is_batch, new_pkgs, errors)

        def update_ui(is_batch, new_pkgs, errors):
            self.status_page.set_title(old_title)
            self.status_page.set_description(old_desc)
            self.choose_btn.set_sensitive(True)
            self.open_button.set_sensitive(True)

            if not is_batch:
                self._is_single_file_inspect = True
                self.package_queue.clear()
            else:
                self._is_single_file_inspect = False

            for pkg in new_pkgs:
                self.package_queue.append(pkg)

            if errors and not self.package_queue:
                # All failed — show first error on status page
                self._is_single_file_inspect = False
                self._show_status_error("Invalid Package(s)", errors[0])
                return
            elif errors:
                # Some failed, some succeeded — log and surface on queue page
                msg = f"{t('msg_skipped_files', n=len(errors))}: {'; '.join(errors)}"
                log.warning("%s", msg)
                self.queue_progress.set_visible(True)
                self.queue_progress.set_fraction(0.0)
                self.queue_progress.set_text(msg)

            if self.package_queue:
                if self._is_single_file_inspect:
                    # Single file selected — go directly to details
                    self._on_queue_review(0)
                else:
                    # Multiple files — show queue
                    self._populate_queue_view()
                    self._show_page("empty")

        threading.Thread(target=worker, daemon=True).start()

    def _populate_queue_view(self):
        """Populate the queue listbox from self.package_queue."""
        # Clear existing rows
        while (child := self.queue_listbox.get_first_child()) is not None:
            self.queue_listbox.remove(child)

        if not self.package_queue:
            self.empty_stack.set_visible_child_name("status")
            return

        self.empty_stack.set_visible_child_name("queue")

        for idx, pkg in enumerate(self.package_queue):
            row = Adw.ActionRow(
                title=pkg["file_name"],
                subtitle=f"{t('queue_files_count', n=len(pkg['files']))} · {pkg['formatted_size']} · {self._mode_display_name(pkg['mode'])}",
            )
            row.add_prefix(Gtk.Image.new_from_icon_name("package-x-generic-symbolic"))

            # Remove button
            btn_remove = Gtk.Button.new_from_icon_name("window-close-symbolic")
            btn_remove.set_valign(Gtk.Align.CENTER)
            btn_remove.add_css_class("flat")
            btn_remove.connect("clicked", lambda _b, i=idx: self._on_queue_remove(i))
            row.add_suffix(btn_remove)

            # Review button
            btn_review = Gtk.Button(label=t("btn_review"))
            btn_review.set_valign(Gtk.Align.CENTER)
            btn_review.connect("clicked", lambda _b, i=idx: self._on_queue_review(i))
            row.add_suffix(btn_review)
            row.set_activatable_widget(btn_review)

            self.queue_listbox.append(row)

    def _on_queue_remove(self, index: int):
        if 0 <= index < len(self.package_queue):
            self.package_queue.pop(index)
            # ponytail: dropping to a single package is no longer a "batch" —
            # switch into single-file review instead of showing a one-row queue.
            if len(self.package_queue) == 1:
                self._is_single_file_inspect = True
                self._on_queue_review(0)
                return
            self._populate_queue_view()
            # Refresh header bar buttons if queue became empty
            if self.current_page == "empty":
                self._show_page("empty")

    def _on_queue_review(self, index: int):
        if not (0 <= index < len(self.package_queue)):
            return
        self._install_token += 1
        pkg = self.package_queue[index]
        self._current_pkg_index = index
        self.current_file_path = pkg["file_path"]
        self.parsed_files = pkg["files"]
        self.pkg_type = pkg["pkg_type"]
        self.game_ver = pkg["game_ver"]

        # Populate modern details view
        self.row_filename.set_subtitle(pkg["file_name"])
        self.row_size.set_subtitle(pkg["formatted_size"])
        self.row_pkg_type.set_subtitle(t(pkg["pkg_type"]) if pkg["pkg_type"] else t("msg_unknown"))
        game_ver_display = t(pkg["game_ver"]) if pkg["game_ver"] else t("msg_unknown")
        truncated = game_ver_display if len(game_ver_display) <= 40 else game_ver_display[:40] + "…"
        self.row_game_ver.set_subtitle(truncated)
        self.game_ver_full_label.set_text(game_ver_display)
        self.row_file_count.set_subtitle(
            f"Total: {len(pkg['files'])} (Primary: {pkg['primary_count']}, CC: {pkg['cc_count']})"
        )
        self.row_path.set_subtitle(pkg["file_path"])

        # Sync mode dropdown with this package's stored mode
        self.row_mode.set_selected(0 if pkg["mode"] == "keep-cc" else 1)

        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text(t("status_ready_install"))
        self.install_button.set_sensitive(True)

        # Populate classic view (for users who switch to classic)
        self._populate_classic_view()

        # Show page based on configured UI layout
        if self.config.get("ui_layout") == "classic":
            self._show_page("classic")
        else:
            self._show_page("details")

    def _run_install(self, file_path, files, mode, progress_bar, install_button,
                      pkg_type="", game_ver=""):
        """Shared install runner for both modern and classic views."""
        prefix = self.config.get("sims2_prefix") or os.path.expanduser("~/EA Games/The Sims 2")
        self._install_in_progress = True
        self._install_token += 1
        current_token = self._install_token
        install_button.set_sensitive(False)

        def do_install():
            try:
                results = install_files(file_path, files, prefix, mode, pkg_type, game_ver)
            except Exception as e:
                GLib.idle_add(lambda: self._install_failed(progress_bar, install_button, str(e)) if self._install_token == current_token else None)
                return

            def update_ui():
                if self._install_token != current_token:
                    return
                self._install_in_progress = False
                progress_bar.set_fraction(1.0)
                msg = t("msg_installed_summary", teleport=results['teleport_count'], cc=results['downloads_count'])
                if results.get("blocked_files"):
                    msg += " " + t("msg_blocked_files", n=len(results['blocked_files']))
                if results.get("skipped_files"):
                    msg += " " + t("msg_skipped_files", n=len(results['skipped_files']))
                if results.get("hack_count", 0) > 0:
                    msg += " " + t("msg_mods_detected", n=results['hack_count'])
                progress_bar.set_text(msg)
                install_button.set_sensitive(True)

            GLib.idle_add(update_ui)

        threading.Thread(target=do_install, daemon=True).start()

    def _run_batch_install(self):
        """Install all packages in the queue sequentially."""
        prefix = self.config.get("sims2_prefix") or os.path.expanduser("~/EA Games/The Sims 2")
        queue = list(self.package_queue)
        total = len(queue)
        if total == 0:
            return

        self._install_in_progress = True
        self.install_button.set_sensitive(False)
        self.queue_progress.set_visible(True)
        self.queue_progress.set_fraction(0.0)

        def do_batch():
            failed = []
            installed = []
            for i, pkg in enumerate(queue):
                idx = i + 1

                def update_progress(current, name):
                    self.queue_progress.set_fraction(current / total)
                    self.queue_progress.set_text(t("msg_package_progress", current=current, total=total, name=name))

                GLib.idle_add(update_progress, idx, pkg["file_name"])

                try:
                    install_files(pkg["file_path"], pkg["files"], prefix, pkg["mode"],
                                  pkg["pkg_type"], pkg["game_ver"])
                    installed.append(pkg)
                except Exception as e:
                    failed.append((pkg["file_name"], str(e)))
                    continue

            def done():
                self._install_in_progress = False
                if failed:
                    self.queue_progress.set_text(
                        t("msg_batch_done", installed=total - len(failed), total=total, failed=len(failed))
                    )
                else:
                    self.queue_progress.set_fraction(1.0)
                    self.queue_progress.set_text(t("msg_batch_installed", total=total))
                self.install_button.set_sensitive(True)
                # ponytail: remove only the packages this batch actually
                # installed, by identity — not a blind clear(). A blind
                # clear() would also wipe packages the user queued while this
                # batch was running, and would silently discard failed
                # packages with no way to see or retry them.
                for pkg in installed:
                    try:
                        self.package_queue.remove(pkg)
                    except ValueError:
                        pass
                self._populate_queue_view()
                self._update_header_bar()

            GLib.idle_add(done)

        threading.Thread(target=do_batch, daemon=True).start()

    def _install_failed(self, progress_bar, install_button, error_msg):
        self._install_in_progress = False
        progress_bar.set_fraction(0.0)
        progress_bar.set_text(t("msg_install_failed", error_msg=error_msg))
        install_button.set_sensitive(True)

    def _on_install_clicked(self, _button):
        """Install handler — batch when on queue page, single when on details."""
        if self._install_in_progress:
            return

        if self.current_page == "empty" and self.package_queue:
            self._run_batch_install()
            return

        if not self.current_file_path or not self.parsed_files:
            return

        mode = "keep-cc" if self.row_mode.get_selected() == 0 else "clean"

        # If this package came from the queue, persist its mode choice and remove it
        if self._current_pkg_index >= 0 and self._current_pkg_index < len(self.package_queue):
            self.package_queue[self._current_pkg_index]["mode"] = mode
            if self._is_single_file_inspect:
                self.package_queue.clear()
                self._is_single_file_inspect = False
            else:
                self.package_queue.pop(self._current_pkg_index)
            self._current_pkg_index = -1

        self._run_install(self.current_file_path, self.parsed_files, mode,
                          self.progress_bar, self.install_button,
                          self.pkg_type, self.game_ver)

    def _on_classic_install_clicked(self, _button):
        """Install handler for classic Mootilda data grid view."""
        if self._install_in_progress:
            return

        if not self.current_file_path or not self.parsed_files:
            return

        selected_files = [
            self.classic_store.get_item(i).f
            for i in range(self.classic_store.get_n_items())
            if self.classic_store.get_item(i).checked
        ]
        if not selected_files:
            self.classic_progress_bar.set_text(t("msg_no_files_selected"))
            return

        # ponytail: mode reflects what the user actually selected, not a fixed
        # keep-cc. If every unselected file was CC, this behaves like "clean";
        # install_files still re-splits primary/cc internally either way.
        selected_has_cc = any(not f.get("is_primary") for f in selected_files)
        mode = "keep-cc" if selected_has_cc else "clean"
        self._run_install(self.current_file_path, selected_files, mode,
                          self.classic_progress_bar, self.classic_btn_install,
                          self.pkg_type, self.game_ver)


class NephilimApp(Adw.Application):
    """Application class for Project Nephilim."""

    def __init__(self):
        super().__init__(
            application_id="org.gnome.Nephilim",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.config = None

    def do_activate(self):
        self.config = load_config()
        apply_color_scheme(self.config.get("color_scheme"))
        self.show_main_window()

    def do_open(self, files, _n_files, _hint):
        """Files passed on the command line or via "Open with" / double-click."""
        self.do_activate()
        paths = [f.get_path() for f in files if f.get_path()]
        if paths:
            self.props.active_window._handle_selected_files(paths)

    def show_main_window(self):
        """Instantiate and present main application window."""
        win = self.props.active_window
        if not win:
            win = NephilimWindow(application=self)
        win.present()
        return win


def main():
    app = NephilimApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
