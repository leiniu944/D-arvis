from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
)


class JarvisLeftPanel(QFrame):
    tab_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedWidth(250)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(3, 10, 18, 225);
                border-right: 1px solid rgba(50, 190, 255, 90);
            }

            QLabel {
                color: rgba(120, 220, 255, 210);
                background-color: transparent
            }

            QPushButton {
                background-color: transparent;
                border: none;
                border-left: 2px solid transparent;
                color: rgba(150, 205, 225, 190);
                text-align: left;
                padding: 12px 12px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: rgba(30, 150, 220, 25);
                border-left: 2px solid rgba(70, 210, 255, 180);
                color: rgba(210, 245, 255, 255);
            }

            QPushButton:pressed {
                background-color: rgba(40, 180, 240, 45);
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 25, 15, 20)
        self.layout.setSpacing(4)

        self.create_header()
        self.create_separator()

        self.buttons = {}

        self.add_button("◈", "PULPIT", "dashboard")
        self.add_button("✉", "POCZTA", "mail")
        self.add_button("⚙", "USTAWIENIA", "settings")
        self.add_button("◉", "KOMPUTER", "computer")
        self.add_button("▣", "PLIKI", "files")
        self.add_button("◇", "APLIKACJE", "apps")
        self.add_button("◌", "SYSTEM", "system")

        self.create_bottom_status()

        self.set_active("dashboard")

    def create_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("JARVIS")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Light))
        title.setStyleSheet("""
            color: rgba(150, 230, 255, 245);
            letter-spacing: 4px;
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()

        self.layout.addLayout(header_layout)

        subtitle = QLabel("ARTIFICIAL INTELLIGENCE")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("""
            color: rgba(80, 180, 220, 130);
            letter-spacing: 2px;
            padding-top: 2px;
            padding-bottom: 10px;
        """)

        self.layout.addWidget(subtitle)

    def create_separator(self):
        separator = QFrame()
        separator.setFixedHeight(1)

        separator.setStyleSheet("""
            background-color: rgba(60, 190, 240, 70);
            
        """)

        self.layout.addWidget(separator)
        self.layout.addSpacing(12)

    def add_button(self, icon, text, identifier):
        button = QPushButton()

        button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icon_label = QLabel(icon)
        icon_label.setFixedWidth(22)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label.setStyleSheet("""
            color: rgba(80, 200, 255, 210);
            font-size: 16px;
            background-color: rgba(60, 190, 240, 70);
        """)

        text_label = QLabel(text)
        text_label.setStyleSheet("""
            color: rgba(155, 210, 230, 200);
            background-color: rgba(60, 190, 240, 70)
            font-size: 12px;
            letter-spacing: 1px;
            
        """)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)

        button.clicked.connect(
            lambda checked=False, value=identifier: self.on_tab_clicked(value)
        )

        self.layout.addWidget(button)

        self.buttons[identifier] = button

    def on_tab_clicked(self, identifier):
        self.set_active(identifier)
        self.tab_changed.emit(identifier)

    def set_active(self, identifier):
        for name, button in self.buttons.items():
            if name == identifier:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(60, 190, 240, 70);
                        border: none;
                        border-left: 2px solid rgba(70, 220, 255, 230);
                        color: rgba(220, 250, 255, 255);
                        text-align: left;
                        padding: 12px 12px;
                        font-size: 13px;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border: none;
                        border-left: 2px solid transparent;
                        color: rgba(150, 205, 225, 190);
                        text-align: left;
                        padding: 12px 12px;
                        font-size: 13px;
                    }

                    QPushButton:hover {
                        background-color: rgba(30, 150, 220, 25);
                        border-left: 2px solid rgba(70, 210, 255, 180);
                        color: rgba(210, 245, 255, 255);
                    }

                    QPushButton:pressed {
                        background-color: rgba(40, 180, 240, 45);
                    }
                """)

    def create_bottom_status(self):
        self.layout.addStretch()

        separator = QFrame()
        separator.setFixedHeight(1)

        separator.setStyleSheet("""
            background-color: rgba(60, 190, 240, 50);
        """)

        self.layout.addWidget(separator)
        self.layout.addSpacing(10)

        status = QLabel("●  SYSTEM ONLINE")
        status.setStyleSheet("""
            color: rgba(70, 220, 170, 190);
            font-size: 10px;
            letter-spacing: 1px;
        """)

        self.layout.addWidget(status)

        version = QLabel("JARVIS CORE  v0.4")
        version.setStyleSheet("""
            color: rgba(90, 160, 190, 120);
            font-size: 9px;
            padding-top: 3px;
        """)

        self.layout.addWidget(version)
