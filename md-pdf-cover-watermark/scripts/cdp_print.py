# -*- coding: utf-8 -*-
"""
极简 Chrome DevTools Protocol 客户端（纯标准库，无第三方依赖）。

用途：驱动本机 Chrome 打印 PDF（支持 printBackground / 自定义页脚页码 /
页边距 / pageRanges），能力等价于 puppeteer / playwright 的 page.pdf()。
"""
import base64
import itertools
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


class CDPError(RuntimeError):
    pass


class _WS:
    """最小 WebSocket 客户端（文本帧 + 分片 + ping/pong）。"""

    def __init__(self, url: str, timeout: float = 180.0):
        assert url.startswith("ws://"), url
        rest = url[5:]
        hostport, _, path = rest.partition("/")
        path = "/" + path
        host, _, port = hostport.partition(":")
        self.host = host
        self.port = int(port or 80)
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._buf = b""
        self._handshake(path)

    # ---------- 底层读写 ----------
    def _read_exact(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            chunk = self.sock.recv(min(65536, n - len(out)))
            if not chunk:
                raise CDPError("连接被对端关闭")
            out.extend(chunk)
        return bytes(out)

    def _handshake(self, path: str):
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        head = b""
        while b"\r\n\r\n" not in head:
            head += self.sock.recv(1)
        if b"101" not in head.split(b"\r\n")[0]:
            raise CDPError("WebSocket 握手失败: " + head.decode(errors="replace"))

    def _send(self, payload: bytes, opcode: int = 0x1):
        header = bytearray()
        header.append(0x80 | opcode)  # FIN + opcode
        mask = os.urandom(4)
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        header += mask
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + masked)

    def _recv_message(self) -> str:
        """读取一条完整文本消息（自动合并分片、自动回 pong）。"""
        data = bytearray()
        while True:
            b0, b1 = self._read_exact(2)
            fin = b0 & 0x80
            opcode = b0 & 0x0F
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read_exact(8))[0]
            payload = self._read_exact(length) if length else b""

            if opcode == 0x9:  # ping
                self._send(payload, opcode=0xA)
                continue
            if opcode == 0xA:  # pong
                continue
            if opcode == 0x8:  # close
                raise CDPError("服务端关闭了 WebSocket")
            if opcode in (0x1, 0x2, 0x0):
                data.extend(payload)
                if fin:
                    return data.decode("utf-8", errors="replace")

    def close(self):
        try:
            self._send(b"", opcode=0x8)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass


class ChromeCDP:
    def __init__(self, chrome_path: str, timeout: float = 180.0):
        self.chrome_path = chrome_path
        self.timeout = timeout
        self.user_data_dir = tempfile.mkdtemp(prefix="cdp-profile-")
        self.proc = None
        self.ws = None
        self._ids = itertools.count(1)
        self._session = None
        self._pending = {}
        self._start()

    # ---------- 生命周期 ----------
    def _start(self):
        args = [
            self.chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--disable-background-networking",
            "--allow-file-access-from-files",
            "--remote-debugging-port=0",
            f"--user-data-dir={self.user_data_dir}",
            "about:blank",
        ]
        self.proc = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        port_file = Path(self.user_data_dir) / "DevToolsActivePort"
        port, path = None, None
        deadline = time.time() + 60
        while time.time() < deadline:
            if port_file.exists():
                try:
                    lines = port_file.read_text(encoding="utf-8").splitlines()
                    if len(lines) >= 2:
                        port, path = int(lines[0]), lines[1].strip()
                        break
                except Exception:
                    pass
            if self.proc.poll() is not None:
                raise CDPError("Chrome 进程已退出")
            time.sleep(0.2)
        if port is None:
            raise CDPError("未能获取 Chrome 调试端口")

        ws_url = f"ws://127.0.0.1:{port}{path}"
        # 等接口可用
        for _ in range(60):
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/json/version", timeout=3
                ).read()
                break
            except Exception:
                time.sleep(0.3)
        self.ws = _WS(ws_url, timeout=self.timeout)

    def close(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=10)
                except Exception:
                    self.proc.kill()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # ---------- 协议 ----------
    def call(self, method: str, params=None, session: bool = True, timeout=None):
        msg_id = next(self._ids)
        payload = {"id": msg_id, "method": method, "params": params or {}}
        if session and self._session:
            payload["sessionId"] = self._session
        self.ws._send(json.dumps(payload).encode("utf-8"))

        limit = time.time() + (timeout or self.timeout)
        while True:
            if time.time() > limit:
                raise CDPError(f"命令超时: {method}")
            raw = self.ws._recv_message()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise CDPError(f"{method} 失败: {msg['error']}")
                return msg.get("result", {})
            # 其他事件（如 loadEventFired）忽略

    def open_page(self, url: str) -> str:
        res = self.call(
            "Target.createTarget", {"url": url}, session=False
        )
        target_id = res["targetId"]
        att = self.call(
            "Target.attachToTarget",
            {"targetId": target_id, "flatten": True},
            session=False,
        )
        self._session = att["sessionId"]
        self.call("Page.enable")
        self.call("Runtime.enable")
        return target_id

    def evaluate(self, expression: str, timeout=None):
        res = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
            timeout=timeout,
        )
        if res.get("exceptionDetails"):
            return None
        return res.get("result", {}).get("value")

    def wait_for(self, expression: str, timeout: float = 90.0, interval: float = 0.4):
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                last = self.evaluate(expression, timeout=30)
            except Exception:
                last = None
            if last:
                return last
            time.sleep(interval)
        return last

    def print_pdf(
        self,
        out_path: str,
        landscape: bool = False,
        print_background: bool = True,
        paper_w: float = 8.27,
        paper_h: float = 11.69,
        margins=(0.0, 0.0, 0.0, 0.0),  # top, right, bottom, left (inch)
        header: str = "",
        footer: str = "",
        page_ranges: str = "",
        scale: float = 1.0,
    ):
        params = {
            "landscape": landscape,
            "displayHeaderFooter": bool(header or footer),
            "printBackground": print_background,
            "scale": scale,
            "paperWidth": paper_w,
            "paperHeight": paper_h,
            "marginTop": margins[0],
            "marginRight": margins[1],
            "marginBottom": margins[2],
            "marginLeft": margins[3],
            "preferCSSPageSize": False,
            "transferMode": "ReturnAsBase64",
        }
        if header or footer:
            # 必须同时给出 headerTemplate，否则 Chromium 会打印默认页眉（日期 + 标题）
            params["headerTemplate"] = header or "<div></div>"
            params["footerTemplate"] = footer or "<div></div>"
        if page_ranges:
            params["pageRanges"] = page_ranges

        res = self.call("Page.printToPDF", params, timeout=600)
        data = base64.b64decode(res["data"])
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_bytes(data)
        return len(data)
