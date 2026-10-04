import base64
from email.utils import parseaddr, parsedate_to_datetime
import mimetypes
import os
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QWidget,
)

BASE_DIR = Path(__file__).resolve().parent.parent

CREDENTIALS_FILE = BASE_DIR / "backend\\credentials.json"
TOKEN_FILE = BASE_DIR / "backend\\token.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


class GmailAPI:
    def __init__(self):
        self.service = None
        self.credentials = None

    def authenticate(self) -> bool:
        """
        Loguje użytkownika przez Google OAuth.

        Przy pierwszym uruchomieniu otworzy przeglądarkę.
        Token zostanie zapisany do token.json.
        """
        try:
            creds = None

            # ------------------------------------------------
            # Istniejący token
            # ------------------------------------------------

            if TOKEN_FILE.exists():
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

            # ------------------------------------------------
            # Token nieważny / wygasły
            # ------------------------------------------------

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            # ------------------------------------------------
            # Brak autoryzacji
            # ------------------------------------------------

            if not creds or not creds.valid:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Nie znaleziono pliku OAuth: \n"
                        f"{CREDENTIALS_FILE} \n\n"
                        f"Pobierz credentials.json z Google CLoud "
                        f"i umieść go w katalogu projektu."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CREDENTIALS_FILE), SCOPES
                )

                creds = flow.run_local_server(
                    port=0, access_type="offline", prompt="consent"
                )

            # ------------------------------------------------
            # Zapis tokenu
            # ------------------------------------------------

            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

            self.credentials = creds

            # ------------------------------------------------
            # Utworzenie klienta Gmail
            # ------------------------------------------------

            self.service = build("gmail", "v1", credentials=creds)

            return True

        except Exception as e:
            print(f"[GMAIL] Błąd autoryzacji: {e}")
            return False

    # ========================================================
    # SPRAWDZENIE POŁĄCZENIA
    # ========================================================

    def is_connected(self) -> bool:
        return self.service is not None

    # ========================================================
    # INFORMACJE O KONCIE
    # ========================================================

    def get_profile(self) -> dict[str, Any] | None:
        """
        Zwraca informacje o aktualnie zalogowanym koncie.
        """

        if not self.service:
            return None

        try:
            profile = self.service.users().getProfile(userId="me").execute()

            return profile

        except HttpError as e:
            print(f"[GMAIL] Błąd pobierania profilu: {e}")
            return None

    # ========================================================
    # LISTOWANIE WIADOMOŚCI
    # ========================================================

    def list_messages(
        self, query: str = "", max_results: int = 20
    ) -> list[dict[str, Any]]:
        """
        Pobiera listę wiadomości.

        Przykłady query:

        is:unread
        from:example@gmail.com
        subject:rachunek
        newer_than:7d
        has:attachment
        is:unread newer_than:1d
        """

        if not self.service:
            return []

        try:
            response = (
                self.service.users()
                .messages()
                .list(userId="me", q=query, maxResults=max_results)
                .execute()
            )

            messages = response.get("messages", [])

            result = []

            for message in messages:
                message_id = message["id"]

                metadata = (
                    self.service.users()
                    .messages()
                    .get(
                        userId="me",
                        id=message_id,
                        format="metadata",
                        metadataHeaders=["From", "To", "Subject", "Date"],
                    )
                    .execute()
                )

                headers = self._get_headers(metadata)

                result.append(
                    {
                        "id": message_id,
                        "thread_id": metadata.get("threadId"),
                        "from": headers.get("From", ""),
                        "to": headers.get("To", ""),
                        "subject": headers.get("Subject", ""),
                        "date": headers.get("Date", ""),
                        "snippet": metadata.get("snippet", ""),
                        "label_ids": metadata.get("labelIds", []),
                    }
                )

            return result

        except HttpError as e:
            print(f"[GMAIL] Błąd listowania wiadomości: {e}")
            return []

    # ========================================================
    # WYSZUKIWANIE
    # ========================================================

    def search_emails(self, query: str, max_results: int = 20) -> list[dict[str, Any]]:
        """
        Wyszukuje wiadomości za pomocą składni Gmail.

        Przykłady:

        search_emails("from:szef@example.com")
        search_emails("subject:faktura")
        search_emails("is:unread")
        search_emails("newer_than:7d")
        search_emails("has:attachment")
        """

        return self.list_messages(query=query, max_results=max_results)

    # ========================================================
    # ODCZYT WIADOMOŚCI
    # ========================================================

    def get_message(
        self, message_id: str, mark_as_read: bool = False
    ) -> dict[str, Any] | None:
        """
        Pobiera pełną wiadomość.
        """

        if not self.service:
            return None

        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = self._get_headers(message)

            body = self._extract_body(message.get("payload", {}))

            attachments = self._extract_attachments(message.get("payload", {}))

            result = {
                "id": message.get("id"),
                "thread_id": message.get("threadId"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "cc": headers.get("Cc", ""),
                "bcc": headers.get("Bcc", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "body": body,
                "snippet": message.get("snippet", ""),
                "label_ids": message.get("labelIds", []),
                "attachments": attachments,
            }

            if mark_as_read:
                self.mark_as_read(message_id)

            return result

        except HttpError as e:
            print(f"[GMAIL] Błąd odczytu wiadomości: {e}")
            return None

    # ========================================================
    # OZNACZANIE JAKO PRZECZYTANE
    # ========================================================

    def mark_as_read(self, message_id: str) -> bool:
        """
        Usuwa etykietę UNREAD.
        """

        if not self.service:
            return False

        try:
            (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
                .execute()
            )

            return True

        except HttpError as e:
            print(f"[GMAIL] Błąd oznaczania jako przeczytane: {e}")
            return False

    # ========================================================
    # OZNACZANIE JAKO NIEPRZECZYTANE
    # ========================================================

    def mark_as_unread(self, message_id: str) -> bool:
        """
        Dodaje etykietę UNREAD.
        """

        if not self.service:
            return False

        try:
            (
                self.service.users()
                .messages()
                .modify(userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]})
                .execute()
            )

            return True

        except HttpError as e:
            print(f"[GMAIL] Błąd oznaczania jako nieprzeczytane: {e}")
            return False

    # ========================================================
    # WYSYŁANIE MAILA
    # ========================================================

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
        attachments: list[str] | None = None,
    ) -> dict[str, Any] | None:
        """
        Wysyła wiadomość.

        Przykład:

        gmail.send_email(
            to="test@gmail.com",
            subject="Test",
            body="To jest wiadomość."
        )

        attachments:
            [
                r"G:\\JARVIS_V2\\Plik.pdf"
            ]
        """

        if not self.service:
            return None

        try:
            message = EmailMessage()

            message["To"] = to
            message["Subject"] = subject

            if cc:
                message["Cc"] = cc

            if bcc:
                message["Bcc"] = bcc

            message.set_content(body)

            # -----------------------------------------------
            # Załączniki
            # -----------------------------------------------

            if attachments:

                for file_path in attachments:

                    path = Path(file_path)

                    if not path.exists():
                        print(f"[GMAIL] Nie znaleziono załącznika: " f"{path}")
                        continue

                    mime_type, _ = mimetypes.guess_type(str(path))

                    if mime_type:
                        maintype, subtype = mime_type.split("/", 1)
                    else:
                        maintype = "application"
                        subtype = "octet-stream"

                    with open(path, "rb") as f:
                        file_data = f.read()

                    message.add_attachment(
                        file_data,
                        maintype=maintype,
                        subtype=subtype,
                        filename=path.name,
                    )

            # -----------------------------------------------
            # Kodowanie
            # -----------------------------------------------

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            send_message = {"raw": encoded_message}

            result = (
                self.service.users()
                .messages()
                .send(userId="me", body=send_message)
                .execute()
            )

            return result

        except HttpError as e:
            print(f"[GMAIL] Błąd wysyłania: {e}")
            return None

        except Exception as e:
            print(f"[GMAIL] Błąd: {e}")
            return None

    # ========================================================
    # ZAŁĄCZNIKI
    # ========================================================

    def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        filename: str,
        output_dir: str | Path = "attachments",
    ) -> str | None:
        """
        Pobiera konkretny załącznik.
        """

        if not self.service:
            return None

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            attachment = (
                self.service.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=attachment_id)
                .execute()
            )

            data = attachment.get("data")

            if not data:
                return None

            file_data = base64.urlsafe_b64decode(data.encode())

            file_path = output_path / filename

            file_path.write_bytes(file_data)

            return str(file_path)

        except HttpError as e:
            print(f"[GMAIL] Błąd pobierania załącznika: {e}")
            return None

    # ========================================================
    # USUWANIE WIADOMOŚCI
    # ========================================================

    def trash_message(self, message_id: str) -> bool:
        """
        Przenosi wiadomość do kosza.
        """

        if not self.service:
            return False

        try:
            (
                self.service.users()
                .messages()
                .trash(userId="me", id=message_id)
                .execute()
            )

            return True

        except HttpError as e:
            print(f"[GMAIL] Błąd przenoszenia do kosza: {e}")
            return False

    # ========================================================
    # FUNKCJE POMOCNICZE
    # ========================================================

    @staticmethod
    def _get_headers(message: dict[str, Any]) -> dict[str, str]:
        """
        Pobiera nagłówki wiadomości.
        """

        headers = {}

        payload = message.get("payload", {})

        for header in payload.get("headers", []):

            name = header.get("name", "")
            value = header.get("value", "")

            headers[name] = value

        return headers

    @staticmethod
    def _decode_body(data: str) -> str:
        """
        Dekoduje body Gmail API.
        """

        try:
            decoded = base64.urlsafe_b64decode(data.encode())

            return decoded.decode("utf-8", errors="replace")

        except Exception:
            return ""

    def _extract_body(self, payload: dict[str, Any]) -> str:
        """
        Wyciąga tekst wiadomości.

        Preferuje text/plain.
        """

        mime_type = payload.get("mimeType", "")

        body_data = payload.get("body", {}).get("data")

        if body_data:
            return self._decode_body(body_data)

        parts = payload.get("parts", [])

        plain_text = None
        html_text = None

        for part in parts:

            part_mime = part.get("mimeType", "")

            part_body = part.get("body", {})

            part_data = part_body.get("data")

            if part_data:

                decoded = self._decode_body(part_data)

                if part_mime == "text/plain":
                    plain_text = decoded

                elif part_mime == "text/html":
                    html_text = decoded

            # ---------------------------------------------
            # Multipart zagnieżdżony
            # ---------------------------------------------

            if part.get("parts"):

                nested_body = self._extract_body(part)

                if nested_body:
                    if not plain_text:
                        plain_text = nested_body

        if plain_text:
            return plain_text

        if html_text:
            return html_text

        return ""

    @staticmethod
    def _extract_attachments(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Zwraca informacje o załącznikach.
        """

        attachments = []

        def process_parts(parts):

            for part in parts:

                filename = part.get("filename")

                body = part.get("body", {})

                attachment_id = body.get("attachmentId")

                if filename and attachment_id:

                    attachments.append(
                        {
                            "filename": filename,
                            "attachment_id": attachment_id,
                            "mime_type": part.get("mimeType", ""),
                            "size": body.get("size", 0),
                        }
                    )

                nested_parts = part.get("parts", [])

                if nested_parts:
                    process_parts(nested_parts)

        process_parts(payload.get("parts", []))

        return attachments


# ============================================================
# PROSTY TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("JARVIS - GMAIL API TEST")
    print("=" * 60)

    gmail = GmailAPI()

    print("\n[GMAIL] Autoryzacja...")

    if not gmail.authenticate():
        print("[GMAIL] Autoryzacja nieudana.")
        raise SystemExit(1)

    print("[GMAIL] Połączono.")

    profile = gmail.get_profile()

    if profile:
        print(f"\nKonto: {profile.get('emailAddress')}")

    print("\nOstatnie wiadomości:")

    messages = gmail.list_messages(max_results=10)

    for index, message in enumerate(messages, start=1):
        print()
        print(f"{index}. {message['subject']}")
        print(f"   Od: {message['from']}")
        print(f"   Data: {message['date']}")
        print(f"   ID: {message['id']}")
        print(f"   {message['snippet'][:100]}")

    print("\n" + "=" * 60)
    print("TEST ZAKOŃCZONY")
    print("=" * 60)


class GmailLoadWorker(QObject):
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, gmail):
        super().__init__()
        self.gmail = gmail

    def run(self):
        try:
            if not self.gmail.is_connected():
                if not self.gmail.authenticate():
                    self.error.emit("Nie udało się zalogować do Gmail.")
                    return
            self.finished.emit(
                self.gmail.list_messages(query="in:inbox", max_results=50)
            )
        except Exception as e:
            self.error.emit(str(e))


class GmailMessageWorker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, gmail, message_id):
        super().__init__()
        self.gmail = gmail
        self.message_id = message_id

    def run(self):
        try:
            message = self.gmail.get_message(self.message_id, mark_as_read=True)
            if message is None:
                self.error.emit("Nie udało się pobrać wiadomości.")
                return
            self.finished.emit(message)
        except Exception as e:
            self.error.emit(str(e))


class EmailCard(QFrame):
    clicked = Signal(str)

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.message_id = message.get("id", "")
        unread = "UNREAD" in message.get("label_ids", [])
        self.setObjectName("emailCard")
        self.setProperty("unread", unread)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(8)

        if unread:
            dot = QLabel("●")
            dot.setObjectName("unreadDot")
            top.addWidget(dot)

        name, address = parseaddr(message.get("from", ""))
        sender = name or address or message.get("from", "") or "(brak nadawcy)"
        sender_label = QLabel(sender)
        sender_label.setObjectName("emailSender")
        top.addWidget(sender_label)
        top.addStretch()

        date_label = QLabel(self.format_date(message.get("date", "")))
        date_label.setObjectName("emailDate")
        top.addWidget(date_label)
        layout.addLayout(top)

        subject = QLabel(message.get("subject", "(brak tematu)"))
        subject.setObjectName("emailSubject")
        layout.addWidget(subject)

        snippet = " ".join(message.get("snippet", "").split())
        if len(snippet) > 170:
            snippet = snippet[:167] + "..."
        snippet_label = QLabel(snippet)
        snippet_label.setObjectName("emailSnippet")
        layout.addWidget(snippet_label)

    @staticmethod
    def format_date(value):
        if not value:
            return ""
        try:
            return parsedate_to_datetime(value).strftime("%d.%m.%Y  %H:%M")
        except Exception:
            return value

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.message_id)
        super().mousePressEvent(event)


class GmailPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gmail = GmailAPI()
        self.load_thread = None
        self.load_worker = None
        self.message_thread = None
        self.message_worker = None
        self.setObjectName("gmailPanel")

        self.setStyleSheet("""
            QFrame#gmailPanel { background-color: rgba(2, 7, 13, 245); }
            QLabel { color: rgba(180, 225, 245, 220); }
            QFrame.card { background-color: rgba(5, 18, 30, 180); border: 1px solid rgba(50, 180, 235, 65); border-radius: 6px; }
            QPushButton { background-color: rgba(20, 90, 125, 45); border: 1px solid rgba(60, 190, 240, 80); border-radius: 4px; color: rgba(180, 230, 250, 230); padding: 10px 16px; font-size: 10px; }
            QPushButton:hover { background-color: rgba(30, 150, 210, 65); border: 1px solid rgba(80, 220, 255, 150); color: rgba(220, 250, 255, 255); }
            QPushButton:pressed { background-color: rgba(40, 180, 240, 90); }
            QPushButton:disabled { color: rgba(100, 140, 155, 130); border-color: rgba(50, 100, 120, 40); }
            QFrame#emailCard { background-color: rgba(4, 16, 27, 210); border: 1px solid rgba(50, 180, 235, 35); border-radius: 5px; }
            QFrame#emailCard:hover { background-color: rgba(5, 18, 30, 180); border: 1px solid rgba(60, 200, 245, 120); }
            QFrame#emailCard[unread="true"] { background-color: rgba(5, 18, 30, 180); border: 3px solid rgba(255, 0, 0, 1); }
            QLabel#emailSender { color: rgba(195, 235, 250, 245); font-size: 12px; font-weight: 600; background-color: rgba(5, 18, 30, 180); }
            QLabel#emailSubject { color: rgba(165, 220, 240, 235); font-size: 11px; background-color: rgba(5, 18, 30, 180);}
            QLabel#emailSnippet { color: rgba(105, 155, 180, 175); font-size: 10px; background-color: rgba(5, 18, 30, 180);}
            QLabel#emailDate { color: rgba(100, 160, 185, 150); font-size: 9px; }
            QLabel#unreadDot { color: rgba(80, 220, 255, 255); font-size: 8px; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: rgba(5, 15, 23, 100); width: 8px; margin: 0; }
            QScrollBar::handle:vertical { background: rgba(60, 180, 220, 100); min-height: 30px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: rgba(80, 210, 245, 160); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QTextBrowser { background-color: rgba(2, 11, 19, 230); border: 1px solid rgba(50, 180, 235, 45); border-radius: 5px; color: rgba(200, 230, 240, 230); padding: 14px; font-size: 11px; selection-background-color: rgba(40, 150, 205, 100); }
        """)
        self.create_ui()

    def create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(35, 30, 35, 30)
        main_layout.setSpacing(18)
        main_layout.addWidget(self.create_header())
        main_layout.addWidget(self.create_section("GMAIL", "OBSŁUGA POCZTY GMAIL"))
        system_grid = QGridLayout()
        system_grid.setSpacing(10)
        self.status_card = self.create_card("GMAIL CLIENT", "STATUS", "OFFLINE", False)
        system_grid.addWidget(self.status_card, 0, 0)
        main_layout.addLayout(system_grid)
        main_layout.addWidget(self.create_windows_card())
        main_layout.addWidget(self.create_thread_card())
        main_layout.addStretch()

    def create_header(self):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        title = QLabel("GMAIL")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Light))
        title.setStyleSheet("color: rgba(190, 240, 255, 245); letter-spacing: 5px;")
        subtitle = QLabel("JARVIS GMAIL SYSTEM")
        subtitle.setStyleSheet(
            "color: rgba(70, 180, 225, 140); font-size: 11px; letter-spacing: 3px;"
        )
        layout.addWidget(title)
        layout.addWidget(subtitle)
        return frame

    def create_section(self, title, description):
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "color: rgba(100, 210, 255, 230); font-size: 11px; letter-spacing: 2px; "
        )
        description_label = QLabel(description)
        description_label.setStyleSheet(
            "color: rgba(120, 170, 195, 150); font-size: 10px;"
        )
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        return frame

    def create_card(self, name, label, value, online=False):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(3)
        name_label = QLabel(name)
        name_label.setStyleSheet(
            "color: rgba(80, 190, 230, 170); font-size: 9px; letter-spacing: 2px; background-color: rgba(5, 18, 30, 180);"
        )
        self.status_value_label = QLabel(value)
        self.status_value_label.setStyleSheet(
            "color: rgba(200, 240, 255, 225); font-size: 17px; letter-spacing: 1px; background-color: rgba(5, 18, 30, 180);"
        )
        layout.addWidget(name_label)
        layout.addWidget(self.status_value_label)
        return card

    def create_windows_card(self):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel("ZARZĄDZANIE SKRZYNKĄ POCZTOWĄ")
        title.setStyleSheet(
            "color: rgba(170, 225, 245, 220); font-size: 11px; letter-spacing: 2px; background-color: rgba(5, 18, 30, 180);"
        )
        header.addWidget(title)
        header.addStretch()
        self.mail_count_label = QLabel("0 WIADOMOŚCI")
        self.mail_count_label.setStyleSheet(
            "color: rgba(80, 190, 230, 150); font-size: 9px; letter-spacing: 1px; background-color: rgba(5, 18, 30, 180);"
        )
        header.addWidget(self.mail_count_label)
        layout.addLayout(header)
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.received_button = QPushButton("ODEBRANE")
        self.received_button.setMinimumHeight(38)
        self.received_button.clicked.connect(self.load_received_emails)
        buttons.addWidget(self.received_button)
        for text in ("WYSŁANE", "ROBOCZE", "KOSZ"):
            button = QPushButton(text)
            button.setMinimumHeight(38)
            button.setEnabled(False)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        return card

    def create_thread_card(self):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(10)
        title_layout = QHBoxLayout()
        title = QLabel("SKRZYNKA ODEBRANE")
        title.setStyleSheet(
            "color: rgba(170, 225, 245, 220); font-size: 11px; letter-spacing: 2px; background-color: rgba(5, 18, 30, 180);"
        )
        title_layout.addWidget(title)
        title_layout.addStretch()
        self.refresh_button = QPushButton("ODŚWIEŻ")
        self.refresh_button.setFixedWidth(90)
        self.refresh_button.clicked.connect(self.load_received_emails)
        title_layout.addWidget(self.refresh_button)
        layout.addLayout(title_layout)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 5, 0)
        self.email_scroll = QScrollArea()
        self.email_scroll.setWidgetResizable(True)
        self.email_container = QWidget()
        self.email_layout = QVBoxLayout(self.email_container)
        self.email_layout.setContentsMargins(2, 2, 2, 2)
        self.email_layout.setSpacing(7)
        self.email_layout.addStretch()
        self.email_scroll.setWidget(self.email_container)
        left_layout.addWidget(self.email_scroll)

        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(5, 0, 0, 0)
        self.message_subject = QLabel("WYBIERZ WIADOMOŚĆ")
        self.message_subject.setWordWrap(True)
        self.message_subject.setStyleSheet(
            "color: rgba(190, 240, 255, 245); font-size: 15px; font-weight: 500; letter-spacing: 1px; background-color: rgba(5, 18, 30, 180);"
        )
        right_layout.addWidget(self.message_subject)
        self.message_meta = QLabel("Brak wybranej wiadomości")
        self.message_meta.setWordWrap(True)
        self.message_meta.setStyleSheet(
            "color: rgba(100, 165, 190, 160); font-size: 10px; background-color: rgba(5, 18, 30, 180);"
        )
        right_layout.addWidget(self.message_meta)
        self.message_body = QTextBrowser()
        self.message_body.setOpenExternalLinks(True)
        self.message_body.setHtml(
            '<div style="color:#6f9aad;">Wybierz wiadomość z listy.</div>'
        )
        right_layout.addWidget(self.message_body)
        self.attachments_label = QLabel("")
        self.attachments_label.setWordWrap(True)
        self.attachments_label.setStyleSheet(
            "color: rgba(100, 190, 220, 180); font-size: 10px; padding-top: 4px; "
        )
        right_layout.addWidget(self.attachments_label)

        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setSizes([430, 650])
        layout.addWidget(self.splitter)
        card.setMinimumHeight(650)
        return card

    def load_received_emails(self):
        if self.load_thread is not None:
            return
        self.received_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.received_button.setText("POBIERANIE...")
        self._clear_email_list()
        self._show_list_status("ŁĄCZENIE Z GMAIL...")
        self.load_thread = QThread()
        self.load_worker = GmailLoadWorker(self.gmail)
        self.load_worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(self.load_worker.run)
        self.load_worker.finished.connect(self.on_received_loaded)
        self.load_worker.error.connect(self.on_gmail_error)
        self.load_worker.finished.connect(self.load_thread.quit)
        self.load_worker.error.connect(self.load_thread.quit)
        self.load_thread.finished.connect(self._load_thread_finished)
        self.load_thread.start()

    def on_received_loaded(self, messages):
        self.received_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.received_button.setText("ODEBRANE")
        self.status_value_label.setText("ONLINE")
        self.status_value_label.setStyleSheet(
            "color: rgba(80, 235, 175, 230); font-size: 17px; letter-spacing: 2px; background-color: rgba(5, 18, 30, 180);"
        )
        self.mail_count_label.setText(f"{len(messages)} WIADOMOŚCI")
        self._clear_email_list()
        if not messages:
            self._show_list_status("BRAK WIADOMOŚCI W SKRZYNCE ODEBRANE")
            return
        for message in messages:
            card = EmailCard(message)
            card.clicked.connect(self.open_message)
            self.email_layout.insertWidget(self.email_layout.count() - 1, card)

    def open_message(self, message_id):
        if self.message_thread is not None:
            return
        self.message_subject.setText("POBIERANIE WIADOMOŚCI...")
        self.message_meta.setText("")
        self.message_body.setHtml(
            '<div style="color:#6f9aad;">Pobieranie treści wiadomości...</div>'
        )
        self.attachments_label.setText("")
        self.message_thread = QThread()
        self.message_worker = GmailMessageWorker(self.gmail, message_id)
        self.message_worker.moveToThread(self.message_thread)
        self.message_thread.started.connect(self.message_worker.run)
        self.message_worker.finished.connect(self.on_message_loaded)
        self.message_worker.error.connect(self.on_gmail_error)
        self.message_worker.finished.connect(self.message_thread.quit)
        self.message_worker.error.connect(self.message_thread.quit)
        self.message_thread.finished.connect(self._message_thread_finished)
        self.message_thread.start()

    def on_message_loaded(self, message):
        self.message_subject.setText(message.get("subject", "(brak tematu)"))
        date = self._format_date(message.get("date", ""))
        meta = f"<b>OD:</b> {message.get('from', '')}<br><b>DO:</b> {message.get('to', '')}<br>"
        if message.get("cc"):
            meta += f"<b>DW:</b> {message.get('cc')}<br>"
        meta += f"<b>DATA:</b> {date}"
        self.message_meta.setText(meta)
        body = message.get("body", "") or "(wiadomość nie zawiera treści tekstowej)"
        self.message_body.setHtml(self._prepare_message_html(body))
        attachments = message.get("attachments", [])
        if attachments:
            names = [a.get("filename", "plik") for a in attachments]
            self.attachments_label.setText("📎 ZAŁĄCZNIKI: " + "   |   ".join(names))
        else:
            self.attachments_label.setText("")

    def on_gmail_error(self, error):
        self.received_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.received_button.setText("ODEBRANE")
        self._clear_email_list()
        self._show_list_status("BŁĄD POŁĄCZENIA Z GMAIL")
        QMessageBox.critical(
            self, "GMAIL", f"Nie udało się wykonać operacji:\n\n{error}"
        )

    def _clear_email_list(self):
        while self.email_layout.count() > 1:
            item = self.email_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_list_status(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "color: rgba(90, 170, 200, 150); font-size: 10px; letter-spacing: 2px; padding: 40px; background-color: rgba(5, 18, 30, 180);"
        )
        self.email_layout.insertWidget(0, label)

    def _prepare_message_html(self, body):
        if "<html" in body.lower():
            return body
        escaped = (
            body.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        return f'<html><body style="background-color:#020b13;color:#c8e6f0;font-family:Segoe UI;font-size:11pt;line-height:1.5;">{escaped}</body></html>'

    @staticmethod
    def _format_date(value):
        if not value:
            return ""
        try:
            return parsedate_to_datetime(value).strftime("%d.%m.%Y  %H:%M")
        except Exception:
            return value

    def _load_thread_finished(self):
        if self.load_thread:
            self.load_thread.deleteLater()
        self.load_thread = None
        self.load_worker = None

    def _message_thread_finished(self):
        if self.message_thread:
            self.message_thread.deleteLater()
        self.message_thread = None
        self.message_worker = None
