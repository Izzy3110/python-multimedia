import subprocess as sp
import time
import miniaudio
from datetime import datetime
import threading
import sys


FFMPEG_BIN = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"  # on Linux


class PlayStream(threading.Thread):
    stream_url = None

    audio_channels_n = 2
    audio_samplerate = 44100

    def __init__(self, stream_url):
        self.stream_url = stream_url
        super(PlayStream, self).__init__()

    def stream_pcm(self, source):
        required_frames = yield b""  # generator initialization
        while True:
            required_bytes = required_frames * 2 * 2
            sample_data = source.read(required_bytes)
            if not sample_data:
                break
            required_frames = yield sample_data

    def run(self) -> None:
        with miniaudio.PlaybackDevice(output_format=miniaudio.SampleFormat.SIGNED16,
                                      nchannels=self.audio_channels_n, sample_rate=self.audio_samplerate) as device:
            ffmpeg_command = [FFMPEG_BIN, "-v", "fatal", "-hide_banner", "-nostdin",
                              "-i", self.stream_url, "-f", "s16le", "-acodec", "pcm_s16le",
                              "-ac", str(self.audio_channels_n), "-ar", str(self.audio_samplerate), "-"]

            ffmpeg = sp.Popen(ffmpeg_command,
                              stdin=None, stdout=sp.PIPE)

            stream = self.stream_pcm(ffmpeg.stdout)
            next(stream)  # start the generator
            device.start(stream)
            input("Audio file playing in the background. Enter to stop playback: ")
            ffmpeg.terminate()


class RecordStream(threading.Thread):

    audio_channels_n = 2
    audio_samplerate = 44100

    def __init__(self, stream_url):
        self.ffmpeg_c = [FFMPEG_BIN, "-v", "fatal", "-hide_banner", "-nostdin",
                    "-i", stream_url, "-f", "mp3", "-acodec", "copy",
                    "-ac", str(self.audio_channels_n), "-ar", str(self.audio_samplerate), "-y",
                    "local_record-" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp3"]
        super(RecordStream, self).__init__()

    def run(self) -> None:
        self.start_record()

    def start_record(self):
        with sp.Popen(self.ffmpeg_c, stderr=sp.PIPE, stdout=sp.PIPE) as self.ps:
            while self.ps.poll():
                print("recording...")
                time.sleep(1)


RecordStream_ = RecordStream("http://trace.dnbradio.com:8000/dnbradio_main.mp3")
RecordStream_.start()
PlayStream_ = PlayStream("http://trace.dnbradio.com:8000/dnbradio_main.mp3")
PlayStream_.start()


