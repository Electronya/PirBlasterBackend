from flask import Flask, Response, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_jsonpify import jsonify
from flask_cors import CORS

import logging
import json
import os

from irReader import IrReader
from irEmitter import IrEmitter
from remote import Protocol, Remote
from device import Device

# Setting up app
app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
socketio = SocketIO(app)
app.logger.info('App setup done')

# Loading configs
hardwareConfig = None
mqttConfig = None
devicesConfig = None

hardwareConfigFile = os.path.join('./', 'config', 'hardware.json')
with open(hardwareConfigFile) as configFile:
    hardwareConfig = json.loads(configFile.read())

mqttConfigFile = os.path.join('./', 'config', 'mqtt.json')
with open(mqttConfigFile) as configFile:
    mqttConfig = json.loads(configFile.read())

devicesConfigFile = os.path.join('./', 'config', 'devices.json')
with open(devicesConfigFile) as configFile:
    devicesConfig = json.loads(configFile.read())

# Instanciating hardware classes
reader = IrReader(hardwareConfig['in'], app.logger)
emitters = []
for outConfig in hardwareConfig['out']:
    emitters.append(IrEmitter(outConfig, app.logger))

# Creating devices
devices = []
for deviceConfig in devicesConfig:
    emitterIter = filter(lambda emitter: emitter['name'] == deviceConfig['linkedEmitter'], hardwareConfig['out'])
    devices.append(Device(deviceConfig, mqttConfig, next(emitterIter), app.logger))

# For Hardware test
# emitters[3].addBit(2400, 590)
# emitters[3].addBit(1200, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(1200, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(1200, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(590, 590)
# emitters[3].addBit(1200, 590)
# emitters[3].addGap(10800)
# emitters[3].sendCommand(0.5)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port =5000, debug=False, threaded=True)
