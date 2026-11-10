import sqlite3
from contextlib import closing

from chat_history import ChatHistory


def test_reopened_database_restores_separate_conversations_in_recent_order(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    history = ChatHistory(path)
    first = history.save_turn("", "Tin robot", "Kết quả", ["lookup"])
    second = history.save_turn("", "Đọc bài này", "Bạn gửi link nhé", ["clarify"])
    assert history.save_turn(first, "Tuần này nhé", "Đây là tin tuần này", ["lookup"]) == first

    reopened = ChatHistory(path)
    assert list(reopened.list_conversations().items()) == [(first, "Tin robot"), (second, "Đọc bài này")]
    assert reopened.read_messages(first) == [
        {"role": "user", "content": "Tin robot"},
        {"role": "assistant", "content": "Kết quả", "tools": ["lookup"]},
        {"role": "user", "content": "Tuần này nhé"},
        {"role": "assistant", "content": "Đây là tin tuần này", "tools": ["lookup"]},
    ]
    assert reopened.read_messages(second) == [
        {"role": "user", "content": "Đọc bài này"},
        {"role": "assistant", "content": "Bạn gửi link nhé", "tools": ["clarify"]},
    ]


def test_images_and_legacy_text_survive_reopening_the_database(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    initial = ChatHistory(path)
    conversation = initial.save_turn("", "Câu hỏi cũ", "Câu trả lời cũ", [])
    with closing(sqlite3.connect(path)) as db, db:
        db.execute("DROP TABLE turn_images")

    upgraded = ChatHistory(path)
    upgraded.save_turn(conversation, "Vẽ hình tròn", "Ảnh đã tạo", [], image=b"image bytes")

    assert ChatHistory(path).read_messages(conversation) == [
        {"role": "user", "content": "Câu hỏi cũ"},
        {"role": "assistant", "content": "Câu trả lời cũ", "tools": []},
        {"role": "user", "content": "Vẽ hình tròn"},
        {"role": "assistant", "content": "Ảnh đã tạo", "tools": [], "image": b"image bytes"},
    ]
