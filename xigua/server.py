"""A small development server with optional rebuild-on-change."""

from __future__ import annotations

import functools
import threading
from collections.abc import Callable, Iterable
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .errors import XiguaError


class SiteRequestHandler(SimpleHTTPRequestHandler):
    """Serve ``index.html`` for pretty URLs and a custom 404 page."""

    def send_head(self):  # type: ignore[override]
        path = Path(self.translate_path(self.path))
        if not path.exists() and not path.suffix:
            index = path / "index.html"
            if index.is_file():
                self.path = self.path.rstrip("/") + "/"
        return super().send_head()

    def send_error(self, code, message=None, explain=None):  # type: ignore[override]
        if code == 404:
            not_found = Path(self.directory) / "404.html"
            if not_found.is_file():
                body = not_found.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return
        super().send_error(code, message, explain)

    def log_message(self, format, *args):  # type: ignore[override]
        # Keep the terminal readable; errors are still visible.
        print(f"  {self.address_string()} {format % args}")


def _snapshot(paths: Iterable[Path]) -> dict[str, int]:
    result: dict[str, int] = {}
    for path in paths:
        if path.is_file():
            try:
                result[str(path)] = path.stat().st_mtime_ns
            except OSError:
                pass
            continue
        if not path.is_dir():
            continue
        for file in path.rglob("*"):
            if not file.is_file():
                continue
            if any(part in {"__pycache__", ".git", ".venv", "dist"} for part in file.parts):
                continue
            try:
                result[str(file)] = file.stat().st_mtime_ns
            except OSError:
                pass
    return result


def _watch(paths: Iterable[Path], rebuild: Callable[[], None], stop: threading.Event) -> None:
    last = _snapshot(paths)
    while not stop.wait(1.0):
        current = _snapshot(paths)
        if current == last:
            continue
        last = current
        try:
            rebuild()
            print("↻ 检测到改动，已重新生成。刷新浏览器即可。")
        except Exception as exc:  # noqa: BLE001 - a bad rebuild must not kill the preview server
            print(f"✗ 重新生成失败：{exc}")


def serve(
    directory: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    watch_paths: Iterable[Path] = (),
    rebuild: Callable[[], None] | None = None,
) -> None:
    handler = functools.partial(SiteRequestHandler, directory=str(directory))
    try:
        httpd = ThreadingHTTPServer((host, port), handler)
    except OSError as exc:
        raise XiguaError(f"无法监听 {host}:{port}：{exc}") from exc

    stop = threading.Event()
    if watch_paths and rebuild is not None:
        thread = threading.Thread(target=_watch, args=(watch_paths, rebuild, stop), daemon=True)
        thread.start()

    display_host = "localhost" if host in {"0.0.0.0", "::"} else host
    print(f"预览：http://{display_host}:{port}/")
    print("按 Ctrl+C 停止。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        stop.set()
        httpd.server_close()
