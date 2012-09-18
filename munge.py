
munge_classes = {}
import os
import tempfile
import shutil
import subprocess

import log

class Munge(object):
    def extension(self):
        """Get the preferred extension for this transform"""
        return None

    def perform(self, fromfile):
        if not fromfile or not os.path.exists(fromfile):
            log.debug("Tried to munge %s but it's not there" % fromfile)
            return None
        prefext = self.extension()
        if prefext:
            ext = prefext
        else:
            ext = os.path.splitext(fromfile)[1]
        if not ext.startswith("."):
            ext = ".%s" % ext
        (handle, tofile) = tempfile.mkstemp("%s" % ext)
        os.close(handle)
        command = self.getExecCommand(fromfile, tofile)
        if command is not None:
            if isinstance(command, tuple):
                log.debug("performing command")
                log.debug(" | ".join([" ".join(c) for c in command]))
                lastc = None
                for c in command:
                    stdin = lastc.stdout if lastc else None
                    com = subprocess.Popen(c, stdin=stdin, stdout=subprocess.PIPE)
                    if lastc:
                        lastc.stdout.close()
                    lastc = com
                lastc.communicate()
            else:
                log.debug("performing command")
                log.debug(" ".join(command))
                p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.communicate()
        else:
            shutil.copyfile(fromfile, tofile)
        return tofile

    def getExecCommand(self, fromfile, tofile):
        raise NotImplementedError("must implement getExecCommand in subclass")

class NoMunge(Munge):
    """ No Munge """
    def getExecCommand(self, fromfile, tofile):
        return None
munge_classes["nomunge"] = NoMunge

class WavConvert(Munge):
    """ Convert anything to wav"""
    def extension(self):
        return "wav"
    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, "--encoding", "signed-integer", tofile]
        return command
munge_classes["wav"] = WavConvert

class Chop(Munge):
    """ limit the start time or length """

    def __init__(self):
        raise NotImplementedError("Implement a subclass that sets start & duration")

    def getExecCommand(self, fromfile, tofile):
        start = self.start
        dur = self.duration
        command = ["ffmpeg", "-i", fromfile, "-b", "128k", "-y"]
        if start:
            command.extend(["-ss", str(start)])
        if dur:
            command.extend(["-t", str(dur)])
        command.append(tofile)
        return command

class Chop30(Chop):
    def __init__(self): pass
    start = None
    duration = 30
class Chop35(Chop):
    def __init__(self): pass
    start = None
    duration = 35
class Chop15(Chop):
    def __init__(self): pass
    start = None
    duration = 15
class Chop8(Chop):
    def __init__(self): pass
    start = None
    duration = 8
class Start30(Chop):
    def __init__(self): pass
    start = 30
    duration = None
class Start60(Chop):
    def __init__(self): pass
    start = 60
    duration = None
munge_classes["chop8"] = Chop8
munge_classes["chop15"] = Chop15
munge_classes["chop30"] = Chop30
munge_classes["chop35"] = Chop35
munge_classes["start30"] = Start30
munge_classes["start60"] = Start60

class Chop3030(Chop):
    def __init__(self): pass
    start = 30
    duration = 30
class Chop3015(Chop):
    def __init__(self): pass
    start = 30
    duration = 15
class Chop308(Chop):
    def __init__(self): pass
    start = 30
    duration = 8
munge_classes["30chop8"] = Chop308
munge_classes["30chop15"] = Chop3015
munge_classes["30chop30"] = Chop3030

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a bitrate")
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-b", "%sk" % self.bitrate, "-y", tofile]
        return command

class Bitrate64(Bitrate):
    def __init__(self): pass
    bitrate = 64
class Bitrate96(Bitrate):
    def __init__(self): pass
    bitrate = 96
munge_classes["bitrate64"] = Bitrate64
munge_classes["bitrate96"] = Bitrate96

class Samplerate22(Munge):
    """ Change to 22k samplerate"""
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-ar", "22050", "-y", tofile]
        return command
munge_classes["sample22"] = Samplerate22

class Mono(Munge):
    """ Change from stereo to mono """
    def getExecCommand(self, fromfile, tofile):
        command = ["ffmpeg", "-i", fromfile, "-ac", "1", "-y", tofile]
        return command
munge_classes["mono"] = Mono

class GSM(Munge):
    """ GSM Reduction """
    def extension(self):
        return "wav"
    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, "-r", "8000", "-c", "1", "--encoding", "gsm-full-rate", tofile]
        return command
