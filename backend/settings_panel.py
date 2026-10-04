from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
)


class SettingsPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("settingsPanel")

        self.setStyleSheet("""
            QFrame#settingsPanel {
                background-color: rgba(2, 7, 13, 245);
            }

            QLabel {
                color: rgba(180, 225, 245, 220);
            }

            QLabel.sectionTitle {
                color: rgba(100, 210, 255, 230);
                font-size: 11px;
                letter-spacing: 2px;
            }

            QLabel.description {
                color: rgba(120, 170, 195, 150);
                font-size: 10px;
            }

            QFrame.card {
                background-color: rgba(5, 18, 30, 180);
                border: 1px solid rgba(50, 180, 235, 65);
                border-radius: 6px;
            }

            QPushButton {
                background-color: rgba(20, 90, 125, 45);
                border: 1px solid rgba(60, 190, 240, 80);
                border-radius: 4px;
                color: rgba(180, 230, 250, 230);
                padding: 10px 16px;
                font-size: 10px;
            }

            QPushButton:hover {
                background-color: rgba(30, 150, 210, 65);
                border: 1px solid rgba(80, 220, 255, 150);
                color: rgba(220, 250, 255, 255);
            }

            QPushButton:pressed {
                background-color: rgba(40, 180, 240, 90);
            }
        """)

        self.create_ui()

    def create_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(35, 30, 35, 30)

        main_layout.setSpacing(18)

        # =========================
        # NAGŁÓWEK
        # =========================

        header = self.create_header()

        main_layout.addWidget(header)

        # =========================
        # SYSTEM
        # =========================

        main_layout.addWidget(
            self.create_section(
                "SYSTEM", "Podstawowe informacje i konfiguracja systemu JARVIS"
            )
        )

        system_grid = QGridLayout()

        system_grid.setSpacing(10)

        system_grid.addWidget(
            self.create_card("JARVIS CORE", "STATUS", "ONLINE", True), 0, 0
        )

        system_grid.addWidget(
            self.create_card("INTERFACE", "VERSION", "0.4", False), 0, 1
        )

        system_grid.addWidget(
            self.create_card("PLATFORM", "SYSTEM", "WINDOWS 11", False), 0, 2
        )

        main_layout.addLayout(system_grid)

        # =========================
        # INTERFEJS
        # =========================

        main_layout.addWidget(
            self.create_section("INTERFEJS", "Wygląd i zachowanie interfejsu JARVIS")
        )

        main_layout.addWidget(self.create_interface_card())

        # =========================
        # WINDOWS
        # =========================

        main_layout.addWidget(
            self.create_section("WINDOWS", "Integracja JARVIS z systemem Windows")
        )

        main_layout.addWidget(self.create_windows_card())

        main_layout.addStretch()

    def create_header(self):
        frame = QFrame()

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(4)

        title = QLabel("USTAWIENIA")

        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Light))

        title.setStyleSheet("""
            color: rgba(190, 240, 255, 245);
            letter-spacing: 5px;
        """)

        subtitle = QLabel("JARVIS SYSTEM CONFIGURATION")

        subtitle.setStyleSheet("""
            color: rgba(70, 180, 225, 140);
            font-size: 9px;
            letter-spacing: 3px;
        """)

        layout.addWidget(title)

        layout.addWidget(subtitle)

        return frame

    def create_section(self, title, description):
        frame = QFrame()

        layout = QVBoxLayout(frame)

        layout.setContentsMargins(0, 5, 0, 0)

        layout.setSpacing(3)

        title_label = QLabel(title)

        title_label.setProperty("class", "sectionTitle")

        description_label = QLabel(description)

        description_label.setProperty("class", "description")

        layout.addWidget(title_label)

        layout.addWidget(description_label)

        return frame

    def create_card(self, name, label, value, online=False):
        card = QFrame()

        card.setProperty("class", "card")

        card.setMinimumHeight(85)

        layout = QVBoxLayout(card)

        layout.setContentsMargins(15, 12, 15, 12)

        layout.setSpacing(3)

        name_label = QLabel(name)

        name_label.setStyleSheet("""
            color: rgba(80, 190, 230, 170);
            background-color: rgba(5, 18, 30, 180);
            font-size: 9px;
            letter-spacing: 2px;
        """)

        value_label = QLabel(value)

        if online:
            value_label.setStyleSheet("""
                color: rgba(80, 235, 175, 230);
                background-color: rgba(5, 18, 30, 180);
                font-size: 17px;
                letter-spacing: 2px;
            """)
        else:
            value_label.setStyleSheet("""
                color: rgba(200, 240, 255, 225);
                background-color: rgba(5, 18, 30, 180);
                font-size: 17px;
                letter-spacing: 1px;
            """)

        info_label = QLabel(label)

        info_label.setStyleSheet("""
            color: rgba(100, 150, 175, 130);
            background-color: rgba(5, 18, 30, 180);
            font-size: 8px;
            letter-spacing: 1px;
        """)

        layout.addWidget(name_label)

        layout.addWidget(value_label)

        layout.addWidget(info_label)

        return card

    def create_interface_card(self):
        card = QFrame()

        card.setProperty("class", "card")

        layout = QVBoxLayout(card)

        layout.setContentsMargins(18, 15, 18, 15)

        layout.setSpacing(12)

        title = QLabel("MOTYW INTERFEJSU")

        title.setStyleSheet("""
            color: rgba(170, 225, 245, 220);
            background-color: rgba(5, 18, 30, 180);
            font-size: 11px;
            letter-spacing: 2px;
        """)

        layout.addWidget(title)

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(8)

        themes = [("JARVIS", True), ("DARK", False), ("LIGHT", False)]

        for name, active in themes:

            button = QPushButton(name)

            button.setMinimumHeight(38)

            if active:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(30, 160, 215, 75);
                        border: 1px solid rgba(80, 220, 255, 180);
                        border-radius: 4px;
                        color: rgba(220, 250, 255, 255);
                        font-size: 10px;
                        letter-spacing: 1px;
                    }
                """)

            buttons_layout.addWidget(button)

        layout.addLayout(buttons_layout)

        return card

    def create_windows_card(self):
        card = QFrame()

        card.setProperty("class", "card")

        layout = QVBoxLayout(card)

        layout.setContentsMargins(18, 15, 18, 15)

        layout.setSpacing(10)

        title = QLabel("CENTRUM SYSTEMU WINDOWS")

        title.setStyleSheet("""
            color: rgba(170, 225, 245, 220);
            background-color: rgba(5, 18, 30, 180);
            font-size: 11px;
            letter-spacing: 2px;
        """)

        description = QLabel(
            "JARVIS może w przyszłości przejąć kontrolę nad "
            "wybranymi funkcjami systemu Windows."
        )

        description.setWordWrap(True)

        description.setStyleSheet("""
            color: rgba(120, 170, 195, 150);
            background-color: rgba(5, 18, 30, 180);
            font-size: 10px;
        """)

        layout.addWidget(title)

        layout.addWidget(description)

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(8)

        categories = ["EKRAN", "DŹWIĘK", "SIEĆ", "BLUETOOTH"]

        for category in categories:

            button = QPushButton(category)

            button.setMinimumHeight(38)

            buttons_layout.addWidget(button)

        layout.addLayout(buttons_layout)

        return card
