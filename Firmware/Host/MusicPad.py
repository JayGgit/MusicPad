import serial, time, json
from serial.tools import list_ports
from pycaw.pycaw import AudioUtilities
import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

vid = 0x2886
pid = 0x0042
global port
global deviceSerial

def findDevice():
    global port
    global deviceSerial
    port = None
    while (port is None):
        for devPorts in list_ports.comports():
            if devPorts.vid == vid and devPorts.pid == pid:
                port = devPorts.device
                print("Found device %s on port %s" % (devPorts.description, devPorts.device))
        if port is None:
            print("Device not found. Retrying in 5 seconds...")
            time.sleep(5)
    deviceSerial = serial.Serial(port, 115200, timeout=0.1)
findDevice()

audioDevice = AudioUtilities.GetSpeakers()
print("Device found: %s" % audioDevice.FriendlyName)
volume = audioDevice.EndpointVolume

isMuted = volume.GetMute()
percentVolume = volume.GetMasterVolumeLevelScalar() * 100
volumeChange = False

async def get_current_media_info():
    sessions = await MediaManager.request_async()
    current_session = sessions.get_current_session()
    
    if current_session:
        playbackInfo = current_session.get_playback_info()
        playbackStatus = playbackInfo.playback_status
        properties = await current_session.try_get_media_properties_async()
        timeline = current_session.get_timeline_properties()
        title = properties.title or "Unknown Title"
        artist = properties.artist or "Unknown Artist"
        duration_seconds = timeline.end_time.total_seconds() if timeline.end_time else 1
        position_seconds = timeline.position.total_seconds() if timeline.position else 0
        return {
            'isPlaying': True,
            'title': title,
            'artist': artist,
            'duration': duration_seconds, 
            'position': position_seconds,
            'playback_status': playbackStatus
        }
    else:
        return {
            'isPlaying': False,
            'title': "",
            'artist': "",
            'duration': 1, 
            'position': 0,
            'playback_status': ""
        }
    
    return None

while True:
    try:
        if (isMuted != volume.GetMute()):
            isMuted = volume.GetMute()
            volumeChange = True
        if (percentVolume != volume.GetMasterVolumeLevelScalar() * 100):
            percentVolume = volume.GetMasterVolumeLevelScalar() * 100
            volumeChange = True
        
        mediaInfo = asyncio.run(get_current_media_info())

        dataToSend = {
            'isPlaying': mediaInfo['isPlaying'] if mediaInfo else False,
            'volumeChange': volumeChange,
            'muted': isMuted,
            'volume': percentVolume,
            'title': mediaInfo['title'] if mediaInfo else "",
            'artist': mediaInfo['artist'] if mediaInfo else "",
            'duration': mediaInfo['duration'] if mediaInfo else 1,
            'position': mediaInfo['position'] if mediaInfo else 0,
            'playback_status': mediaInfo['playback_status'] if mediaInfo else ""
        }
        deviceSerial.write((json.dumps(dataToSend) + "\n").encode('utf-8'))
        volumeChange = False
        time.sleep(1)
        
        # Prints returned data
        if (deviceSerial.in_waiting > 0):
            response = deviceSerial.readline().decode('utf-8').strip()
            print(response)
            time.sleep(1)
    except Exception as e:
        print("Error using port: " + str(port))
        print("Error:", e)
        findDevice()
        time.sleep(5)