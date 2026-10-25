"""Opt-in local hotspot photo inbox for one authenticated teacher lesson."""

from base64 import b64decode
from binascii import Error as Base64Error
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secrets import token_urlsafe
from threading import Lock, Thread
from time import monotonic
from uuid import uuid4
import hmac
import json
import os
import socket

from portal_v2.ui.lesson_evidence_card import MAX_PHOTO_BYTES, image_mime

_active = None
_active_lock = Lock()


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("192.0.2.1", 80))  # Route selection only; sends no packet.
            return sock.getsockname()[0]
    except OSError:
        return "<IP-máy-tính>"


def _page():
    return '''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gửi ảnh cho bài học</title>
<style>body{font:18px/1.5 system-ui;background:#edf6ff;color:#143a58;margin:0;padding:22px}
main{max-width:570px;margin:auto;background:white;border-radius:18px;padding:22px;box-shadow:0 12px 32px #102e4a20}
label{display:block;margin:16px 0}input,select,button{font:inherit;padding:12px;width:100%;box-sizing:border-box}
button{background:#125887;color:white;border:0;border-radius:10px;cursor:pointer;margin-top:12px}
.hint{font-size:.85em;color:#496678}#status{min-height:2em}img{max-width:100%;max-height:45vh}</style></head>
<body><main><h1>Gửi ảnh cho tiết học</h1>
<p class="hint">Dùng điện thoại hoặc iPad của giáo viên. Ảnh chỉ vào hộp chờ, máy tính phải duyệt trước khi hiện trong bài giảng.</p>
<label>Mã ghép cặp <input id="code" autocomplete="off" maxlength="32" required></label>
<label>Thiết bị <select id="device"><option>Điện thoại</option><option>iPad</option></select></label>
<label>Chụp ảnh <input id="camera" type="file" accept="image/*" capture="environment"></label>
<label>Hoặc chọn ảnh có sẵn <input id="file" type="file" accept="image/*"></label>
<img id="preview" alt="Ảnh sắp gửi" hidden><button id="send" type="button">Gửi vào hộp chờ giáo viên</button>
<p id="status" role="status"></p></main><script>
const camera=document.getElementById('camera'),file=document.getElementById('file');
const preview=document.getElementById('preview'),status=document.getElementById('status');
let chosen=null;
function show(input){chosen=input.files[0]||null;if(chosen){preview.src=URL.createObjectURL(chosen);preview.hidden=false;}}
camera.addEventListener('change',()=>show(camera));file.addEventListener('change',()=>show(file));
async function jpeg(file){
  const img=new Image(),url=URL.createObjectURL(file);
  try{
    img.src=url;await img.decode();
    for(const edge of [1600,1200,900,700]){
      const scale=Math.min(1,edge/Math.max(img.naturalWidth,img.naturalHeight));
      const canvas=document.createElement('canvas');
      canvas.width=Math.max(1,Math.round(img.naturalWidth*scale));
      canvas.height=Math.max(1,Math.round(img.naturalHeight*scale));
      canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);
      for(const quality of [.82,.7,.55]){
        const encoded=canvas.toDataURL('image/jpeg',quality).split(',')[1];
        if(encoded.length<=600000) return encoded;
      }
    }
    throw Error('Ảnh quá lớn sau khi thu nhỏ. Hãy chụp lại gần nội dung hơn.');
  }finally{URL.revokeObjectURL(url);}
}
document.getElementById('send').addEventListener('click',async()=>{
  const code=document.getElementById('code').value.trim();
  if(!code||!chosen){status.textContent='Nhập mã và chọn ảnh trước khi gửi.';return;}
  const button=document.getElementById('send');button.disabled=true;status.textContent='Đang chuẩn bị ảnh…';
  try{
    const data=await jpeg(chosen);
    const response=await fetch('/upload',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({code,device:document.getElementById('device').value,data})});
    const result=await response.json();
    status.textContent=result.message;
  }catch(error){status.textContent='Chưa gửi được: '+error.message;}
  finally{button.disabled=false;}
});
</script></body></html>'''


