<img width="630" height="514" alt="image" src="https://github.com/user-attachments/assets/b8d39352-7168-445f-a3da-df12ece97e1a" />

This project is based on the work of the late great Mootilda. Nothing I did here would have been possible without the legacy of the original Clean Installer. She is the most important person here.

NINA is an independent reimplementation based on the file format specification. In other words: instead of taking the original code and just changing the language, the program was built from scratch by understanding how `.sims2pack` files are actually structured internally — and then recreating, in its own way, a smaller and simpler version focused on properly reading and installing these files, without all the extra weight of screens, dependencies, and side features.

The utility is written in Python and uses libadwaita, with a modern interface and polished UX. It supports installing multiple packages at once. In testing, **one hundred** lots were installed in a single run without a single hiccup. (I have no idea what the actual limit is, so feel free to absolutely go nuts.)

---

# AI Usage

This application was made using AI. I am not a programmer — I'm still learning, and very little of what was made here was actually made by a human. So I strongly encourage people to fork this and keep working on it, because I honestly don't know how long I'll keep maintaining NINA myself.

I used Claude, KIMI, and Gemini. And the AGENTS.MD PONYTAIL.

I'm also more than happy if an actual developer wants to jump in as a contributor bc i have other projects for the game on Linux in mind for the future. Or fork it to continue as manteiner, idk how long i will to that by myself.

---

# How to install

NINA **does not have a pre-built installer** (no Flatpak, no AppImage, no distro package). You download the source code and run it directly: it's just Python.

## 1. Install the dependencies

NINA needs Python 3, GTK 4, libadwaita, PyGObject (the bridge between Python and GTK), and `defusedxml`. Copy the command for your distro:

**Fedora**
```bash
sudo dnf install python3-gobject gtk4 libadwaita python3-defusedxml
```

**Ubuntu / Debian / Mint**
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 python3-defusedxml
```

**Arch**
```bash
sudo pacman -S python-gobject gtk4 libadwaita python-defusedxml
```

**openSUSE**
```bash
sudo zypper install python3-gobject typelib-1_0-Gtk-4_0 typelib-1_0-Adw-1 python3-defusedxml
```

Package names may vary slightly between versions. If NINA complains about `gi`, `Gtk`, `Adw`, or `defusedxml` when you launch it, something from this list is probably missing.

## 2. Download NINA

With git:

```bash
git clone https://github.com/usernamespacefightclub/NINA.git
cd NINA
```

Or, without git: on GitHub, click **Code → Download ZIP**, extract it, and enter the folder.

## 3. Test it

Inside the NINA folder:

```bash
python3 gui.py
```

To open a package directly:

```bash
python3 gui.py /path/to/file.sims2pack
```

## 4. Add NINA to the application menu

NINA is just a few Python files in a folder, so there's nothing to install. This step only creates a **shortcut** (a `.desktop` file) that points to the folder where you downloaded it, so NINA shows up in your app launcher and you don't have to open a terminal every time.

Run this **from inside the NINA folder**. Nothing is installed system-wide, so no `sudo`:

```bash
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/NINA.desktop <<EOF
[Desktop Entry]
Type=Application
Name=NINA
Comment=Install .Sims2Pack files into The Sims 2
Exec=python3 $PWD/gui.py %F
Icon=$PWD/NINA_PLACEHOLDER_ICON.png
Terminal=false
StartupNotify=true
Categories=Game;
MimeType=application/x-sims2pack;
EOF

update-desktop-database ~/.local/share/applications
```

NINA should now show up in your menu (usually under Games). If it doesn't, log out and back in. On KDE Plasma you can also run `kbuildsycoca6 --noincremental` to refresh the menu.

If you prefer, you can skip the terminal and create the same shortcut by hand with your desktop's menu editor (on KDE: right-click the menu → *Edit Applications*). Use `python3 /full/path/to/NINA/gui.py` as the program, and click the icon button to pick `NINA_PLACEHOLDER_ICON.png` from inside the NINA folder.

**Important:** the shortcut points to the folder where NINA is. If you move or delete that folder, the shortcut breaks. Just redo this step (or remove the shortcut, see below).

### Associate `.sims2pack` files with NINA

This makes double-clicking a `.sims2pack` open NINA. The simplest way is to right-click any `.sims2pack` file → **Open With** → pick NINA → tick "Always". Your file manager does the rest.

If you'd rather do it from the terminal, you first need to tell the system what a `.sims2pack` is:

```bash
mkdir -p ~/.local/share/mime/packages

