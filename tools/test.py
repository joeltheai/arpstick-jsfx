#!/usr/bin/env python3
"""Assert engine state and emitted MIDI using the real EEL2 interpreter."""
import re
import subprocess
import sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
binary=sys.argv[1]
run=subprocess.run([sys.executable,str(root/'tools/validate.py'),binary,'--driver',str(root/'tools/assertions.eel')],capture_output=True,text=True)
print(run.stdout,end=''); print(run.stderr,end='',file=sys.stderr)
if run.returncode: sys.exit(run.returncode)
events=[tuple(map(int,m)) for m in re.findall(r'MIDI \d+: st=(\d+) d1=(\d+) d2=(\d+) offs=(\d+)\.0',run.stdout)]
expected=[(144,48,100,20),(144,51,100,20),(144,55,100,20),(128,48,0,45),(128,51,0,45),(128,55,0,45)]
assert events[:6]==expected, f'Timestamped chord output mismatch: {events[:6]}'
assert events[6]==(144,60,91,30), f'Timestamped arp output mismatch: {events[6]}'
print('PASS: emitted chord and arp MIDI pitches, velocities, and sample offsets')
