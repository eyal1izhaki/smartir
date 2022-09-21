# smartir
Home Assistant custom component for controlling your Air Conditioner using Tuya S06 Smart IR device

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
      local_ip: <local ip of the smart IR device> (optional, if specified, we won't need to scan the network to get the device ip)
      access_id: <from Tuya iot>
      access_secret: <from Tuya iot>
      data_file: <a data file from smartit/data_files dir>
      debug: <boolean, set to true in order to get debug logs> 

After that, you will get a remote entity that you can use to control your air conditioner.

![screenshot of the entity](https://github.com/eyal1izhaki/smartir/blob/master/screenshots/1.png)
