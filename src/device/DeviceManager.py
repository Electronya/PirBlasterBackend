import os
import json

from .Device import Device


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
        """
        Constructor.

        Params:
            logger:     The logging instance.
            appConfig:  The application configuration.
        """
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
        """
        Start all the device loops.
        """
        self.logger.info('Starting device loops.')
        for device in self.devices:
            self.logger.debug(f"{device.getLocation()}.{device.getName()}: "
                              f"starting loop")
            device.loop_start()

    def stopLoops(self):
        """
        Stop all the device loops (disconnect all devices).
        """
        self.logger.info('Stopping device loops.')
        for device in self.devices:
            self.logger.debug(f"{device.getLocation()}.{device.getName()}: "
                              f"stopping loop")
            device.disconnect()

    def getDefaultConfig(self):
        """
        Get the device default configuration.
        """
        return self.DEFAULT_CONFIG

    def getDeviceByName(self, name, location):
        """
        Get a device by its name.

        Params:
            name:       The device name.
            location:   The device location.

        Return:
            The found device if successful, None otherwise.
        TODO: Use exception.
        """
        filterItr = filter(lambda device: device.getConfig()['name'] == name
                           and device.getConfig()['location']
                           == location, self.devices)
        return next(filterItr, None)

    def getDeviceByIdx(self, devIdx):
        """
        Get the device by its index.

        Params:
            devIdx:     The device index.

        Return:
            The found device if successful, None otherwise.
        TODO: Use exception.
        """
        if devIdx < len(self.devices):
            return self.devices[devIdx]
        return None

    def getDevsCount(self):
        """
        Get the active device count.

        Return:
            The number of active devices.
        """
        return len(self.devices)

    def getDevices(self):
        """
        Get the device list.

        Return:
            The device list.
        """
        return self.devices

    def addDevice(self, newDevConfig):
        """
        Add a device to the active device list.

        Params:
            newDevConfig:   The configuration of the new device.

        Return:
            The operation resuslt.
        TODO: Use exception.
        """
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
        """
        Get the active device configuration list.

        Return:
            The list of active device configurations.
        """
        devsConfigList = []

        for device in self.devices:
            devsConfigList.append(device.getConfig())

        return devsConfigList

    def saveDevices(self):
        """
        Save the active device configurations.

        Return:
            The result of the operation.
        TODO: Use exception.
        """
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
        """
        Get the list of currenty supported manufacturer.

        Return:
            The list of currently supported manufacturer.
        TODO: Use exception.
        """
        manufacturers = []
        for r, d, f in os.walk('./commandSets'):
            for manufacturer in d:
                manufacturers.append(manufacturer)
        return manufacturers

    def listCommandSets(self, manufacturer):
        """
        Get the list of currently supported command set for a manufacturer.

        Return:
            The list fo currently supported command set for the manufacturer.
        TODO: Use exception.
        """
        cmdSets = []
        for r, d, f in os.walk(os.path.join('./commandSets', manufacturer)):
            for commandSet in f:
                cmdSets.append(commandSet[:-5])
        return cmdSets