class PhotoInbox:
    def __init__(self, owner_id, lesson_key, port):
        self.owner_id = owner_id
        self.lesson_key = lesson_key
        self.code = token_urlsafe(9)
        self.expires_at = monotonic() + 20 * 60
        self.pending = []
        self.attempts = {}
        self.lock = Lock()
        self.port = port
        inbox = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass  # Do not log pairing codes, lesson media, or browser headers.

            def _send(self, status, payload, *, kind="application/json"):
                raw = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", kind + "; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                if kind == "text/html":
                    self.send_header("Content-Security-Policy", "default-src 'none'; img-src blob: data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                if self.path != "/":
                    self._send(404, {"message": "Không tìm thấy."})
                    return
                self._send(200, _page().encode("utf-8"), kind="text/html")

            def do_POST(self):
                if self.path != "/upload" or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                    self._send(404, {"message": "Đường gửi không hợp lệ."})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if not 0 < length <= 800_000:
                        raise ValueError("Ảnh gửi vượt giới hạn.")
                    payload = json.loads(self.rfile.read(length))
                    if not isinstance(payload, dict):
                        raise ValueError("Dữ liệu không hợp lệ.")
                    ip = self.client_address[0]
                    with inbox.lock:
                        attempts = [t for t in inbox.attempts.get(ip, []) if monotonic() - t < 60]
                        if len(attempts) >= 5:
                            raise ValueError("Thử quá nhiều lần. Vui lòng chờ một phút.")
                        code = payload.get("code")
                        if (monotonic() > inbox.expires_at or not isinstance(code, str)
                                or not hmac.compare_digest(code, inbox.code)):
                            inbox.attempts[ip] = [*attempts, monotonic()]
                            raise ValueError("Mã ghép cặp sai hoặc đã hết hạn.")
                        if payload.get("device") not in ("Điện thoại", "iPad"):
                            raise ValueError("Thiết bị không hợp lệ.")
                        encoded = payload.get("data")
                        if not isinstance(encoded, str) or len(encoded) > 600_000:
                            raise ValueError("Ảnh vượt giới hạn.")
                        try:
                            data = b64decode(encoded, validate=True)
                        except Base64Error as exc:
                            raise ValueError("Ảnh không hợp lệ.") from exc
                        if not data or len(data) > MAX_PHOTO_BYTES or image_mime(data) != "image/jpeg":
                            raise ValueError("Ảnh cần là JPEG dưới 450 KB.")
                        if len(inbox.pending) >= 10:
                            raise ValueError("Hộp chờ đầy; duyệt ảnh trên máy tính trước.")
                        inbox.pending.append({"id": str(uuid4()), "device": payload["device"],
                                              "data": data, "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
                    self._send(200, {"message": "Đã gửi. Chờ giáo viên duyệt trên máy tính."})
                except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
                    self._send(400, {"message": str(exc)})

        self.server = ThreadingHTTPServer(("127.0.0.1" if port == 0 else "0.0.0.0", port), Handler)
        self.thread = Thread(target=self.server.serve_forever, name="lesson-phone-inbox", daemon=True)
        self.thread.start()

    def list_pending(self):
        with self.lock:
            return list(self.pending)

    def remove(self, photo_id):
        with self.lock:
            self.pending = [photo for photo in self.pending if photo["id"] != photo_id]

    def rotate_code(self):
        with self.lock:
            self.code = token_urlsafe(9)
            self.expires_at = monotonic() + 20 * 60
            self.attempts.clear()
            return self.code

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def start_inbox(owner_id, lesson_key):
    global _active
    if os.getenv("MATHTEACHER_LOCAL_PHONE_INBOX") != "1":
        raise ValueError("Cần bật MATHTEACHER_LOCAL_PHONE_INBOX=1 trên máy giáo viên.")
    with _active_lock:
        if _active is not None:
            if (_active.owner_id, _active.lesson_key) != (owner_id, lesson_key):
                raise ValueError("Hộp nhận đang dùng cho bài khác. Dừng hộp nhận trước.")
            return _active
        port = int(os.getenv("MATHTEACHER_PHONE_INBOX_PORT", "8515"))
        if not 1024 <= port <= 65535:
            raise ValueError("Cổng hộp nhận không hợp lệ.")
        _active = PhotoInbox(owner_id, lesson_key, port)
        return _active


def current_inbox(owner_id, lesson_key):
    with _active_lock:
        if _active is not None and (_active.owner_id, _active.lesson_key) == (owner_id, lesson_key):
            return _active
    return None


def stop_inbox(owner_id, lesson_key):
    global _active
    with _active_lock:
        if _active is None or (_active.owner_id, _active.lesson_key) != (owner_id, lesson_key):
            return
        active, _active = _active, None
    active.close()


def stop_owner_inbox(owner_id):
    global _active
    with _active_lock:
        if _active is None or _active.owner_id != owner_id:
            return
        active, _active = _active, None
    active.close()
