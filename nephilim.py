#!/usr/bin/env python3
import os
import sys
import argparse
import re
import html
import struct
import hashlib
import uuid
import xml.etree.ElementTree as ET
import defusedxml.ElementTree as defused_ET

# DBPF TypeIDs. The index stores them as little-endian uint32 and parse_archive reads
# them with struct "<I", so a 4-char tag's value is its ASCII bytes read big-endian
# (b"BHAV" -> 0x42484156); the on-disk bytes are reversed.
TYPE_BHAV = 0x42484156  # "BHAV" Behavior function
TYPE_BCON = 0x42434F4E  # "BCON" Behavior constant
TYPE_TTAB = 0x54544142  # "TTAB" Pie menu table
TYPE_TTAS = 0x54544173  # "TTAs" Pie menu strings

TYPE_HOUS = 0x484F5553  # "HOUS" House descriptor
TYPE_FAMI = 0x46414D49  # "FAMI" Family information
TYPE_AGED = 0xAC598EAC  # AgeData numeric TypeID
TYPE_FACE = 0xCCCEF852  # FacialStructure numeric TypeID

HACK_TYPE_IDS = {TYPE_BHAV, TYPE_BCON, TYPE_TTAB, TYPE_TTAS}
PRIMARY_TYPE_IDS = {TYPE_HOUS, TYPE_FAMI, TYPE_AGED, TYPE_FACE}

class Colors:
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    DARK_GRAY = '\033[90m'
    RESET = '\033[0m'

def format_bytes(b: int) -> str:
    if b >= 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    if b >= 1024:
        return f"{b / 1024:.2f} KB"
    return f"{b} B"

def sanitise_file_name(name: str) -> str:
    name = os.path.basename(name.replace('\\', os.sep).replace('/', os.sep))
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', name)
    return name if name and name.strip('.') else "_unnamed"

def resolve_directory(prefix: str, default_name: str) -> str:
    if os.path.isfile(prefix):
        raise IOError(f"'{prefix}' is a file.")
    if not os.path.exists(prefix):
        target = os.path.join(prefix, default_name)
        os.makedirs(target, exist_ok=True)
        return target
    for dirname in os.listdir(prefix):
        full = os.path.join(prefix, dirname)
        if os.path.isdir(full) and dirname.lower() == default_name.lower():
            return full
    target = os.path.join(prefix, default_name)
    os.makedirs(target, exist_ok=True)
    return target

def stream_copy(src, dest, length: int, buf_size=81920):
    rem = length
    while rem > 0:
        chunk = src.read(min(rem, buf_size))
        if not chunk: break
        dest.write(chunk)
        rem -= len(chunk)
    if rem > 0:
        raise IOError("Unexpected end of file during copy")

_md5_cache = {}

