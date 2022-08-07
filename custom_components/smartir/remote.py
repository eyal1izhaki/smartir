from typing import Iterable
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.remote import RemoteEntity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import tinytuya
import json
import os
import logging

from .const import *
from .exceptions import *

_LOGGER = logging.getLogger(__name__)

__version__ = "0.0.1"

COMPONENT_REPO = "https://github.com/eyal1izhaki/smartir"

REQUIREMENTS = ["tinytuya"]

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_IP = "local_ip"
CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_DEVICE_HEAD_VALUE = "device_head_value"
CONF_DATA_FILE = "data_file"
CONF_DEBUG = "debug"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_ACCESS_ID): cv.string,
        vol.Required(CONF_ACCESS_SECRET): cv.string,
        vol.Required(CONF_DATA_FILE): cv.string,
        vol.Optional(CONF_LOCAL_IP): cv.string,
        vol.Optional(CONF_DEBUG): cv.string
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([AirConditionerRemote(
        name = config[CONF_NAME],
        device_id=config[CONF_DEVICE_ID],
        access_id=config[CONF_ACCESS_ID], 
        access_secret=config[CONF_ACCESS_SECRET],
        data_file=config[CONF_DATA_FILE],
        ip_address=config.get(CONF_LOCAL_IP),
        debug=config.get(CONF_DEBUG, False)
    )])


