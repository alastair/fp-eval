#!/usr/bin/python

import acoustid
import sys
import audioread

with audioread.audio_open(sys.argv[1]) as f:
    duration = int(f.duration)
    fp = acoustid.fingerprint(f.samplerate, f.channels, iter(f))

user_key = "VUz6PQRB"
app_key = "k3QqfYqe"

acoustid.set_base_url("http://132.206.14.136/ws/v2/")

print acoustid.lookup(app_key, fp, duration)
