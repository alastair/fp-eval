# This file is part of audioread.
# Copyright 2011, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Command-line tool to decode audio files to WAV files."""
import audioread
import sys
import os
import wave
import contextlib

def decode(filename):
    filename = os.path.abspath(os.path.expanduser(filename))
    if not os.path.exists(filename):
        print >>sys.stderr, "File not found."
        sys.exit(1)

    try:
        with audioread.audio_open(filename) as f:
            print >>sys.stderr, \
                'Input file: %i channels at %i Hz; %.1f seconds.' % \
                (f.channels, f.samplerate, f.duration)
            print >>sys.stderr, 'Backend:', \
                str(type(f).__module__).split('.')[1]

            with contextlib.closing(wave.open(filename + '.wav', 'w')) as of:
                of.setnchannels(f.channels)
                of.setframerate(f.samplerate)
                of.setsampwidth(2)

                for buf in f:
                    of.writeframes(buf)

    except audioread.DecodeError:
        print >>sys.stderr, "File could not be decoded."
        sys.exit(1)

if __name__ == '__main__':
    decode(sys.argv[1])
