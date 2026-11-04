from __future__ import annotations

import json
import os
import stat
import time
from pathlib import Path
from typing import Callable, TypeVar

from .errors import SecHttpError

try:
    import msvcrt
except ImportError:  # pragma: no cover - Windows is the accepted P11 runtime.
    msvcrt = None  # type: ignore[assignment]


_RATE_REASON = "P11_RATE_LIMIT_SCOPE_UNSAFE"
_SCHEMA = "p11-sec-rate-gate-v1"
_INTERVAL_NS = 125_000_000
_POLL_NS = 25_000_000
_LOCK_TIMEOUT_NS = 5_000_000_000
_T = TypeVar("_T")


def _unsafe(message: str) -> SecHttpError:
    return SecHttpError(_RATE_REASON, message)


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _is_reparse(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    attrs = getattr(info, "st_file_attributes", 0)
    return bool(attrs & flag)


def _require_regular_or_missing(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or _is_reparse(path):
        raise _unsafe(f"unsafe rate-gate path: {path.name}")
    try:
        mode = path.stat().st_mode
    except OSError as exc:
        raise _unsafe(f"cannot inspect rate-gate path: {path.name}") from exc
    if not stat.S_ISREG(mode):
        raise _unsafe(f"rate-gate path is not a regular file: {path.name}")


def _prepare_rate_dir(project_root: Path) -> Path:
    resolved = project_root.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("project_root must be an existing directory")
    current = resolved
    for name in ("workspace", "sec", "rate"):
        nxt = current / name
        if nxt.exists() or nxt.is_symlink():
            if nxt.is_symlink() or _is_reparse(nxt) or not nxt.is_dir():
                raise _unsafe(f"unsafe rate-gate directory: {name}")
        else:
            try:
                nxt.mkdir()
            except FileExistsError:
                pass
            except OSError as exc:
                raise _unsafe(f"cannot create rate-gate directory: {name}") from exc
            if nxt.is_symlink() or _is_reparse(nxt) or not nxt.is_dir():
                raise _unsafe(f"unsafe rate-gate directory: {name}")
        try:
            actual = nxt.resolve(strict=True)
        except OSError as exc:
            raise _unsafe(f"cannot resolve rate-gate directory: {name}") from exc
        if not _inside(resolved, actual):
            raise _unsafe("rate-gate directory escapes project_root")
        current = actual
    return current


class SecRateGate:
    def __init__(self, project_root: Path) -> None:
        if msvcrt is None:
            raise _unsafe("P11 SEC rate gate requires Windows byte-range locking")
        self.project_root = project_root.expanduser().resolve(strict=True)
        if not self.project_root.is_dir():
            raise ValueError("project_root must be an existing directory")
        self.rate_dir = _prepare_rate_dir(self.project_root)
        self.lock_path = self.rate_dir / "sec-rate-gate.lock"
        self.state_path = self.rate_dir / "sec-rate-gate-v1.json"
        self.temp_path = self.rate_dir / "sec-rate-gate-v1.json.tmp"
        for path in (self.lock_path, self.state_path, self.temp_path):
            _require_regular_or_missing(path)
        self._ensure_lock_file()

    def _ensure_lock_file(self) -> None:
        try:
            if not self.lock_path.exists():
                try:
                    with self.lock_path.open("xb") as handle:
                        handle.write(b"0")
                        handle.flush()
                        os.fsync(handle.fileno())
                except FileExistsError:
                    pass
            _require_regular_or_missing(self.lock_path)
            if self.lock_path.stat().st_size < 1:
                with self.lock_path.open("r+b") as handle:
                    handle.write(b"0")
                    handle.flush()
                    os.fsync(handle.fileno())
        except SecHttpError:
            raise
        except OSError as exc:
            raise _unsafe("cannot prepare rate-gate lock file") from exc

    def _acquire(self, deadline_ns: int) -> object:
        _require_regular_or_missing(self.lock_path)
        handle = self.lock_path.open("r+b", buffering=0)
        started = time.monotonic_ns()
        while True:
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return handle
            except OSError:
                now = time.monotonic_ns()
                if now >= deadline_ns:
                    handle.close()
                    raise SecHttpError("P11_HTTP_FAILED", "logical fetch deadline exceeded while waiting for SEC rate gate")
                if now - started >= _LOCK_TIMEOUT_NS:
                    handle.close()
                    raise _unsafe("cannot acquire shared SEC rate gate within 5 seconds")
                self._sleep_until(min(now + _POLL_NS, deadline_ns), deadline_ns)

    @staticmethod
    def _release(handle: object) -> None:
        try:
            handle.seek(0)  # type: ignore[attr-defined]
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
        except OSError as exc:
            raise _unsafe("cannot release shared SEC rate gate") from exc
        finally:
            handle.close()  # type: ignore[attr-defined]

    @staticmethod
    def _sleep_until(target_ns: int, deadline_ns: int) -> None:
        while True:
            now = time.monotonic_ns()
            if now >= target_ns:
                return
            if now >= deadline_ns:
                raise SecHttpError("P11_HTTP_FAILED", "logical fetch deadline exceeded")
            remaining = min(target_ns, deadline_ns) - now
            time.sleep(min(remaining / 1_000_000_000, 0.005))

    def _read_state(self) -> dict[str, object] | None:
        _require_regular_or_missing(self.state_path)
        if not self.state_path.exists():
            return None
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        if set(raw) != {"last_start_monotonic_ns", "last_start_unix_ns", "phase", "schema_version"}:
            return None
        if raw.get("schema_version") != _SCHEMA or raw.get("phase") not in {"READY", "RESERVED"}:
            return None
        for key in ("last_start_monotonic_ns", "last_start_unix_ns"):
            value = raw.get(key)
            if type(value) is not int or value < 0:
                return None
        return raw

    def _write_state(self, phase: str, monotonic_ns: int, unix_ns: int) -> None:
        for path in (self.state_path, self.temp_path):
            _require_regular_or_missing(path)
        payload = {
            "last_start_monotonic_ns": monotonic_ns,
            "last_start_unix_ns": unix_ns,
            "phase": phase,
            "schema_version": _SCHEMA,
        }
        data = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        try:
            with self.temp_path.open("wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(self.temp_path, self.state_path)
        except OSError as exc:
            raise _unsafe("cannot commit shared SEC rate-gate state") from exc

    def emit(self, send: Callable[[], _T], on_start: Callable[[], None], deadline_ns: int) -> _T:
        handle = self._acquire(deadline_ns)
        send_error: BaseException | None = None
        result: _T | None = None
        try:
            state = self._read_state()
            now = time.monotonic_ns()
            if state is None or state["phase"] == "RESERVED" or int(state["last_start_monotonic_ns"]) > now:
                self._sleep_until(now + _INTERVAL_NS, deadline_ns)
            else:
                elapsed = now - int(state["last_start_monotonic_ns"])
                if elapsed < _INTERVAL_NS:
                    self._sleep_until(now + (_INTERVAL_NS - elapsed), deadline_ns)
            self._write_state("RESERVED", time.monotonic_ns(), time.time_ns())
            on_start()
            try:
                result = send()
            except BaseException as exc:  # preserve the transport failure after crash-safe READY.
                send_error = exc
            ready_mono = time.monotonic_ns()
            self._write_state("READY", ready_mono, time.time_ns())
        finally:
            self._release(handle)
        if send_error is not None:
            raise send_error
        return result  # type: ignore[return-value]