from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional


MIN_LENGTH = 4
MAX_LENGTH = 64

DIGITS = "0123456789"
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?/"

DEFAULT_DB_FILE = Path(__file__).with_name("db.json")


def load_data(path: Path | str = DEFAULT_DB_FILE) -> dict:
    path = Path(path)
    if not path.exists():
        return {"history": []}

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError:
        return {"history": []}

    if not isinstance(data, dict):
        return {"history": []}

    history = data.get("history", [])
    if not isinstance(history, list):
        data["history"] = []
    return data


def save_data(data: dict, path: Path | str = DEFAULT_DB_FILE) -> None:
    path = Path(path)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def validate_length(length: int) -> tuple[bool, str]:
    if not isinstance(length, int):
        return False, "Length must be an integer."
    if length < MIN_LENGTH:
        return False, f"Password length must be at least {MIN_LENGTH}."
    if length > MAX_LENGTH:
        return False, f"Password length must be at most {MAX_LENGTH}."
    return True, ""


def get_pools(use_digits: bool, use_letters: bool, use_symbols: bool) -> list[str]:
    pools = []
    if use_digits:
        pools.append(DIGITS)
    if use_letters:
        pools.append(LETTERS)
    if use_symbols:
        pools.append(SYMBOLS)
    return pools


def generate_password(
    length: int,
    use_digits: bool,
    use_letters: bool,
    use_symbols: bool,
    rng: random.Random | random.Random = random,
) -> str:
    valid, message = validate_length(length)
    if not valid:
        raise ValueError(message)

    pools = get_pools(use_digits, use_letters, use_symbols)
    if not pools:
        raise ValueError("Select at least one character group.")

    password_chars: list[str] = [rng.choice(pool) for pool in pools]
    all_chars = "".join(pools)

    for _ in range(length - len(password_chars)):
        password_chars.append(rng.choice(all_chars))

    rng.shuffle(password_chars)
    return "".join(password_chars)


def add_history_entry(
    history: list[dict],
    password: str,
    length: int,
    use_digits: bool,
    use_letters: bool,
    use_symbols: bool,
    created_at: str | None = None,
) -> dict:
    next_id = 1 if not history else max(int(item.get("id", 0)) for item in history) + 1
    entry = {
        "id": next_id,
        "password": password,
        "length": length,
        "useDigits": use_digits,
        "useLetters": use_letters,
        "useSymbols": use_symbols,
        "createdAt": created_at or datetime.now().isoformat(timespec="seconds"),
    }
    history.append(entry)
    return entry


def filter_history(history: list[dict], query: str) -> list[dict]:
    query = query.strip().lower()
    if not query:
        return list(history)

    result = []
    for item in history:
        haystack = " ".join(
            [
                str(item.get("id", "")),
                str(item.get("password", "")),
                str(item.get("length", "")),
                str(item.get("useDigits", "")),
                str(item.get("useLetters", "")),
                str(item.get("useSymbols", "")),
                str(item.get("createdAt", "")),
            ]
        ).lower()
        if query in haystack:
            result.append(item)
    return result


def history_to_table_rows(history: list[dict]) -> list[tuple]:
    rows = []
    for item in history:
        rows.append(
            (
                item.get("id", ""),
                item.get("password", ""),
                item.get("length", ""),
                "Да" if item.get("useDigits") else "Нет",
                "Да" if item.get("useLetters") else "Нет",
                "Да" if item.get("useSymbols") else "Нет",
                item.get("createdAt", ""),
            )
        )
    return rows
