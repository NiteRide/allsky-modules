import allsky_shared as allsky_shared
from allsky_base import ALLSKYMODULEBASE

import time
import requests
import json

class ALLSKYLIGHTNING(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Lightning Detection",
		"description": "Detects lightning using an as3935 sensor",
		"docs": "docs/allsky_modules/extra/lightning.html",   
		"version": "v1.0.0",
		"module": "allsky_lightning", 
		"centersettings": "false",
		"testable": "true",
		"experimental": "true",
		"group": "Data Sensor",
		"events": [
			"day",
			"night",
			"periodic"
		],
		"extradatafilename": "allsky_lightning.json", 
		"extradata": {
			"values": {
				"AS_LIGHTNING_COUNT": {
					"name": "${LIGHTNING_COUNT}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Number of lightning strikes",
					"type": "number"
				},
				"AS_LIGHTNING_DIST": {
					"name": "${LIGHTNING_DIST}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Approx distance of last strike",
					"type": "number"
				},
				"AS_LIGHTNING_ENERGY": {
					"name": "${LIGHTNING_ENERGY}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Energy of last strike",
					"type": "number"
				},
				"AS_LIGHTNING_LAST": {
					"name": "${LIGHTNING_LAST}",
					"format": "",
					"sample": "",                 
					"group": "Environment",
					"description": "Date/Time of last strike",
					"type": "timestamp"
				}                                        
			}                
		},
		"arguments":{
			"i2caddress": "",
			"interruptpin": "",
			"maskdisturbers": "True",
			"noiselevel": 2,
			"watchdogthreshold": 2,
			"spikerejection": 2,
			"lightningthreshold": 1,
			"expirestrikes": 600
		},
		"argumentdetails": {
			"i2caddress": {
				"required": "false",
				"description": "I2C Address",
				"help": "Override the standard i2c address for a device. NOTE: This value must be hex, i.e., 0x03.",
				"type": {
					"fieldtype": "i2c"
				}           
			},
			"interruptpin": {
				"required": "false",
				"description": "Input Pin",
				"help": "The input pin for the lightning sensor.",
				"type": {
					"fieldtype": "gpio"
				}           
			},
			"maskdisturbers" : {
				"required": "false",
				"description": "Mask disturbers",
				"help": "If enabled disturbers will be ignored.",
				"tab": "Advanced",
				"type": {
					"fieldtype": "checkbox"
				}            
			},
			"noiselevel" : {
				"required": "false",
				"description": "Noise level",
				"help": "Sets the base noise level, 1 is lowest 7 is highest ambient noise.",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 7,
					"step": 1
				}                      
			},
			"watchdogthreshold" : {
				"required": "false",
				"description": "Watchdog Threshold",
				"help": "Minimum signal level to trigger the lightning verification algorithm (1-10).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 1
				}                      
			},
			"spikerejection" : {
				"required": "false",
				"description": "Spike Rejection",
				"help": "The default setting is two. The shape of the spike is analyzed during the chip's validation routine. You can round this spike at the cost of sensitivity to distant events (1-11).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 11,
					"step": 1
				}                      
			},
			"lightningthreshold" : {
				"required": "false",
				"description": "Strike Threshold",
				"help": "The number of strikes detected before an event is triggered.",
				"tab": "Advanced",
				"type": {
					"fieldtype": "select",
					"values": "1,5,9,16",
					"default": "None"
				}
			},
			"expirestrikes" : {
				"required": "false",
				"description": "Expire Strikes",
				"help": "If a strike is detected then after this number of seconds of no strikes the strikes overlay variable and strike counter will be reset. Default is 600 seconds (10 minutes).",
				"tab": "Advanced",            
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 3600,
					"step": 1
				}                      
			}                                                     
		},
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Alex Greenland",
					"authorurl": "https://github.com/allskyteam",
					"changes": "Initial Release"
				}
			]                              
		}         
	}
    
	def run(self):
     
		mask_disturbers = self.get_param('maskdisturbers', True, bool)
		noise_level = self.get_param('noiselevel', 2, int)
		watchdog_threshold = self.get_param('watchdogthreshold', 2, int)
		spike_rejection = self.get_param('spikerejection', 2, int)
		lightning_threshold = self.get_param('lightningthreshold', 1, int)
		expire_strikes = self.get_param('expirestrikes', 600, int)
		interrupt_pin = self.get_param('interruptpin', '21', str, True)
		i2c_address = self.get_param('i2caddress', '', str)

		config = {
			"interruptpin": interrupt_pin,
			"i2caddress": i2c_address,
			"maskdisturbers": mask_disturbers,
			"noiselevel": noise_level,
			"watchdogthreshold": watchdog_threshold,
			"spikerejection": spike_rejection,
			"lightningthreshold": lightning_threshold
		}

		try:
			api_url = allsky_shared.get_api_url()
			config_response = requests.put(f'{api_url}/lightning/config', json=config, timeout=5)
			if config_response.status_code == 503:
				data = config_response.json()
				result = data.get("error", "Lightning monitor is not available")
				self.log(0, f'ERROR in {__file__}: {result}')
				return result

			config_response.raise_for_status()

			status_response = requests.get(f'{api_url}/lightning/status', timeout=2)
			status_response.raise_for_status()
			status = status_response.json()
   
			print(json.dumps(status, indent=4))
   
			if not status.get("running"):
				result = status.get("error", "Lightning monitor is not running")
				self.log(0, f'ERROR in {__file__}: {result}')
				return result

			count = int(status.get("strike_count") or 0)
			last_strike_time = status.get("last_strike")
			distance_to_storm = status.get("distance") or 0
			lightning_energy = status.get("energy") or 0
			last_interrupt_type = status.get("last_interrupt_type")

			extra_data = {}
			extra_data['AS_LIGHTNING_COUNT'] = count
			extra_data['AS_LIGHTNING_LAST'] = last_strike_time
			extra_data['AS_LIGHTNING_DIST'] = distance_to_storm
			extra_data['AS_LIGHTNING_ENERGY'] = lightning_energy

			if last_strike_time is not None:
				now = int(time.time())
				if (now - int(last_strike_time)) > expire_strikes:
					requests.post(f'{api_url}/lightning/reset', timeout=2).raise_for_status()
					count = 0
					last_strike_time = None
					extra_data['AS_LIGHTNING_COUNT'] = 0
					extra_data['AS_LIGHTNING_LAST'] = None
					extra_data['AS_LIGHTNING_DIST'] = 0
					extra_data['AS_LIGHTNING_ENERGY'] = 0

			allsky_shared.saveExtraData(self.meta_data['extradatafilename'], extra_data, self.meta_data['module'], self.meta_data['extradata'], event=self.event)
			allsky_shared.dbUpdate('allsky_lightning_strike_counter', count)
			if last_strike_time is not None:
				allsky_shared.dbUpdate('allsky_lightning_last_strike', last_strike_time)
			else:
				allsky_shared.db_delete_key('allsky_lightning_last_strike')

			result = f'Lightning monitor running on GPIO {interrupt_pin}. Strikes: {count}'
			if last_interrupt_type == "lightning":
				result = f'Strike detected. Approx distance: {distance_to_storm}km, Energy: {lightning_energy}, Total Strikes: {count}'

			self.log(4, f'INFO: {result}')
			return result

		except requests.exceptions.ConnectionError:
			result = 'Unable to connect to the Allsky server. Is it running?'
			self.log(0, f'ERROR in {__file__}: {result}')
			return result
		except requests.exceptions.RequestException as e:
			result = f'Lightning monitor request failed: {e}'
			self.log(0, f'ERROR in {__file__}: {result}')
			return result
   							
def lightning(params, event):
	allsky_lightning = ALLSKYLIGHTNING(params, event)
	result = allsky_lightning.run()
 
	return result

def lightning_cleanup():
	moduleData = {
	    "metaData": ALLSKYLIGHTNING.meta_data,
	    "cleanup": {
	        "files": {
	            ALLSKYLIGHTNING.meta_data['extradatafilename']
	        },
	        "env": {}
	    }
	}
	allsky_shared.cleanupModule(moduleData)
