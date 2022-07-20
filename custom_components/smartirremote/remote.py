from typing import Iterable
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.remote import RemoteEntity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME
import tinytuya
from copy import copy
import json
import os

__version__ = "0.0.1"

COMPONENT_REPO = "https://github.com/eyal1izhaki/smartir"

REQUIREMENTS = ["tinytuya"]

CONF_DEVICE_ID = "device_id"
CONF_LOCAL_IP = "local_ip"
CONF_ACCESS_ID = "access_id"
CONF_ACCESS_SECRET = "access_secret"
CONF_DEVICE_HEAD_VALUE = "device_head_value"
CONF_DEVICE_ACTIONS = "device_actions"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_LOCAL_IP): cv.string,
        vol.Required(CONF_ACCESS_ID): cv.string,
        vol.Required(CONF_ACCESS_SECRET): cv.string,
        vol.Required(CONF_DEVICE_HEAD_VALUE): cv.string,
        vol.Required(CONF_DEVICE_ACTIONS): cv.match_all
    }
)


def setup_platform(hass, config, add_devices, discovery_info=None):
    add_devices([MyRemote(
        name = config[CONF_NAME],
        device_id=config[CONF_DEVICE_ID],
        ip_address=config[CONF_LOCAL_IP],
        access_id=config[CONF_ACCESS_ID], 
        access_secret=config[CONF_ACCESS_SECRET],
        head=config[CONF_DEVICE_HEAD_VALUE],
        actions=config[CONF_DEVICE_ACTIONS]
    )])


class MyRemote(RemoteEntity):

    def __init__(self, name: str, device_id: str, ip_address: str, access_id: str, access_secret: str, head: str, actions: dict) -> None:

        super().__init__()
        
        self._attr_name = name
        self._attr_state = None

        self._device_id = device_id
        self._ip_address = ip_address
        self._access_id = access_id
        self._access_secret = access_secret
        self._head = head
        self._actions = copy(actions)
        self._lower_keys(self._actions)

        
        self._cloud = tinytuya.Cloud('eu', access_id, access_secret, device_id)
        
        self._local_key = self._get_local_key()
        self._device = tinytuya.Device(self._device_id, self._ip_address, self._local_key)

        self._device.set_version(3.3)

    def _get_local_key(self):
        devices = self._cloud.getdevices()

        for device in devices:
            if device["id"] == self._device_id:
                print(device["key"])
                return device["key"]


    def _lower_keys(self, dict):

        for key in dict.keys():
            if type(key) != str:
                raise Exception("Keys names must be in str type!")
        value = dict[key]
        del dict[key]
        dict[key.lower()] = value

    def _send_ir_signal(self, key1):
        command = {"control": "send_ir", "head": self._head, "key1": key1, "type": 0, " delay": 300}
        payload = self._device.generate_payload(tinytuya.CONTROL, {"201": json.dumps(command)})
        self._device.send(payload)

    def send_action(self, action_name: str):

        try:
            ir_key1 = self._actions[action_name.lower()]
        except KeyError:
            raise self.UnknownAction

        self._send_ir_signal(ir_key1)

    def _get_action_from_command(self, command):

        power = ""
        mode = ""
        fan = ""
        temperature = ""

        for item in command:
            if item.startswith("power_"):
                power = item.split('_')[1]

            elif item.startswith("mode_"):
                mode = item.split('_')[1]

            elif item.startswith("fan_"):
                fan = item.split('_')[1]

            elif item.startswith("temperature_"):
                temperature = item.split('_')[1]

        if power == 'off':
            return 'off'

        return f"{power}_{mode}_{fan}_{temperature}"

    def send_command(self, command: Iterable[str], **kwargs):
        """Send commands to a device."""

        action = self._get_action_from_command(command)

        self.send_action(action)

    @property
    def state(self):
        return 'online'

    class UnknownAction(Exception):
        pass
