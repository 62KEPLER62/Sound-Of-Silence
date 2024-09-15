import eel
import pyaudio
import wave
import threading
import os
from pytube import YouTube
from moviepy.editor import *

# Set web files folder and optionally specify which file types to check for eel.expose()
eel.init('web')

# Global variable to control sound playing
stop_sound = False
clicked =  True
intensity = 0.05
# Function to list available audio devices
def list_audio_devices():
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        dev = p.get_device_info_by_index(i)
        device_name = f"{dev['name']} - {int(dev['defaultSampleRate'])} Hz"
        devices.append({
            'index': i,
            'name': device_name
        })
    p.terminate()
    return devices

# Function to redirect audio from input device to output device
@eel.expose
def redirect_audio(input_device_index, output_device_index):
    global stop_sound
    stop_sound = False

    def _redirect_audio():
        CHUNK = 1024
        
        p = pyaudio.PyAudio()

        # Open a stream to capture audio from input device
        input_stream = p.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=44100,
                              input=True,
                              frames_per_buffer=CHUNK,
                              input_device_index=input_device_index)

        # Open a stream to play audio to the output device
        output_stream = p.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=44100,
                               output=True,
                               output_device_index=output_device_index)

        # Redirect audio from input device to output device
        while not stop_sound:
            data = input_stream.read(CHUNK)
            output_stream.write(data)

        # Close the streams and terminate PyAudio
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
        p.terminate()
    
    threading.Thread(target=_redirect_audio).start()

# Function to play audio file to the selected output device
@eel.expose
def play_audio(file_path, input_device_index, output_device_index):
    global intensity
    sound_level = (intensity / 100.0)

    global clicked
    clicked = True
    global stop_sound
    stop_sound = False

    def _play_audio():
        CHUNK = 1024
        wf = wave.open(file_path, 'rb')

        p = pyaudio.PyAudio()

        # Open a stream with the same parameters as the audio file for the selected output device
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True,
                        output_device_index=output_device_index)

        # Open a stream with the same parameters as the audio file for the default output device
        default_output_stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                       channels=wf.getnchannels(),
                                       rate=wf.getframerate(),
                                       output=True)  # No need to specify output device index for default output

        data = wf.readframes(CHUNK)

        # Play the audio file with adjusted volume level to both devices
        while not stop_sound and data:
            # Adjust volume level
            data = apply_volume(data)
            stream.write(data)
            default_output_stream.write(data)  # Write to default output device
            data = wf.readframes(CHUNK)

        # Close the streams and terminate PyAudio
        stream.stop_stream()
        stream.close()
        default_output_stream.stop_stream()
        default_output_stream.close()
        p.terminate()
        redirect_audio(input_device_index, output_device_index)
    
    threading.Thread(target=_play_audio).start()

def apply_volume(data):
    # Adjust the volume of audio data
    # Convert data to bytearray to modify it
    global intensity
    volume = intensity

    data = bytearray(data)
    for i in range(0, len(data), 2):
        sample = int.from_bytes(data[i:i+2], byteorder='little', signed=True)
        sample = int(sample * volume)
        sample = max(min(sample, 32767), -32768)  # clamp sample to 16-bit range
        data[i:i+2] = sample.to_bytes(2, byteorder='little', signed=True)
    return bytes(data)
@eel.expose
def updateVolume(val):
    global intensity
    intensity = val*0.001

# Function to stop audio playback
@eel.expose
def stop_audio():
    global stop_sound
    global clicked
    if clicked:
        stop_sound = True
        clicked = False

# Function to get list of sound files in a specific folder
@eel.expose
def get_sound_files(folder_path='sounds'):
    sound_files = []
    for file in os.listdir(folder_path):
        if file.endswith('.wav'):
            sound_files.append(file)
    return sound_files

# Function to download YouTube video and convert it to WAV
@eel.expose
def download_youtube_audio(url,name):
    try:
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        video.download(filename="sounds/temp.mp4")

# Convert the video to audio
        video_path = "sounds/temp.mp4"
        audio_path = f"sounds/{name}.wav"
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(audio_path)

# Clean up
        video_clip.close()
        audio_clip.close()

# Delete the temporary video file
        os.remove(video_path)
        return True
    except Exception as e:
        print(e)
        return False

# Expose function to get list of available audio devices
eel.expose(list_audio_devices)

def kapa(x,y):
    os._exit(0)


if __name__ == "__main__":
    eel.start('index.html', size=(600, 400),close_callback=kapa)
