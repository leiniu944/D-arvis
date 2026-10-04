import ctypes
import json
import os
import subprocess

from PySide6.QtCore import QFileInfo, Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QFileIconProvider,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", ctypes.c_void_p),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", ctypes.c_uint),
        ("szDisplayName", ctypes.c_wchar * 260),
        ("szTypeName", ctypes.c_wchar * 80),
    ]


class AppsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("appsPanel")

        self.applications = []

        self.icon_provider = QFileIconProvider()
        self.icon_cache = {}

        self.embedded_hwnd = None
        self.embedded_application = None

        self.window_search_timer = None
        self.embedded_resize_timer = None

        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)

        self.setStyleSheet("""
            QFrame#appsPanel {
                background-color: rgba(2, 7, 13, 245);
            }

            QFrame.card {
                background-color: rgba(5, 18, 30, 190);
                border: 1px solid rgba(50, 180, 235, 65);
                border-radius: 6px;
            }

            QFrame#embeddedHost {
                background-color: rgb(8, 8, 8);
                border: 1px solid rgba(50, 180, 235, 80);
            }

            QLabel {
                background: transparent;
            }

            QPushButton {
                background-color: rgba(20, 90, 125, 45);
                border: 1px solid rgba(60, 190, 240, 80);
                border-radius: 4px;
                color: rgba(180, 230, 250, 230);
                padding: 7px 12px;
                font-size: 10px;
                letter-spacing: 1px;
            }

            QPushButton:hover {
                background-color: rgba(30, 150, 210, 65);
                border: 1px solid rgba(80, 220, 255, 150);
                color: rgba(220, 250, 255, 255);
            }

            QPushButton:pressed {
                background-color: rgba(40, 180, 240, 90);
            }

            QLineEdit {
                background-color: rgba(3, 15, 25, 220);
                border: 1px solid rgba(50, 180, 235, 70);
                border-radius: 4px;
                color: rgba(190, 235, 250, 235);
                padding: 8px 10px;
                font-size: 10px;
                selection-background-color: rgba(50, 180, 235, 100);
            }

            QLineEdit:focus {
                border: 1px solid rgba(70, 210, 255, 150);
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QScrollBar:vertical {
                background: rgba(5, 20, 30, 100);
                width: 6px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background: rgba(60, 180, 230, 100);
                border-radius: 3px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.create_ui()
        self.load_applications()

    # =========================================================
    # UI
    # =========================================================

    def create_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(35, 30, 35, 25)

        main_layout.setSpacing(15)

        # =====================================================
        # NAGŁÓWEK
        # =====================================================

        header = QVBoxLayout()

        header.setSpacing(4)

        title = QLabel("APLIKACJE")

        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Light))

        title.setStyleSheet("""
            color: rgba(190, 240, 255, 245);
            letter-spacing: 5px;
        """)

        subtitle = QLabel("JARVIS APPLICATION CONTROL")

        subtitle.setStyleSheet("""
            color: rgba(70, 180, 225, 140);
            font-size: 9px;
            letter-spacing: 3px;
        """)

        header.addWidget(title)
        header.addWidget(subtitle)

        main_layout.addLayout(header)

        # =====================================================
        # PANEL STEROWANIA
        # =====================================================

        control_card = QFrame()

        control_card.setProperty("class", "card")

        control_layout = QVBoxLayout(control_card)

        control_layout.setContentsMargins(12, 10, 12, 10)

        control_layout.setSpacing(8)

        top_row = QHBoxLayout()

        top_row.setSpacing(6)

        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText("SZUKAJ APLIKACJI...")

        self.search_edit.textChanged.connect(self.filter_applications)

        top_row.addWidget(self.search_edit, 1)

        self.refresh_button = QPushButton("⟳ ODŚWIEŻ")

        self.refresh_button.setFixedWidth(110)

        self.refresh_button.clicked.connect(self.load_applications)

        top_row.addWidget(self.refresh_button)

        self.back_button = QPushButton("← LISTA APLIKACJI")

        self.back_button.setFixedWidth(130)

        self.back_button.hide()

        self.back_button.clicked.connect(self.close_embedded_application)

        top_row.addWidget(self.back_button)

        control_layout.addLayout(top_row)

        main_layout.addWidget(control_card)

        # =====================================================
        # LISTA APLIKACJI
        # =====================================================

        self.content_container = QWidget()

        self.content_layout = QVBoxLayout(self.content_container)

        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.content_layout.setSpacing(5)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.content_container)

        main_layout.addWidget(self.scroll_area, 1)

        # =====================================================
        # KONTENER DLA ZEWNĘTRZNEGO OKNA
        # =====================================================

        self.embedded_host = QFrame()

        self.embedded_host.setObjectName("embeddedHost")

        self.embedded_host.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)

        self.embedded_host.hide()

        main_layout.addWidget(self.embedded_host, 1)

        # =====================================================
        # STATUS
        # =====================================================

        self.status_label = QLabel("GOTOWY")

        self.status_label.setStyleSheet("""
            color: rgba(90, 180, 215, 150);
            font-size: 9px;
            letter-spacing: 1px;
        """)

        main_layout.addWidget(self.status_label)

    # =========================================================
    # ŁADOWANIE APLIKACJI
    # =========================================================

    def load_applications(self):

        self.refresh_button.setEnabled(False)

        self.status_label.setText("SKANOWANIE APLIKACJI...")

        self.search_edit.blockSignals(True)

        self.search_edit.clear()

        self.search_edit.blockSignals(False)

        applications = []

        applications.extend(self.get_windows_apps())

        applications.extend(self.get_start_menu_shortcuts())

        unique = {}

        for application in applications:

            name = str(application.get("name", "")).strip()

            if not name:
                continue

            application["name"] = name

            key = name.casefold()

            if key not in unique:

                unique[key] = application

        self.applications = list(unique.values())

        self.applications.sort(key=lambda item: item["name"].casefold())

        self.show_applications(self.applications)

        self.refresh_button.setEnabled(True)

    # =========================================================
    # APLIKACJE WINDOWS
    # =========================================================

    def get_windows_apps(self):

        applications = []

        powershell_script = r"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Get-StartApps |
    Select-Object Name, AppID |
    ConvertTo-Json -Compress
"""

        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            powershell_script,
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if result.returncode != 0:
                return applications

            output_bytes = result.stdout

            if not output_bytes:
                return applications

            # -------------------------------------------------
            # UTF-8
            # -------------------------------------------------

            try:

                output = output_bytes.decode("utf-8")

            except UnicodeDecodeError:

                # Fallback dla starszego PowerShell
                try:

                    output = output_bytes.decode("utf-16")

                except UnicodeDecodeError:

                    output = output_bytes.decode("mbcs", errors="replace")

            output = output.strip()

            if not output:
                return applications

            data = json.loads(output)

            if isinstance(data, dict):

                data = [data]

            for item in data:

                name = str(item.get("Name", ""))

                app_id = str(item.get("AppID", ""))

                if not name or not app_id:
                    continue

                applications.append(
                    {
                        "name": name,
                        "path": app_id,
                        "type": "WINDOWS APP",
                        "source": "windows",
                    }
                )

        except Exception:

            pass

        return applications

    # =========================================================
    # SKRÓTY MENU START
    # =========================================================

    def get_start_menu_shortcuts(self):

        applications = []

        paths = []

        program_data = os.environ.get("ProgramData")

        app_data = os.environ.get("APPDATA")

        if program_data:

            paths.append(
                os.path.join(
                    program_data, "Microsoft", "Windows", "Start Menu", "Programs"
                )
            )

        if app_data:

            paths.append(
                os.path.join(app_data, "Microsoft", "Windows", "Start Menu", "Programs")
            )

        for start_menu in paths:

            if not os.path.isdir(start_menu):
                continue

            try:

                for root, dirs, files in os.walk(start_menu):

                    # -------------------------------------------------
                    # Ukrywamy katalogi systemowe
                    # -------------------------------------------------

                    dirs[:] = [
                        directory
                        for directory in dirs
                        if directory.lower() not in {"desktop.ini"}
                    ]

                    for filename in files:

                        extension = os.path.splitext(filename)[1].lower()

                        # -------------------------------------------------
                        # Standardowe skróty aplikacji
                        # -------------------------------------------------

                        if extension == ".lnk":

                            full_path = os.path.join(root, filename)

                            name = os.path.splitext(filename)[0]

                            applications.append(
                                {
                                    "name": name,
                                    "path": full_path,
                                    "type": "SKRÓT",
                                    "source": "shortcut",
                                }
                            )

            except Exception:

                continue

        return applications

    # =========================================================
    # POBIERANIE IKONY Z HICON
    # =========================================================

    def hicon_to_qicon(self, hicon):

        if not hicon:
            return QIcon()

        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        class ICONINFO(ctypes.Structure):

            _fields_ = [
                ("fIcon", ctypes.c_bool),
                ("xHotspot", ctypes.c_uint32),
                ("yHotspot", ctypes.c_uint32),
                ("hbmMask", ctypes.c_void_p),
                ("hbmColor", ctypes.c_void_p),
            ]

        class BITMAPINFOHEADER(ctypes.Structure):

            _fields_ = [
                ("biSize", ctypes.c_uint32),
                ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32),
            ]

        icon_info = ICONINFO()

        try:

            if not user32.GetIconInfo(hicon, ctypes.byref(icon_info)):

                return QIcon()

            hbm_color = icon_info.hbmColor

            hbm_mask = icon_info.hbmMask

            if not hbm_color:

                return QIcon()

            bitmap_info = BITMAPINFOHEADER()

            bitmap_info.biSize = ctypes.sizeof(BITMAPINFOHEADER)

            bitmap_info.biWidth = 0

            bitmap_info.biHeight = 0

            bitmap_info.biPlanes = 1

            bitmap_info.biBitCount = 32

            bitmap_info.biCompression = 0

            # -------------------------------------------------
            # Pobieramy rozmiar bitmapy
            # -------------------------------------------------

            class BITMAP(ctypes.Structure):

                _fields_ = [
                    ("bmType", ctypes.c_long),
                    ("bmWidth", ctypes.c_long),
                    ("bmHeight", ctypes.c_long),
                    ("bmWidthBytes", ctypes.c_long),
                    ("bmPlanes", ctypes.c_ushort),
                    ("bmBitsPixel", ctypes.c_ushort),
                    ("bmBits", ctypes.c_void_p),
                ]

            bitmap = BITMAP()

            if not gdi32.GetObjectW(
                hbm_color, ctypes.sizeof(bitmap), ctypes.byref(bitmap)
            ):

                return QIcon()

            width = int(bitmap.bmWidth)

            height = int(bitmap.bmHeight)

            if width <= 0 or height <= 0:

                return QIcon()

            bitmap_info.biWidth = width

            bitmap_info.biHeight = -height

            buffer_size = width * height * 4

            pixel_buffer = ctypes.create_string_buffer(buffer_size)

            gdi32.GetDIBits(
                ctypes.c_void_p(user32.GetDC(0)),
                hbm_color,
                0,
                height,
                pixel_buffer,
                ctypes.byref(bitmap_info),
                0,
            )

            image = QImage(
                pixel_buffer, width, height, width * 4, QImage.Format.Format_ARGB32
            ).copy()

            if image.isNull():

                return QIcon()

            pixmap = QPixmap.fromImage(image)

            return QIcon(pixmap)

        except Exception:

            return QIcon()

        finally:

            try:

                if icon_info.hbmColor:

                    gdi32.DeleteObject(icon_info.hbmColor)

                if icon_info.hbmMask:

                    gdi32.DeleteObject(icon_info.hbmMask)

            except Exception:

                pass

    # =========================================================
    # IKONA Z PLIKU
    # =========================================================

    def get_file_icon(self, path):

        if not path:

            return QIcon()

        try:

            path = os.path.abspath(path)

        except Exception:

            return QIcon()

        if not os.path.exists(path):

            return QIcon()

        cache_key = ("file", path.lower())

        if cache_key in self.icon_cache:

            return self.icon_cache[cache_key]

        icon = QIcon()

        # =====================================================
        # WINDOWS SHELL
        # =====================================================

        try:

            shell32 = ctypes.windll.shell32

            file_info = SHFILEINFOW()

            SHGFI_ICON = 0x000000100
            SHGFI_LARGEICON = 0x000000000
            SHGFI_USEFILEATTRIBUTES = 0x000000010

            result = shell32.SHGetFileInfoW(
                path,
                0,
                ctypes.byref(file_info),
                ctypes.sizeof(file_info),
                SHGFI_ICON | SHGFI_LARGEICON,
            )

            if result and file_info.hIcon:

                icon = self.hicon_to_qicon(file_info.hIcon)

                ctypes.windll.user32.DestroyIcon(file_info.hIcon)

        except Exception:

            icon = QIcon()

        # =====================================================
        # FALLBACK QT
        # =====================================================

        if icon.isNull():

            try:

                icon = self.icon_provider.icon(QFileInfo(path))

            except Exception:

                icon = QIcon()

        self.icon_cache[cache_key] = icon

        return icon

    # =========================================================
    # IKONA WINDOWS APP
    # =========================================================

    def get_windows_app_icon(self, app_id):

        if not app_id:

            return QIcon()

        cache_key = ("windows", app_id)

        if cache_key in self.icon_cache:

            return self.icon_cache[cache_key]

        icon = QIcon()

        try:

            shell32 = ctypes.windll.shell32
            ole32 = ctypes.windll.ole32

            # -------------------------------------------------
            # Tworzymy pełną ścieżkę Shell
            # -------------------------------------------------

            shell_path = "shell:AppsFolder\\" + app_id

            # -------------------------------------------------
            # ILCreateFromPathW
            # -------------------------------------------------

            shell32.ILCreateFromPathW.restype = ctypes.c_void_p

            shell32.ILCreateFromPathW.argtypes = [ctypes.c_wchar_p]

            pidl = shell32.ILCreateFromPathW(shell_path)

            if pidl:

                try:

                    SHGFI_PIDL = 0x000000008
                    SHGFI_ICON = 0x000000100
                    SHGFI_LARGEICON = 0x000000000

                    file_info = SHFILEINFOW()

                    result = shell32.SHGetFileInfoW(
                        ctypes.c_void_p(pidl),
                        0,
                        ctypes.byref(file_info),
                        ctypes.sizeof(file_info),
                        SHGFI_PIDL | SHGFI_ICON | SHGFI_LARGEICON,
                    )

                    if result and file_info.hIcon:

                        icon = self.hicon_to_qicon(file_info.hIcon)

                        ctypes.windll.user32.DestroyIcon(file_info.hIcon)

                finally:

                    ole32.CoTaskMemFree(ctypes.c_void_p(pidl))

        except Exception:

            icon = QIcon()

        # =====================================================
        # FALLBACK SHELL.APPLICATION
        # =====================================================

        if icon.isNull():

            try:

                import win32com.client

                shell = win32com.client.Dispatch("Shell.Application")

                apps_folder = shell.Namespace("shell:AppsFolder")

                if apps_folder:

                    item = apps_folder.ParseName(app_id)

                    if item:

                        try:

                            icon_location = item.ExtendedProperty("System.IconLocation")

                        except Exception:

                            icon_location = None

                        if icon_location:

                            icon_location = str(icon_location)

                            icon_path = icon_location.split(",")[0].strip()

                            icon_path = os.path.expandvars(icon_path)

                            if os.path.isfile(icon_path):

                                icon = self.get_file_icon(icon_path)

            except Exception:

                pass

        self.icon_cache[cache_key] = icon

        return icon

    # =========================================================
    # GŁÓWNE POBIERANIE IKONY
    # =========================================================

    def get_application_icon(self, application):

        path = application.get("path", "")

        source = application.get("source", "")

        if not path:

            return QIcon()

        # =====================================================
        # WINDOWS / MICROSOFT STORE
        # =====================================================

        if source == "windows":

            return self.get_windows_app_icon(path)

        # =====================================================
        # ZWYKŁY PLIK / SKRÓT
        # =====================================================

        return self.get_file_icon(path)

    # =========================================================
    # WYŚWIETLANIE
    # =========================================================

    def show_applications(self, applications):

        self.clear_content()

        for application in applications:

            self.add_application_row(application)

        self.content_layout.addStretch()

        self.status_label.setText(f"{len(applications)} APLIKACJI")

    def add_application_row(self, application):

        row = QFrame()

        row.setProperty("class", "card")

        row.setFixedHeight(58)

        layout = QHBoxLayout(row)

        layout.setContentsMargins(12, 6, 12, 6)

        layout.setSpacing(10)

        # =====================================================
        # IKONA
        # =====================================================

        icon_label = QLabel()

        icon_label.setFixedSize(36, 36)

        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label.setStyleSheet("""
            background: transparent;
        """)

        icon = self.get_application_icon(application)

        if not icon.isNull():

            pixmap = icon.pixmap(32, 32)

            if not pixmap.isNull():

                icon_label.setPixmap(pixmap)

        layout.addWidget(icon_label)

        # =====================================================
        # NAZWA + ŚCIEŻKA
        # =====================================================

        name_container = QVBoxLayout()

        name_container.setContentsMargins(0, 0, 0, 0)

        name_container.setSpacing(2)

        name_label = QLabel(application["name"])

        name_label.setStyleSheet("""
            color: rgba(190, 230, 245, 230);
            font-size: 11px;
            font-weight: bold;
        """)

        path_label = QLabel(application["path"])

        path_label.setStyleSheet("""
            color: rgba(90, 150, 175, 130);
            font-size: 8px;
        """)

        path_label.setToolTip(application["path"])

        name_container.addWidget(name_label)

        name_container.addWidget(path_label)

        layout.addLayout(name_container, 1)

        # =====================================================
        # TYP
        # =====================================================

        type_label = QLabel(application.get("type", "APPLICATION"))

        type_label.setFixedWidth(100)

        type_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        type_label.setStyleSheet("""
            color: rgba(110, 170, 195, 150);
            font-size: 8px;
        """)

        layout.addWidget(type_label)

        # =====================================================
        # URUCHOM
        # =====================================================

        launch_button = QPushButton("URUCHOM")

        launch_button.setFixedWidth(90)

        launch_button.clicked.connect(
            lambda checked=False, app=application: self.launch_application(app)
        )

        layout.addWidget(launch_button)

        # =====================================================
        # DWUKLIK
        # =====================================================

        row.mouseDoubleClickEvent = (
            lambda event, app=application: self.launch_application(app)
        )

        row._application_name = application["name"]

        self.content_layout.addWidget(row)

    # =========================================================
    # URUCHAMIANIE
    # =========================================================

    def launch_application(self, application):

        try:

            if self.embedded_hwnd:

                self.close_embedded_application()

            source = application.get("source", "shortcut")

            path = application["path"]

            self.embedded_application = application

            # =================================================
            # WINDOWS APP
            # =================================================

            if source == "windows":

                subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{path}"])

            # =================================================
            # ZWYKŁY PLIK / SKRÓT
            # =================================================

            else:

                os.startfile(path)

            self.status_label.setText(f'URUCHAMIANIE: {application["name"]}...')

            # =================================================
            # CZEKAMY NA OKNO
            # =================================================

            self.window_search_attempts = 0

            if self.window_search_timer:

                self.window_search_timer.stop()

                self.window_search_timer.deleteLater()

            self.window_search_timer = QTimer(self)

            self.window_search_timer.timeout.connect(
                lambda: self.find_and_embed_window(application)
            )

            self.window_search_timer.start(250)

        except Exception as error:

            self.status_label.setText(f"NIE MOŻNA URUCHOMIĆ: {error}")

    # =========================================================
    # SZUKANIE OKNA WINDOWS
    # =========================================================

    def find_and_embed_window(self, application):

        self.window_search_attempts += 1

        if self.window_search_attempts > 60:

            if self.window_search_timer:

                self.window_search_timer.stop()

            self.status_label.setText("NIE ZNALEZIONO OKNA APLIKACJI")

            return

        hwnd = self.find_application_window(application)

        if not hwnd:

            return

        if self.window_search_timer:

            self.window_search_timer.stop()

        if self.embed_window(hwnd):

            self.status_label.setText(f'URUCHOMIONO W JARVIS: {application["name"]}')

    # =========================================================
    # ZNAJDOWANIE OKNA
    # =========================================================

    def find_application_window(self, application):

        user32 = ctypes.windll.user32

        foreground = user32.GetForegroundWindow()

        if foreground:

            title = self.get_window_title(foreground)

            app_name = application["name"].casefold()

            title_lower = title.casefold()

            if title and (app_name in title_lower or title_lower in app_name):

                return foreground

        # =====================================================
        # ENUMERACJA WSZYSTKICH OKIEN
        # =====================================================

        found = []

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p
        )

        @WNDENUMPROC
        def enum_callback(hwnd, lparam):

            if not user32.IsWindowVisible(hwnd):

                return True

            length = user32.GetWindowTextLengthW(hwnd)

            if length <= 0:

                return True

            buffer = ctypes.create_unicode_buffer(length + 1)

            user32.GetWindowTextW(hwnd, buffer, length + 1)

            title = buffer.value.strip()

            if not title:

                return True

            app_name = application["name"].casefold()

            title_lower = title.casefold()

            if app_name in title_lower or title_lower in app_name:

                found.append(hwnd)

                return False

            return True

        user32.EnumWindows(enum_callback, 0)

        if found:

            return found[0]

        return None

    # =========================================================
    # TYTUŁ OKNA
    # =========================================================

    def get_window_title(self, hwnd):

        user32 = ctypes.windll.user32

        length = user32.GetWindowTextLengthW(hwnd)

        if length <= 0:

            return ""

        buffer = ctypes.create_unicode_buffer(length + 1)

        user32.GetWindowTextW(hwnd, buffer, length + 1)

        return buffer.value

    # =========================================================
    # OSADZANIE OKNA
    # =========================================================

    def embed_window(self, hwnd):

        try:

            user32 = ctypes.windll.user32

            host_hwnd = int(self.embedded_host.winId())

            if not host_hwnd:

                return False

            GWL_STYLE = -16

            WS_CHILD = 0x40000000
            WS_POPUP = 0x80000000
            WS_CAPTION = 0x00C00000
            WS_THICKFRAME = 0x00040000
            WS_MINIMIZE = 0x20000000
            WS_MAXIMIZE = 0x01000000
            WS_SYSMENU = 0x00080000
            WS_MAXIMIZEBOX = 0x00010000
            WS_MINIMIZEBOX = 0x00020000

            style = user32.GetWindowLongW(hwnd, GWL_STYLE)

            style &= ~WS_POPUP
            style &= ~WS_CAPTION
            style &= ~WS_THICKFRAME
            style &= ~WS_MINIMIZE
            style &= ~WS_MAXIMIZE
            style &= ~WS_SYSMENU
            style &= ~WS_MAXIMIZEBOX
            style &= ~WS_MINIMIZEBOX

            style |= WS_CHILD

            user32.SetWindowLongW(hwnd, GWL_STYLE, style)

            result = user32.SetParent(hwnd, host_hwnd)

            if not result and result != 0:

                return False

            self.embedded_hwnd = hwnd

            self.scroll_area.hide()

            self.embedded_host.show()

            self.back_button.show()

            self.refresh_button.hide()

            self.search_edit.hide()

            self.resize_embedded_window()

            if not self.embedded_resize_timer:

                self.embedded_resize_timer = QTimer(self)

                self.embedded_resize_timer.timeout.connect(self.resize_embedded_window)

            self.embedded_resize_timer.start(100)

            user32.ShowWindow(hwnd, 5)

            user32.SetForegroundWindow(hwnd)

            return True

        except Exception as error:

            self.status_label.setText(f"BŁĄD OSADZANIA: {error}")

            return False

    # =========================================================
    # DOPASOWANIE ROZMIARU
    # =========================================================

    def resize_embedded_window(self):

        if not self.embedded_hwnd:

            return

        try:

            user32 = ctypes.windll.user32

            if not user32.IsWindow(self.embedded_hwnd):

                self.embedded_hwnd = None

                return

            width = self.embedded_host.width()

            height = self.embedded_host.height()

            user32.MoveWindow(self.embedded_hwnd, 0, 0, width, height, True)

        except Exception:

            pass

    # =========================================================
    # ZAMKNIĘCIE / POWRÓT
    # =========================================================

    def close_embedded_application(self):

        if self.embedded_resize_timer:

            self.embedded_resize_timer.stop()

        hwnd = self.embedded_hwnd

        if hwnd:

            try:

                user32 = ctypes.windll.user32

                user32.SetParent(hwnd, 0)

                GWL_STYLE = -16

                WS_OVERLAPPEDWINDOW = 0x00CF0000

                user32.SetWindowLongW(hwnd, GWL_STYLE, WS_OVERLAPPEDWINDOW)

                user32.ShowWindow(hwnd, 5)

            except Exception:

                pass

        self.embedded_hwnd = None

        self.embedded_application = None

        self.embedded_host.hide()

        self.scroll_area.show()

        self.back_button.hide()

        self.refresh_button.show()

        self.search_edit.show()

        self.status_label.setText("LISTA APLIKACJI")

    # =========================================================
    # ZMIANA ROZMIARU PANELU
    # =========================================================

    def resizeEvent(self, event):

        super().resizeEvent(event)

        QTimer.singleShot(0, self.resize_embedded_window)

    # =========================================================
    # WYSZUKIWANIE
    # =========================================================

    def filter_applications(self, text):

        search = text.strip().casefold()

        visible_count = 0

        for index in range(self.content_layout.count()):

            item = self.content_layout.itemAt(index)

            widget = item.widget()

            if widget is None:

                continue

            name = getattr(widget, "_application_name", "")

            visible = not search or search in name.casefold()

            widget.setVisible(visible)

            if visible:

                visible_count += 1

        self.status_label.setText(
            f"{visible_count} / " f"{len(self.applications)} APLIKACJI"
        )

    # =========================================================
    # CZYSZCZENIE
    # =========================================================

    def clear_content(self):

        while self.content_layout.count():

            item = self.content_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()
