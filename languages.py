#!/usr/bin/env python3
"""Project Nephilim - Language & Localization Module.

Provides UI translations for supported languages (English and Portuguese pt-BR),
auto-detects system locale using standard library `locale`, and handles fallback.
"""

import locale
import logging
import os
import sys

DEFAULT_LANGUAGE = "en"

log = logging.getLogger(__name__)

TRANSLATIONS = {
    "en": {
        # Buttons
        "btn_open": "Open Sims2Pack File",
        "btn_back": "Back",
        "btn_preferences": "Preferences",
        "btn_install": "Install",
        "btn_install_package": "Install Package",
        "btn_install_all": "Install All",
        "btn_install_selected": "Install Selected",
        "btn_browse_prefix": "Browse Prefix…",
        "btn_select_file": "Select File…",
        "btn_select_all": "Select All",
        "btn_deselect_all": "Deselect All",
        "btn_browse": "Browse…",
        "btn_review": "Review",
        "btn_donate": "Donate",

        # Pages / Headers
        "welcome_title": "Welcome to NINA pack installer",
        "welcome_subtitle": "Please select your Sims 2 default documents directory to get started.",
        "no_file_title": "No File Selected",
        "no_file_subtitle": "Select or drop a .Sims2Pack file to inspect and install.",

        # Preferences Groups
        "pref_group_package_info": "Package Information",
        "pref_group_install_opts": "Installation Options",
        "pref_group_general": "General",
        "pref_group_color_scheme": "Color Scheme",
        "pref_group_misc": "Miscellaneous",

        # Configuration Rows
        "row_filename": "File Name",
        "row_size": "Size",
        "row_pkg_type": "Package Type",
        "row_contents_summary": "Contents Summary",
        "row_full_path": "Full Path",
        "row_game_version": "Game Version",
        "row_install_mode": "Install Mode",
        "row_wine_prefix": "Game wine prefix",
        "row_clean_install": "Clean Install",
        "row_clean_install_sub": "Only install primary files (strip custom content by default)",
        "row_classic_layout": "Classic GUI Layout",
        "row_classic_layout_sub": "Use Mootilda 2014 Clean Installer grid layout",
        "row_donate_sub": "Support the project development (coming soon)",
        "row_language": "Language",

        # Dropdowns / Options
        "opt_keep_cc": "Keep Custom Content",
        "opt_clean_primary": "Clean (Primary Only)",
        "opt_theme_system": "Follow System",
        "opt_theme_light": "Light",
        "opt_theme_dark": "Dark",
        "filter_all": "Everything",
        "filter_no_hacks": "No Hacks/Mods",
        "filter_primary_only": "Primary Only",
        "filter_cc_only": "Custom Content Only",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Package Description",
        "classic_pkg_details": "Package Details",
        "classic_filter": "Filter:",
        "classic_strip_cc": "Strip Custom Content",

        # Status / Messages
        "status_ready": "Ready",
        "status_ready_install": "Ready to install",
        "msg_unknown": "Unknown",
        "msg_skipped_files": "Skipped {n} file(s)",
        "msg_no_files_selected": "No files selected for installation.",
        "msg_installed_summary": "Installed: {teleport} teleport, {cc} CC files.",
        "msg_blocked_files": "Blocked {n} file(s).",
        "msg_mods_detected": "⚠️ {n} behavior mod(s) detected!",
        "banner_mods_before": "{n} file(s) change how the game behaves (mods). Only install if you trust the source.",
        "banner_mods_after": "{n} behavior mod(s) were installed.",
        "msg_install_failed": "Install failed: {error_msg}",
        "msg_package_progress": "Package {current} of {total} — {name}",
        "msg_batch_done": "Done: {installed}/{total} installed. {failed} failed.",
        "msg_batch_installed": "Installed {total} packages",
        "dlg_select_prefix": "Select Sims 2 Prefix Directory",
        "dlg_select_packs": "Select Sims2Pack Files",
        "queue_files_count": "{n} file(s)",

        # Direct string literal mappings
        "Install Selected": "Install Selected",
        "Browse…": "Browse…",
        "Donate": "Donate",
        "Package Information": "Package Information",
        "Installation Options": "Installation Options",
        "General": "General",
        "Color Scheme": "Color Scheme",
        "Miscellaneous": "Miscellaneous",
        "File Name": "File Name",
        "Size": "Size",
        "Package Type": "Package Type",
        "Package Type:": "Package Type:",
        "Contents Summary": "Contents Summary",
        "Full Path": "Full Path",
        "Game Version": "Game Version",
        "Game Version:": "Game Version:",
        "Install Mode": "Install Mode",
        "Game wine prefix": "Game wine prefix",
        "Clean Install": "Clean Install",
        "Only install primary files (strip custom content by default)": "Only install primary files (strip custom content by default)",
        "Classic GUI Layout": "Classic GUI Layout",
        "Use Mootilda 2014 Clean Installer grid layout": "Use Mootilda 2014 Clean Installer grid layout",
        "Support the project development (coming soon)": "Support the project development (coming soon)",
        "Follow System": "Follow System",
        "Light": "Light",
        "Dark": "Dark",
        "No description available.": "No description available.",
        "Lot": "Lot",
        "Status": "Status",
        "Name": "Name",
        "Type": "Type",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Subfolder",
        "Selected: {selected} / {total} files": "Selected: {selected} / {total} files",
        "Invalid Package(s)": "Invalid Package(s)",
        "Remote File Not Supported": "Remote File Not Supported",
        "Please select local files only.": "Please select local files only.",
        "Language": "Language",
    },
    "pt-BR": {
        # Buttons
        "btn_open": "Abrir .sims2pack",
        "btn_back": "Voltar",
        "btn_preferences": "Preferências",
        "btn_install": "Instalar",
        "btn_install_package": "Instalar pacote",
        "btn_install_all": "Instalar tudo",
        "btn_install_selected": "Instalar selecionados",
        "btn_browse_prefix": "Procurar prefixo…",
        "btn_select_file": "Selecionar arquivo…",
        "btn_select_all": "Selecionar tudo",
        "btn_deselect_all": "Desmarcar tudo",
        "btn_browse": "Procurar…",
        "btn_review": "Revisar",
        "btn_donate": "Doar",

        # Pages / Headers
        "welcome_title": "Bem-vindo ao NINA pack installer",
        "welcome_subtitle": "Selecione a pasta padrão de documentos do The Sims 2 para começar.",
        "no_file_title": "Nenhum arquivo selecionado",
        "no_file_subtitle": "Selecione ou arraste um arquivo .Sims2Pack para inspecionar e instalar.",

        # Preferences Groups
        "pref_group_package_info": "Informações do pacote",
        "pref_group_install_opts": "Opções de instalação",
        "pref_group_general": "Geral",
        "pref_group_color_scheme": "Esquema de cores",
        "pref_group_misc": "Diversos",

        # Configuration Rows
        "row_filename": "Nome do arquivo",
        "row_size": "Tamanho",
        "row_pkg_type": "Tipo de pacote",
        "row_contents_summary": "Resumo do conteúdo",
        "row_full_path": "Caminho completo",
        "row_game_version": "Versão do jogo",
        "row_install_mode": "Modo de instalação",
        "row_wine_prefix": "Prefixo do Wine",
        "row_clean_install": "Instalação limpa",
        "row_clean_install_sub": "Instalar apenas os arquivos primários (remover CC por padrão)",
        "row_classic_layout": "Interface clássica",
        "row_classic_layout_sub": "Usar o layout em grade do Clean Installer de 2014 da Mootilda",
        "row_donate_sub": "Apoie o desenvolvimento do projeto (em breve)",
        "row_language": "Idioma",

        # Dropdowns / Options
        "opt_keep_cc": "Manter CC",
        "opt_clean_primary": "Limpo (apenas primários)",
        "opt_theme_system": "Seguir o sistema",
        "opt_theme_light": "Claro",
        "opt_theme_dark": "Escuro",
        "filter_all": "Tudo",
        "filter_no_hacks": "Sem mods",
        "filter_primary_only": "Apenas primários",
        "filter_cc_only": "Apenas CC",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Descrição do pacote",
        "classic_pkg_details": "Detalhes do pacote",
        "classic_filter": "Filtrar:",
        "classic_strip_cc": "Remover CC",

        # Status / Messages
        "status_ready": "Pronto",
        "status_ready_install": "Pronto para instalar",
        "msg_unknown": "Desconhecido",
        "msg_skipped_files": "{n} arquivo(s) ignorado(s)",
        "msg_no_files_selected": "Nada marcado para instalação",
        "msg_installed_summary": "Instalado(s) {teleport} teleport, {cc} arquivo(s) de CC",
        "msg_blocked_files": "{n} arquivo(s) bloqueado(s)",
        "msg_mods_detected": "⚠️ {n} mod(s) de comportamento detectado(s)!",
        "banner_mods_before": "{n} arquivo(s) alteram o comportamento do jogo (mods). Instale apenas se confiar na origem.",
        "banner_mods_after": "{n} mod(s) de comportamento foram instalados.",
        "msg_install_failed": "Falha na instalação: {error_msg}",
        "msg_package_progress": "Pacote {current} de {total} — {name}",
        "msg_batch_done": "Concluído: {installed}/{total} instalado(s). {failed} com falha.",
        "msg_batch_installed": "{total} pacote(s) instalado(s)",
        "dlg_select_prefix": "Selecionar diretório do prefixo do Sims 2",
        "dlg_select_packs": "Selecionar arquivos Sims2Pack",
        "queue_files_count": "{n} arquivo(s)",

        # Direct string literal mappings
        "Install Selected": "Instalar selecionados",
        "Browse…": "Procurar…",
        "Donate": "Doar",
        "Package Information": "Informações do pacote",
        "Installation Options": "Opções de instalação",
        "General": "Geral",
        "Color Scheme": "Esquema de cores",
        "Miscellaneous": "Diversos",
        "File Name": "Nome do arquivo",
        "Size": "Tamanho",
        "Package Type": "Tipo de pacote",
        "Package Type:": "Tipo de pacote:",
        "Contents Summary": "Resumo do conteúdo",
        "Full Path": "Caminho completo",
        "Game Version": "Versão do jogo",
        "Game Version:": "Versão do jogo:",
        "Install Mode": "Modo de instalação",
        "Game wine prefix": "Prefixo do Wine",
        "Clean Install": "Instalação limpa",
        "Only install primary files (strip custom content by default)": "Instalar apenas os arquivos primários (remover CC por padrão)",
        "Classic GUI Layout": "Interface clássica",
        "Use Mootilda 2014 Clean Installer grid layout": "Usar o layout em grade do Clean Installer de 2014 da Mootilda",
        "Support the project development (coming soon)": "Apoie o desenvolvimento do projeto (em breve)",
        "Follow System": "Seguir o sistema",
        "Light": "Claro",
        "Dark": "Escuro",
        "No description available.": "Sem descrição disponível",
        "Lot": "Lote",
        "Status": "Estado",
        "Name": "Nome",
        "Type": "Tipo",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Subpasta",
        "Selected: {selected} / {total} files": "Selecionado(s): {selected}/{total} arquivo(s)",
        "Invalid Package(s)": "Pacote(s) inválido(s)",
        "Remote File Not Supported": "Arquivo remoto não suportado",
        "Please select local files only.": "Selecione apenas arquivos locais.",
        "Language": "Idioma",
    },
    "de": {
        # Buttons
        "btn_open": "Sims2Pack-Datei öffnen",
        "btn_back": "Zurück",
        "btn_preferences": "Einstellungen",
        "btn_install": "Installieren",
        "btn_install_package": "Paket installieren",
        "btn_install_all": "Alle installieren",
        "btn_install_selected": "Auswahl installieren",
        "btn_browse_prefix": "Präfix durchsuchen…",
        "btn_select_file": "Datei auswählen…",
        "btn_select_all": "Alles auswählen",
        "btn_deselect_all": "Auswahl aufheben",
        "btn_browse": "Durchsuchen…",
        "btn_review": "Überprüfen",
        "btn_donate": "Spenden",

        # Pages / Headers
        "welcome_title": "Willkommen beim NINA pack installer",
        "welcome_subtitle": "Bitte wähle deinen Sims 2-Standardordner für Dokumente aus, um zu beginnen.",
        "no_file_title": "Keine Datei ausgewählt",
        "no_file_subtitle": "Wähle eine .Sims2Pack-Datei aus oder ziehe sie hierher, um sie zu prüfen und zu installieren.",

        # Preferences Groups
        "pref_group_package_info": "Paketinformationen",
        "pref_group_install_opts": "Installationsoptionen",
        "pref_group_general": "Allgemein",
        "pref_group_color_scheme": "Farbschema",
        "pref_group_misc": "Sonstiges",

        # Configuration Rows
        "row_filename": "Dateiname",
        "row_size": "Größe",
        "row_pkg_type": "Pakettyp",
        "row_contents_summary": "Inhaltsübersicht",
        "row_full_path": "Vollständiger Pfad",
        "row_game_version": "Spielversion",
        "row_install_mode": "Installationsmodus",
        "row_wine_prefix": "Wine-Präfix des Spiels",
        "row_clean_install": "Saubere Installation",
        "row_clean_install_sub": "Nur primäre Dateien installieren (CC wird standardmäßig ausgeschlossen)",
        "row_classic_layout": "Klassisches Layout",
        "row_classic_layout_sub": "Raster-Layout des Mootilda 2014 Clean Installer verwenden",
        "row_donate_sub": "Unterstütze die Projektentwicklung (demnächst verfügbar)",
        "row_language": "Sprache",

        # Dropdowns / Options
        "opt_keep_cc": "CC behalten",
        "opt_clean_primary": "Sauber (nur primäre)",
        "opt_theme_system": "Systemeinstellung",
        "opt_theme_light": "Hell",
        "opt_theme_dark": "Dunkel",
        "filter_all": "Alles",
        "filter_no_hacks": "Keine Hacks/Mods",
        "filter_primary_only": "Nur primäre",
        "filter_cc_only": "Nur CC",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Paketbeschreibung",
        "classic_pkg_details": "Paketdetails",
        "classic_filter": "Filter:",
        "classic_strip_cc": "CC ausschließen",

        # Status / Messages
        "status_ready": "Bereit",
        "status_ready_install": "Bereit zur Installation",
        "msg_unknown": "Unbekannt",
        "msg_skipped_files": "{n} Datei(en) übersprungen",
        "msg_no_files_selected": "Keine Dateien zur Installation ausgewählt.",
        "msg_installed_summary": "Installiert: {teleport} in Teleport, {cc} CC-Dateien.",
        "msg_blocked_files": "{n} Datei(en) blockiert.",
        "msg_mods_detected": "⚠️ {n} Behavior-Mod(s) erkannt!",
        "banner_mods_before": "{n} Datei(en) ändern das Spielverhalten (Mods). Nur installieren, wenn du der Quelle vertraust.",
        "banner_mods_after": "{n} Behavior-Mod(s) wurden installiert.",
        "msg_install_failed": "Installation fehlgeschlagen: {error_msg}",
        "msg_package_progress": "Paket {current} von {total} — {name}",
        "msg_batch_done": "Fertig: {installed}/{total} installiert. {failed} fehlgeschlagen.",
        "msg_batch_installed": "{total} Pakete installiert",
        "dlg_select_prefix": "Sims-2-Prefix-Verzeichnis auswählen",
        "dlg_select_packs": "Sims2Pack-Dateien auswählen",
        "queue_files_count": "{n} Datei(en)",

        # Direct string literal mappings
        "Install Selected": "Auswahl installieren",
        "Browse…": "Durchsuchen…",
        "Donate": "Spenden",
        "Package Information": "Paketinformationen",
        "Installation Options": "Installationsoptionen",
        "General": "Allgemein",
        "Color Scheme": "Farbschema",
        "Miscellaneous": "Sonstiges",
        "File Name": "Dateiname",
        "Size": "Größe",
        "Package Type": "Pakettyp",
        "Package Type:": "Pakettyp:",
        "Contents Summary": "Inhaltsübersicht",
        "Full Path": "Vollständiger Pfad",
        "Game Version": "Spielversion",
        "Game Version:": "Spielversion:",
        "Install Mode": "Installationsmodus",
        "Game wine prefix": "Wine-Präfix des Spiels",
        "Clean Install": "Saubere Installation",
        "Only install primary files (strip custom content by default)": "Nur primäre Dateien installieren (CC wird standardmäßig ausgeschlossen)",
        "Classic GUI Layout": "Klassisches Layout",
        "Use Mootilda 2014 Clean Installer grid layout": "Raster-Layout des Mootilda 2014 Clean Installer verwenden",
        "Support the project development (coming soon)": "Unterstütze die Projektentwicklung (demnächst verfügbar)",
        "Follow System": "Systemeinstellung",
        "Light": "Hell",
        "Dark": "Dunkel",
        "No description available.": "Keine Beschreibung verfügbar.",
        "Lot": "Grundstück",
        "Status": "Status",
        "Name": "Name",
        "Type": "Typ",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Unterordner",
        "Selected: {selected} / {total} files": "Ausgewählt: {selected} / {total} Dateien",
        "Invalid Package(s)": "Ungültige(s) Paket(e)",
        "Remote File Not Supported": "Remote-Dateien werden nicht unterstützt",
        "Please select local files only.": "Bitte wähle nur lokale Dateien aus.",
        "Language": "Sprache",
    },
    "es": {
        # Buttons
        "btn_open": "Abrir archivo Sims2Pack",
        "btn_back": "Atrás",
        "btn_preferences": "Preferencias",
        "btn_install": "Instalar",
        "btn_install_package": "Instalar paquete",
        "btn_install_all": "Instalar todo",
        "btn_install_selected": "Instalar seleccionados",
        "btn_browse_prefix": "Buscar prefijo…",
        "btn_select_file": "Seleccionar archivo…",
        "btn_select_all": "Seleccionar todo",
        "btn_deselect_all": "Deseleccionar todo",
        "btn_browse": "Buscar…",
        "btn_review": "Revisar",
        "btn_donate": "Donar",

        # Pages / Headers
        "welcome_title": "Bienvenido al NINA pack installer",
        "welcome_subtitle": "Selecciona tu carpeta de documentos predeterminada de Sims 2 para comenzar.",
        "no_file_title": "Ningún archivo seleccionado",
        "no_file_subtitle": "Selecciona o arrastra un archivo .Sims2Pack para inspeccionarlo e instalarlo.",

        # Preferences Groups
        "pref_group_package_info": "Información del paquete",
        "pref_group_install_opts": "Opciones de instalación",
        "pref_group_general": "General",
        "pref_group_color_scheme": "Esquema de color",
        "pref_group_misc": "Varios",

        # Configuration Rows
        "row_filename": "Nombre del archivo",
        "row_size": "Tamaño",
        "row_pkg_type": "Tipo de paquete",
        "row_contents_summary": "Resumen del contenido",
        "row_full_path": "Ruta completa",
        "row_game_version": "Versión del juego",
        "row_install_mode": "Modo de instalación",
        "row_wine_prefix": "Prefijo de Wine del juego",
        "row_clean_install": "Instalación limpia",
        "row_clean_install_sub": "Instalar solo archivos primarios (excluye contenido personalizado por defecto)",
        "row_classic_layout": "Diseño de interfaz clásica",
        "row_classic_layout_sub": "Usar el diseño de cuadrícula del Clean Installer de Mootilda 2014",
        "row_donate_sub": "Apoya el desarrollo del proyecto (próximamente)",
        "row_language": "Idioma",

        # Dropdowns / Options
        "opt_keep_cc": "Mantener contenido personalizado",
        "opt_clean_primary": "Limpio (solo primarios)",
        "opt_theme_system": "Seguir sistema",
        "opt_theme_light": "Claro",
        "opt_theme_dark": "Oscuro",
        "filter_all": "Todo",
        "filter_no_hacks": "Sin hacks/mods",
        "filter_primary_only": "Solo primarios",
        "filter_cc_only": "Solo contenido personalizado",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Descripción del paquete",
        "classic_pkg_details": "Detalles del paquete",
        "classic_filter": "Filtro:",
        "classic_strip_cc": "Excluir contenido personalizado",

        # Status / Messages
        "status_ready": "Listo",
        "status_ready_install": "Listo para instalar",
        "msg_unknown": "Desconocido",
        "msg_skipped_files": "Se omitieron {n} archivo(s)",
        "msg_no_files_selected": "No se seleccionaron archivos para instalar.",
        "msg_installed_summary": "Instalado(s): {teleport} teleport, {cc} archivo(s) de CC.",
        "msg_blocked_files": "Se bloquearon {n} archivo(s).",
        "msg_mods_detected": "⚠️ ¡Se detectaron {n} mod(s) de comportamiento!",
        "banner_mods_before": "{n} archivo(s) cambian el comportamiento del juego (mods). Instala solo si confías en el origen.",
        "banner_mods_after": "Se instalaron {n} mod(s) de comportamiento.",
        "msg_install_failed": "La instalación falló: {error_msg}",
        "msg_package_progress": "Paquete {current} de {total} — {name}",
        "msg_batch_done": "Listo: {installed}/{total} instalado(s). {failed} con error.",
        "msg_batch_installed": "{total} paquete(s) instalado(s)",
        "dlg_select_prefix": "Seleccionar directorio del prefijo de Sims 2",
        "dlg_select_packs": "Seleccionar archivos Sims2Pack",
        "queue_files_count": "{n} archivo(s)",

        # Direct string literal mappings
        "Install Selected": "Instalar seleccionados",
        "Browse…": "Buscar…",
        "Donate": "Donar",
        "Package Information": "Información del paquete",
        "Installation Options": "Opciones de instalación",
        "General": "General",
        "Color Scheme": "Esquema de color",
        "Miscellaneous": "Varios",
        "File Name": "Nombre del archivo",
        "Size": "Tamaño",
        "Package Type": "Tipo de paquete",
        "Package Type:": "Tipo de paquete:",
        "Contents Summary": "Resumen del contenido",
        "Full Path": "Ruta completa",
        "Game Version": "Versión del juego",
        "Game Version:": "Versión del juego:",
        "Install Mode": "Modo de instalación",
        "Game wine prefix": "Prefijo de Wine del juego",
        "Clean Install": "Instalación limpia",
        "Only install primary files (strip custom content by default)": "Instalar solo archivos primarios (excluye contenido personalizado por defecto)",
        "Classic GUI Layout": "Diseño de interfaz clásica",
        "Use Mootilda 2014 Clean Installer grid layout": "Usar el diseño de cuadrícula del Clean Installer de Mootilda 2014",
        "Support the project development (coming soon)": "Apoya el desarrollo del proyecto (próximamente)",
        "Follow System": "Seguir sistema",
        "Light": "Claro",
        "Dark": "Oscuro",
        "No description available.": "No hay descripción disponible.",
        "Lot": "Solar",
        "Status": "Estado",
        "Name": "Nombre",
        "Type": "Tipo",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Subcarpeta",
        "Selected: {selected} / {total} files": "Seleccionado(s): {selected} / {total} archivo(s)",
        "Invalid Package(s)": "Paquete(s) inválido(s)",
        "Remote File Not Supported": "Archivo remoto no compatible",
        "Please select local files only.": "Selecciona solo archivos locales.",
        "Language": "Idioma",
    },
    "pl": {
        # Buttons
        "btn_open": "Otwórz plik Sims2Pack",
        "btn_back": "Wstecz",
        "btn_preferences": "Preferencje",
        "btn_install": "Zainstaluj",
        "btn_install_package": "Zainstaluj paczkę",
        "btn_install_all": "Zainstaluj wszystko",
        "btn_install_selected": "Zainstaluj zaznaczone",
        "btn_browse_prefix": "Przeglądaj prefiks…",
        "btn_select_file": "Wybierz plik…",
        "btn_select_all": "Zaznacz wszystko",
        "btn_deselect_all": "Odznacz wszystko",
        "btn_browse": "Przeglądaj…",
        "btn_review": "Podgląd",
        "btn_donate": "Wesprzyj",

        # Pages / Headers
        "welcome_title": "Witaj w NINA pack installer",
        "welcome_subtitle": "Wybierz domyślny folder dokumentów Sims 2, aby rozpocząć.",
        "no_file_title": "Nie wybrano pliku",
        "no_file_subtitle": "Wybierz lub przeciągnij plik .Sims2Pack, aby go sprawdzić i zainstalować.",

        # Preferences Groups
        "pref_group_package_info": "Informacje o paczce",
        "pref_group_install_opts": "Opcje instalacji",
        "pref_group_general": "Ogólne",
        "pref_group_color_scheme": "Motyw kolorystyczny",
        "pref_group_misc": "Różne",

        # Configuration Rows
        "row_filename": "Nazwa pliku",
        "row_size": "Rozmiar",
        "row_pkg_type": "Typ paczki",
        "row_contents_summary": "Podsumowanie zawartości",
        "row_full_path": "Pełna ścieżka",
        "row_game_version": "Wersja gry",
        "row_install_mode": "Tryb instalacji",
        "row_wine_prefix": "Prefiks Wine gry",
        "row_clean_install": "Czysta instalacja",
        "row_clean_install_sub": "Instaluj tylko pliki podstawowe (CC pomijany domyślnie)",
        "row_classic_layout": "Klasyczny układ interfejsu",
        "row_classic_layout_sub": "Użyj układu siatki z Mootilda 2014 Clean Installer",
        "row_donate_sub": "Wesprzyj rozwój projektu (wkrótce)",
        "row_language": "Język",

        # Dropdowns / Options
        "opt_keep_cc": "Zachowaj CC",
        "opt_clean_primary": "Czysta (tylko podstawowe)",
        "opt_theme_system": "Zgodnie z systemem",
        "opt_theme_light": "Jasny",
        "opt_theme_dark": "Ciemny",
        "filter_all": "Wszystko",
        "filter_no_hacks": "Bez hacków/modów",
        "filter_primary_only": "Tylko podstawowe",
        "filter_cc_only": "Tylko CC",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Opis paczki",
        "classic_pkg_details": "Szczegóły paczki",
        "classic_filter": "Filtr:",
        "classic_strip_cc": "Pomiń CC",

        # Status / Messages
        "status_ready": "Gotowe",
        "status_ready_install": "Gotowe do instalacji",
        "msg_unknown": "Nieznany",
        "msg_skipped_files": "Pominięto plików: {n}",
        "msg_no_files_selected": "Nie wybrano plików do instalacji.",
        "msg_installed_summary": "Zainstalowano: {teleport} w Teleport, {cc} plików CC.",
        "msg_blocked_files": "Zablokowano plików: {n}.",
        "msg_mods_detected": "⚠️ Wykryto behavior-modów: {n}!",
        "banner_mods_before": "Pliki zmieniające zachowanie gry (mody): {n}. Instaluj tylko, jeśli ufasz źródłu.",
        "banner_mods_after": "Zainstalowano behavior-modów: {n}.",
        "msg_install_failed": "Instalacja nie powiodła się: {error_msg}",
        "msg_package_progress": "Paczka {current} z {total} — {name}",
        "msg_batch_done": "Gotowe: zainstalowano {installed}/{total}. Niepowodzeń: {failed}.",
        "msg_batch_installed": "Zainstalowano paczek: {total}",
        "dlg_select_prefix": "Wybierz katalog prefiksu Sims 2",
        "dlg_select_packs": "Wybierz pliki Sims2Pack",
        "queue_files_count": "{n} plik(ów)",

        # Direct string literal mappings
        "Install Selected": "Zainstaluj zaznaczone",
        "Browse…": "Przeglądaj…",
        "Donate": "Wesprzyj",
        "Package Information": "Informacje o paczce",
        "Installation Options": "Opcje instalacji",
        "General": "Ogólne",
        "Color Scheme": "Motyw kolorystyczny",
        "Miscellaneous": "Różne",
        "File Name": "Nazwa pliku",
        "Size": "Rozmiar",
        "Package Type": "Typ paczki",
        "Package Type:": "Typ paczki:",
        "Contents Summary": "Podsumowanie zawartości",
        "Full Path": "Pełna ścieżka",
        "Game Version": "Wersja gry",
        "Game Version:": "Wersja gry:",
        "Install Mode": "Tryb instalacji",
        "Game wine prefix": "Prefiks Wine gry",
        "Clean Install": "Czysta instalacja",
        "Only install primary files (strip custom content by default)": "Instaluj tylko pliki podstawowe (CC pomijany domyślnie)",
        "Classic GUI Layout": "Klasyczny układ interfejsu",
        "Use Mootilda 2014 Clean Installer grid layout": "Użyj układu siatki z Mootilda 2014 Clean Installer",
        "Support the project development (coming soon)": "Wesprzyj rozwój projektu (wkrótce)",
        "Follow System": "Zgodnie z systemem",
        "Light": "Jasny",
        "Dark": "Ciemny",
        "No description available.": "Brak dostępnego opisu.",
        "Lot": "Parcela",
        "Status": "Stan",
        "Name": "Nazwa",
        "Type": "Typ",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Podfolder",
        "Selected: {selected} / {total} files": "Zaznaczono: {selected} / {total} plików",
        "Invalid Package(s)": "Nieprawidłowa(e) paczka(i)",
        "Remote File Not Supported": "Pliki zdalne nie są obsługiwane",
        "Please select local files only.": "Wybieraj tylko pliki lokalne.",
        "Language": "Język",
    },
    "ru": {
        # Buttons
        "btn_open": "Открыть файл Sims2Pack",
        "btn_back": "Назад",
        "btn_preferences": "Настройки",
        "btn_install": "Установить",
        "btn_install_package": "Установить пакет",
        "btn_install_all": "Установить всё",
        "btn_install_selected": "Установить выбранное",
        "btn_browse_prefix": "Обзор префикса…",
        "btn_select_file": "Выбрать файл…",
        "btn_select_all": "Выбрать всё",
        "btn_deselect_all": "Снять выбор",
        "btn_browse": "Обзор…",
        "btn_review": "Просмотр",
        "btn_donate": "Поддержать",

        # Pages / Headers
        "welcome_title": "Добро пожаловать в NINA pack installer",
        "welcome_subtitle": "Выберите папку документов Sims 2 по умолчанию, чтобы начать.",
        "no_file_title": "Файл не выбран",
        "no_file_subtitle": "Выберите или перетащите файл .Sims2Pack для проверки и установки.",

        # Preferences Groups
        "pref_group_package_info": "Информация о пакете",
        "pref_group_install_opts": "Параметры установки",
        "pref_group_general": "Общие",
        "pref_group_color_scheme": "Цветовая схема",
        "pref_group_misc": "Разное",

        # Configuration Rows
        "row_filename": "Имя файла",
        "row_size": "Размер",
        "row_pkg_type": "Тип пакета",
        "row_contents_summary": "Сводка содержимого",
        "row_full_path": "Полный путь",
        "row_game_version": "Версия игры",
        "row_install_mode": "Режим установки",
        "row_wine_prefix": "Wine-префикс игры",
        "row_clean_install": "Чистая установка",
        "row_clean_install_sub": "Устанавливать только основные файлы (CC исключается по умолчанию)",
        "row_classic_layout": "Классический интерфейс",
        "row_classic_layout_sub": "Использовать сеточный макет из Mootilda 2014 Clean Installer",
        "row_donate_sub": "Поддержать разработку проекта (скоро)",
        "row_language": "Язык",

        # Dropdowns / Options
        "opt_keep_cc": "Сохранить CC",
        "opt_clean_primary": "Чисто (только основные)",
        "opt_theme_system": "Как в системе",
        "opt_theme_light": "Светлая",
        "opt_theme_dark": "Тёмная",
        "filter_all": "Всё",
        "filter_no_hacks": "Без хаков/модов",
        "filter_primary_only": "Только основные",
        "filter_cc_only": "Только CC",

        # Dynamic Labels (Classic View)
        "classic_pkg_desc": "Описание пакета",
        "classic_pkg_details": "Детали пакета",
        "classic_filter": "Фильтр:",
        "classic_strip_cc": "Исключить CC",

        # Status / Messages
        "status_ready": "Готово",
        "status_ready_install": "Готово к установке",
        "msg_unknown": "Неизвестно",
        "msg_skipped_files": "Пропущено файлов: {n}",
        "msg_no_files_selected": "Не выбрано файлов для установки.",
        "msg_installed_summary": "Установлено: {teleport} в Teleport, {cc} файлов CC.",
        "msg_blocked_files": "Заблокировано файлов: {n}.",
        "msg_mods_detected": "⚠️ Обнаружено behavior-модов: {n}!",
        "banner_mods_before": "Файлов, меняющих поведение игры (моды): {n}. Устанавливайте, только если доверяете источнику.",
        "banner_mods_after": "Установлено behavior-модов: {n}.",
        "msg_install_failed": "Ошибка установки: {error_msg}",
        "msg_package_progress": "Пакет {current} из {total} — {name}",
        "msg_batch_done": "Готово: установлено {installed}/{total}. Ошибок: {failed}.",
        "msg_batch_installed": "Установлено пакетов: {total}",
        "dlg_select_prefix": "Выберите каталог префикса Sims 2",
        "dlg_select_packs": "Выберите файлы Sims2Pack",
        "queue_files_count": "{n} файл(ов)",

        # Direct string literal mappings
        "Install Selected": "Установить выбранное",
        "Browse…": "Обзор…",
        "Donate": "Поддержать",
        "Package Information": "Информация о пакете",
        "Installation Options": "Параметры установки",
        "General": "Общие",
        "Color Scheme": "Цветовая схема",
        "Miscellaneous": "Разное",
        "File Name": "Имя файла",
        "Size": "Размер",
        "Package Type": "Тип пакета",
        "Package Type:": "Тип пакета:",
        "Contents Summary": "Сводка содержимого",
        "Full Path": "Полный путь",
        "Game Version": "Версия игры",
        "Game Version:": "Версия игры:",
        "Install Mode": "Режим установки",
        "Game wine prefix": "Wine-префикс игры",
        "Clean Install": "Чистая установка",
        "Only install primary files (strip custom content by default)": "Устанавливать только основные файлы (CC исключается по умолчанию)",
        "Classic GUI Layout": "Классический интерфейс",
        "Use Mootilda 2014 Clean Installer grid layout": "Использовать сеточный макет из Mootilda 2014 Clean Installer",
        "Support the project development (coming soon)": "Поддержать разработку проекта (скоро)",
        "Follow System": "Как в системе",
        "Light": "Светлая",
        "Dark": "Тёмная",
        "No description available.": "Описание недоступно.",
        "Lot": "Участок",
        "Status": "Статус",
        "Name": "Имя",
        "Type": "Тип",
        "MD5 / CRC": "MD5 / CRC",
        "Subfolder": "Подпапка",
        "Selected: {selected} / {total} files": "Выбрано: {selected} / {total} файлов",
        "Invalid Package(s)": "Недействительный(е) пакет(ы)",
        "Remote File Not Supported": "Удалённые файлы не поддерживаются",
        "Please select local files only.": "Выбирайте только локальные файлы.",
        "Language": "Язык",
    },
}


