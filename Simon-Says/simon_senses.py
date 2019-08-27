#--------------------------
# Amit Yehezkelov
# link to video:
# https://youtu.be/8j06bRrQMns
#--------------------------

import RPi.GPIO as GPIO
import random
import wiringpi
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import time
from time import sleep
from mpu6050 import mpu6050

# initialize GPIO pins and sensors
red_light = 16
yellow_light = 20
green_light = 21
blue_light = 17
siren = 5
CLK = 18
MISO = 23
MOSI = 24
CS = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)
gyro = mpu6050(0x68)

# initialize arrays to hold the corresponding sounds and lights
sounds_arr = [440, 523, 659, 784]
lights_arr = [red_light, yellow_light, green_light, blue_light]

# initialization of sequence, player moves and flags
simonz_sequence = []
player_moves = []
stage_number = 1
current_stage_move_number = 0
stage_complete = False
player_lost = False
is_displaying = False


def main():
    initialize_matrix()
    print("Welcome to Simon Says!\n")
    print("Good luck and may the odds be ever in your favor :)\n")
    lets_play()


def initialize_matrix():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # setup default values for lights
    GPIO.setup(lights_arr, GPIO.OUT, initial=GPIO.LOW)
    
    # initialize siren
    wiringpi.wiringPiSetupGpio()
    wiringpi.softToneCreate(siren)

def lets_play():
    welcome_show()
    while True:
        add_step_to_simonz_sequence()
        sleep(1)
        display_full_stage_sequence()
        listen_to_player_moves()
        if player_lost:
            terminate_game()
            GPIO.cleanup()
            exit()


# flash lights and play music for game start
def welcome_show():
    for i in range(0,4):
        GPIO.output(lights_arr[i], GPIO.HIGH)
        play_sound(sounds_arr[i])
        sleep(0.1)
    for i in range(3,-1,-1):
        GPIO.output(lights_arr[i], GPIO.LOW)
        play_sound(sounds_arr[i])
        sleep(0.1)
    sleep(0.3)


def flicker_light(light):
    GPIO.output(light, GPIO.HIGH)
    time.sleep(0.2)
    GPIO.output(light, GPIO.LOW)


def play_sound(sound):
    for i in range(1, 10, 2):
        wiringpi.softToneWrite(siren, sound)
        sleep(0.1)
    wiringpi.softToneWrite(siren, 0)


def add_step_to_simonz_sequence():
    global stage_complete, current_stage_move_number
    stage_complete = False
    current_stage_move_number = 0
    simonz_next_move = random.randint(0, 3)
    simonz_sequence.append(simonz_next_move)


def display_full_stage_sequence():
    global is_displaying_pattern
    is_displaying_pattern = True
    for i in range(stage_number):
        flicker_light(lights_arr[simonz_sequence[i]])
        play_sound(sounds_arr[simonz_sequence[i]])
    is_displaying_pattern = False


def check_playerz_move(move):
    global current_stage_move_number, stage_number, stage_complete, player_lost
    if not is_displaying_pattern and not stage_complete and not player_lost:
        flick_light(move)
        play_sound(sounds_arr[move])
        if move == simonz_sequence[current_stage_move_number]:
            current_stage_move_number += 1
            if current_stage_move_number >= stage_number:
                stage_number += 1
                stage_complete = True
        else:
            player_lost = True


def listen_to_player_moves():
    print("Simon has made his choice, Your turn!\n")
    while not stage_complete and not player_lost:
        time.sleep(0.3)
        
        # check for gyro x or y movement to light up red light
        val_gyro = gyro.get_accel_data()
        if abs(val_gyro['x']) > 2 or abs(val_gyro['y']) > 2:
            check_playerz_move(0)

        # check for potenciometer high value to light up yellow light 
        val_potenciometer = mcp.read_adc(0)
        if val_potenciometer > 1000: 
            check_playerz_move(1)

        # check light sensor for shadow to light up green light
        val_light_sensor = mcp.read_adc(1)
        if val_light_sensor < 700:
            check_playerz_move(2)

        # check for close proximity to light up blue light
        val_proximity = mcp.read_adc(2)
        if val_proximity < 100:
            check_playerz_move(3)


def flick_light(sense): 
    flicker_light(lights_arr[sense])


def terminate_game():
    print("Game Over! :( \n")
    for i in lights_arr:
        GPIO.output(i, GPIO.HIGH)
    for i in range(0,2):
        play_sound(400)
    for i in range(0,2):
        play_sound(800)
    for i in lights_arr:
        GPIO.output(i, GPIO.LOW)


if __name__ == '__main__':
    main()
