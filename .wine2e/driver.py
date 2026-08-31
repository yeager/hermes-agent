"""A/B driver for PR salvage of #97758 — Bot Mode query-file stdin inherit.

Runs tools.bot_mode_dm._run_delivery (query-file path) with a trivial python
child while THIS process's stdin is an invalid/closed handle (launched from
Git Bash after `exec 0<&-`). On main (no stdin=DEVNULL) the child spawn on
native Windows fails with OSError WinError 6 before it starts. With the fix
it returns rc 0.

Usage: python driver.py expect-fail | expect-pass
"""
import os
import sys
import tempfile

sys.path.insert(0, os.getcwd())

from tools import bot_mode_dm  # noqa: E402

mode = sys.argv[1]

fd, dm_file = tempfile.mkstemp(suffix=".txt")
os.write(fd, b"live A/B message")
os.close(fd)

argv = [sys.executable, "-c", "import sys; sys.stdout.write('child-ok')"]

try:
    rc = bot_mode_dm._run_delivery(argv, dm_file, stdin_file=False)
except OSError as exc:
    print(f"OSERROR winerror={getattr(exc, 'winerror', None)} {exc}")
    if mode == "expect-fail":
        print("REPRO-FIRED: inherited-stdin spawn failure reproduced")
        sys.exit(0)
    print("FIX-LEG-FAILED: OSError still raised with fix applied")
    sys.exit(1)

print(f"rc={rc}")
if mode == "expect-pass":
    sys.exit(0 if rc == 0 else 1)
# expect-fail leg reaching here means the symptom did NOT fire
print("REPRO-DID-NOT-FIRE: main path succeeded; premise not reproduced")
sys.exit(1)