def parse_archive(source_path: str):
    with open(source_path, "rb") as stream:
        magic = stream.read(18).decode('ascii', errors='ignore')
        if magic != "Sims2 Packager 1.0":
            raise ValueError("Invalid magic header")

        first_offset = struct.unpack("<I", stream.read(4))[0]
        if first_offset < 22:
            raise ValueError("Invalid header: first_offset too small")
        root = defused_ET.fromstring(stream.read(first_offset - 22))

        pkg_type = root.get("type", "")
        game_ver = getattr(root.find("GameVersion"), "text", "") or ""

        file_size = os.fstat(stream.fileno()).st_size

        files = []
        for f_elem in root.findall("PackagedFile"):
            get_val = lambda t: getattr(f_elem.find(t), "text", "") or ""
            try:
                length = int(get_val("Length") or "0")
                f_offset = int(get_val("Offset") or "0")
            except ValueError:
                continue
            if f_offset < 0:
                continue
            abs_offset = first_offset + f_offset
            if abs_offset + length > file_size:
                continue

            clean_name = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', html.unescape(get_val("Name")))
            clean_desc = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', html.unescape(get_val("Description")))
            f = {
                "name": clean_name,
                "length": length,
                "type": get_val("Type"),
                "crc": get_val("Crc"),
                "desc": clean_desc,
                "abs_offset": abs_offset,
                "is_primary": False,
                "is_hack": False
            }

            if not f["crc"]:
                # ponytail: full MD5 read happens here at preview time, before
                # the user has chosen to install anything, and these same
                # bytes get read again later during extraction. Known cost —
                # defer this to install time instead if it becomes a real
                # complaint on large packages with missing CRCs.
                cache_key = (source_path, abs_offset, length)
                if cache_key in _md5_cache:
                    f["crc"] = _md5_cache[cache_key]
                else:
                    stream.seek(abs_offset)
                    md5 = hashlib.md5()
                    rem = length
                    while rem > 0:
                        chunk = stream.read(min(rem, 81920))
                        if not chunk: break
                        md5.update(chunk)
                        rem -= len(chunk)
                    f["crc"] = _md5_cache[cache_key] = md5.hexdigest().upper()

            f["is_primary"] = f["type"].lower() in ("lot", "family", "sim", "person")

            stream.seek(abs_offset)
            if length >= 48 and stream.read(4) == b"DBPF":
                stream.seek(abs_offset + 36)
                hdr = stream.read(12)
                if len(hdr) == 12:
                    num_files, idx_offset, idx_size = struct.unpack("<III", hdr)
                    if num_files > 0 and idx_offset > 0:
                        abs_idx = abs_offset + idx_offset
                        entry_size = idx_size // num_files
                        if entry_size in (20, 24) and abs_idx + idx_size <= abs_offset + length:
                            stream.seek(abs_idx)
                            for _ in range(num_files):
                                type_data = stream.read(4)
                                if len(type_data) < 4: break
                                type_id = struct.unpack("<I", type_data)[0]
                                stream.seek(entry_size - 4, os.SEEK_CUR)

                                if type_id in HACK_TYPE_IDS:
                                    f["is_hack"] = True
                                if type_id in PRIMARY_TYPE_IDS:
                                    f["is_primary"] = True
            files.append(f)

    return pkg_type, game_ver, files

