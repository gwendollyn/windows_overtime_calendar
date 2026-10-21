from __future__ import annotations

import json
import sys
from datetime import datetime, date, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import tkinter as tk
from tkinter import messagebox

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar: read/write events in the user's calendar.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TZ_NAME = "Asia/Taipei"
TITLE = "待確認：可能有加班"
SCRIPT_DIR = Path(__file__).resolve().parent
CLIENT_SECRET_FILE = SCRIPT_DIR / "credentials.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"
STATE_FILE = SCRIPT_DIR / "processed_dates.json"


def show_message(title: str, message: str, error: bool = False) -> None:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if error:
        messagebox.showerror(title, message, parent=root)
    else:
        messagebox.showinfo(title, message, parent=root)
    root.destroy()


def ask_overtime() -> bool:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    answer = messagebox.askyesno(
        "加班紀錄確認",
        "今天 18:00 後有因公工作嗎？\n\n"
        "選「是」會在 Google 日曆新增：\n"
        f"「{TITLE}」\n\n"
        "這只是個人紀錄，不代表公司已核准加班。",
        parent=root,
    )
    root.destroy()
    return answer


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_calendar_service():
    if not CLIENT_SECRET_FILE.exists():
        raise FileNotFoundError(
            "找不到 credentials.json。\n"
            "請先在 Google Cloud Console 建立 OAuth 桌面應用程式，"
            "下載 OAuth 用戶端 JSON，並將它放在本程式同一個資料夾，"
            "檔名改為 credentials.json。"
        )

    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def event_exists(service, day: date) -> bool:
    tz = ZoneInfo(TZ_NAME)
    start = datetime.combine(day, time.min, tzinfo=tz)
    end = start + timedelta(days=1)
    result = service.events().list(
        calendarId="primary",
        timeMin=start.isoformat(),
        timeMax=end.isoformat(),
        singleEvents=True,
        maxResults=250,
    ).execute()

    for event in result.get("items", []):
        if event.get("summary") == TITLE:
            return True
    return False


def create_all_day_event(service, day: date) -> None:
    next_day = day + timedelta(days=1)
    service.events().insert(
        calendarId="primary",
        body={
            "summary": TITLE,
            "start": {"date": day.isoformat()},
            "end": {"date": next_day.isoformat()},
            "description": (
                "由個人 Windows 加班提醒工具建立。\n"
                "用途：提醒本人核對出勤、事前申請核准及事後加班申請。\n"
                "此事件不是正式加班申請或核准證明。"
            ),
        },
    ).execute()


def main() -> int:
    now = datetime.now(ZoneInfo(TZ_NAME))
    today = now.date()
    # If Task Scheduler runs late after a missed trigger, don't create a prompt
    # before 18:00 or silently record a different date.
    if now.time() < time(18, 0):
        return 0

    state = load_state()
    day_key = today.isoformat()
    if state.get(day_key) in {"no_overtime", "created", "already_exists"}:
        return 0

    if not ask_overtime():
        state[day_key] = "no_overtime"
        save_state(state)
        return 0

    try:
        service = get_calendar_service()
        if event_exists(service, today):
            state[day_key] = "already_exists"
            save_state(state)
            show_message("加班紀錄", f"今天日曆已有「{TITLE}」，不重複新增。")
            return 0

        create_all_day_event(service, today)
        state[day_key] = "created"
        save_state(state)
        show_message("加班紀錄完成", f"已在 Google 日曆新增「{TITLE}」。")
        return 0
    except Exception as exc:
        # Do not mark the day as processed on failure; rerunning the script can retry.
        show_message(
            "建立日曆事件失敗",
            "沒有成功建立事件，因此今天仍可重新執行本程式重試。\n\n"
            f"錯誤：{exc}",
            error=True,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
