import os
import json


class Config:
    CONFIG_PATH = './config/components'
    HW_CONFIG_FILE = 'hardware.json'
    MQTT_CONFIG_FILE = 'mqtt.json'

    SAVE_MQTT_CONFIG = 'MQTT configuration saved'
    ERR_SAVE_MQTT_CONFIG = 'Error accessing MQTT configuration file!!'
    SAVE_HW_CONFIG = 'Hardware configuration saved'
    ERR_SAVE_HW_CONFIG = 'Error accessing hardware configuration file!!'

    # Constructor
    def __init__(self, logger):
        self.logger = logger.getLogger('CONFIG')

        # Reading MQTT config
        self.logger.info('Opening MQTT configuration')
        with open(os.path.join(self.CONFIG_PATH,
                  self.MQTT_CONFIG_FILE)) as mqttConfig:
            self.mqttConfig = json.loads(mqttConfig.read())

        # Reading hardware config
        self.logger.info('Opening hardware configuration')
        with open(os.path.join(self.CONFIG_PATH,
                  self.HW_CONFIG_FILE)) as hwConfig:
            self.hwConfig = json.loads(hwConfig.read())

    def getBrokerHostname(self):
        return self.mqttConfig['broker']['hostname']

    def setBrokerHostname(self, newIp):
        self.mqttConfig['broker']['hostname'] = newIp

    def getBrokerPort(self):
        return self.mqttConfig['broker']['port']

    def setBrokerPort(self, newPort):
        self.mqttConfig['broker']['port'] = newPort

    def getUserName(self):
        return self.mqttConfig['user']['name']

    def setMqttUserName(self, newUserName):
        self.mqttConfig['user']['name'] = newUserName

    def getUserPassword(self):
        return self.mqttConfig['user']['password']

    def setUserPassword(self, newPassword):
        self.mqttConfig['user']['password'] = newPassword

    def saveMqttConfig(self):
        self.logger.info('Saving MQTT configuration')
        result = {'result': 'failed'}
        try:
            with open(os.path.join(self.CONFIG_PATH,
                      self.MQTT_CONFIG_FILE)) as configFile:
                newContent = json.dumps(self.mqttConfig, sort_keys=True,
                                        indent=2)
                configFile.write(newContent)
            result['result'] = self.SAVE_MQTT_CONFIG
        except EnvironmentError:
            result['message'] = self.ERR_SAVE_MQTT_CONFIG
            self.logger.error(f"{result['message']}")
        return result

    def getInputName(self):
        return self.hwConfig['in']['name']

    def getInputGpioId(self):
        return self.hwConfig['in']['gpioId']

    def setInputGpioId(self, newGpioId):
        self.hwConfig['in']['gpioId'] = newGpioId

    def getOutputCount(self):
        return len(self.hwConfig['out'])

    def getOuputName(self, ouputIdx):
        if ouputIdx < len(self.hwConfig['out']):
            return self.hwConfig['out'][ouputIdx]['name']
        return None

    def getOuputGpioId(self, ouputIdx):
        if ouputIdx < len(self.hwConfig['out']):
            return self.hwConfig['out'][ouputIdx]['gpioId']
        return None

    def setOutputGpioId(self, ouputIdx, newGpioId):
        if ouputIdx < len(self.hwConfig['out']):
            self.hwConfig['out'][ouputIdx]['gpioId'] = newGpioId

    def saveHwConfig(self):
        self.logger.info('Saving hardware configuration')
        result = {'result': 'failed'}
        try:
            with open(os.path.join(self.CONFIG_PATH,
                      self.HW_CONFIG_FILE)) as configFile:
                newContent = json.dumps(self.hwConfig, sort_keys=True,
                                        indent=2)
                configFile.write(newContent)
            result['result'] = self.SAVE_HW_CONFIG
        except EnvironmentError:
            result['message'] = self.ERR_SAVE_HW_CONFIG
            self.logger.error(f"{result['message']}")
        return result