def install_files(source_path: str, files: list, prefix: str, mode: str,
                   pkg_type: str = "", game_ver: str = "", *,
                   fallback_to_first: bool = True) -> dict:
    for f in files:
        if not re.fullmatch(r"[0-9A-Fa-f]{32}", f.get("crc", "")):
            raise ValueError("Invalid file CRC")

    primary_files = [f for f in files if f["is_primary"]]
    cc_files = [f for f in files if not f["is_primary"]]
    if fallback_to_first and not primary_files and files:
        primary_files.append(files[0])
        cc_files = [f for f in cc_files if f is not files[0]]

    teleport_dir = resolve_directory(prefix, "Teleport")
    downloads_dir = None

    teleport_count = 0
    downloads_count = 0
    stripped_count = 0
    hack_count = 0
    blocked_files = []
    skipped_files = []
    installed_details = []

    written_targets = []
    try:
        with open(source_path, "rb") as stream:
            for f in primary_files:
                target = os.path.join(teleport_dir, f"{f['crc']}.Sims2Tmp")
                # ponytail: skip on collision rather than renaming; Teleport files
                # must match the manifest's <Crc> tag for Sims 2 import to succeed.
                if os.path.exists(target):
                    skipped_files.append(f["name"])
                    installed_details.append({
                        "category": "skipped",
                        "name": f["name"],
                        "target": f"{f['crc']}.Sims2Tmp"
                    })
                    continue
                with open(target, "wb") as out:
                    written_targets.append(target)
                    stream.seek(f["abs_offset"])
                    stream_copy(stream, out, f["length"])
                teleport_count += 1
                if f["is_hack"]:
                    hack_count += 1
                installed_details.append({
                    "category": "teleport",
                    "name": f["name"],
                    "length": f["length"],
                    "target": f"{f['crc']}.Sims2Tmp",
                    "is_hack": f["is_hack"]
                })

            if primary_files:
                p_crc = primary_files[0]["crc"]

                root_elem = ET.Element("Sims2Package", type=pkg_type)
                ET.SubElement(root_elem, "GameVersion").text = game_ver

                o_idx = 0
                desc_map = {}
                for idx, f in enumerate(primary_files):
                    pf = ET.SubElement(root_elem, "PackagedFile")
                    ET.SubElement(pf, "Name").text = f["name"]
                    ET.SubElement(pf, "Length").text = str(f["length"])
                    ET.SubElement(pf, "Type").text = f["type"]
                    ET.SubElement(pf, "Crc").text = f["crc"]
                    ET.SubElement(pf, "Offset").text = str(o_idx)

                    placeholder = uuid.uuid4().hex
                    clean_desc = f["desc"].replace("]]>", "]]]]><![CDATA[>")
                    desc_map[placeholder.encode('utf-8')] = f"<![CDATA[{clean_desc}]]>".encode('utf-8')
                    ET.SubElement(pf, "Description").text = placeholder

                    o_idx += f["length"]

                manifest_bytes = b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root_elem, encoding="UTF-8")
                for ph, cdata in desc_map.items():
                    manifest_bytes = manifest_bytes.replace(ph, cdata)

                manifest_target = os.path.join(teleport_dir, f"{p_crc}.Sims2Import")
                if os.path.exists(manifest_target):
                    skipped_files.append(f"{p_crc}.Sims2Import")
                    installed_details.append({
                        "category": "skipped",
                        "name": f"{p_crc}.Sims2Import",
                        "target": f"{p_crc}.Sims2Import"
                    })
                else:
                    with open(manifest_target, "wb") as out:
                        written_targets.append(manifest_target)
                        out.write(b"Sims2 Packager 1.0")
                        out.write(struct.pack("<I", len(manifest_bytes) + 22))
                        out.write(manifest_bytes)
                        for f in primary_files:
                            stream.seek(f["abs_offset"])
                            stream_copy(stream, out, f["length"])
                    installed_details.append({
                        "category": "manifest",
                        "target": f"{p_crc}.Sims2Import"
                    })

            for f in cc_files:
                if mode == "keep-cc":
                    if downloads_dir is None:
                        downloads_dir = resolve_directory(prefix, "Downloads")
                    safe = sanitise_file_name(f["name"])
                    target = os.path.join(downloads_dir, safe)
                    if os.path.realpath(target).startswith(os.path.realpath(downloads_dir) + os.sep):
                        if os.path.exists(target):
                            skipped_files.append(f["name"])
                            installed_details.append({
                                "category": "skipped",
                                "name": f["name"]
                            })
                            continue
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        with open(target, "wb") as out:
                            written_targets.append(target)
                            stream.seek(f["abs_offset"])
                            stream_copy(stream, out, f["length"])
                        downloads_count += 1
                        if f["is_hack"]:
                            hack_count += 1
                        installed_details.append({
                            "category": "downloads",
                            "name": f["name"],
                            "length": f["length"],
                            "is_hack": f["is_hack"]
                        })
                    else:
                        blocked_files.append(f["name"])
                        installed_details.append({
                            "category": "blocked",
                            "name": f["name"]
                        })
                else:
                    stripped_count += 1
                    installed_details.append({
                        "category": "stripped",
                        "name": f["name"],
                        "length": f["length"]
                    })
    except Exception:
        for t in written_targets:
            try:
                if os.path.exists(t):
                    os.unlink(t)
            except OSError:
                pass
        raise

    return {
        "teleport_count": teleport_count,
        "downloads_count": downloads_count,
        "stripped_count": stripped_count,
        "hack_count": hack_count,
        "blocked_files": blocked_files,
        "skipped_files": skipped_files,
        "installed_details": installed_details
    }

