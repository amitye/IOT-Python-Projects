#--------------------------
# Amit Yehezkelov
#--------------------------

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import time
import argparse
import json
import RPi.GPIO as GPIO
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import Adafruit_DHT
from mpu6050 import mpu6050

# init of sensors
temperature_humidity = Adafruit_DHT.DHT22
temperature_humidity_pin = 4
accelerometer = mpu6050(0x68)
CLK = 18
CS = 25
MISO = 23
MOSI = 24
mcp = Adafruit_MCP3008.MCP3008(clk = CLK,cs = CS,miso = MISO, mosi = MOSI)

# Change according to your configuration
host = 'a1rpddawph4ysg-ats.iot.eu-west-1.amazonaws.com'
rootCA = './certificates/root-CA.crt'
privateKey = './certificates/56075c5af2-private.pem.key'
cert = './certificates/56075c5af2-certificate.pem.crt'
thingName = 'amit_thing'
deviceId = thingName
topic = 'amit_topic'
defaultInterval = 10
notConnected = True

# this interval denotes the time during which sound devation is calculated
# this means that the publishing interval is longer due to the other
# calculations that occur between each publish
interval = None

# Sound Diff Calculator (this method uses time.sleep)
# During the inteval (given from the shadow) calculates the average devation
# from the base room's sound level during each second. The second that
# recorded the maximal devation is stored and returned at the end
def soundDiffCalc(baseRoomSound):
    accumlatedDifference = 0
    numberOfSamplesPerInterval = 100
    numberOfTotalSamples = int(interval) * numberOfSamplesPerInterval
    maxSoundDiff = 0
    for j in xrange(int(interval)):
        for i in xrange(numberOfSamplesPerInterval):
            currentMeasurement = mcp.read_adc(2)
            accumlatedDifference += abs(baseRoomSound - currentMeasurement)
        if(accumlatedDifference / numberOfSamplesPerInterval > maxSoundDiff):
             maxSoundDiff = accumlatedDifference / numberOfSamplesPerInterval
        time.sleep(1)
        accumlatedDifference = 0
    return maxSoundDiff

# this method is called once to initialize the room's base sounds level
def calculateBaseRoomSound():
    soundSensorData = 0
    numberOfSamples = 1000
    for i in xrange(numberOfSamples):
        soundSensorData += mcp.read_adc(2)
    return soundSensorData / numberOfSamples

# Custom Shadow callbacks
def customShadowCallback_Update(payload, responseStatus, token):
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Update request with token: " + token + " accepted!")
        print("property: " + str(payloadDict["state"]))
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Update request " + token + " rejected!")

def customShadowCallback_Get(payload, responseStatus, token):
    global interval
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    payloadDict = json.loads(payload)
    print("++++++++GET++++++++++")
    if 'delta' in payloadDict['state']:
        if 'interval' in payloadDict['state']['delta']:
            interval = str(payloadDict['state']['delta']['interval'])
            print("interval: " + interval)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
        else :
            interval = defaultInterval
            print("No interval found, using default {}".format(interval))
        newPayload = '{"state":{"reported":' + json.dumps(payloadDict['state']['delta']) + '}}'
        deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)
    elif 'reported' in payloadDict['state']:
        if 'interval' in payloadDict['state']['reported']:
            interval = str(payloadDict['state']['reported']['interval'])
            print("interval: " + interval)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
        else :
        	interval = defaultInterval
            print("No interval found, using default {}".format(interval))
        newPayload = '{"state":{"reported":' + json.dumps(payloadDict['state']['delta']) + '}}'
        deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)
    elif 'reported' in payloadDict['state']:
        if 'interval' in payloadDict['state']['reported']:
            interval = str(payloadDict['state']['reported']['interval'])
            print("interval: " + interval)
            print("version: " + str(payloadDict["version"]))
            print("+++++++++++++++++++++++\n\n")
        else :
            interval = defaultInterval
            print("No interval found, using default {}".format(interval))
    else:
        interval = defaultInterval
        print("No interval found, using default {}".format(interval))
        newPayload = '{"state":{"reported": {"interval" : '+json.dumps(interval)+'}}}'
        deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)

def customShadowCallback_Delta(payload, responseStatus, token):
    global interval
    # payload is a JSON string ready to be parsed using json.loads(...)
    # in both Py2.x and Py3.x
    payloadDict = json.loads(payload)
    print(payloadDict)
    print("++++++++DELTA++++++++++")
    if 'interval' in payloadDict['state']:
        interval = str(payloadDict['state']['interval'])
        print("interval: " + interval)
        print("+++++++++++++++++++++++\n\n")
    else :
        interval = defaultInterval
        print("No interval found, using default {}".interval)
    newPayload = '{"state":{"reported":' + json.dumps(payloadDict['state']) + '}}'
    deviceShadowHandler.shadowUpdate(newPayload, customShadowCallback_Update, 5)

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.WARNING)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter(
                              '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(deviceId)
myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
myAWSIoTMQTTShadowClient.configureCredentials(rootCA, privateKey, cert)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
while(notConnected):
    try:
        myAWSIoTMQTTShadowClient.connect()
        notConnected = False
    except:
        print('Failed to connect to AWS... Trying again')

# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
# Listen on deltas
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)
deviceShadowHandler.shadowGet(customShadowCallback_Get,5)
myMQTTClient = myAWSIoTMQTTShadowClient.getMQTTConnection()

# Infinite offline Publish queueing
myMQTTClient.configureOfflinePublishQueueing(-1)
myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
time.sleep(3)
baseRoomSound = calculateBaseRoomSound()
while True:
    # Get data from sensors
    humidity, temperature = Adafruit_DHT.read_retry(temperature_humidity, temperature_humidity_pin)
    accel_data = accelerometer.get_accel_data()
    gyro_data = accelerometer.get_gyro_data()
    light_sensor_data = mcp.read_adc(1)
    # calculating the noise is the only method that is time based
    # therefore time.sleep is used inside of it
    sound_sensor_data = soundDiffCalc(baseRoomSound)
    fire_sensor_data = mcp.read_adc(3)
    proximity_data = mcp.read_adc(4)
    
    # Create json
    data = {
        'temperature': temperature,
        'humidity': humidity,
        'acc-x': accel_data['x'],
        'acc-y': accel_data['y'],
        'acc-z': accel_data['z'],
        'gyro-x': gyro_data['x'],
        'gyro-y': gyro_data['y'],
        'gyro-z': gyro_data['z'],
        'light': light_sensor_data,
        'noise': sound_sensor_data,
        'fire': fire_sensor_data,
        'proximity': proximity_data
    }

    # Publish data every interval (with respect to the noise calculation
    try:    
        myMQTTClient.publish(topic, json.dumps(data), 1)
    except:
        print('failed to publish')