cat > ~/.local/share/mime/packages/NINA.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-sims2pack">
    <comment>The Sims 2 package</comment>
    <glob pattern="*.sims2pack" case-sensitive="false"/>
  </mime-type>
</mime-info>
EOF

update-mime-database ~/.local/share/mime
xdg-mime default NINA.desktop application/x-sims2pack
```

On KDE you may see `qtpaths: command not found` after the last command. It's only a warning from `xdg-mime` and usually harmless. If double-clicking still doesn't open NINA, use the **Open With** method above.

## Updating

If you downloaded it with git, run `git pull` inside the folder. If you downloaded the ZIP, download it again and replace the folder. The menu shortcut keeps working as long as the folder stays in the same place.

## Uninstalling

There's nothing to uninstall: NINA is only the folder you downloaded plus the optional shortcut.

1. Delete the NINA folder.
2. Remove the menu shortcut:

```bash
rm -f ~/.local/share/applications/NINA.desktop
update-desktop-database ~/.local/share/applications
```

3. If you did the optional `.sims2pack` association from the terminal, remove it too:

```bash
rm -f ~/.local/share/mime/packages/NINA.xml
update-mime-database ~/.local/share/mime
```

4. If you also want to erase your settings (including the Sims 2 path you selected):

```bash
rm -rf ~/.config/nephilim
```

Packages NINA has already installed into the game **stay there**: NINA does not uninstall them.

---

# TRIVIA

## What is a `.sims2pack`?

Think of it as a sealed box. Inside are the items, with a label on the outside telling you what each item is. That's a `.sims2pack` file.

The game can't open this box by itself: someone has to open it, read the label, and put each item in the correct drawer inside the The Sims 2 folder.

## What NINA does

NINA is that someone.

You point it at one or more packages, it opens the boxes, shows you what's inside, and puts everything where it belongs:

- **Lots** (houses and lots) go into the `Teleport` folder, where the game imports them the next time it starts.
- **Custom Content** (CC included with the package) goes into the `Downloads` folder.

If a package contains something that changes the game's rules (a hack), NINA warns you before installing it, so you can make the decision with your eyes open.

## What's the difference between this and Clean Installer?

Sims2Pack Clean Installer (S2PCI) is the original tool, created by Karol Rybak in 2004 and later maintained by Mootilda until 2014. It is the program that taught the entire community how to install lots without making a mess of the game, and NINA would not exist without it.

NINA is not a copy of it, nor is it a port: the AI understood how the file is structured internally and wrote a new program, my way.

The practical differences:

- **The original is Windows-only.** It relies on the Windows registry and .NET. NINA is made for Linux: it opens like any other application, with no Wine involved, and you simply tell it where your game folder is (the one inside Lutris/Wine).
- **Smaller and leaner.** The original comes with its own installer, online list updates, a Windows Explorer menu extension, and a RAR reader. NINA does one thing: read and properly install packages.
- **Multiple packages at once**, queued up without having to open them one by one.
- **Modern UI.** It uses GTK4 and libadwaita, the look used by modern GNOME applications. There is also a "classic" table view for anyone who misses the original.

In short: Clean Installer is the reference. NINA is the version made specifically for people who play The Sims 2 on Linux.

---

Soon I'll open up ways to support me.

Keep in mind that I made all of this over the course of a few months while suffering through the free tiers of Claude, Kimi, and Gemini.

The available languages were chosen based on empirical observation of which languages are most common within the community, as well as through research. It is unlikely that any additional languages will be added.

I don't really know how GitHub works, so sorry if I did something wrong. Everything here looks confusing. That's why I encourage an actual programmer to fork or get the project transfred even more.

Thank you.
