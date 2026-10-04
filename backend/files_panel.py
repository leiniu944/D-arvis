import os
import string
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class FilesPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("filesPanel")

        self.current_path = os.path.expanduser("~")
        self.history = []

        self.setStyleSheet("""
            QFrame#filesPanel {
                background-color: rgba(2, 7, 13, 245);
            }

            QFrame.card {
                background-color: rgba(5, 18, 30, 190);
                border: 1px solid rgba(50, 180, 235, 65);
                border-radius: 6px;
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
        self.load_directory(self.current_path)

    # ==========================================================
    # UI
    # ==========================================================

    def create_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(35, 30, 35, 25)
        main_layout.setSpacing(15)

        # ==================================================
        # HEADER
        # ==================================================

        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel("PLIKI")

        title.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Weight.Light,
            )
        )

        title.setStyleSheet("""
            color: rgba(190, 240, 255, 245);
            letter-spacing: 5px;
        """)

        subtitle = QLabel("JARVIS FILE SYSTEM")

        subtitle.setStyleSheet("""
            color: rgba(70, 180, 225, 140);
            font-size: 9px;
            letter-spacing: 3px;
        """)

        header.addWidget(title)
        header.addWidget(subtitle)

        main_layout.addLayout(header)

        # ==================================================
        # NAVIGATION
        # ==================================================

        navigation_card = QFrame()
        navigation_card.setProperty("class", "card")

        navigation_layout = QVBoxLayout(navigation_card)

        navigation_layout.setContentsMargins(12, 10, 12, 10)
        navigation_layout.setSpacing(8)

        # --------------------------------------------------
        # BUTTONS + PATH
        # --------------------------------------------------

        navigation_top = QHBoxLayout()
        navigation_top.setSpacing(6)

        self.back_button = QPushButton("←")
        self.back_button.setFixedWidth(40)
        self.back_button.clicked.connect(self.go_back)

        self.up_button = QPushButton("↑")
        self.up_button.setFixedWidth(40)
        self.up_button.clicked.connect(self.go_up)

        self.refresh_button = QPushButton("⟳")
        self.refresh_button.setFixedWidth(40)
        self.refresh_button.clicked.connect(
            lambda: self.load_directory(self.current_path)
        )

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Ścieżka...")
        self.path_edit.returnPressed.connect(self.path_entered)

        navigation_top.addWidget(self.back_button)
        navigation_top.addWidget(self.up_button)
        navigation_top.addWidget(self.refresh_button)
        navigation_top.addWidget(self.path_edit, 1)

        navigation_layout.addLayout(navigation_top)

        # --------------------------------------------------
        # SEARCH
        # --------------------------------------------------

        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("SZUKAJ W AKTUALNYM FOLDERZE...")

        self.search_edit.textChanged.connect(self.filter_items)

        search_layout.addWidget(self.search_edit)

        navigation_layout.addLayout(search_layout)

        main_layout.addWidget(navigation_card)

        # ==================================================
        # CONTENT
        # ==================================================

        self.content_container = QWidget()

        self.content_layout = QVBoxLayout(self.content_container)

        self.content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.content_layout.setSpacing(5)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.content_container)

        main_layout.addWidget(
            self.scroll_area,
            1,
        )

        # ==================================================
        # STATUS
        # ==================================================

        self.status_label = QLabel("GOTOWY")

        self.status_label.setStyleSheet("""
            color: rgba(90, 180, 215, 150);
            font-size: 9px;
            letter-spacing: 1px;
        """)

        main_layout.addWidget(self.status_label)

    # ==========================================================
    # DIRECTORY LOADING
    # ==========================================================

    def load_directory(
        self,
        path,
        add_history=True,
    ):
        path = os.path.abspath(path)

        if not os.path.isdir(path):
            self.status_label.setText("FOLDER NIE ISTNIEJE")
            return

        if add_history and path != self.current_path:
            self.history.append(self.current_path)

        self.current_path = path

        self.path_edit.setText(self.current_path)

        self.search_edit.blockSignals(True)
        self.search_edit.clear()
        self.search_edit.blockSignals(False)

        self.clear_content()

        try:
            entries = os.listdir(self.current_path)

            folders = []
            files = []

            for name in entries:
                full_path = os.path.join(
                    self.current_path,
                    name,
                )

                try:
                    if os.path.isdir(full_path):
                        folders.append(name)
                    else:
                        files.append(name)
                except OSError:
                    continue

            folders.sort(key=str.lower)

            files.sort(key=str.lower)

            for name in folders:
                self.add_file_row(
                    name,
                    os.path.join(
                        self.current_path,
                        name,
                    ),
                    True,
                )

            for name in files:
                self.add_file_row(
                    name,
                    os.path.join(
                        self.current_path,
                        name,
                    ),
                    False,
                )

            total = len(folders) + len(files)

            self.status_label.setText(
                f"{total} ELEMENTÓW  |  "
                f"{len(folders)} FOLDERÓW  |  "
                f"{len(files)} PLIKÓW"
            )

        except PermissionError:
            self.status_label.setText("BRAK DOSTĘPU DO FOLDERU")

        except Exception as error:
            self.status_label.setText(f"BŁĄD: {error}")

        self.update_navigation_buttons()

    # ==========================================================
    # FILE ROW
    # ==========================================================

    def add_file_row(
        self,
        name,
        path,
        is_directory,
    ):
        row = QFrame()

        row.setProperty(
            "class",
            "card",
        )

        row.setFixedHeight(48)

        layout = QHBoxLayout(row)

        layout.setContentsMargins(
            12,
            5,
            12,
            5,
        )

        layout.setSpacing(10)

        # --------------------------------------------------
        # ICON
        # --------------------------------------------------

        if is_directory:
            icon_text = "▣"
            icon_color = "rgba(90, 210, 255, 230)"
        else:
            icon_text = self.get_file_icon(name)
            icon_color = "rgba(170, 205, 220, 200)"

        icon = QLabel(icon_text)

        icon.setFixedWidth(25)

        icon.setAlignment(Qt.AlignCenter)

        icon.setStyleSheet(f"""
            color: {icon_color};
            font-size: 16px;
        """)

        layout.addWidget(icon)

        # --------------------------------------------------
        # NAME
        # --------------------------------------------------

        name_label = QLabel(name)

        name_label.setStyleSheet("""
            color: rgba(190, 230, 245, 225);
            font-size: 11px;
        """)

        layout.addWidget(
            name_label,
            1,
        )

        # --------------------------------------------------
        # TYPE
        # --------------------------------------------------

        type_label = QLabel()

        if is_directory:
            type_label.setText("FOLDER")
        else:
            type_label.setText(self.get_file_type(name))

        type_label.setFixedWidth(100)

        type_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        type_label.setStyleSheet("""
            color: rgba(110, 170, 195, 150);
            font-size: 9px;
        """)

        layout.addWidget(type_label)

        # --------------------------------------------------
        # SIZE
        # --------------------------------------------------

        size_label = QLabel()

        if is_directory:
            size_label.setText("—")
        else:
            size_label.setText(self.get_file_size(path))

        size_label.setFixedWidth(90)

        size_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        size_label.setStyleSheet("""
            color: rgba(150, 195, 215, 180);
            font-size: 9px;
        """)

        layout.addWidget(size_label)

        # --------------------------------------------------
        # DATE
        # --------------------------------------------------

        date_label = QLabel(self.get_modified_date(path))

        date_label.setFixedWidth(130)

        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        date_label.setStyleSheet("""
            color: rgba(110, 160, 180, 140);
            font-size: 9px;
        """)

        layout.addWidget(date_label)

        row.mouseDoubleClickEvent = (
            lambda event, p=path, directory=is_directory: self.open_item(
                p,
                directory,
            )
        )

        self.content_layout.addWidget(row)

        row._file_path = path
        row._file_name = name
        row._is_directory = is_directory

    # ==========================================================
    # OPEN ITEM
    # ==========================================================

    def open_item(
        self,
        path,
        is_directory,
    ):
        if is_directory:
            self.load_directory(path)
            return

        try:
            os.startfile(path)

            self.status_label.setText(f"OTWARTO: {os.path.basename(path)}")

        except Exception as error:
            self.status_label.setText(f"NIE MOŻNA OTWORZYĆ PLIKU: {error}")

    # ==========================================================
    # NAVIGATION
    # ==========================================================

    def go_back(self):
        if not self.history:
            return

        previous = self.history.pop()

        self.load_directory(
            previous,
            add_history=False,
        )

    def go_up(self):
        parent = os.path.dirname(self.current_path)

        if parent == self.current_path:
            return

        self.load_directory(parent)

    def path_entered(self):
        path = self.path_edit.text().strip()

        if not path:
            return

        if os.path.isdir(path):
            self.load_directory(path)
        else:
            self.status_label.setText("NIEPRAWIDŁOWA ŚCIEŻKA")

    def update_navigation_buttons(self):
        self.back_button.setEnabled(bool(self.history))

        parent = os.path.dirname(self.current_path)

        self.up_button.setEnabled(parent != self.current_path)

    # ==========================================================
    # SEARCH / FILTER
    # ==========================================================

    def filter_items(self, text):
        search = text.strip().lower()

        for index in range(self.content_layout.count()):
            item = self.content_layout.itemAt(index)

            widget = item.widget()

            if widget is None:
                continue

            name = getattr(
                widget,
                "_file_name",
                "",
            )

            visible = not search or search in name.lower()

            widget.setVisible(visible)

    # ==========================================================
    # CONTENT
    # ==========================================================

    def clear_content(self):
        while self.content_layout.count():

            item = self.content_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    # ==========================================================
    # FILE INFORMATION
    # ==========================================================

    def get_file_size(self, path):
        try:
            size = os.path.getsize(path)

            units = [
                "B",
                "KB",
                "MB",
                "GB",
                "TB",
            ]

            value = float(size)

            for unit in units:
                if value < 1024:
                    return f"{value:.1f} {unit}"

                value /= 1024

            return f"{value:.1f} PB"

        except Exception:
            return "—"

    def get_modified_date(self, path):
        try:
            timestamp = os.path.getmtime(path)

            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

        except Exception:
            return "—"

    def get_file_type(self, name):
        extension = os.path.splitext(name)[1].lower()

        if not extension:
            return "PLIK"

        mapping = {
            ".py": "PYTHON",
            ".js": "JAVASCRIPT",
            ".ts": "TYPESCRIPT",
            ".tsx": "TYPESCRIPT",
            ".jsx": "JAVASCRIPT",
            ".json": "JSON",
            ".xml": "XML",
            ".html": "HTML",
            ".css": "CSS",
            ".cpp": "C++",
            ".h": "C/C++",
            ".hpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".java": "JAVA",
            ".txt": "TEKST",
            ".md": "MARKDOWN",
            ".pdf": "PDF",
            ".doc": "WORD",
            ".docx": "WORD",
            ".xls": "EXCEL",
            ".xlsx": "EXCEL",
            ".ppt": "POWERPOINT",
            ".pptx": "POWERPOINT",
            ".jpg": "OBRAZ",
            ".jpeg": "OBRAZ",
            ".png": "OBRAZ",
            ".gif": "OBRAZ",
            ".webp": "OBRAZ",
            ".bmp": "OBRAZ",
            ".mp3": "AUDIO",
            ".wav": "AUDIO",
            ".flac": "AUDIO",
            ".mp4": "VIDEO",
            ".mkv": "VIDEO",
            ".avi": "VIDEO",
            ".zip": "ARCHIWUM",
            ".rar": "ARCHIWUM",
            ".7z": "ARCHIWUM",
            ".exe": "PROGRAM",
            ".msi": "INSTALATOR",
        }

        return mapping.get(
            extension,
            extension.upper()[1:] + " PLIK",
        )

    def get_file_icon(self, name):
        extension = os.path.splitext(name)[1].lower()

        if extension in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
        }:
            return "▧"

        if extension in {
            ".mp3",
            ".wav",
            ".flac",
        }:
            return "♫"

        if extension in {
            ".mp4",
            ".mkv",
            ".avi",
        }:
            return "▶"

        if extension in {
            ".zip",
            ".rar",
            ".7z",
        }:
            return "▤"

        if extension in {
            ".exe",
            ".msi",
        }:
            return "◆"

        if extension in {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".java",
        }:
            return "◇"

        return "▱"
