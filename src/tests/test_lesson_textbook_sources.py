from types import SimpleNamespace

import pytest

from portal_v2.ui.lesson_textbook_sources import load_reviewed_sources, save_reviewed_source


class Query:
    def __init__(self, rows):
        self.rows, self.filters = rows, {}

    def select(self, *_): return self
    def eq(self, key, value): self.filters[key] = value; return self
    def limit(self, *_): return self
    def upsert(self, record, *, on_conflict):
        assert on_conflict == "owner_user_id,textbook_unit_id,source_label"
        self.rows.append(dict(record, source_id="source-1"))
        return self
    def execute(self):
        return SimpleNamespace(data=[row for row in self.rows if all(
            row.get(key) == value for key, value in self.filters.items())])


class Client:
    def __init__(self): self.rows = []
    def table(self, name):
        assert name == "teacher_textbook_lesson_sources"
        return Query(self.rows)


def test_reviewed_excerpt_is_scoped_to_owner_book_and_lesson():
    client = Client()
    lesson = "unit-math-kntt-g6-lesson-002"
    save_reviewed_source(client, user_id="teacher-1", book_id="book-1",
                         lesson_id=lesson, label="Cách ghi số tự nhiên",
                         excerpt="Giáo viên kiểm tra kiến thức đúng bài. " * 5,
                         pdf_bytes=None, pdf_page=None)
    assert len(load_reviewed_sources(client, user_id="teacher-1", book_id="book-1",
                                     lesson_id=lesson)) == 1
    assert not load_reviewed_sources(client, user_id="teacher-2", book_id="book-1",
                                     lesson_id=lesson)
    assert not load_reviewed_sources(client, user_id="teacher-1", book_id="book-1",
                                     lesson_id="unit-math-kntt-g6-lesson-001")


def test_short_or_unlocated_excerpt_cannot_be_reviewed_source():
    client = Client()
    args = dict(user_id="teacher-1", book_id="book-1", lesson_id="lesson-1",
                label="Một mục", excerpt="Một dòng", pdf_bytes=None, pdf_page=None)
    with pytest.raises(ValueError, match="80"):
        save_reviewed_source(client, **args)
    with pytest.raises(ValueError, match="trang PDF"):
        save_reviewed_source(client, **dict(args, excerpt="Nội dung được kiểm tra. " * 5,
                                            pdf_bytes=b"pdf", pdf_page=None))
