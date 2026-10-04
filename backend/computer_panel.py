import os
import platform
import shutil
import socket
import subprocess
import psutil

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel
)


class ComputerPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("computerPanel")

        self.setStyleSheet("""
            QFrame#computerPanel {
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
        """)

        self.previous_net = psutil.net_io_counters()
        self.last_disk_update = 0

        self.create_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

        self.update_data()

    def create_ui(self):
        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            35,
            30,
            35,
            30
        )

        layout.setSpacing(18)

        # =========================
        # HEADER
        # =========================

        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel("KOMPUTER")

        title.setFont(
            QFont(
                "Segoe UI",
                24,
                QFont.Weight.Light
            )
        )

        title.setStyleSheet("""
            color: rgba(190, 240, 255, 245);
            letter-spacing: 5px;
        """)

        subtitle = QLabel(
            "REAL-TIME SYSTEM MONITOR"
        )

        subtitle.setStyleSheet("""
            color: rgba(70, 180, 225, 140);
            font-size: 9px;
            letter-spacing: 3px;
        """)

        header.addWidget(title)
        header.addWidget(subtitle)

        layout.addLayout(header)

        # =========================
        # MAIN CARDS
        # =========================

        grid = QGridLayout()
        grid.setSpacing(12)

        self.cpu_card = self.create_metric_card(
            "CPU",
            "PROCESSOR"
        )

        self.ram_card = self.create_metric_card(
            "RAM",
            "MEMORY"
        )

        self.gpu_card = self.create_metric_card(
            "GPU",
            "GRAPHICS"
        )

        self.disk_card = self.create_metric_card(
            "DYSK C:",
            "STORAGE"
        )

        grid.addWidget(
            self.cpu_card,
            0,
            0
        )

        grid.addWidget(
            self.ram_card,
            0,
            1
        )

        grid.addWidget(
            self.gpu_card,
            1,
            0
        )

        grid.addWidget(
            self.disk_card,
            1,
            1
        )

        layout.addLayout(grid)

        # =========================
        # NETWORK
        # =========================

        network_card = QFrame()
        network_card.setProperty(
            "class",
            "card"
        )

        network_layout = QVBoxLayout(
            network_card
        )

        network_layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        network_layout.setSpacing(8)

        network_title = QLabel(
            "NETWORK"
        )

        network_title.setStyleSheet("""
            color: rgba(80, 190, 230, 170);
            font-size: 9px;
            letter-spacing: 2px;
        """)

        self.network_status = QLabel(
            "ANALYZING..."
        )

        self.network_status.setStyleSheet("""
            color: rgba(200, 240, 255, 225);
            font-size: 16px;
            letter-spacing: 1px;
        """)

        self.network_details = QLabel(
            "↓ 0 KB/s     ↑ 0 KB/s"
        )

        self.network_details.setStyleSheet("""
            color: rgba(110, 180, 210, 170);
            font-size: 10px;
        """)

        network_layout.addWidget(
            network_title
        )

        network_layout.addWidget(
            self.network_status
        )

        network_layout.addWidget(
            self.network_details
        )

        layout.addWidget(
            network_card
        )

        # =========================
        # SYSTEM INFORMATION
        # =========================

        info_card = QFrame()
        info_card.setProperty(
            "class",
            "card"
        )

        info_layout = QVBoxLayout(
            info_card
        )

        info_layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        info_layout.setSpacing(6)

        info_title = QLabel(
            "SYSTEM INFORMATION"
        )

        info_title.setStyleSheet("""
            color: rgba(80, 190, 230, 170);
            font-size: 9px;
            letter-spacing: 2px;
        """)

        self.hostname_label = QLabel()
        self.windows_label = QLabel()
        self.python_label = QLabel()

        for label in [
            self.hostname_label,
            self.windows_label,
            self.python_label
        ]:
            label.setStyleSheet("""
                color: rgba(150, 200, 225, 180);
                font-size: 10px;
            """)

        info_layout.addWidget(
            info_title
        )

        info_layout.addWidget(
            self.hostname_label
        )

        info_layout.addWidget(
            self.windows_label
        )

        info_layout.addWidget(
            self.python_label
        )

        layout.addWidget(
            info_card
        )

        layout.addStretch()

    def create_metric_card(
        self,
        name,
        subtitle
    ):
        card = QFrame()

        card.setProperty(
            "class",
            "card"
        )

        card.setMinimumHeight(
            135
        )

        layout = QVBoxLayout(card)

        layout.setContentsMargins(
            18,
            15,
            18,
            15
        )

        layout.setSpacing(4)

        title = QLabel(
            name
        )

        title.setStyleSheet("""
            color: rgba(80, 190, 230, 170);
            font-size: 9px;
            letter-spacing: 2px;
        """)

        value = QLabel(
            "--"
        )

        value.setStyleSheet("""
            color: rgba(200, 240, 255, 235);
            font-size: 25px;
            letter-spacing: 1px;
        """)

        details = QLabel(
            subtitle
        )

        details.setStyleSheet("""
            color: rgba(100, 160, 185, 140);
            font-size: 8px;
            letter-spacing: 1px;
        """)

        bar_background = QFrame()

        bar_background.setFixedHeight(
            5
        )

        bar_background.setStyleSheet("""
            background-color: rgba(40, 100, 125, 50);
            border-radius: 2px;
        """)

        bar = QFrame(
            bar_background
        )

        bar.setGeometry(
            0,
            0,
            1,
            5
        )

        bar.setStyleSheet("""
            background-color: rgba(60, 210, 255, 190);
            border-radius: 2px;
        """)

        layout.addWidget(title)
        layout.addWidget(value)
        layout.addWidget(details)
        layout.addStretch()
        layout.addWidget(bar_background)

        card.value_label = value
        card.details_label = details
        card.bar_background = bar_background
        card.bar = bar

        return card

    def update_card(
        self,
        card,
        value,
        details,
        percentage
    ):
        card.value_label.setText(
            value
        )

        card.details_label.setText(
            details
        )

        percentage = max(
            0,
            min(
                100,
                percentage
            )
        )

        width = int(
            card.bar_background.width() *
            percentage /
            100
        )

        card.bar.setGeometry(
            0,
            0,
            width,
            card.bar_background.height()
        )

    def update_data(self):
        # =========================
        # CPU
        # =========================

        cpu = psutil.cpu_percent(
            interval=None
        )

        cpu_name = platform.processor()

        if not cpu_name:
            cpu_name = "PROCESSOR"

        self.update_card(
            self.cpu_card,
            f"{cpu:.0f}%",
            cpu_name[:42],
            cpu
        )

        # =========================
        # RAM
        # =========================

        memory = psutil.virtual_memory()

        ram_used = memory.used / (
            1024 ** 3
        )

        ram_total = memory.total / (
            1024 ** 3
        )

        self.update_card(
            self.ram_card,
            f"{memory.percent:.0f}%",
            f"{ram_used:.1f} / {ram_total:.1f} GB",
            memory.percent
        )

        # =========================
        # GPU
        # =========================

        gpu_usage, gpu_name = self.get_gpu_info()

        if gpu_usage is None:
            self.update_card(
                self.gpu_card,
                "N/A",
                gpu_name,
                0
            )
        else:
            self.update_card(
                self.gpu_card,
                f"{gpu_usage:.0f}%",
                gpu_name,
                gpu_usage
            )

        # =========================
        # DISK
        # =========================

        try:
            disk = shutil.disk_usage(
                os.environ.get(
                    "SystemDrive",
                    "C:"
                ) + "\\"
            )

            disk_used = (
                disk.used /
                disk.total *
                100
            )

            used_gb = disk.used / (
                1024 ** 3
            )

            total_gb = disk.total / (
                1024 ** 3
            )

            self.update_card(
                self.disk_card,
                f"{disk_used:.0f}%",
                f"{used_gb:.0f} / {total_gb:.0f} GB",
                disk_used
            )

        except Exception:
            self.update_card(
                self.disk_card,
                "N/A",
                "STORAGE",
                0
            )

        # =========================
        # NETWORK
        # =========================

        current_net = psutil.net_io_counters()

        download = (
            current_net.bytes_recv -
            self.previous_net.bytes_recv
        )

        upload = (
            current_net.bytes_sent -
            self.previous_net.bytes_sent
        )

        self.previous_net = current_net

        download_kb = download / 1024
        upload_kb = upload / 1024

        self.network_status.setText(
            self.get_network_status()
        )

        self.network_details.setText(
            f"↓ {download_kb:.1f} KB/s     "
            f"↑ {upload_kb:.1f} KB/s"
        )

        # =========================
        # SYSTEM INFO
        # =========================

        self.hostname_label.setText(
            f"HOST: {socket.gethostname()}"
        )

        self.windows_label.setText(
            f"SYSTEM: {platform.system()} "
            f"{platform.release()}"
        )

        self.python_label.setText(
            f"PYTHON: {platform.python_version()}"
        )

    def get_network_status(self):
        try:
            connections = psutil.net_if_stats()

            active = []

            for name, stats in connections.items():
                if stats.isup:
                    active.append(name)

            if active:
                return (
                    "ONLINE  //  " +
                    active[0]
                )

            return "OFFLINE"

        except Exception:
            return "UNKNOWN"

    def get_gpu_info(self):
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,name",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return None, "NVIDIA GPU NOT FOUND"

            line = result.stdout.strip().splitlines()[0]

            usage, name = line.split(
                ",",
                1
            )

            return (
                float(usage.strip()),
                name.strip()
            )

        except Exception:
            return None, "GPU DATA UNAVAILABLE"
