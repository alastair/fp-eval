
munge_classes = {}

"""
    if decoder == 'mpg123':
        cmd = ["mpg123", "-q", "-w", target]
        if start > 0: cmd.extend(["-k", str(int(start*44100 / 1152))])
        if duration > 0: cmd.extend(["-n", str(int(duration*44100 / 1152))])
        if volume > 0: cmd.extend(["-f", str(int( (float(volume)/100.0) * 32768.0 ))])
        if downsample_to_22: cmd.extend(["-2"])
        if channels < 2: cmd.extend(["-0"])
        if speed_up: cmd.extend(["-d", "2"])
        if slow_down: cmd.extend(["-h", "2"])
        cmd.append(file)
    elif decoder =="ffmpeg":
        cmd = ["ffmpeg", "-i", file, "-f", "wav", "-y"]
        if start > 0: cmd.extend(["-ss", str(start)])
        if duration > 0: cmd.extend(["-t", str(duration)])
        #if volume > 0: cmd.extend(["-vol", str(int( (float(volume)/100.0) * 32768.0 ))]
        # -vol is undocumented, but apparently 256 is "normal"
        if downsample_to_22: cmd.extend(["-ar", "22050"])
        if channels < 2: cmd.extend(["-ac", "1"])
        #if speed_up: cmd.extend(["-d", "2"])
        #if slow_down: cmd.extend(["-h", "2"])
        cmd.append(target)
    elif decoder == "mad":
        cmd = ["madplay", "-Q", "-o", "wave:%s" % target]
        if start > 0: cmd.extend(["-s", str(start)])
        if duration > 0: cmd.extend(["-t", str(duration)])
        #if volume > 0: cmd.extend(["-f", str(int( (float(volume)/100.0) * 32768.0 ))]
        # --attenuate or --amplify takes in dB -> need to convert % to db
        if downsample_to_22: cmd.extend("--downsample")
        if channels < 2: cmd.extend(["-m"])
        #if speed_up: cmd.extend(["-d", "2"])
        #if slow_down: cmd.extend(["-h", "2"])
        cmd.append(file)
    elif decoder == "sox":
        cmd = ["sox", file, target]
        if start < 0: start = 0
        cmd.extend(["trim", str(start)])
        if duration > 0: cmd.extend([str(duration)])
        #if volume > 0: cmd.extend()
        if downsample_to_22: cmd.extend(["rate", "22050"])
        if channels < 2: cmd.extend(["channels", "1"])
        if speed_up: cmd.extend(["speed", "2.0"])
        if slow_down: cmd.extend(["speed", "0.5"])
"""

class Munge(object):
    def perform(self, fromfile, tofile):
        command = self.getExecCommand(fromfile, tofile)
        if command is not None:
            pass

    def getExecCommand(self, fromfile, tofile):
        raise NotImplementedError("must implement getExecCommand in subclass")

class NoMunge(Munge):
    """ No Munge """
    def getExecCommand(self, fromfile, tofile):
        return None
munge_classes["nomunge"] = NoMunge

class Chop(Munge):
    """ limit the start time or length """
    def getExecCommand(self, fromfile, tofile):
        start = self.start
        dur = self.duration

class Chop60(Chop):
    start = None
    duration = 60
class Chop30(Chop):
    start = None
    duration = 30
class Start30(Chop):
    start = 30
    duration = None
class Start60(Chop):
    start = 60
    duration = None
munge_classes["chop60"] = Chop60
munge_classes["chop60"] = Chop60
munge_classes["start30"] = Start30
munge_classes["start60"] = Start60

class Bitrate(Munge):
    """ Re-encode as MP3 with a different bitrate """
    def getExecCommand(self, fromfile, tofile):
        return self.bitrate
class Bitrate64(Bitrate):
    bitrate = 64
class Bitrate96(Bitrate):
    bitrate = 96
munge_classes["bitrate64"] = Bitrate64
munge_classes["bitrate96"] = Bitrate96

class GSM(Munge):
    """ GSM Reduction """
    # sox
    pass

class SoundMix(Munge):
    """ Mix in some other noises """
    pass

class WhiteNoiseMix(SoundMix):
    pass
class CarNoiseMix(SoundMix):
    pass
class PersonNoiseMix(SoundMix):
    pass
#munge_classes["whitenoise"] = WhiteNoiseMix
#munge_classes["carnoise"] = CarNoiseMix
#munge_classes["personnoise"] = PersonNoiseMix

class Volume(Munge):
    """ Change the volume """
    pass

class Volume50(Volume):
    volume = 0.5
class Volume80(Volume):
    volume = 0.8
class Volume120(Volume):
    volume = 1.2
munge_classes["volume50"] = Volume50
munge_classes["volume80"] = Volume80
munge_classes["volume120"] = Volume120

class Lowpass(Munge):
    """ Low pass filter """
    pass
#munge_classes["lowpass"] = Lowpass

class Compress(Munge):
    """ Add compression """
    pass
#munge_classes["compress"] = Compress

class EQ(Munge):
    """ Perform equalisation """
    pass
#munge_classes["eq"] = EQ

class YouTube(Munge):
    """ Reduce quality to a standard 240p youtube quality """
    def getExecCommand(self, fromfile, tofile):
        return tofile
#munge_classes["youtube"] = YouTube

class FMFilter(Munge):
    """ Similar bandwidth and filters as what comes out of
    the radio """
    pass
#munge_classes["radio"] = RadioFilter

class FMSpeed(Munge):
    """ Adjust the speed and pitch of music """
    pass
#munge_classes["radiospeed"] = RadioSpeed
