#--------------------------
#Amit Yehezkelov 312531262
#--------------------------

import RPi.GPIO as GPIO
import time
import random
import wiringpi
from time import sleep

# initialize GPIO pins
red_btn = 6
yellow_btn = 22
green_btn = 26
blue_btn = 19
red_light = 16
yellow_light = 20
green_light = 21
blue_light = 25
siren = 5

# initialize arrays to hold the corresponding lights, buttons and sounds
lights_arr = [red_light, yellow_light, green_light, blue_light]
buttons_arr = [red_btn, yellow_btn, green_btn, blue_btn]
sounds_arr = [440, 523, 659, 784]

# initialization of sequence, player moves and flags
simonz_sequence = []
player_moves = []
stage_number = 1
current_stage_move_number = 0
player_lost = False
stage_complete = False
is_displaying = False


def main():
    initialize_matrix()
    print("Welcome to Simon Says!\n")
    print("Good luck and may the odds be even in your favor :)\n")
    lets_play()

def initialize_matrix():
    
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    
    # setup default values for button and lights
    GPIO.setup(buttons_arr, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(lights_arr, GPIO.OUT, initial=GPIO.LOW)
    
    # set listener for button clicks
    GPIO.add_event_detect(red_btn, GPIO.FALLING, callback=check_playerz_move)
    GPIO.add_event_detect(yellow_btn, GPIO.FALLING, callback=check_playerz_move)
    GPIO.add_event_detect(green_btn, GPIO.FALLING, callback=check_playerz_move)
    GPIO.add_event_detect(blue_btn, GPIO.FALLING, callback=check_playerz_move)
    
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
        play_sound(sounds_arr[buttons_arr.index(move)])
        if move == buttons_arr[simonz_sequence[current_stage_move_number]]:
            current_stage_move_number += 1
            if current_stage_move_number >= stage_number:
                stage_number += 1
                stage_complete = True
        else:
            player_lost = True

def listen_to_player_moves():
    print("Simon has made his choice, Your turn!\n")
    while not stage_complete and not player_lost:
        time.sleep(0.1)

def flick_light(button):
    light = lights_arr[buttons_arr.index(button)]
    flicker_light(light)

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
