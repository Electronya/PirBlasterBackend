import paho.mqtt.client as mqtt
from ircodec.command import CommandSet

import os
import json

CMD_SETS_ROOT = './commandSets'
SAVE_CMD_SET = 'Saving command set'
ERR_CMD_SET = 'Error accessing command set file!!'


class Device(mqtt.Client):
    # Constants
    STATUS_TOPIC = 'status'
    CMD_TOPIC = 'command'
    RESULT_TOPIC = 'result'

    ONLINE_MSG = 'ONLINE'
    OFFLINE_MSG = 'OFFLINE'
    SUCCESS_MSG = 'done'
    ERROR_MSG = 'unsupported'

    # Constructor
    def __init__(self, logger, appConfig, devConfig, isNew=False):
        super().__init__(client_id=f"{devConfig['location']}."
                         f"{devConfig['name']}")
        self.config = devConfig
        self.logger = logger.getLogger(f"{devConfig['location']}."
                                       f"{devConfig['name']}")

        if isNew:
            self.logger.info('Creating new device')

            emitter = self.config['commandSet']['emitterGpio']
            receiver = self.config['commandSet']['receiverGpio']
            description = self.config['commandSet']['description']
            self.commandSet = CommandSet(emitter_gpio=emitter,
                                         receiver_gpio=receiver,
                                         description=description)
        else:
            self.logger.info('Loading existing device')

            manufacturer = self.config['commandSet']['manufacturer']
            model = self.config['commandSet']['model']
            self.commandSet = CommandSet.load(os.path.join('./commandSets',
                                              manufacturer, f"{model}.json"))

        self.baseTopic = f"{self.config['topicPrefix']}/{self.config['location']}/{self.config['name']}/"   # noqa: E501

        self._initMqttClient(appConfig.getUserName(),
                             appConfig.getUserPassword(),
                             appConfig.getBrokerHostname(),
                             appConfig.getBrokerPort(),
                             self.config['lastWill'])

    # Init device mqtt client
    def _initMqttClient(self, userName, userPassword,
                        brokerIp, brokerPort, lastWill):
        willTopic = self.baseTopic + self.STATUS_TOPIC

        # Set client settings
        self.will_set(willTopic, self.OFFLINE_MSG,
                      lastWill['qos'], lastWill['retain'])
        self.username_pw_set(userName, userPassword)
        # TODO: Implement switch for secure or not.
        # self.tls_set()
        # self.tls_insecure_set(True)

        self.logger.info(f"Connecting to {brokerIp}:{brokerPort}")
        self.logger.debug(f"Connecting as {userName} with password "
                          f"{userPassword}")

        # Connect to broker
        self.connect(brokerIp, port=brokerPort)

    # Publish command result
    def _publishCmdResult(self, success):
        resultTopic = self.baseTopic + self.RESULT_TOPIC
        if success:
            self.logger.info('Command sent')
            self.publish(resultTopic, payload=self.SUCCESS_MSG)
        else:
            self.logger.warning('Command unsupported')
            self.publish(resultTopic, payload=self.ERROR_MSG)

    # On connection
    def on_connect(self, client, usrData, flags, rc):
        self.logger.info('Connected')
        self.logger.debug(f"rc {rc}")

        # Publish ONLINE status
        statusTopic = self.baseTopic + self.STATUS_TOPIC
        self.publish(statusTopic, payload=self.ONLINE_MSG, qos=1, retain=True)

        # Subscribing to command topic
        cmdTopic = self.baseTopic + self.CMD_TOPIC
        self.subscribe(cmdTopic)

    # On disconnect
    def on_disconnect(self, client, usrData, rc):
        self.logger.info('Disconnected')
        self.logger.debug(f"rc {rc}")

    # On message
    def on_message(self, client, usrData, msg):
        receivedMsg = msg.payload.decode('utf-8')
        self.logger.info(f"Message recieved {receivedMsg}")
        for i in range(0, 4):
            self.logger.debug(f"Sending packet #{i}")
            # TODO: Manage unsupported command
            gap = self.config['commandSet']['packetGap']
            self.commandSet.emit(receivedMsg, emit_gap=gap)
        self._publishCmdResult(True)

    # On publish
    def on_publish(self, client, usrData, mid):
        self.logger.info('Message published')
        self.logger.debug(f"mid {mid}")

    # On subscribe
    def on_subscribe(self, client, usrData, mid, grantedQoS):
        self.logger.info(f"Subscibed with QoS {grantedQoS}")
        self.logger.debug(f"mid {mid}")

    # On log
    def on_log(self, client, usrData, logLevel, logMsg):
        switcher = {
            mqtt.MQTT_LOG_INFO: self.logger.info,
            mqtt.MQTT_LOG_NOTICE: self.logger.info,
            mqtt.MQTT_LOG_WARNING: self.logger.warning,
            mqtt.MQTT_LOG_ERR: self.logger.error,
            mqtt.MQTT_LOG_DEBUG: self.logger.debug,
        }
        switcher[logLevel](logMsg)

    # Get device name
    def getName(self):
        return self.config['name']

    # Get device location
    def getLocation(self):
        return self.config['location']

    # Set device config
    def setConfig(self, config):
        self.logger.debug(f"Setting device config to {config}")
        self.config = config

    # Get device config
    def getConfig(self):
        self.logger.debug('Getting device config')
        return self.config

    # Get command list
    def getCommandList(self):
        self.logger.debug('Getting command list')
        return self.commandSet.to_json()

    # Add a command
    def addCommand(self, command, description):
        self.logger.debug(f"Adding command {command} to command set")
        self.commandSet.add(command, description=description)

    # Delete a command
    def deleteCommand(self, command):
        self.logger.debug(f"Deleting command {command} from command set")
        self.commandSet.remove(command)

    # Save device command set
    def saveCommandSet(self):
        result = {'result': 'failed'}
        try:
            self.commandSet.save_as(os.path.join('./commandSets',
                                    f"{self.config['commandSet']}.json"))
            result['result'] = 'success'
        except EnvironmentError:
            result['message'] = 'Error accessing command set file'
        return result