munge_classes["gsm"] = GSM

class SoundMix(Munge):
    """ Mix in some other noises """
    def extension(self):
        return "wav"
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a noisefile")

    def getExecCommand(self, fromfile, tofile):
        from chromaprint_support import audioread
        with audioread.audio_open(fromfile) as f:
            if f.samplerate == 44100:
                return ["sox", "-m", fromfile, self.mixfile, tofile, "trim", "0", "35"]
            else:
                c1 = ["sox", fromfile, "-t", "sox", "-", "trim", "0", "35", "rate", "44100"]
                c2 = ["sox", "-m", "-t", "sox", "-", self.mixfile, tofile]
                return (c1, c2)
        # sox Memory\ Pain.mp3 -t sox - trim 0 35 rate 44100 |sox -m -t sox - sounds/pink-20.wav y.wav

class PinkNoiseMix10(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/pink-norm.wav"
class CarNoiseMix10(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/car-norm.wav"
class PersonNoiseMix10(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/babble-norm.wav"

class PinkNoiseMix20(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/pink-10.wav"
class CarNoiseMix20(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/car2-10.wav"
class PersonNoiseMix20(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/babble-10.wav"

class PinkNoiseMix30(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/pink-20.wav"
class CarNoiseMix30(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/car2-20.wav"
class PersonNoiseMix30(SoundMix):
    def __init__(self): pass
    mixfile = "sounds/babble-20.wav"

munge_classes["pink10"] = PinkNoiseMix30
munge_classes["car10"] = CarNoiseMix30
munge_classes["babble10"] = PersonNoiseMix30
munge_classes["pink20"] = PinkNoiseMix30
munge_classes["car20"] = CarNoiseMix30
munge_classes["babble20"] = PersonNoiseMix30
munge_classes["pink30"] = PinkNoiseMix30
munge_classes["car30"] = CarNoiseMix30
munge_classes["babble30"] = PersonNoiseMix30

class Volume(Munge):
    """ Change the volume """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a volume")

    def getExecCommand(self, fromfile, tofile):
        command = ["sox", "-v", "%s" % self.volume, fromfile, tofile]
        return command

class Volume50(Volume):
    def __init__(self): pass
    volume = 0.5
class Volume80(Volume):
    def __init__(self): pass
    volume = 0.8
class Volume120(Volume):
    def __init__(self): pass
    volume = 1.2
munge_classes["volume50"] = Volume50
munge_classes["volume80"] = Volume80
munge_classes["volume120"] = Volume120

class FMFilter(Munge):
    """ Similar bandwidth and filters as what comes out of
    the radio """
    def extension(self):
        return "wav"
    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, tofile, "gain", "-3", ":", "sinc", "8000-", "29", "100", ":", "mcompand",
                   "0.005,0.1 -47,-40,-34,-34,-17,-33", "100",
                   "0.003,0.05 -47,-40,-34,-34,-17,-33", "400",
                   "0.000625,0.0125 -47,-40,-34,-34,-15,-33", "1600",
                   "0.0001,0.025 -47,-40,-34,-34,-31,-31,-0,-30", "6400",
                   "0,0.025 -38,-31,-28,-28,-0,-25",
                   "gain", "15", "highpass", "22", ":", "highpass", "22", ":", "sinc", "-n", "255", "-b", "16", "-17500",
                   "gain", "9", "lowpass", "-1", "17801"
                ]
        return command
munge_classes["radio"] = FMFilter

class Speed(Munge):
    """ Change the speed and pitch """
    def __init__(self):
        raise NotImplementedException("Run a subclass that supplies a speed ratio")

    def getExecCommand(self, fromfile, tofile):
        command = ["sox", fromfile, tofile, "speed", "%s" % self.speed]
        return command

class SpeedUp5(Speed):
    def __init__(self): pass
    speed = 1.05
class SpeedDown5(Speed):
    def __init__(self): pass
    speed = 0.95
class SpeedUp25(Speed):
    def __init__(self): pass
    speed = 1.025
class SpeedDown25(Speed):
    def __init__(self): pass
    speed = 0.975
munge_classes["speedup5"] = SpeedUp5
munge_classes["speeddown5"] = SpeedDown5
munge_classes["speedup25"] = SpeedUp25
munge_classes["speeddown25"] = SpeedDown25