def main():
    print(f"{Colors.MAGENTA}=================================================================================")
    print("                       ✦ PROJECT NEPHILIM: Sims 2 Package Installer ✦                ")
    print(f"================================================================================={Colors.RESET}")

    parser = argparse.ArgumentParser(description="Install Sims 2 packages securely.")
    parser.add_argument("-s", "--source", required=True, help="Path to the .sims2pack archive.")
    parser.add_argument("-p", "--prefix", required=True, help="Path to Sims 2 Documents prefix folder.")
    parser.add_argument("-m", "--mode", required=True, choices=['clean', 'keep-cc'], help="Installation mode.")
    args = parser.parse_args()

    try:
        print(f"{Colors.CYAN}[🔍] Parsing Sims2Pack archive: '{os.path.basename(args.source)}'...{Colors.RESET}")
        pkg_type, game_ver, files = parse_archive(args.source)

        print(f"{Colors.GREEN}[✅] Sims2Pack Archive successfully parsed!{Colors.RESET}\n")
        print("---------------------------------------------------------------------------------")
        print(f"  Package Type:   {pkg_type}")
        print(f"  Game Version:   {game_ver}")
        print(f"  Total Files:    {len(files)}")
        print(f"  Selected Mode:  {args.mode.upper()}")
        print("---------------------------------------------------------------------------------\n")

        results = install_files(args.source, files, args.prefix, args.mode, pkg_type, game_ver)

        for d in results["installed_details"]:
            cat = d["category"]
            if cat == "teleport":
                print(f"  {Colors.CYAN}[🏡 TELEPORT]{Colors.RESET} {d['name']} ({format_bytes(d['length'])}) -> {d['target']}")
                if d["is_hack"]:
                    print(f"                 {Colors.RED}⚠️ Warning: Primary file contains behavioral changes / mods!{Colors.RESET}")
            elif cat == "manifest":
                print(f"  {Colors.CYAN}[📄 MANIFEST]{Colors.RESET} Created import manifest -> {d['target']}")
            elif cat == "downloads":
                if d["is_hack"]:
                    print(f"  {Colors.RED}[💥 CC HACK]{Colors.RESET}  {d['name']} ({format_bytes(d['length'])}) -> Downloads/ [BEHAVIOR MOD]")
                else:
                    print(f"  {Colors.GREEN}[📦 CC FILE]{Colors.RESET}  {d['name']} ({format_bytes(d['length'])}) -> Downloads/")
            elif cat == "blocked":
                print(f"  {Colors.RED}[🚫 BLOCKED]{Colors.RESET}  '{d['name']}' — path traversal attempt detected, skipping.")
            elif cat == "skipped":
                print(f"  {Colors.YELLOW}[⏭️ SKIPPED]{Colors.RESET}  '{d['name']}' — file already exists, skipping.")
            elif cat == "stripped":
                print(f"  {Colors.DARK_GRAY}[🗑️ STRIPPED]{Colors.RESET} {d['name']} ({format_bytes(d['length'])})")

        print(f"\n{Colors.MAGENTA}=================================================================================")
        print(f"{Colors.GREEN}                        Installation Finished Successfully!")
        print(f"{Colors.CYAN}     Teleport Folder:    {results['teleport_count']} files installed")
        print(f"     Downloads Folder:   {results['downloads_count']} files installed")
        if results.get("skipped_files"):
            print(f"     Files Skipped:      {len(results['skipped_files'])} (already exist)")
        print(f"     CC Files Stripped:  {results['stripped_count']} files")

        if results["hack_count"] > 0:
            print(f"{Colors.RED}     [⚠️ WARNING]: {results['hack_count']} behavior-changing mods/hacks were detected!")
        print(f"{Colors.MAGENTA}================================================================================={Colors.RESET}")

    except Exception as e:
        import traceback
        print(f"\n{Colors.RED}[❌] Fatal Error during installation: {e}")
        traceback.print_exc()
        print(Colors.RESET)
        sys.exit(1)

if __name__ == "__main__":
    main()
