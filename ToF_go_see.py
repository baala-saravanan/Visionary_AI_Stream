# INSTALLATION : "python3.9 -m pip install smbus2"

import os
import time
import sys
import vlc
import gpio as GPIO
import subprocess
import pyttsx3
from smbus2 import SMBus
from pydub import AudioSegment
sys.path.insert(0, '/home/rock/Desktop/Hearsight/')
from play_audio import GTTSA
#from English.go_see.what import SSD

engine = pyttsx3.init()
engine.setProperty('voice', 'en-gb')
engine.setProperty('rate', 140)
#what_obj = SSD()
play_audio = GTTSA()
GPIO.setup(448, GPIO.IN)  # Exit Button
bus = SMBus(3)
time.sleep(1)
addr = 0x74

def read_reg(reg, size):
    try:
        data = bus.read_i2c_block_data(addr, reg, size)
        return data
    except IOError:
        return None

def write_reg(reg, data):
    try:
        bus.write_i2c_block_data(addr, reg, data)
        return True
    except IOError:
        return False

def main():
    dat = 0xB0
    distance = 0
    meter_to_feet = 3.28084  # Conversion factor from meters to feet
    try:
        while True:
            write_reg(0x10, [dat])
            time.sleep(0.03)
            buf = read_reg(0x02, 2)
            
            if buf:
                distance_mm = (buf[0] << 8) + buf[1] + 10
                distance_m = distance_mm / 1000.0  # Convert mm to meters
#                print(f"distance={distance_m}m")
                distance_ft = distance_m * meter_to_feet  # Convert meters to feet
                distance = str(distance_ft).split(".")
                distance = distance[0]
                print(f"Distance = {distance_ft} Feet")
                print(f"Distance = {distance} Feet")
#                print ("  Distance : %.1f ft" % distance_ft)
#                distance_ft = round(distance_ft)
#                print("Distance in Feet:", distance_ft)
#                print("Distance:", round(distance_ft))
                
#                if 1.524 <= distance_m <= 2.1336: #5 to 7 feet
                if 5 <= distance_ft <= 7:  # 5 to 7 feet
                    media = vlc.MediaPlayer("/home/rock/Desktop/Hearsight/audios/beeb/340Hz-5sec.wav")
                    media.play()
                    time.sleep(1.25)
                    media.stop()
                    print("ALERT!!!")
                    engine.say(f'ALERT listen carefully in {distance} feet distance')
                    engine.runAndWait()
                    os.system("python3.9 /home/rock/Desktop/Hearsight/English/go_see/demo.py")

#                    elapsed_time = what_obj.detect()
#                    elapsed = str(elapsed_time).split('.')
#                    if int(elapsed[0]) == 0:
#                        engine.say(f'undefined object at {distance} feet distance')
#                    else:
#                        engine.say(f'at {distance} feet distance')
#                    engine.runAndWait()
                    
#                elif 0.9144 <= distance_m <= 1.2192: #3 to 4 feet
                elif 3 <= distance_ft <= 4:  # 3 to 4 feet
                    media = vlc.MediaPlayer("/home/rock/Desktop/Hearsight/audios/beeb/3_long_high.mp3")
                    media.play()
                    time.sleep(1.25)
                    media.stop()
                    print("STOP!!!")
                    engine.say(f'STOP listen carefully in {distance} feet distance')
                    engine.runAndWait()
                    os.system("python3.9 /home/rock/Desktop/Hearsight/English/go_see/demo.py")

#                    elapsed_time = what_obj.detect()
#                    elapsed = str(elapsed_time).split('.')
#                    if int(elapsed[0]) == 0:
#                        engine.say(f'undefined object at {distance} feet distance')
#                    else:
#                        engine.say(f'at {distance} feet distance')
#                    engine.runAndWait() 

                input_state = GPIO.input(448)
                if input_state:
                    bus.close()
                    play_audio.play_machine_audio("feature_exited.mp3")
#                    sys.exit()
                    os._exit(0)
                    break
                
            time.sleep(0.1)
            
    except Exception as e:
        print(f"Error occurred: {e}")
        play_audio.play_machine_audio("hold_on_connection_in_progress_initiating_shortly.mp3")
        play_audio.play_machine_audio("Thank You.mp3")
        subprocess.run(["reboot"])

if __name__ == "__main__":
    main()

