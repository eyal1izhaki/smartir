# smartir
Home Assistant custom component to control your Air Conditioner using Tuya S06 Smart IR device

# This component is under development, Please feel free to open an issue for any question or a bug.


This component provides local control, using tiny tuya python package.

Prerequirements:
  1. Read https://github.com/jasonacox/tinytuya/blob/master/README.md carfully and follow the instructions in order to create tuya developer account.
  2. Get the device id, access id, access secret from tyua iot. Read https://github.com/jasonacox/tinytuya/blob/master/README.md again.
  3. You need to create a data file that fits your air conditioner, this data file will contain all the codes to control the air contidioner.

Add to homeassistant:

  1. Clone this repo
  2. Copy custom_component/smartir dir into your homeassistant config/custom_compoent dir.
  3. Add to your config/configurations.yaml
  
    remote:
      platform: smartir
      name: <Name of the entity>
      device_id: <from Tuya iot>
      local_ip: <local ip of the smart IR device>
      access_id: <from Tuya iot>
      access_secret: <from Tuya iot>
      data_file: <a data file from smartit/data_files dir>