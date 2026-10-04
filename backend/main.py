import math
import sys
import ctypes
import os
import time
import subprocess
import importlib
import traceback

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QFont, QPainter, QColor, QSurfaceFormat
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
)

from ai_core import AICore
from left_panel import JarvisLeftPanel
from settings_panel import SettingsPanel
from computer_panel import ComputerPanel
from system_panel import SystemPanel
from files_panel import FilesPanel
from apps_panel import AppsPanel
from gmail_panel import GmailPanel


class HotReloadManager:
    def __init__(self, jarvis):
        self.jarvis = jarvis

        self.modules = {
            "apps_panel": "apps_panel",
            "files_panel": "files_panel",
            "system_panel": "system_panel",
            "computer_panel": "computer_panel",
            "settings_panel": "settings_panel",
            "gmail_panel": "gmail_panel",
            "ai_core": "ai_core",
            "left_panel": "left_panel",
        }

        self.files = {}

        self.scan_files()

    def scan_files(self):
        for module_name, file_name in self.modules.items():

            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), file_name + ".py"
            )

            if os.path.exists(path):
                try:
                    self.files[module_name] = os.path.getmtime(path)
                except OSError:
                    pass

    def check(self):

        for module_name, file_name in self.modules.items():

            path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), file_name + ".py"
            )

            if not os.path.exists(path):
                continue

            try:
                current_time = os.path.getmtime(path)
            except OSError:
                continue

            old_time = self.files.get(module_name)

            if old_time is None:
                self.files[module_name] = current_time
                continue

            if current_time != old_time:

                self.files[module_name] = current_time

                self.reload_module(module_name)

    def reload_module(self, module_name):

        try:

            print(f"[HOT RELOAD] {module_name}.py")

            module = importlib.import_module(module_name)

            importlib.reload(module)

            self.jarvis.replace_panel(module_name, module)

            print(f"[HOT RELOAD] OK: {module_name}")

        except Exception:

            print(f"[HOT RELOAD] ERROR: {module_name}")

            traceback.print_exc()


