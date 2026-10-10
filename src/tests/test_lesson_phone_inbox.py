import json
from base64 import b64encode
from urllib import error, request

from portal_v2.ui.lesson_phone_inbox import PhotoInbox


def test_teacher_pairing_queues_photo_for_review_only():
    inbox = PhotoInbox("teacher", "lesson", 0)
    url = f"http://127.0.0.1:{inbox.server.server_port}/upload"
    photo = b"\xff\xd8\xff" + b"0" * 100

    def send(code):
        payload = json.dumps({"code": code, "device": "iPad",
                              "data": b64encode(photo).decode("ascii")}).encode()
        return request.urlopen(request.Request(url, data=payload,
                               headers={"Content-Type": "application/json"}), timeout=3)

    try:
        try:
            send("not-the-code")
        except error.HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError("unpaired upload accepted")
        assert inbox.list_pending() == []
        with send(inbox.code) as response:
            assert "Chờ giáo viên duyệt" in json.load(response)["message"]
        waiting = inbox.list_pending()
        assert len(waiting) == 1 and waiting[0]["data"] == photo
        previous = inbox.code
        assert inbox.rotate_code() != previous
        try:
            send(previous)
        except error.HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError("old pairing code accepted")
        inbox.remove(waiting[0]["id"])
        assert inbox.list_pending() == []
    finally:
        inbox.close()