class DeviceManager:
    """
    The device manager class.
    """
    DEVICES_FILE = './config/components/devices.json'
    SAVE_DEVS = 'Devices saved.'
    ERR_SAVE_DEVS = 'Error accessing devices file!!'

    DEFAULT_CONFIG = {
        'name': 'myDevice',
        'location': 'myDevLocation',
        'linkedEmitter': 'OUT0',
        'commandSet': {
            'model': 'rm-s103',
            'manufacturer': 'sony',
            'description': 'My Device Description',
            'emitterGpio': 22,
            'receiverGpio': 11,
            'packetGap': 0.01,
        },
        'topicPrefix': 'myDevPrefix',
        'lastWill': {
            'qos': 1,
            'retain': True,
        },
    }

    devices = []

    # Contructor
    def __init__(self, logger, appConfig):
        devsConfig = None
        self.appConfig = appConfig
        self.logger = logger.getLogger('DeviceManager')
        self.logger.info('Loading devices')

        # Loading devices
        with open(self.DEVICES_FILE) as devicesFile:
            devsConfig = json.loads(devicesFile.read())

        for devConfig in devsConfig:
            self.devices.append(Device(logger, appConfig, devConfig))

    def startLoops(self):
        self.logger.info('Starting device loops.')
        for device in self.devices:
            self.logger.debug(f"{device.getLocation()}.{device.getName()}: "
                              f"starting loop")
            device.loop_start()

    def stopLoops(self):
        self.logger.info('Stopping device loops.')
        for device in self.devices:
            self.logger.debug(f"{device.getLocation()}.{device.getName()}: "
                              f"stopping loop")
            device.disconnect()

    def getDefaultConfig(self):
        return self.DEFAULT_CONFIG

    def getDeviceByName(self, name, location):
        filterItr = filter(lambda device: device.getConfig()['name'] == name
                           and device.getConfig()['location']
                           == location, self.devices)
        return next(filterItr, None)

    def getDeviceByIdx(self, devIdx):
        if devIdx < len(self.devices):
            return self.devices[devIdx]
        return None

    def getDevsCount(self):
        return len(self.devices)

    def getDevices(self):
        return self.devices

    def addDevice(self, newDevConfig):
        devAlreadyExist = False
        result = {'result': 'failed'}

        for device in self.devices:
            if device.getName() == newDevConfig['name'] \
                    and device.getLocation() == newDevConfig['location']:
                devAlreadyExist = True

        if devAlreadyExist:
            result['message'] = "Error: Device already exists!!"
        else:
            self.devices.append(Device(self.logger, self.appConfig,
                                newDevConfig, isNew=True))
            result['result'] = 'success'

        return result

    def getDevsConfigList(self):
        devsConfigList = []

        for device in self.devices:
            devsConfigList.append(device.getConfig())

        return devsConfigList

    def saveDevices(self):
        devsConfig = []
        result = {'result': 'failed'}

        for device in self.devices:
            devsConfig.append(device.getConfig())

        self.logger.info('Saving devices')
        try:
            with open(self.DEVICES_FILE) as devicesFile:
                newContent = json.dumps(devsConfig, sort_keys=True, indent=2)
                devicesFile.write(newContent)
            result['result'] = self.SAVE_DEVS
        except EnvironmentError:
            result['message'] = self.ERR_SAVE_DEVS
            self.logger.error(result['message'])
        return result

    def listManufacturer(self):
        manufacturers = []
        for r, d, f in os.walk(CMD_SETS_ROOT):
            for manufacturer in d:
                manufacturers.append(manufacturer)
        return manufacturers

    def listCommandSets(self, manufacturer):
        cmdSets = []
        for r, d, f in os.walk(os.path.join(CMD_SETS_ROOT, manufacturer)):
            for commandSet in f:
                cmdSets.append(commandSet[:-5])
        return cmdSets