def detect_language() -> str:
    """Auto-detect the OS language using stdlib locale and environment variables.
    Defaults to 'en' if unsupported or undetected.
    """
    candidate = None
    try:
        candidate = locale.getlocale()[0]
    except Exception:
        pass

    if not candidate:
        for env_var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            val = os.environ.get(env_var)
            if val:
                candidate = val
                break

    if candidate:
        norm = candidate.lower().replace("-", "_")
        if norm.startswith("pt_br"):
            return "pt-BR"
        if norm.startswith("de"):
            return "de"
        if norm.startswith("es"):
            return "es"
        if norm.startswith("pl"):
            return "pl"
        if norm.startswith("ru"):
            return "ru"
        if norm.startswith("en"):
            return "en"

    return DEFAULT_LANGUAGE


_current_language = detect_language()


def get_language() -> str:
    """Return the currently active language code."""
    return _current_language


def set_language(lang_code: str) -> str:
    """Set active language. Normalizes locale tags and falls back to default."""
    global _current_language
    if not lang_code:
        _current_language = DEFAULT_LANGUAGE
    elif lang_code in TRANSLATIONS:
        _current_language = lang_code
    else:
        norm = lang_code.lower().replace("-", "_")
        if norm.startswith("pt_br"):
            _current_language = "pt-BR"
        elif norm.startswith("de"):
            _current_language = "de"
        elif norm.startswith("es"):
            _current_language = "es"
        elif norm.startswith("pl"):
            _current_language = "pl"
        elif norm.startswith("ru"):
            _current_language = "ru"
        elif norm.startswith("en"):
            _current_language = "en"
        else:
            _current_language = DEFAULT_LANGUAGE
    return _current_language