class JarvisDisplay(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JARVIS")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self.current_tab = "dashboard"
        self.grid_offset = 0.0
        self.scan_position = 0.0

        # =========================
        # GŁÓWNY UKŁAD
        # =========================

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # =========================
        # PANEL LEWY
        # =========================

        self.left_panel = JarvisLeftPanel(self)
        self.left_panel.tab_changed.connect(self.change_tab)

        self.main_layout.addWidget(self.left_panel)

        # =========================
        # OBSZAR GŁÓWNY
        # =========================

        self.content_area = QFrame(self)

        self.content_area.setStyleSheet("""
            QFrame {
                background-color: rgb(2, 7, 13);
            }
        """)

        self.main_layout.addWidget(self.content_area, 1)

        # =========================
        # PRZYCISK WYJŚCIA
        # =========================

        self.exit_button = QPushButton("WYJDŹ", self.content_area)

        self.exit_button.setFixedSize(90, 34)

        self.exit_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(10, 20, 30, 210);
                border: 1px solid rgba(80, 190, 240, 100);
                color: rgba(130, 220, 255, 210);
                font-size: 10px;
                letter-spacing: 1px;
            }

            QPushButton:hover {
                background-color: rgba(30, 150, 210, 80);
                border: 1px solid rgba(100, 220, 255, 220);
                color: rgba(220, 250, 255, 255);
            }

            QPushButton:pressed {
                background-color: rgba(50, 190, 240, 120);
            }
        """)

        self.exit_button.clicked.connect(QApplication.quit)

        # =========================
        # AI CORE
        # =========================

        self.ai_core = AICore(self.content_area)

        self.ai_core.setGeometry(0, 0, 1000, 800)

        self.ai_core.lower()

        # =========================
        # PANEL USTAWIEŃ
        # =========================

        self.settings_panel = SettingsPanel(self.content_area)
        self.settings_panel.hide()

        self.computer_panel = ComputerPanel(self.content_area)
        self.computer_panel.hide()

        self.system_panel = SystemPanel(self.content_area)
        self.system_panel.hide()

        self.files_panel = FilesPanel(self.content_area)
        self.files_panel.hide()

        self.apps_panel = AppsPanel(self.content_area)
        self.apps_panel.hide()

        self.gmail_panel = GmailPanel(self.content_area)
        self.gmail_panel.hide()

        # =========================
        # NAPIS ŚRODKOWY
        # =========================

        self.section_title = QLabel("JARVIS", self.content_area)

        self.section_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Light))

        self.section_title.setStyleSheet("""
            color: rgba(120, 210, 245, 170);
            letter-spacing: 5px;
            background: transparent;
        """)

        # =========================
        # STATUS LEWY DÓŁ
        # =========================

        self.status_left = QLabel("SYSTEM ONLINE", self.content_area)

        self.status_left.setFont(QFont("Consolas", 9))

        self.status_left.setStyleSheet("""
            color: rgba(80, 210, 180, 190);
            background: transparent;
        """)

        # =========================
        # STATUS PRAWY DÓŁ
        # =========================

        self.status_right = QLabel("JARVIS OS    //    V0.4", self.content_area)

        self.status_right.setFont(QFont("Consolas", 9))

        self.status_right.setStyleSheet("""
            color: rgba(90, 180, 220, 160);
            background: transparent;
        """)

        # =========================
        # INFORMACJA O ZAKŁADCE
        # =========================

        self.tab_info = QLabel("CORE", self.content_area)

        self.tab_info.setFont(QFont("Consolas", 8))

        self.tab_info.setStyleSheet("""
            color: rgba(100, 200, 240, 120);
            background: transparent;
        """)

        # =========================
        # EXIT BUTTON - NA WIERZCHU
        # =========================

        self.exit_button.raise_()

        # =========================
        # TIMER
        # =========================

        self.timer = QTimer(self)

        self.timer.timeout.connect(self.animate_background)

        self.timer.start(16)

        # =========================
        # HOT RELOAD
        # =========================

        self.hot_reload = HotReloadManager(self)

        self.hot_reload_timer = QTimer(self)

        self.hot_reload_timer.timeout.connect(self.hot_reload.check)

        self.hot_reload_timer.start(500)

        # =========================
        # FULLSCREEN
        # =========================

        self.showFullScreen()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                try:
                    import ctypes

                    user32 = ctypes.windll.user32

                    hwnd = int(self.winId())

                    HWND_TOPMOST = -1

                    SWP_NOMOVE = 0x0002
                    SWP_NOSIZE = 0x0001
                    SWP_SHOWWINDOW = 0x0040

                    user32.SetWindowPos(
                        hwnd,
                        HWND_TOPMOST,
                        0,
                        0,
                        0,
                        0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
                    )

                except Exception:
                    pass

        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if not hasattr(self, "content_area"):
            return

        width = self.content_area.width()
        height = self.content_area.height()

        # AI CORE
        self.ai_core.setGeometry(0, 0, width, height)

        # PRZYCISK WYJŚCIA
        if hasattr(self, "exit_button"):
            self.exit_button.move(width - self.exit_button.width() - 25, 22)

        # TYTUŁ
        if hasattr(self, "section_title"):
            self.section_title.adjustSize()
            self.section_title.move(28, 25)

        # STATUS
        if hasattr(self, "status_left"):
            self.status_left.adjustSize()
            self.status_left.move(28, height - 35)

        if hasattr(self, "status_right"):
            self.status_right.adjustSize()
            self.status_right.move(width - self.status_right.width() - 28, height - 35)

        if hasattr(self, "tab_info"):
            self.tab_info.adjustSize()
            self.tab_info.move(28, height - 55)

        if hasattr(self, "settings_panel"):
            self.settings_panel.setGeometry(0, 0, width, height)

        if hasattr(self, "computer_panel"):
            self.computer_panel.setGeometry(0, 0, width, height)

        if hasattr(self, "system_panel"):
            self.system_panel.setGeometry(0, 0, width, height)

        if hasattr(self, "files_panel"):
            self.files_panel.setGeometry(0, 0, width, height)

        if hasattr(self, "apps_panel"):
            self.apps_panel.setGeometry(0, 0, width, height)

        if hasattr(self, "gmail_panel"):
            self.gmail_panel.setGeometry(0, 0, width, height)

    def animate_background(self):
        self.grid_offset += 0.35

        if self.grid_offset > 40:
            self.grid_offset = 0

        self.scan_position += 0.004

        if self.scan_position > 1.0:
            self.scan_position = 0.0

        self.content_area.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # =========================
        # TŁO
        # =========================

        painter.fillRect(self.rect(), QColor(2, 7, 13))

        # =========================
        # OBSZAR CONTENT
        # =========================

        if hasattr(self, "left_panel"):

            x_start = self.left_panel.width()

            painter.fillRect(
                x_start, 0, self.width() - x_start, self.height(), QColor(2, 7, 13)
            )

            # =========================
            # GRID
            # =========================

            painter.setPen(QColor(20, 100, 140, 25))

            grid_size = 40

            offset = int(self.grid_offset)

            x = x_start - offset

            while x < self.width():

                painter.drawLine(x, 0, x, self.height())

                x += grid_size

            y = -offset

            while y < self.height():

                painter.drawLine(x_start, y, self.width(), y)

                y += grid_size

            # =========================
            # CENTRALNY OKRĄG HUD
            # =========================

            center_x = x_start + (self.width() - x_start) // 2

            center_y = self.height() // 2

            for radius, alpha in [(320, 15), (280, 20), (240, 25)]:

                painter.setPen(QColor(40, 180, 240, alpha))

                painter.drawEllipse(
                    center_x - radius, center_y - radius, radius * 2, radius * 2
                )

            # =========================
            # LINIE HUD
            # =========================

            painter.setPen(QColor(50, 180, 230, 35))

            frame_left = center_x - 390
            frame_right = center_x + 390
            frame_top = center_y - 300
            frame_bottom = center_y + 300

            painter.drawLine(frame_left, frame_top, frame_left + 45, frame_top)

            painter.drawLine(frame_right - 45, frame_top, frame_right, frame_top)

            painter.drawLine(frame_left, frame_bottom, frame_left + 45, frame_bottom)

            painter.drawLine(frame_right - 45, frame_bottom, frame_right, frame_bottom)

            # =========================
            # SKANUJĄCA LINIA
            # =========================

            scan_y = int(self.scan_position * self.height())

            painter.setPen(QColor(60, 200, 255, 18))

            painter.drawLine(x_start, scan_y, self.width(), scan_y)

        painter.end()

    def change_tab(self, identifier):
        names = {
            "dashboard": "CORE",
            "mail": "POCZTA",
            "settings": "USTAWIENIA",
            "computer": "KOMPUTER",
            "files": "PLIKI",
            "apps": "APLIKACJE",
            "system": "SYSTEM",
        }

        self.current_tab = identifier

        self.tab_info.setText(names.get(identifier, "CORE"))

        self.tab_info.adjustSize()

        # =========================
        # UKRYJ WSZYSTKIE MODUŁY
        # =========================

        self.ai_core.hide()
        self.settings_panel.hide()
        self.computer_panel.hide()
        self.system_panel.hide()
        self.files_panel.hide()
        self.apps_panel.hide()
        self.gmail_panel.hide()

        # =========================
        # WYBRANY MODUŁ
        # =========================

        if identifier == "settings":

            self.settings_panel.show()
            self.settings_panel.raise_()

        elif identifier == "computer":

            self.computer_panel.show()
            self.computer_panel.raise_()

        elif identifier == "system":

            self.system_panel.show()
            self.system_panel.raise_()

        elif identifier == "dashboard":

            self.ai_core.show()
            self.ai_core.raise_()

        elif identifier == "files":

            self.files_panel.show()
            self.files_panel.raise_()

        elif identifier == "apps":

            self.apps_panel.show()
            self.apps_panel.raise_()

        elif identifier == "mail":

            self.gmail_panel.show()
            self.gmail_panel.raise_()

        else:

            self.ai_core.show()
            self.ai_core.raise_()

        self.exit_button.raise_()

    def release_for_external_app(self):
        """
        Tymczasowo oddaje pierwszeństwo aplikacji uruchamianej
        z JARVIS-a.
        """

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)

        self.show()

        self.lower()

        self.activateWindow()

    def restart_application(self):
        """
        Restartuje cały JARVIS po wykryciu zmiany
        w plikach Python.
        """

        print()
        print("=" * 60)
        print("JARVIS HOT RELOAD")
        print("Wykryto zmianę w kodzie.")
        print("Restartowanie...")
        print("=" * 60)

        QApplication.quit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()
            return

        super().keyPressEvent(event)

    def replace_panel(self, module_name, module):

        current_tab = self.current_tab

        old_panel = None
        new_panel = None

        # ==========================================
        # APPS
        # ==========================================

        if module_name == "apps_panel":

            old_panel = self.apps_panel

            new_panel = module.AppsPanel(self.content_area)

            self.apps_panel = new_panel

        # ==========================================
        # FILES
        # ==========================================

        elif module_name == "files_panel":

            old_panel = self.files_panel

            new_panel = module.FilesPanel(self.content_area)

            self.files_panel = new_panel

        # ==========================================
        # SYSTEM
        # ==========================================

        elif module_name == "system_panel":

            old_panel = self.system_panel

            new_panel = module.SystemPanel(self.content_area)

            self.system_panel = new_panel

        # ==========================================
        # COMPUTER
        # ==========================================

        elif module_name == "computer_panel":

            old_panel = self.computer_panel

            new_panel = module.ComputerPanel(self.content_area)

            self.computer_panel = new_panel

        # ==========================================
        # SETTINGS
        # ==========================================

        elif module_name == "settings_panel":

            old_panel = self.settings_panel

            new_panel = module.SettingsPanel(self.content_area)

            self.settings_panel = new_panel

        # ==========================================
        # GMAIL
        # ==========================================

        elif module_name == "gmail_panel":

            old_panel = self.gmail_panel

            new_panel = module.GmailPanel(self.content_area)

            self.gmail_panel = new_panel

        # ==========================================
        # AI CORE
        # ==========================================

        elif module_name == "ai_core":

            old_panel = self.ai_core

            new_panel = module.AICore(self.content_area)

            self.ai_core = new_panel

        # ===========================================
        # LEFT PANEL
        # ===========================================

        elif module_name == "left_panel":
            old_panel = self.left_panel

            new_panel = module.JarvisLeftPanel(self)
            new_panel.tab_changed.connect(self.change_tab)

            index = self.main_layout.indexOf(old_panel)

            self.main_layout.removeWidget(old_panel)

            old_panel.hide()
            old_panel.setParent(None)
            old_panel.deleteLater()

            self.main_layout.insertWidget(index, new_panel)

            self.left_panel = new_panel

            new_panel.show()
            new_panel.raise_()

        # ==========================================
        # BRAK MODUŁU
        # ==========================================

        else:
            return

        # ==========================================
        # ROZMIAR
        # ==========================================

        if new_panel is not None:

            new_panel.setGeometry(
                0, 0, self.content_area.width(), self.content_area.height()
            )

            # new_panel.hide()

        # ==========================================
        # USUNIĘCIE STAREGO
        # ==========================================

        if old_panel is not None:

            old_panel.hide()

            old_panel.deleteLater()

        # ==========================================
        # ODTWORZENIE AKTYWNEGO PANELU
        # ==========================================

        if current_tab == "apps" and module_name == "apps_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "files" and module_name == "files_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "system" and module_name == "system_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "computer" and module_name == "computer_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "settings" and module_name == "settings_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "mail" and module_name == "gmail_panel":
            new_panel.show()
            new_panel.raise_()

        elif current_tab == "dashboard" and module_name == "ai_core":
            new_panel.show()
            new_panel.raise_()

        # ==========================================
        # EXIT BUTTON
        # ==========================================

        self.exit_button.raise_()

        self.status_left.setText(f"HOT RELOAD: {module_name}")
        self.status_left.adjustSize()
        self.status_left.update()

        print(f"[HOT RELOAD] Panel replaced: {module_name}")


def main():
    # =========================
    # OPENGL
    # =========================

    fmt = QSurfaceFormat()

    fmt.setRenderableType(QSurfaceFormat.RenderableType.OpenGL)

    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)

    fmt.setVersion(2, 1)

    fmt.setAlphaBufferSize(8)

    QSurfaceFormat.setDefaultFormat(fmt)

    # =========================
    # APPLICATION
    # =========================

    app = QApplication(sys.argv)

    app.setApplicationName("JARVIS")

    app.setStyle("Fusion")

    window = JarvisDisplay()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
