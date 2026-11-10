from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from uuid import uuid4


HISTORY_PATH = Path(__file__).with_name(".chat_history") / "history.sqlite3"


class ChatHistory:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    tools TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS turns_conversation ON turns (conversation_id, id)")
            db.execute("""
                CREATE TABLE IF NOT EXISTS turn_images (
                    turn_id INTEGER PRIMARY KEY REFERENCES turns(id),
                    data BLOB NOT NULL
                )
            """)

    def list_conversations(self) -> dict[str, str]:
        with closing(sqlite3.connect(self.path)) as db:
            return dict(db.execute("""
                SELECT turns.conversation_id, turns.question
                FROM turns
                JOIN (
                    SELECT MIN(id) AS first_id, MAX(id) AS last_id
                    FROM turns GROUP BY conversation_id
                ) AS conversations ON turns.id = conversations.first_id
                ORDER BY conversations.last_id DESC
            """))

    def read_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        with closing(sqlite3.connect(self.path)) as db:
            turns = db.execute(
                """
                SELECT turns.question, turns.answer, turns.tools, turn_images.data
                FROM turns LEFT JOIN turn_images ON turn_images.turn_id = turns.id
                WHERE turns.conversation_id = ? ORDER BY turns.id
                """,
                (conversation_id,),
            )
            for question, answer, tools, image in turns:
                messages.append({"role": "user", "content": question})
                reply = {"role": "assistant", "content": answer, "tools": json.loads(tools)}
                if image is not None:
                    reply["image"] = image
                messages.append(reply)
        return messages

    def save_turn(
        self, conversation_id: str, question: str, answer: str, tools: list[str], *, image: bytes | None = None,
    ) -> str:
        conversation_id = conversation_id or uuid4().hex
        with closing(sqlite3.connect(self.path)) as db, db:
            turn = db.execute(
                "INSERT INTO turns (conversation_id, question, answer, tools) VALUES (?, ?, ?, ?)",
                (conversation_id, question, answer, json.dumps(tools)),
            )
            if image is not None:
                db.execute("INSERT INTO turn_images (turn_id, data) VALUES (?, ?)", (turn.lastrowid, image))
        return conversation_id