LANGUAGE_NAMES = {
    "en": "English",
    "pt-BR": "Português (Brasil)",
    "de": "Deutsch",
    "es": "Español",
    "pl": "Polski",
    "ru": "Русский",
}


def get_language_name(lang_code: str) -> str:
    """Return the human-readable display name for a language code."""
    return LANGUAGE_NAMES.get(lang_code, lang_code)


def get_supported_languages() -> list[str]:
    """Return list of supported language codes, alphabetically by display name."""
    return sorted(TRANSLATIONS.keys(), key=get_language_name)


def t(key: str, **kwargs) -> str:
    """Translate a key or English text into the active language.
    Falls back to English and raw key if missing. Formats kwargs if provided.
    """
    lang_dict = TRANSLATIONS.get(_current_language, TRANSLATIONS[DEFAULT_LANGUAGE])
    en_dict = TRANSLATIONS[DEFAULT_LANGUAGE]

    text = lang_dict.get(key)
    if text is None:
        text = en_dict.get(key, key)

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception as e:
            log.warning("t(%r) format failed: %r", key, e)
            return text
    return text


if __name__ == "__main__":
    # Self-check: every language has exactly the same keys as English
    for _code, _d in TRANSLATIONS.items():
        assert set(_d) == set(TRANSLATIONS["en"]), (_code, set(_d) ^ set(TRANSLATIONS["en"]))

    # Self-check: Portuguese lookup
    set_language("pt-BR")
    assert t("btn_open") == "Abrir .sims2pack"
    assert t("Language") == "Idioma"
    assert t("Lot") == "Lote"
    assert t("Package Type:") == "Tipo de pacote:"
    assert t("Game Version:") == "Versão do jogo:"
    assert t("No description available.") == "Sem descrição disponível"
    assert t("Status") == "Estado"
    assert t("Subfolder") == "Subpasta"
    assert t("Selected: {selected} / {total} files", selected=1, total=5) == "Selecionado(s): 1/5 arquivo(s)"
    assert t("msg_mods_detected", n=3) == "⚠️ 3 mod(s) de comportamento detectado(s)!"
    assert t("queue_files_count", n=2) == "2 arquivo(s)"

    # Self-check: English lookup
    set_language("en")
    assert t("btn_open") == "Open Sims2Pack File"
    assert t("Language") == "Language"
    assert t("Lot") == "Lot"
    assert t("Package Type:") == "Package Type:"
    assert t("Game Version:") == "Game Version:"
    assert t("Status") == "Status"
    assert t("Subfolder") == "Subfolder"
    assert t("msg_mods_detected", n=3) == "⚠️ 3 behavior mod(s) detected!"
    assert t("queue_files_count", n=2) == "2 file(s)"

    # Self-check: German lookup
    set_language("de")
    assert t("btn_open") == "Sims2Pack-Datei öffnen"
    assert t("Language") == "Sprache"
    assert t("Lot") == "Grundstück"
    assert t("Package Type:") == "Pakettyp:"
    assert t("Game Version:") == "Spielversion:"
    assert t("Status") == "Status"
    assert t("Subfolder") == "Unterordner"
    assert t("msg_mods_detected", n=3) == "⚠️ 3 Behavior-Mod(s) erkannt!"
    assert t("queue_files_count", n=2) == "2 Datei(en)"

    # Self-check: Spanish lookup
    set_language("es")
    assert t("btn_open") == "Abrir archivo Sims2Pack"
    assert t("Language") == "Idioma"
    assert t("Lot") == "Solar"
    assert t("Package Type:") == "Tipo de paquete:"
    assert t("Game Version:") == "Versión del juego:"
    assert t("Status") == "Estado"
    assert t("Subfolder") == "Subcarpeta"
    assert t("msg_mods_detected", n=3) == "⚠️ ¡Se detectaron 3 mod(s) de comportamiento!"
    assert t("queue_files_count", n=2) == "2 archivo(s)"

    # Self-check: Polish lookup
    set_language("pl")
    assert t("btn_open") == "Otwórz plik Sims2Pack"
    assert t("Language") == "Język"
    assert t("Lot") == "Parcela"
    assert t("Package Type:") == "Typ paczki:"
    assert t("Game Version:") == "Wersja gry:"
    assert t("Status") == "Stan"
    assert t("Subfolder") == "Podfolder"
    assert t("msg_mods_detected", n=3) == "⚠️ Wykryto behavior-modów: 3!"
    assert t("queue_files_count", n=2) == "2 plik(ów)"

    # Self-check: Russian lookup
    set_language("ru")
    assert t("btn_open") == "Открыть файл Sims2Pack"
    assert t("Language") == "Язык"
    assert t("Lot") == "Участок"
    assert t("Package Type:") == "Тип пакета:"
    assert t("Game Version:") == "Версия игры:"
    assert t("Status") == "Статус"
    assert t("Subfolder") == "Подпапка"
    assert t("msg_mods_detected", n=3) == "⚠️ Обнаружено behavior-модов: 3!"
    assert t("queue_files_count", n=2) == "2 файл(ов)"

    # Self-check: Fallback for unknown language defaults to English
    set_language("fr_FR")
    assert get_language() == "en"
    assert t("btn_open") == "Open Sims2Pack File"

    # Self-check: batch/dialog keys format in every language
    for _code in TRANSLATIONS:
        set_language(_code)
        assert "3" in t("msg_batch_done", installed=2, total=3, failed=1)
        assert "3" in t("msg_batch_installed", total=3)
        assert "4" in t("msg_package_progress", current=2, total=4, name="x") and "x" in t("msg_package_progress", current=2, total=4, name="x")
        assert t("dlg_select_prefix") != "dlg_select_prefix" and t("dlg_select_packs") != "dlg_select_packs"

    # Self-check: only pt-BR maps to pt-BR; other pt* fall back to en
    assert set_language("pt_BR.UTF-8") == "pt-BR"
    assert set_language("pt_PT") == "en"
    assert set_language("pt") == "en"

    # Self-check: placeholder mismatch logs a warning and returns raw text
    set_language("en")
    with __import__("unittest").TestCase().assertLogs(log, "WARNING"):
        assert t("Selected: {selected} / {total} files", selected=1) == "Selected: {selected} / {total} files"

    # Self-check: Missing key returns raw key
    assert t("non_existent_key") == "non_existent_key"

    print("All language self-checks passed successfully.")