class AirConditionerRemote(RemoteEntity):

    def __init__(self, name: str, device_id: str, access_id: str, access_secret: str, data_file: str, ip_address:str | None, debug: bool) -> None:

        if debug == True:
            _LOGGER.setLevel(logging.DEBUG)

        super().__init__()

        # Represents the remote state
        self._current_power = 'off'
        self._current_mode = 'cold'
        self._current_fan = 'middle'
        self._current_temperature = 21


        # Home assistant entity attributes
        self._attr_name = name
        self._attr_state = None
        self._attr_extra_state_attributes = {
            "power": self.current_power,
            "mode": self.current_mode,
            "fan": self.current_fan,
            "temperature": self.current_temperature
        }

        # Whether the device have a static ip in lan or not.
        self._static_ip = True if ip_address is not None else False

        # Tyua stuff
        self._device_id = device_id
        self._access_id = access_id
        self._access_secret = access_secret
        self._ip_address = ip_address

        _LOGGER.debug(f"Creating tinytuya 'Cloud' instance with these parameters: region='eu', access_id='{access_id}', access_secret='{'*' * len(access_secret)}', device_id={device_id}")
        self._cloud = tinytuya.Cloud('eu', access_id, access_secret, device_id)

        self.create_device_connection()

        _LOGGER.debug("Loading data file...")
        self._head, self._actions = self._get_head_and_actions(data_file)
        _LOGGER.debug(f"{len(self._actions)} actions loaded.")

    @property
    def current_power(self):
        return self._current_power
    
    @current_power.setter
    def current_power(self, value):
        if value not in POWER_MODES:
            raise UnknownPowerMode
        self._current_power = value
    
    @property
    def current_mode(self):
        return self._current_mode
    
    @current_mode.setter
    def current_mode(self, value):
        if value not in MODES:
            raise UnknownMode
        self._current_mode = value

    @property
    def current_fan(self):
        return self._current_fan
    
    @current_fan.setter
    def current_fan(self, value):
        if value not in FAN_SPEEDS:
            raise UnknownFanSpeed
        self._current_fan = value

    @property
    def current_temperature(self):
        return self._current_temperature
    
    @current_temperature.setter
    def current_temperature(self, value):
        if type(value) != int:
            raise UnknownTemperature
        
        if value > MAX_TEMP or value < MIN_TEMP:
            raise UnsupportedTemperature
        
        self._current_temperature = value

    @property
    def state(self):
        return 'online'

    def create_device_connection(self):
        """
        Creates new tinytuya 'Device' instance with the currect ip address and local key.

        This function is being called on creating and when the device status changes from unavailable to online.
        Then we need to retrive the correct local key and the ip address of the device.
        
        """

        if self._static_ip == False:
            
            self._ip_address = ""

            # Scanning the netwotk to get device ip address
            devices_on_lan = tinytuya.deviceScan()

            for key in devices_on_lan.keys():
                if devices_on_lan[key]["id"] == self._device_id:
                    self._ip_address = devices_on_lan[key]["ip"]
            
            if self._ip_address == "":
                raise DeviceNotFoundOnLan

        self._local_key = self._get_local_key()

        _LOGGER.debug(f"Creating tinytuya 'Device' instance with these parameters: device_id='{self._device_id}', ip_address='{self._ip_address}', local_key: '{self._local_key}'")
        self._device = tinytuya.Device(self._device_id, self._ip_address, self._local_key)
        self._device.set_version(3.3)

    def _get_head_and_actions(self, data_file):
        """
        Reads data file and retuns the 'head' value (tyua IR stuff) and the IR actions
        """

        dir_name = os.path.dirname(__file__)
        path = os.path.join(dir_name, f'data_files/{data_file}')

        with open(path, 'r') as file:
            data = file.read()
            parsed = json.loads(data)

            head = parsed["device_head"]
            actions = parsed["actions"]
        
        return head, actions

    def _get_local_key(self):
        """
        Returns 'local_key' code. Used for tyua local communicating with the IR device
        """

        _LOGGER.debug("Retriving new local key...")

        local_key = ""
        devices = self._cloud.getdevices()

        for device in devices:
            if device["id"] == self._device_id:
                local_key = device["key"]
        
        _LOGGER.debug(f"New local key is '{local_key}'")

        return local_key

    def _send_ir_signal(self, key1):
        """
        Sends the actual IR packet to the IR transmitter device.
        """

        command = {"control": "send_ir", "head": self._head, "key1": key1, "type": 0, " delay": 300}
        _LOGGER.debug(f"Sending IR signal to the device. {command}")

        payload = self._device.generate_payload(tinytuya.CONTROL, {"201": json.dumps(command)})


        self._device.send(payload)

    def _send_action(self, action_name: str):
        """
        By a given action name, passes the corresponding IR code to _send_ir_signal function.
        """

        _LOGGER.debug(f"Performing '{action_name}' action.")

        if action_name.startswith('off'):
            action_name = 'off'

        try:
            ir_key1 = self._actions[action_name]
        except KeyError:
            raise UnknownCommand

        self._send_ir_signal(ir_key1)
    
    def send_ir_signal_current_state(self):
        """
        Sends an IR packet as the current state of the remote.
        """
        
        action_name = f"{self.current_power}_{self.current_mode}_{self.current_fan}_{str(self.current_temperature)}"

        self._send_action(action_name)

    def increase_temperature(self):
        """
        Increases temperature by 1 and sends it to the transmitter device. 
        """

        if self._current_temperature >= MAX_TEMP:
            return
        self._current_temperature +=1

    def decrease_temperature(self):
        """
        decreases temperature by 1 and sends it to the transmitter device. 
        """

        if self._current_temperature <= MIN_TEMP:
            return
        self._current_temperature -= 1
    
    def toggle_power(self):
        current_index = POWER_MODES.index(self.current_power)

        if current_index == len(POWER_MODES) - 1:
            self.current_power = POWER_MODES[0]
        else:
            self.current_power = POWER_MODES[current_index+1]
    
    def toggle_mode(self):
        current_index = MODES.index(self.current_mode)

        if current_index == len(MODES) - 1:
            self.current_mode = MODES[0]
        else:
            self.current_mode = MODES[current_index+1]
    
    def toggle_fan(self):
        current_index = FAN_SPEEDS.index(self.current_fan)

        if current_index == len(FAN_SPEEDS) - 1:
            self.current_fan = FAN_SPEEDS[0]
        else:
            self.current_fan = FAN_SPEEDS[current_index+1]
    


    ####################################
    # Functions used by home assistant #
    ####################################

    def send_command(self, command: Iterable[str], **kwargs):
        """Send commands to a device."""

        for item in command:
            if item not in SUPPORTED_COMMANDS:
                raise UnknownCommand

        if "toggle_power" in command:
            self.toggle_power()
        
        if "toggle_mode" in command:
            self.toggle_mode()
        
        if "toggle_fan" in command:
            self.toggle_fan()
        
        if "increase_temperature" in command:
            self.increase_temperature()
        
        if "decrease_temperature" in command:
            self.decrease_temperature()
        
        self.send_ir_signal_current_state()

    def update(self):
        
        _LOGGER.debug("Updating entity state...")

        result = os.system(f'ping -c 1 {self._ip_address} > /dev/null')

        if result != 0:
            self._attr_available = False

        elif self._attr_available == False: # Only if previously was unavailable.
            self._attr_available = True

            # Reconnecting to the device, using the new local key.
            self._local_key = self._get_local_key()

            _LOGGER.debug(f"Creating tinytuya 'Device' instance with these parameters: device_id='{self._device_id}', ip_address='{self._ip_address}', local_key: '{self._local_key}'")
            self._device = tinytuya.Device(self._device_id, self._ip_address, self._local_key)

            self._device.set_version(3.3)


        self._attr_extra_state_attributes['power'] = self.current_power
        self._attr_extra_state_attributes['mode'] = self.current_mode
        self._attr_extra_state_attributes['fan'] = self.current_fan
        self._attr_extra_state_attributes['temperature'] = self.current_temperature





