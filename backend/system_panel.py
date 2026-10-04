import os
import platform
import socket
import shutil
import subprocess
import time

from matplotlib.pyplot import bar
import psutil

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QWidget,
)


class DiagnosticWorker(QThread):
    progress = Signal(int, str)
    result = Signal(dict)

    def run(self):
        results = {}

        self.check_windows(results)
        self.check_cpu(results)
        self.check_memory(results)
        self.check_storage(results)
        ##self.check_smart(results)
        self.check_network(results)
        self.check_audio(results)
        self.check_power(results)
        self.check_uptime(results)
        self.check_windows_services(results)
        self.check_windows_update(results)
        self.check_drivers(results)
        self.check_event_log(results)
        self.check_gpu_temperature(results)
        self.check_cpu_temperature(results)

        self.progress.emit(100, "DIAGNOSTYKA KOMPLETNA")

        self.result.emit(results)

    # ==========================================================
    # WINDOWS
    # ==========================================================

    def check_windows(self, results):
        self.progress.emit(5, "SPRAWDZANIE SYSTEMU WINDOWS...")

        try:
            system = platform.system()
            release = platform.release()
            version = platform.version()

            ok = system == "Windows"

            results["windows"] = {
                "ok": ok,
                "severity": "error" if not ok else "ok",
                "title": "WINDOWS",
                "details": (f"{system} {release} | " f"BUILD {version}"),
            }

        except Exception as error:
            results["windows"] = {
                "ok": False,
                "severity": "error",
                "title": "WINDOWS",
                "details": str(error),
            }

    # ==========================================================
    # CPU
    # ==========================================================

    def check_cpu(self, results):
        self.progress.emit(10, "SPRAWDZANIE CPU...")

        try:
            load = psutil.cpu_percent(interval=1)

            physical = psutil.cpu_count(logical=False)

            logical = psutil.cpu_count(logical=True)

            processor = platform.processor() or "PROCESSOR"

            if load >= 95:
                ok = False
                severity = "warning"
            else:
                ok = True
                severity = "ok"

            results["cpu"] = {
                "ok": ok,
                "severity": severity,
                "title": "CPU",
                "details": (
                    f"{processor} | "
                    f"{physical or '?'} RDZENIE / "
                    f"{logical or '?'} WĄTKI | "
                    f"OBCIĄŻENIE {load:.0f}%"
                ),
            }

        except Exception as error:
            results["cpu"] = {
                "ok": False,
                "severity": "error",
                "title": "CPU",
                "details": str(error),
            }

    # ==========================================================
    # RAM
    # ==========================================================

    def check_memory(self, results):
        self.progress.emit(17, "SPRAWDZANIE RAM...")

        try:
            memory = psutil.virtual_memory()

            total = memory.total / (1024**3)
            used = memory.used / (1024**3)
            available = memory.available / (1024**3)
            usage = memory.percent

            if usage >= 95:
                ok = False
                severity = "error"

            elif usage >= 90:
                ok = False
                severity = "warning"

            else:
                ok = True
                severity = "ok"

            results["memory"] = {
                "ok": ok,
                "severity": severity,
                "title": "PAMIĘĆ",
                "details": (
                    f"{total:.1f} GB CAŁKOWICIE | "
                    f"{used:.1f} GB WYKORZYSTANE | "
                    f"{available:.1f} GB DOSTĘPNE | "
                    f"{usage:.0f}%"
                ),
            }

        except Exception as error:
            results["memory"] = {
                "ok": False,
                "severity": "error",
                "title": "RAM",
                "details": str(error),
            }

    # ==========================================================
    # STORAGE
    # ==========================================================

    def check_storage(self, results):
        self.progress.emit(24, "SPRAWDZANIE DYSKÓW...")

        try:
            physical_drives = self.get_physical_drives()

            if not physical_drives:
                results["storage"] = {
                    "ok": False,
                    "severity": "error",
                    "title": "PAMIĘĆ MASOWA",
                    "details": ("BRAK WYKRYTYCH DYSKÓW FIZYCZNYCH"),
                }
                return

            healthy = 0
            warnings = 0
            errors = 0

            drive_details = []

            for drive in physical_drives:
                name = drive.get("name", "NIEZNANY")

                media_type = drive.get("media_type", "NIEZNANY")

                health = drive.get("health", "NIEZNANY")

                operational = drive.get("operational", "NIEZNANY")

                size = drive.get("size", 0)

                size_gb = size / (1024**3)

                if health.upper() == "HEALTHY":

                    if operational.upper() == "OK":
                        healthy += 1
                        status = "OK"

                    else:
                        warnings += 1
                        status = "OSTRZEŻENIE"

                else:
                    errors += 1
                    status = "BŁĄD"

                drive_details.append(
                    f"{status}: {name} | "
                    f"{media_type} | "
                    f"{size_gb:.0f} GB | "
                    f"{health}"
                )

            if errors > 0:
                overall_ok = False
                severity = "error"

            elif warnings > 0:
                overall_ok = False
                severity = "warning"

            else:
                overall_ok = True
                severity = "ok"

            results["storage"] = {
                "ok": overall_ok,
                "severity": severity,
                "title": "DYSKI TWARDE",
                "details": (
                    f"{healthy} zdrowe | "
                    f"{warnings} ostrzeżenia | "
                    f"{errors} błędy"
                ),
                "extra": drive_details,
            }

            # ==================================================
            # PARTITIONS
            # ==================================================

            partitions = []

            for partition in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(partition.mountpoint)

                    total = usage.total / (1024**3)

                    used = usage.used / (1024**3)

                    free = usage.free / (1024**3)

                    percent = usage.percent

                    drive_letter = partition.device.rstrip("\\/")

                    partitions.append(
                        {
                            "drive": drive_letter,
                            "mountpoint": partition.mountpoint,
                            "total": total,
                            "used": used,
                            "free": free,
                            "percent": percent,
                            "fstype": partition.fstype,
                        }
                    )

                except Exception:
                    continue

            results["partitions"] = {
                "ok": True,
                "severity": "info",
                "title": "PARTYCJE",
                "details": (f"{len(partitions)} " f"PARTYCJA(JE) WYKRYTE"),
                "partitions": partitions,
            }

        except Exception as error:
            results["storage"] = {
                "ok": False,
                "severity": "error",
                "title": "PAMIĘĆ MASOWA",
                "details": str(error),
            }

    def get_physical_drives(self):
        command = """
        Get-PhysicalDisk |
        Select-Object `
        FriendlyName,
        MediaType,
        HealthStatus,
        OperationalStatus,
        Size |
        ConvertTo-Csv -NoTypeInformation
        """

        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15,
        )

        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        if len(lines) <= 1:
            return []

        drives = []

        for line in lines[1:]:
            values = self.parse_csv_line(line)

            if len(values) < 5:
                continue

            drives.append(
                {
                    "name": values[0],
                    "media_type": values[1],
                    "health": values[2],
                    "operational": values[3],
                    "size": self.safe_int(values[4]),
                }
            )

        return drives

    def parse_csv_line(self, line):
        import csv
        from io import StringIO

        try:
            reader = csv.reader(StringIO(line))

            return next(reader)

        except Exception:
            return []

    def safe_int(self, value):
        try:
            return int(value.replace(",", "").strip())

        except Exception:
            return 0

    def check_smart(self, results):
        self.progress.emit(32, "SPRAWDZANIE SMART / STAN DYSKÓW...")

        try:
            drives = self.get_physical_drives()

            if not drives:
                results["smart"] = {
                    "ok": True,
                    "severity": "info",
                    "title": "SMART",
                    "details": ("SMART INFO NIEDOSTĘPNE"),
                }
                return

            problems = []
            healthy = 0

            for drive in drives:

                name = drive.get("name", "NIEZNANE")

                health = drive.get("health", "NIEZNANY")

                operational = drive.get("operational", "NIEZNANY")

                if health.upper() == "ZDROWY" and operational.upper() == "OK":
                    healthy += 1

                else:
                    problems.append(f"{name}: " f"{health} / " f"{operational}")

            if problems:

                results["smart"] = {
                    "ok": False,
                    "severity": "error",
                    "title": "SMART / STAN DYSKÓW",
                    "details": (f"{len(problems)} DYSK(I) " f"WYMAGAJĄ UWAGI"),
                    "extra": problems,
                }

            else:

                results["smart"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "SMART / STAN DYSKÓW",
                    "details": (f"{healthy} DYSK(I) " f"ZDROWE"),
                }

        except Exception:
            results["smart"] = {
                "ok": True,
                "severity": "info",
                "title": "SMART / STAN DYSKÓW",
                "details": ("SPRAWDZANIE SMART NIEDOSTĘPNE"),
            }

    # ==========================================================
    # NETWORK
    # ==========================================================

    def check_network(self, results):
        self.progress.emit(40, "SPRAWDZANIE SIECI...")

        try:
            interfaces = psutil.net_if_stats()
            addresses = psutil.net_if_addrs()

            active = []

            for name, stats in interfaces.items():

                if not stats.isup:
                    continue

                if name.lower() in ("loopback", "lo"):
                    continue

                ip_address = "NO IP"

                for address in addresses.get(name, []):
                    if address.family == socket.AF_INET:
                        ip_address = address.address
                        break

                active.append(f"{name} [{ip_address}]")

            if active:
                results["network"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "SIECI",
                    "details": " | ".join(active[:3]),
                }

            else:
                results["network"] = {
                    "ok": False,
                    "severity": "error",
                    "title": "SIECI",
                    "details": ("NO ACTIVE NETWORK INTERFACE"),
                }

        except Exception as error:
            results["network"] = {
                "ok": False,
                "severity": "error",
                "title": "SIECI",
                "details": str(error),
            }

    # ==========================================================
    # AUDIO
    # ==========================================================

    def check_audio(self, results):
        self.progress.emit(47, "SPRAWDZANIE URZĄDZEŃ AUDIO...")

        try:
            command = (
                "Get-CimInstance Win32_SoundDevice | "
                "Where-Object {$_.Status -eq 'OK'} | "
                "Select-Object -ExpandProperty Name"
            )

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=5,
            )

            devices = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]

            if devices:
                results["audio"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "AUDIO",
                    "details": devices[0],
                }

            else:
                results["audio"] = {
                    "ok": False,
                    "severity": "warning",
                    "title": "AUDIO",
                    "details": ("NO WORKING AUDIO DEVICE"),
                }

        except Exception:
            results["audio"] = {
                "ok": True,
                "severity": "info",
                "title": "AUDIO",
                "details": ("AUDIO CHECK UNAVAILABLE"),
            }

    # ==========================================================
    # POWER
    # ==========================================================

    def check_power(self, results):
        self.progress.emit(53, "SPRAWDZANIE ZASILANIA...")

        try:
            battery = psutil.sensors_battery()

            if battery is None:

                results["power"] = {
                    "ok": True,
                    "severity": "info",
                    "title": "ZASILANIE",
                    "details": ("KOMPUTER STACJONARNY / ZASILANIE SIECIOWE"),
                }

                return

            plugged = "ZASILANIE SIECIOWE" if battery.power_plugged else "BATERIA"

            percent = battery.percent

            if percent < 10 and not battery.power_plugged:
                ok = False
                severity = "warning"

            else:
                ok = True
                severity = "ok"

            results["power"] = {
                "ok": ok,
                "severity": severity,
                "title": "ZASILANIE",
                "details": (f"{percent:.0f}% | " f"{plugged}"),
            }

        except Exception:
            results["power"] = {
                "ok": True,
                "severity": "info",
                "title": "ZASILANIE",
                "details": ("INFORMACJA O ZASILANIU NIEDOSTĘPNA"),
            }

    # ==========================================================
    # UPTIME
    # ==========================================================

    def check_uptime(self, results):
        self.progress.emit(58, "SPRAWDZANIE CZASU DZIAŁANIA SYSTEMU...")

        try:
            boot_time = psutil.boot_time()

            seconds = time.time() - boot_time

            days = int(seconds // 86400)

            hours = int((seconds % 86400) // 3600)

            minutes = int((seconds % 3600) // 60)

            results["uptime"] = {
                "ok": True,
                "severity": "info",
                "title": "CZAS DZIAŁANIA",
                "details": (f"{days}D " f"{hours}H " f"{minutes}M"),
            }

        except Exception as error:
            results["uptime"] = {
                "ok": False,
                "severity": "warning",
                "title": "CZAS DZIAŁANIA",
                "details": str(error),
            }

    # ==========================================================
    # WINDOWS SERVICES
    # ==========================================================

    def check_windows_services(self, results):
        self.progress.emit(64, "SPRAWDZANIE USŁUG WINDOWS...")

        try:
            services = ["Winmgmt", "EventLog", "Dhcp", "Dnscache", "wuauserv", "BITS"]

            stopped = []

            for service in services:

                command = (
                    f"(Get-Service -Name '{service}' "
                    f"-ErrorAction SilentlyContinue).Status"
                )

                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )

                status = result.stdout.strip().lower()

                if status != "running":
                    stopped.append(service)

            if stopped:

                results["services"] = {
                    "ok": False,
                    "severity": "warning",
                    "title": "USŁUGI WINDOWS",
                    "details": ("NIE DZIAŁAJĄ: " + ", ".join(stopped)),
                }

            else:

                results["services"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "USŁUGI WINDOWS",
                    "details": ("WSZYSTKIE USŁUGI DZIAŁAJĄ"),
                }

        except Exception:
            results["services"] = {
                "ok": True,
                "severity": "info",
                "title": "USŁUGI WINDOWS",
                "details": ("SPRAWDZANIE USŁUG NIEDOSTĘPNE"),
            }

    # ==========================================================
    # WINDOWS UPDATE
    # ==========================================================

    def check_windows_update(self, results):
        self.progress.emit(70, "SPRAWDZANIE AKTUALIZACJI WINDOWS...")

        try:
            service_command = (
                "(Get-Service -Name 'wuauserv' " "-ErrorAction SilentlyContinue).Status"
            )

            service_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", service_command],
                capture_output=True,
                text=True,
                timeout=5,
            )

            service_status = service_result.stdout.strip()

            hotfix_command = (
                "Get-HotFix | "
                "Sort-Object InstalledOn -Descending | "
                "Select-Object -First 1 "
                "HotFixID,InstalledOn | "
                "ConvertTo-Csv -NoTypeInformation"
            )

            hotfix_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", hotfix_command],
                capture_output=True,
                text=True,
                timeout=10,
            )

            hotfix_lines = [
                line.strip()
                for line in hotfix_result.stdout.splitlines()
                if line.strip()
            ]

            latest = "UNKNOWN"

            if len(hotfix_lines) >= 2:
                latest = hotfix_lines[1].replace('"', "")

            if service_status.lower() == "running":

                results["update"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "AKTUALIZACJE WINDOWS",
                    "details": (f"USŁUGA DZIAŁA | " f"OSTATNI HOTFIX: {latest}"),
                }

            elif service_status.lower() == "stopped":
                results["update"] = {
                    "ok": False,
                    "severity": "warning",
                    "title": "AKTUALIZACJE WINDOWS",
                    "details": (f"USŁUGA ZATRZYMANA | " f"OSTATNI HOTFIX: {latest}"),
                }

            else:

                results["update"] = {
                    "ok": False,
                    "severity": "warning",
                    "title": "AKTUALIZACJE WINDOWS",
                    "details": (
                        f"AKTUALIZACJE: "
                        f"{service_status or 'NIEZNANE'} | "
                        f"OSTATNI HOTFIX: {latest}"
                    ),
                }

        except Exception:
            results["update"] = {
                "ok": True,
                "severity": "info",
                "title": "AKTUALIZACJE WINDOWS",
                "details": ("SPRAWDZANIE AKTUALIZACJI NIEDOSTĘPNE"),
            }

    # ==========================================================
    # DEVICE DRIVERS
    # ==========================================================

    def check_drivers(self, results):
        self.progress.emit(76, "SPRAWDZANIE STEROWNIKÓW URZĄDZEŃ...")

        try:
            command = "pnputil /enum-devices /problem"

            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=15
            )

            output = result.stdout.strip()

            problem_lines = []

            for line in output.splitlines():

                line_lower = line.lower()

                if "problem code" in line_lower or "problem:" in line_lower:
                    problem_lines.append(line.strip())

            if problem_lines:

                results["drivers"] = {
                    "ok": False,
                    "severity": "warning",
                    "title": "STEROWNIKI URZĄDZEŃ",
                    "details": (
                        f"{len(problem_lines)} " f"WYKRYTO PROBLEMY ZE STEROWNIKAMI"
                    ),
                }

            else:

                results["drivers"] = {
                    "ok": True,
                    "severity": "ok",
                    "title": "STEROWNIKI URZĄDZEŃ",
                    "details": ("BRAK WYKRYTYCH PROBLEMÓW ZE STEROWNIKAMI"),
                }

        except Exception:
            results["drivers"] = {
                "ok": True,
                "severity": "info",
                "title": "STEROWNIKI URZĄDZEŃ",
                "details": ("SPRAWDZANIE STEROWNIKÓW NIEDOSTĘPNE"),
            }

    # ==========================================================
    # EVENT VIEWER
    # ==========================================================

    def check_event_log(self, results):
        self.progress.emit(83, "ANALIZOWANIE EVENT LOGU SYSTEMU...")

        try:
            command = """
            $since = (Get-Date).AddHours(-24);
            $logs = Get-WinEvent -FilterHashtable @{
                LogName='System';
                StartTime=$since
            } -ErrorAction SilentlyContinue;

            $errors = @(
                $logs |
                Where-Object {
                    $_.LevelDisplayName -eq 'Error'
                }
            ).Count;

            $warnings = @(
                $logs |
                Where-Object {
                    $_.LevelDisplayName -eq 'Warning'
                }
            ).Count;

            Write-Output "$errors|$warnings"
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=20,
            )

            output = result.stdout.strip()

            parts = output.split("|")

            if len(parts) == 2:

                errors = int(parts[0])
                warnings = int(parts[1])

                if errors >= 10:
                    ok = False
                    severity = "error"

                elif errors > 0:
                    ok = False
                    severity = "warning"

                else:
                    ok = True
                    severity = "ok"

                results["events"] = {
                    "ok": ok,
                    "severity": severity,
                    "title": "PODGLĄD ZDARZEŃ",
                    "details": (
                        "OSTATNIE 24H | " f"{errors} BŁĘDÓW | " f"{warnings} OSTRZEŻEŃ"
                    ),
                }

            else:

                results["events"] = {
                    "ok": True,
                    "severity": "info",
                    "title": "PODGLĄD ZDARZEŃ",
                    "details": ("DANE EVENT LOGU NIEDOSTĘPNE"),
                }

        except Exception:
            results["events"] = {
                "ok": True,
                "severity": "info",
                "title": "PODGLĄD ZDARZEŃ",
                "details": ("SPRAWDZANIE EVENT LOGU NIEDOSTĘPNE"),
            }

    # ==========================================================
    # NVIDIA GPU TEMPERATURE
    # ==========================================================

    def check_gpu_temperature(self, results):
        self.progress.emit(90, "SPRAWDZANIE TEMPERATURY GPU...")

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,temperature.gpu,utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                results["gpu_temp"] = {
                    "ok": True,
                    "severity": "info",
                    "title": "TEMPERATURA GPU",
                    "details": ("GPU NIE WYKRYTE"),
                }
                return

            lines = [
                line.strip() for line in result.stdout.splitlines() if line.strip()
            ]

            if not lines:
                raise RuntimeError("BRAK DANYCH Z GPU")

            parts = [value.strip() for value in lines[0].split(",")]

            name = parts[0]
            temperature = float(parts[1])
            usage = parts[2]

            if temperature >= 90:
                ok = False
                severity = "error"

            elif temperature >= 80:
                ok = False
                severity = "warning"

            else:
                ok = True
                severity = "ok"

            results["gpu_temp"] = {
                "ok": ok,
                "severity": severity,
                "title": "TEMPERATURA GPU",
                "details": (f"{name} | " f"{temperature:.0f}°C | " f"LOAD {usage}%"),
            }

        except Exception:
            results["gpu_temp"] = {
                "ok": True,
                "severity": "info",
                "title": "TEMPERATURA GPU",
                "details": (" TEMPERATURA GPU NIEDOSTĘPNA"),
            }

    # ==========================================================
    # CPU TEMPERATURE
    # ==========================================================

    def check_cpu_temperature(self, results):
        self.progress.emit(95, "SPRAWDZANIE TEMPERATURY CPU...")

        try:
            command = """
            Get-CimInstance -Namespace root/wmi `
                -ClassName MSAcpi_ThermalZoneTemperature `
                -ErrorAction Stop |
                Select-Object CurrentTemperature
            """

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=8,
            )

            values = []

            for line in result.stdout.splitlines():

                line = line.strip()

                if line.isdigit():

                    value = int(line)

                    if value > 2732:

                        celsius = (value / 10) - 273.15

                        if 0 <= celsius <= 120:
                            values.append(celsius)

            if values:

                temperature = max(values)

                if temperature >= 95:
                    ok = False
                    severity = "error"

                elif temperature >= 85:
                    ok = False
                    severity = "warning"

                else:
                    ok = True
                    severity = "ok"

                results["cpu_temp"] = {
                    "ok": ok,
                    "severity": severity,
                    "title": "TEMPERATURA CPU",
                    "details": (f"{temperature:.0f}°C"),
                }

            else:

                results["cpu_temp"] = {
                    "ok": True,
                    "severity": "info",
                    "title": "TEMPERATURA CPU",
                    "details": ("TEMPERATURA CPU " "NIE JEST DOSTĘPNA"),
                }

        except Exception:

            results["cpu_temp"] = {
                "ok": True,
                "severity": "info",
                "title": "TEMPERATURA CPU",
                "details": ("TEMPERATURA CPU " "NIE JEST DOSTĘPNA"),
            }


class SystemPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("systemPanel")

        self.worker = None

        self.setStyleSheet("""
            QFrame#systemPanel {
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
                padding: 10px 18px;
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

            QProgressBar {
                background-color: rgba(30, 80, 110, 60);
                border: none;
                border-radius: 2px;
                height: 4px;
            }

            QProgressBar::chunk {
                background-color: rgba(60, 210, 255, 190);
                border-radius: 2px;
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

            QProgressBar#driveUsed {
            background-color: rgba(245, 245, 245, 235);
            border: none;
            border-radius: 4px;
            height: 9px;
            text-align: center;
            }

            QProgressBar#driveUsed::chunk {
                border-radius: 4px;
            }
        """)

        self.create_ui()

    def create_ui(self):
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(35, 30, 35, 25)

        main_layout.setSpacing(15)

        # ==================================================
        # HEADER
        # ==================================================

        header = QVBoxLayout()

        header.setSpacing(4)

        title = QLabel("SYSTEM")

        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Light))

        title.setStyleSheet("""
            color: rgba(190, 240, 255, 245);
            letter-spacing: 5px;
        """)

        subtitle = QLabel("JARVIS NARZĘDZIE DIAGNOSTYCZNE SYSTEMU")

        subtitle.setStyleSheet("""
            color: rgba(70, 180, 225, 140);
            font-size: 9px;
            letter-spacing: 3px;
        """)

        header.addWidget(title)

        header.addWidget(subtitle)

        main_layout.addLayout(header)

        # ==================================================
        # STATUS
        # ==================================================

        status_card = QFrame()

        status_card.setProperty("class", "card")

        status_layout = QVBoxLayout(status_card)

        status_layout.setContentsMargins(18, 15, 18, 15)

        status_layout.setSpacing(8)

        self.status_label = QLabel("GOTOWY")

        self.status_label.setStyleSheet("""
            color: rgba(190, 240, 255, 235);
            font-size: 22px;
            letter-spacing: 2px;
        """)

        self.status_details = QLabel("SILNIK DIAGNOSTYCZNY JEST GOTOWY DO URUCHOMIENIA")

        self.status_details.setStyleSheet("""
            color: rgba(120, 180, 205, 160);
            font-size: 18px;
        """)

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(0, 100)

        self.progress_bar.setValue(0)

        status_layout.addWidget(self.status_label)

        status_layout.addWidget(self.status_details)

        status_layout.addWidget(self.progress_bar)

        main_layout.addWidget(status_card)

        # ==================================================
        # RESULTS
        # ==================================================

        self.results_container = QWidget()

        self.results_layout = QVBoxLayout(self.results_container)

        self.results_layout.setContentsMargins(0, 0, 0, 0)

        self.results_layout.setSpacing(7)

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(True)

        self.scroll_area.setWidget(self.results_container)

        main_layout.addWidget(self.scroll_area, 1)

        # ==================================================
        # BUTTON
        # ==================================================

        button_layout = QHBoxLayout()

        self.scan_button = QPushButton("PEŁNA DIAGNOSTYKA SYSTEMU")

        self.scan_button.setMinimumHeight(40)

        self.scan_button.clicked.connect(self.start_diagnostic)

        button_layout.addWidget(self.scan_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def start_diagnostic(self):
        if self.worker is not None and self.worker.isRunning():
            return

        self.clear_results()

        self.progress_bar.setValue(0)

        self.status_label.setText("DIAGNOSTYKA W TRAKCIE")

        self.status_label.setStyleSheet("""
            color: rgba(80, 210, 255, 235);
            font-size: 22px;
            letter-spacing: 2px;
        """)

        self.status_details.setText("INICJOWANIE SKANOWANIA SYSTEMU...")

        self.scan_button.setEnabled(False)

        self.worker = DiagnosticWorker()

        self.worker.progress.connect(self.update_progress)

        self.worker.result.connect(self.show_results)

        self.worker.finished.connect(self.diagnostic_finished)

        self.worker.start()

    def update_progress(self, percentage, message):
        self.progress_bar.setValue(percentage)

        self.status_details.setText(message)

    def diagnostic_finished(self):
        self.scan_button.setEnabled(True)

    def clear_results(self):
        while self.results_layout.count():

            item = self.results_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def show_results(self, results):
        passed = 0
        warnings = 0
        errors = 0
        info = 0
        total = 0

        for result in results.values():

            # PARTITIONS to tylko wizualne rozwinięcie
            # sekcji STORAGE i nie powinno być osobnym
            # wynikiem diagnostycznym.
            if "partitions" in result:
                section = self.create_partitions_view(result)
                self.results_layout.addWidget(section)
                continue

            # Każdy pozostały element results = 1 test diagnostyczny
            total += 1

            severity = result.get("severity", "ok")

            if severity == "ok":
                passed += 1

            elif severity == "warning":
                warnings += 1

            elif severity == "error":
                errors += 1

            elif severity == "info":
                info += 1

            row = self.create_result_row(result)

            self.results_layout.addWidget(row)

        self.results_layout.addStretch()

        # ==========================================
        # FINAL STATUS
        # ==========================================

        if errors > 0:

            self.status_label.setText("SYSTEM WYMAGA UWAGI")

            self.status_label.setStyleSheet("""
                color: rgba(255, 100, 100, 235);
                font-size: 22px;
                letter-spacing: 2px;
            """)

        elif warnings > 0:

            self.status_label.setText("OSTRZEŻENIA W SYSTEMIE")

            self.status_label.setStyleSheet("""
                color: rgba(245, 200, 80, 235);
                font-size: 22px;
                letter-spacing: 2px;
            """)

        else:

            self.status_label.setText("SYSTEM FUNKCJONUJE POPRAWNIE")

            self.status_label.setStyleSheet("""
                color: rgba(80, 235, 175, 235);
                font-size: 22px;
                letter-spacing: 2px;
            """)

        self.status_details.setText(
            f"{passed} OK  |  "
            f"{warnings} OSTRZEŻEŃ  |  "
            f"{errors} BŁĘDY  |  "
            f"{info} INFORMACJE  |  "
            f"{total} ŁĄCZNIE"
        )

        self.progress_bar.setValue(100)

    # ==========================================================
    # PARTITION VISUALIZATION
    # ==========================================================

    def create_partitions_view(self, result):
        container = QFrame()

        container.setProperty("class", "card")

        layout = QVBoxLayout(container)

        layout.setContentsMargins(14, 10, 14, 10)

        layout.setSpacing(8)

        # ------------------------------------------------------
        # HEADER
        # ------------------------------------------------------

        header = QHBoxLayout()

        title = QLabel("UŻYCIE DYSKÓW")

        title.setStyleSheet("""
            color: rgba(175, 225, 245, 220);
            font-size: 10px;
            letter-spacing: 2px;
        """)

        count = QLabel(result.get("details", ""))

        count.setStyleSheet("""
            color: rgba(100, 180, 215, 150);
            font-size: 8px;
            letter-spacing: 1px;
        """)

        header.addWidget(title)

        header.addStretch()

        header.addWidget(count)

        layout.addLayout(header)

        # ------------------------------------------------------
        # DRIVES GRID
        # ------------------------------------------------------

        partitions = result.get("partitions", [])

        grid = QGridLayout()

        grid.setContentsMargins(0, 0, 0, 0)

        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        for index, partition in enumerate(partitions):

            row = index // 2
            column = index % 2

            drive_card = self.create_drive_card(partition)

            grid.addWidget(drive_card, row, column)

        # ------------------------------------------------------
        # EMPTY
        # ------------------------------------------------------

        if not partitions:

            empty = QLabel("NIE WYKRYTO PARTYCJI")

            empty.setStyleSheet("""
                color: rgba(120, 170, 195, 150);
                font-size: 9px;
            """)

            layout.addWidget(empty)

        else:

            layout.addLayout(grid)

        return container

    def create_drive_card(self, drive):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(5, 15, 25, 180);
                border: 1px solid rgba(50, 190, 255, 55);
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(9, 7, 9, 7)
        layout.setSpacing(4)

        # =========================
        # GÓRNY WIERSZ
        # =========================
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        drive_label = QLabel(drive["drive"])
        drive_label.setStyleSheet("""
            color: rgba(130, 225, 255, 255);
            font-size: 15px;
            font-weight: bold;
        """)

        used_label = QLabel(f'{drive["percent"]:.0f}% UŻYWANE')
        used_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        used_label.setStyleSheet("""
            color: rgba(245, 245, 245, 240);
            font-size: 12px;
            font-weight: bold;
        """)

        top.addWidget(drive_label)
        top.addStretch()
        top.addWidget(used_label)

        layout.addLayout(top)

        # =========================
        # INFORMACJE
        # =========================
        info = QHBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(12)

        used_text = QLabel(f'{drive["used"]:.1f} GB / {drive["total"]:.1f} GB')
        used_text.setStyleSheet("""
            color: rgba(210, 230, 240, 230);
            font-size: 11px;
        """)

        free_text = QLabel(f'{drive["free"]:.1f} GB DOSTĘPNE')
        free_text.setStyleSheet("""
            color: rgba(150, 220, 170, 230);
            font-size: 11px;
            font-weight: bold;
        """)

        fs_text = QLabel(drive["fstype"] if drive["fstype"] else "NIEZNANE")
        fs_text.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        fs_text.setStyleSheet("""
            color: rgba(130, 160, 175, 190);
            font-size: 10px;
        """)

        info.addWidget(used_text)
        info.addWidget(free_text)
        info.addStretch()
        info.addWidget(fs_text)

        layout.addLayout(info)

        # =========================
        # PASEK ZAJĘTE / WOLNE
        # =========================
        free_percent = 100 - drive["percent"]

        if free_percent > 30:
            free_color = "rgba(70, 210, 120, 240)"
        elif free_percent >= 20:
            free_color = "rgba(245, 195, 70, 240)"
        else:
            free_color = "rgba(235, 70, 70, 240)"

        bar = QProgressBar()
        bar.setObjectName("driveUsed")
        bar.setRange(0, 100)
        bar.setValue(int(drive["percent"]))
        bar.setTextVisible(False)
        bar.setFixedHeight(8)

        bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {free_color};
                border: none;
                border-radius: 4px;
            }}

            QProgressBar::chunk {{
                background-color: rgba(245, 245, 245, 245);
                border-radius: 4px;
            }}
        """)

        layout.addWidget(bar)

        return card

    # ==========================================================
    # STANDARD RESULT ROW
    # ==========================================================

    def create_result_row(self, result):
        row = QFrame()

        row.setProperty("class", "card")

        layout = QHBoxLayout(row)

        layout.setContentsMargins(15, 10, 15, 10)

        layout.setSpacing(15)

        severity = result.get("severity", "ok")

        if severity == "error":

            status_text = "[ BŁĄD ]"

            status_color = """
                color: rgba(255, 90, 90, 240);
                font-size: 9px;
                letter-spacing: 1px;
            """

        elif severity == "warning":

            status_text = "[ OSTRZEŻENIE ]"

            status_color = """
                color: rgba(245, 200, 80, 240);
                font-size: 9px;
                letter-spacing: 1px;
            """

        elif severity == "info":

            status_text = "[ INFO ]"

            status_color = """
                color: rgba(100, 190, 230, 200);
                font-size: 9px;
                letter-spacing: 1px;
            """

        else:

            status_text = "[ OK ]"

            status_color = """
                color: rgba(80, 235, 175, 230);
                font-size: 9px;
                letter-spacing: 1px;
            """

        status = QLabel(status_text)

        status.setFixedWidth(90)

        status.setStyleSheet(status_color)

        title = QLabel(result["title"])

        title.setFixedWidth(150)

        title.setStyleSheet("""
            color: rgba(175, 220, 240, 210);
            font-size: 10px;
            letter-spacing: 1px;
        """)

        details_text = result["details"]

        extra = result.get("extra", [])

        if extra:
            details_text += "\n" + "\n".join(extra)

        details = QLabel(details_text)

        details.setWordWrap(True)

        details.setStyleSheet("""
            color: rgba(120, 175, 200, 170);
            font-size: 9px;
        """)

        layout.addWidget(status)

        layout.addWidget(title)

        layout.addWidget(details, 1)

        return row

    def showEvent(self, event):
        super().showEvent(event)

        if self.worker is None or not self.worker.isRunning():
            self.start_diagnostic()
