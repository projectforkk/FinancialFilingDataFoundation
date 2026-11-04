from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from financial_filing_data_foundation.sec import SecHttpError
from financial_filing_data_foundation.sec.rate_gate import SecRateGate
from financial_filing_data_foundation.sec import rate_gate as rate_mod


def test_p11d_42_two_process_shared_gate_spacing_and_window_limit(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    worker = tmp_path / "worker.py"
    worker.write_text(
        "from pathlib import Path\n"
        "import sys,time\n"
        "from financial_filing_data_foundation.sec.rate_gate import SecRateGate\n"
        "root=Path(sys.argv[1]); out=Path(sys.argv[2])\n"
        "gate=SecRateGate(root)\n"
        "seen=[]\n"
        "gate.emit(lambda: None, lambda: seen.append(time.monotonic_ns()), time.monotonic_ns()+10_000_000_000)\n"
        "out.write_text(str(seen[0]),encoding='ascii')\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parents[3] / "src")
    a = tmp_path / "a.txt"; b = tmp_path / "b.txt"
    p1 = subprocess.Popen([sys.executable, str(worker), str(root), str(a)], env=env)
    p2 = subprocess.Popen([sys.executable, str(worker), str(root), str(b)], env=env)
    assert p1.wait(timeout=15) == 0 and p2.wait(timeout=15) == 0
    starts = sorted([int(a.read_text()), int(b.read_text())])
    assert starts[1] - starts[0] >= 125_000_000
    assert len(starts) <= 8


def test_p11d_43_crash_holder_os_lock_release_recovery(tmp_path: Path) -> None:
    root = tmp_path / "project"; root.mkdir()
    gate = SecRateGate(root)
    locker = tmp_path / "locker.py"
    locker.write_text(
        "import msvcrt,os,sys\n"
        "p=sys.argv[1]\n"
        "h=open(p,'r+b',buffering=0); h.seek(0); msvcrt.locking(h.fileno(),msvcrt.LK_NBLCK,1); os._exit(7)\n",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(locker), str(gate.lock_path)], check=False)
    assert proc.returncode == 7
    seen=[]
    gate.emit(lambda: None, lambda: seen.append(True), time.monotonic_ns()+5_000_000_000)
    assert seen == [True]


@pytest.mark.parametrize("state", [None, b"not-json", b'{"phase":"RESERVED","schema_version":"p11-sec-rate-gate-v1","last_start_monotonic_ns":1,"last_start_unix_ns":1}\n'])
def test_p11d_44_missing_malformed_reserved_state_full_125ms_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, state: bytes | None) -> None:
    root=tmp_path/"project"; root.mkdir(); gate=SecRateGate(root)
    if state is None:
        if gate.state_path.exists(): gate.state_path.unlink()
    else:
        gate.state_path.write_bytes(state)
    waits=[]
    original=gate._sleep_until
    monkeypatch.setattr(gate,"_sleep_until",lambda target,deadline: waits.append(target-time.monotonic_ns()))
    gate.emit(lambda: None, lambda: None, time.monotonic_ns()+5_000_000_000)
    assert waits and waits[0] >= 120_000_000


def test_p11d_45_delayed_sender_cannot_collapse_spacing(tmp_path: Path) -> None:
    root=tmp_path/"project"; root.mkdir(); gate=SecRateGate(root)
    starts=[]
    def slow_send(): time.sleep(0.05)
    gate.emit(slow_send,lambda:starts.append(time.monotonic_ns()),time.monotonic_ns()+5_000_000_000)
    gate.emit(lambda:None,lambda:starts.append(time.monotonic_ns()),time.monotonic_ns()+5_000_000_000)
    assert len(starts)==2
    assert starts[1]-starts[0] >= 170_000_000


def test_p11d_46_lock_acquisition_over_5s_maps_scope_unsafe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root=tmp_path/"project"; root.mkdir(); gate=SecRateGate(root)
    calls={"n":0}
    def fake_locking(*args,**kwargs):
        raise OSError("busy")
    base=1_000_000_000
    def fake_mono():
        calls["n"]+=1
        return base + calls["n"]*1_000_000_000
    monkeypatch.setattr(rate_mod.msvcrt,"locking",fake_locking)
    monkeypatch.setattr(rate_mod.time,"monotonic_ns",fake_mono)
    monkeypatch.setattr(gate,"_sleep_until",lambda *a,**k:None)
    with pytest.raises(SecHttpError) as exc:
        gate._acquire(base+20_000_000_000)
    assert exc.value.reason_code=="P11_RATE_LIMIT_SCOPE_UNSAFE"
