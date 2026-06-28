import allsky_shared as allsky_shared
import resizeImage as img_resize
from allsky_base import ALLSKYMODULEBASE

import os
import re
import shlex
import subprocess
import datetime
from pathlib import Path
import cv2
import glob
import shutil
import numpy as np

# GLOBALS
ALLSKY_HOME = allsky_shared.getEnvironmentVariable("ALLSKY_HOME")
ALLSKY_IMAGES = allsky_shared.getEnvironmentVariable("ALLSKY_IMAGES", fatal=True)
base_dir = allsky_shared.getSetting("imagepath") or ALLSKY_IMAGES
ALLSKY_CONFIG = allsky_shared.getEnvironmentVariable("ALLSKY_CONFIG", fatal=True)
ALLSKY_TMP = allsky_shared.ALLSKY_TMP
EXT = allsky_shared.get_environment_variable("ALLSKY_EXTENSION", fatal=True)

default_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")	# today minus one
process_date = ""
process_dir = ""
debug_logging_timelapse = False
timelapse_use_AS_settings = False
timelapse_debug_test = False

class ALLSKYKEOTIMELAPSESTARTRAILS(ALLSKYMODULEBASE):

	meta_data = {
		"name": "Allsky Keo Timelapse Stars",
		"description": "Create daily Keogram, Timelapse, and Startrails files.",
		"module": "allsky_keo_timelapse_startrails", 
		"version": "v1.0.0",   
		"centersettings": "false",
		"testable": "true",
		"group": "Allsky Core",
		"pythonversion": "3.10.0",
		"events": [
			"nightday"
		],
		"experimental": "true",
		
		"arguments": {
			"keogram_use_settings":"",
			"keogram_create" : "",
			"keogram_expand" : "",
			"keogram_rotation" : "0",
			"keogram_resize": "",
			"keogram_show_labels": "Date and Time",
			"keogram_font_name" : "Simplex",
			"keogram_font_color" : "#ffffff",
			"keogram_font_size" : 2,
			"keogram_font_thickness" : 2,
			"keogram_extraparams" : "",

			"startrails_use_settings":"",
			"startrails_create" :"",
			"startrails_brightness" : 0.2,
			"startrails_dayimages" : "",
			"startrails_image_range" : 0,
			"startrails_mask" :"",
			"startrails_extraparams" :"",

			"timelapse_use_AS_settings": "Module Settings",
			"timelapse_create" : "true",
			"keolapse_overlay" : "true",
			"timelapse_fps": "24",
			"timelapse_bitrate": "2000",
			"resolution": "720p",
			"timelapse_custom_resolution": "720",
			"timelapse_max_length": "120",
			"timelapse_extraparams" : "",
			"timelapse_preset": "medium",
			"timelapse_vcodec": "libx264",
			"timelapse_pixel_format": "yuv420p",
			"keolapse_mask" : "",
			"keolapse_start_position": "Bottom",
			"keolapse_height": "175",
			"keolapse_edge_borders": "3",
			"keolapse_progress_color": "White",
			"keolapse_progress_color_custom": "#f801ae",
			"keolapse_border_width": "2",
			"keolapse_border_color": "Blue Steel",
			"keolapse_border_color_custom": "#99a8c4",

			"process_date" : "",
			"keogram_test" : "",
			"startrails_test" : "",
			"timelapse_test" : "None",

			"timelapse_setup_test": "false",
			"debug_generate": "Debug Image",

			"debug_logging_timelapse": "false",
			"timelapse_keep_sequence" : "false"

		},

		"argumentdetails" : {        
			"keogram_use_settings": {
				"required": "false",
				"description": "Settings to Use",
				"help": "Use module settings (from this tab) or use settings you configured in the Main Allsky Settings page.  When using module settings you should disable 'Generate' on the main settings page to reduce duplicate processing.",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "select",
					"values": "Module Settings,Allsky Settings Page"
				}
			},
			"keogram_create" : {
				"required": "false",
				"description": "Generate",
				"help": "Enable to create daily keogram",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"keogram_expand" : {
				"required": "false",
				"description": "Expand",
				"help": "Enable to expand keogram to the image width. (Will avoid tall skinny images)",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}                 
			},
			"keogram_rotation" : {
				"required": "false",
				"description": "Rotate",
				"help": "(Optional) Number of degrees to rotate captured images so the North-South meridian would go straight from top to bottom when building the keogram.  <i><code>+</code> for counterclockwise, <code>-</code> for clockwise</i><br><i>Original images will not be rotated.</i><hr>",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "spinner",
					"min": -364,
					"max": 364,
					"step": 1
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				} 
			},			
			"keogram_resize": {
				"required": "false",
				"description": "Resize Upload",
				"help": "Resize the uploaded image.  Specify a target percent, width, height, or fixed dimensions.<ul><li>Percent of original size (eg '50<span class='WebUIValue'>%</span>)</li><li>Height (eg '720<span class='WebUIValue'>h</span>') <i>Width is auto-scaled</i></li><li>Width (eg '1000<span class='WebUIValue'>w</span>')  <i>Height is auto-scaled</i></li><li>Fixed dimensions in WxH (eg '640<span class='WebUIValue'>x</span>480')</li></ul>",
				"tab": "Keogram Settings",
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				} 
			},
			"keogram_show_labels": {
				"required": "false",
				"description": "Show labels",
				"help": "Choose which marker labels will display on the keogram.<hr>",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "select",
					"values": "Date and Time,Time Only,No Labels"
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}              
			},
			"keogram_font_name": {
				"required": "true",
				"description": "Font Name",
				"help": "Font name.",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "select",
					"values": "Simplex,Plain,Duplex,Complex,Complex Small,Triplex,Script Simplex,Script Complex"
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				} 
			},
			"keogram_font_color": {
				"required": "false",
				"description": "Font Color",
				"help": "Font color.  #ffffff is white.  See the documentation for a description of this field.<br><hr>",
				"tab": "Keogram Settings",
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"keogram_font_size": {
				"required": "false",
				"description": "Font Size",
				"help": "Font Size.",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 0.1
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}           
			},
			"keogram_font_thickness": {
				"required": "false",
				"description": "Font thickness",
				"help": "Font Line thickness.",
				"tab": "Keogram Settings",
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 10,
					"step": 1
				},
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}           
			},
			"keogram_extraparams": {
				"required": "false",
				"description": "Extra parameters",
				"tab": "Keogram Settings",
				"help": "Optional additional keogram creation parameters.<br>Run <code>~/allsky/bin/keogram --help</code> for a list of options or see the documentation.",
				"filters": {
					"filter": "keogram_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},

			"stars_notice_a": {
				"message": "Using Module settings allows to mask final image and to use only nighttime images.",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				}
			},
			"startrails_use_settings": {
				"required": "false",
				"description": "Settings to Use",
				"help": "Use module settings (from this tab) or use settings you configured in the Main Allsky Settings page.  When using module settings you should disable 'Generate' on the main settings page to reduce duplicate processing.",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "select",
					"values": "Module Settings,Allsky Settings Page"
				}
			},
			"startrails_create" : {
				"required": "false",
				"description": "Generate",
				"help": "Enable to create a daily startrails image.",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "startrails_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},	
			"startrails_brightness" : {
				"required": "false",
				"description": "Brightness Threshold",
				"help": "Images with a brightness higher than this threshold will not be included in the startrails.",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 1,
					"step": 0.01
				},           
				"filters": {
					"filter": "startrails_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"startrails_mask" : {
				"required": "false",
				"description": "Mask final image",
				"help": "Select or create a mask to remove items such as blurred overlay text from the final startrails image.<hr>",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "image"
				},     
				"filters": {
					"filter": "startrails_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"startrails_dayimages" : {
				"required": "false",
				"description": "Include Daytime Images",
				"help": "By default the module only uses Nighttime images to create startrails.  Enable to include daytime images when creating startrails image (rarely used).",
				"tab": "Startrails Settings",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "startrails_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},				
			"startrails_extraparams" : {
				"required": "false",
				"description": "Extra Parameters",
				"help": "Optional additional startrails creation parameters.<br>Run <code>~/allsky/bin/startrails --help</code> for a list of options.",
				"tab": "Startrails Settings",           
				"filters": {
					"filter": "startrails_use_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},			

			"timelapse_create" : {
				"required": "false",
				"description": "Generate",
				"help": "Enable to create a daily timelapse.",
				"tab": "Timelapse Settings",			
				"type": {
					"fieldtype": "checkbox"
				}
			},		
			"timelapse_use_AS_settings": {
				"required": "false",
				"description": "Parameters From",
				"help": "Use module settings (from this tab) or use settings you configured in the Main Allsky Settings page.  When using module settings you should disable 'Generate' on the main settings page to reduce duplicate processing.",
				"tab": "Timelapse Settings",
				"type": {
					"fieldtype": "select",
					"values": "Module Settings,Allsky Settings Page"
				}
			},			
			"resolution": {
				"required": "true",
				"description": "Target Output Resolution",
				"help": "Target resolution of output video. Higher resolutions require more processing time",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "video_size",
					"title": "Video Size",
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "720p,1080p,4k,Custom,No Resizing"
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_custom_resolution": {
				"required": "false",
				"description": "Target Height",
				"help": "Specify target height of video in pixels. Higher resolutions require more processing time.",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "video_size",
					"title": "Video Size",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 80,
					"max": 10000,
					"step": 20
				},
				"filters": [
					{
						"filter": "timelapse_use_AS_settings",
						"filtertype": "show",
						"values": [
							"Module Settings"
						]
					},
					{
						"filter": "resolution",
						"filtertype": "show",
						"values": [
							"Custom"
						]
					}
				]
			},
			"timelapse_max_length": {
				"required": "true",
				"description": "Max Length (s)",
				"help": "Target maximum length in seconds. Longer videos require more processing time and storage",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "video_settings",
					"title": "Video Setup",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 15,
					"max": 300,
					"step": 5
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_fps": {
				"required": "true",
				"description": "FPS (speed)",
				"help": "Frames Per Second. Higher values create smoother but faster videos",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "video_settings",
					"title": "Video Setup",
					"width": 4
				},			
				"type": {
					"fieldtype": "spinner",
					"min": 5,
					"max": 30,
					"step": 1
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_bitrate": {
				"required": "true",
				"description": "Bitrate (kbps)",
				"help": "Bitrate for video",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "video_settings",
					"title": "Video Setup",
					"width": 4
				},			
				"type": {
					"fieldtype": "spinner",
					"min": 800,
					"max": 8000,
					"step": 100
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},

			"video_advanced_settings_notice": {
				"tab": "Timelapse Settings",
				"source": "local",
				"html": "<HR><b>Advanced Video Settings (rarely used):</b><br><br>",
				"type": {
					"fieldtype": "html"
				}
			},
			"timelapse_extraparams" : {
				"required": "false",
				"description": "Extra Parameters",
				"help": "Optional additional timelapse creation parameters. Run ffmpeg -? to see the options.  If quality is poor or the video does not play on Apple devices, try adding -level 3.1.",
				"tab": "Timelapse Settings",
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_preset": {
				"required": "false",
				"description": "Preset",
				"help": "Encoder speed/quality preset for timelapse. Slower presets usually compress better but take longer.",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "adv_params",
					"title": "Encoder Settings     ",					
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "veryfast,faster,fast,medium,slow,slower,veryslow"
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_vcodec": {
				"required": "false",
				"description": "VCODEC",
				"help": "Video encoder for timelapse. Rarely changed.",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "adv_params",
					"title": "Encoder Settings     ",
					"width": 4
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},
			"timelapse_pixel_format": {
				"required": "false",
				"description": "Pixel format",
				"help": "Pixel format for timelapse. Rarely changed.",
				"tab": "Timelapse Settings",
				"layout" : {
					"row": "adv_params",
					"width": 4
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			},

			"keolapse_overlay" : {
				"required": "false",
				"description": "Overlay on Timelapse",
				"help": "Overlays an animated keogram tracked in sync with the timelapse (like a clock going around).",
				"tab": "Keolapse Animation",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"keolapse_mask" : {
				"required": "false",
				"description": "Keolapse Positioning",
				"help": "Select or create a circular mask to position the keogram.  The circle's border represents the inner edge for the keogram. If blank a really big circle will be used.",
				"tab": "Keolapse Animation",
				"type": {
					"fieldtype": "image"
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_height": {
				"required": "true",
				"description": "Ring Height (px)",
				"help": "Height of keogram ring in pixels",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_fit",
					"title":"Keolapse Fit",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 50,
					"max": 400,
					"step": 25
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_edge_borders": {
				"required": "true",
				"description": "Image Padding (px)",
				"help": "Minimum padding between edge of keolapse and edges of the image (in pixels)",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_fit",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 0,
					"max": 25,
					"step": 1
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_start_position": {
				"required": "true",
				"description": "Start Position",
				"help": "Clock hour position to start keogram (12: top, 3: right, 6: bottom, 9: left)",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_progress_indicator",
					"title":"Progress Indicator",
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "Top,Bottom,Left,Right"
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_progress_color": {
				"required": "true",
				"description": "Color",
				"help": "Color of progress indicator on the keogram",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_progress_indicator",
					"title":"Progress Indicator",
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "White,Cyan,Red,Yellow,Green,Moon Glow,Blue Steel,Midnight,Black,Custom"
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_progress_color_custom": {
				"required": "false",
				"description": "Hex Code",
				"help": "hex color for progress indicator on the keogram",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_progress_indicator",
					"width": 4
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					},
					{
						"filter": "keolapse_progress_color",
						"filtertype": "show",
						"values": [
							"Custom"
						]
					}
				]
			},
			"keolapse_border_width": {
				"required": "true",
				"description": "Width (px)",
				"help": "Width of inner and outer edges of the keogram in pixels",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_border_colors",
					"title":"Keolapse Border",
					"width": 4
				},
				"type": {
					"fieldtype": "spinner",
					"min": 1,
					"max": 8,
					"step": 1
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_border_color": {
				"required": "true",
				"description": "Color",
				"help": "Color of inner and outer edges of the keogram",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_border_colors",
					"title":"Keolapse Borders",
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "White,Cyan,Red,Yellow,Green,Moon Glow,Blue Steel,Midnight,Black,Custom"
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					}
				]
			},
			"keolapse_border_color_custom": {
				"required": "false",
				"description": "Custom Hex Code",
				"help": "hex color for border on the keogram",
				"tab": "Keolapse Animation",
				"layout" : {
					"row": "keo_border_colors",
					"width": 4
				},
				"filters": [
					{
						"filter": "keolapse_overlay",
						"filtertype": "show",
						"values": [
							"true"
						]
					},
					{
						"filter": "keolapse_border_color",
						"filtertype": "show",
						"values": [
							"Custom"
						]
					}
				]
			},

			"process_date": {
				"required": "false",
				"description": "Folder to process",
				"help": "Images folder to process.  eg \"20250801\"  -- Will use the prior nights folder if left blank.",
				"tab": "Testing - Generate for Day"
			},

			"startrails_test" : {
				"required": "false",
				"description": "Startrails",
				"help": "",
				"tab": "Testing - Generate for Day",
				"type": {
					"fieldtype": "select",
					"values": "None,Generate,Generate and Upload,Upload Only,Quick Setup Test"
				}
			},
			"keogram_test" : {
				"required": "false",
				"description": "Keogram",
				"help": "",
				"tab": "Testing - Generate for Day",
				"type": {
					"fieldtype": "select",
					"values": "None,Generate,Generate and Upload,Upload Only,Quick Setup Test"
				}
			},
			"timelapse_test" : {
				"required": "false",
				"description": " ",
				"help": "",
				"tab": "Testing - Generate for Day",
				"layout" : {
					"row": "timelapse_testing",
					"title":"Timelapse / Keolapse",
					"width": 6
				},
				"type": {
					"fieldtype": "select",
					"values": "None,Generate,Generate and Upload,Upload Only,Quick Setup Test"
				}
			},
			"debug_generate": {
				"required": "true",
				"description": " ",
				"help": "",
				"tab": "Testing - Generate for Day",
				"layout" : {
					"row": "timelapse_testing",
					"title":"Timelapse / Keolapse",
					"width": 4
				},
				"type": {
					"fieldtype": "select",
					"values": "Debug Image,Debug Video"
				},
				"filters": {
					"filter": "timelapse_test",
					"filtertype": "show",
					"values": [
						"Quick Setup Test"
					]
				}
			},
			"fake_field": {
				"required": "false",
				"description": "Has to be here so alert box is indented in layout/row (filtered to be hidden)",
				"help": "",
				"tab": "Testing - Generate for Day",
				"layout" : {
					"row": "timelapse_testing2",
					"title":" ",
					"width": 0
				},
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "timelapse_test",
					"filtertype": "show",
					"values": [
						"BARF!"
					]
				}
			},
			"test_quicktimelapse_notice": {
				"message": "Quick Setup uses a temporary copy of about one hour's worth of images to speed creation. Outputs can be viewed below, or from the images/test folder until removed at the end of each night.<br><p style=\"margin-left: 120px;\"><a href=\"images/test/keolapse_debug.jpg\" target=\"_blank\">View Test Image</a><span style=\"margin-left: 80px;\"><a href=\"images/test/allsky-test.mp4\" target=\"_blank\">View Test Video</a></span></p>",
				"tab": "Testing - Generate for Day",
				"layout" : {
					"row": "timelapse_testing2",
					"title":" ",
					"width": 12
				},
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "light"
						}
					}
				},
				"filters": {
					"filter": "timelapse_test",
					"filtertype": "show",
					"values": [
						"Quick Setup Test"
					]
				}
			},
			"test_notice": {
				"message": "Using the [Test Module] button:  <ul><li>Choose a folder to process</li><li>Choose files you to generate and or upload to your local or remote websites or servers as configured in Allsky Settings.</li><li>This will overwrite existing files on your pi and/or the destination. It can act as a 'generate for day' function.</li><li>For Timelapse/Keolapse, you can choose 'Quick Setup Test' for a fast validation run.</li></ul>",
				"tab": "Testing - Generate for Day",
				"type": {
					"fieldtype": "text",
					"style": {
						"width": "full",
						"alert": {
							"class": "info"
						}
					}
				},
				"filters": {
					"filter": "timelapse_test",
					"filtertype": "hide",
					"values": [
						"Quick Setup Test BARF!"
					]
				}
			},

			"timelapse_debug_notice": {
				"tab": "Debug",
				"source": "local",
				"html": "<HR><b>Timelapse Debug Settings:</b><br><br>",
				"type": {
					"fieldtype": "html"
				}
			},

			"debug_logging_timelapse": {
				"required": "false",
				"description": "Enable Debug Logging",
				"help": "Enable detailed logging for troubleshooting",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				}
			},
			"timelapse_keep_sequence" : {
				"required": "false",
				"description": "Keep Video Sequence",
				"help": "For debugging purposes only. Enable to keep the list of files used in creating the timelapse video.",
				"tab": "Debug",
				"type": {
					"fieldtype": "checkbox"
				},
				"filters": {
					"filter": "timelapse_use_AS_settings",
					"filtertype": "show",
					"values": [
						"Module Settings"
					]
				}
			}
		},
		"enabled": "true",
		"changelog": {
			"v1.0.0" : [
				{
					"author": "Kentner Cottingham",
					"authorurl": "https://github.com/AllskyTeam",
					"changes": [
						"Refactored and incorporated Keoplapse code originally completed by Jim Cauthen",
						"Modified settings for keolapse including using mask for placement color optoins video quality NEW"
					]
				}
			],
			"v0.0.1": [
				{
					"author": "Kentner Cottingham",
					"authorurl": "https://github.com/AllskyTeam",
					"changes": [
						"Initial version",
						"Configured to run kepgram and startrails"
					]
				}
			]
		}
	}

	def __check_extra_params(self, extra_params: str, blocked_flags: set, param_type: str) -> list:
		'''Parse and validate extra parameters against a set of blocked flags.
		
		Args:
			extra_params: Space or quote-separated parameter string
			blocked_flags: Set of flag names that are reserved (not allowed) by module settings
			param_type: Name of the feature for error messages (e.g., "Startrails", "Keogram")
			
		Returns:
			List of parsed arguments if valid
			
		Raises:
			ValueError: If parsing fails or blocked flags are detected
		'''
		if not extra_params:
			return []
		
		try:
			extra_args = shlex.split(extra_params)
		except ValueError as ex:
			raise ValueError(f"Invalid {param_type} extra parameters: {ex}")
		
		conflicts = []
		for token in extra_args:
			if token in blocked_flags:
				conflicts.append(token)
			elif token.startswith("--") and "=" in token:
				base_flag = token.split("=", 1)[0]
				if base_flag in blocked_flags:
					conflicts.append(base_flag)
		
		if conflicts:
			unique_conflicts = ", ".join(sorted(set(conflicts)))
			raise ValueError(f"{param_type} extra parameters contain blocked option(s): {unique_conflicts}. Remove these options from Extra Parameters.")
		
		return extra_args

	def __run_script(self, script: Path, *args: str) -> tuple[int, str, str]:

		script_str = str(script)
		
		# Ensure output tokens are separate already in *args
		if os.access(script, os.X_OK):
			cmd = [script_str, *args]
		
		if not os.access(script_str, os.X_OK):
			cmd = ["bash", script_str, *args]		# Fallback to bash if not executable

		# Avoid sudo permission issues in debug runs by executing as ALLSKY_OWNER when available.
		if self.debugmode:
			username = allsky_shared.get_environment_variable("ALLSKY_OWNER")
			if username:
				cmd = ["runuser", "-u", username, "--", script_str, *args]
				if not os.access(script_str, os.X_OK):
					cmd = ["runuser", "-u", username, "--", "bash", script_str, *args]
					allsky_shared.log(1, "running as bash")
			else:
				allsky_shared.log(1, "WARNING: ALLSKY_OWNER not set; running script directly in debug mode")

		allsky_shared.log(4, f"DEBUG: Script Args - {cmd}")

		try:
			script_result = subprocess.run(cmd, capture_output=True, text=True, check=False)
			if script_result.returncode == 0:
				allsky_shared.log(3, f"INFO: Successful: {script_str}")
			else:
				allsky_shared.log(0, f"ERROR: {script_str} - rc={script_result.returncode}\nSTDERR:\n{script_result.stderr}")
			return script_result.returncode, script_result.stdout, script_result.stderr
		
		except Exception as e:
			return 1, "", str(e)

	def __do_upload(self, type, filename, source_fullpath, thumbname=None, source_thumbpath=None):
		'''parses required details for filetype and then calls upload script
		'''
		out_subdir = ""
		out_thumb_dir = ""
		tmp_image_path=""
		target_file = filename
		up_thumb = allsky_shared.getSetting("timelapseuploadthumbnail")
		source_fullpath = source_fullpath
		uselocalweb = allsky_shared.getSetting("uselocalwebsite")
		useremoteweb = allsky_shared.getSetting("useremotewebsite")
		useremoteserver = allsky_shared.getSetting("useremotewebserver")
		result =""
		
		def call_upload_script(target, source_fullpath, remote_dir, target_file):
			source_fullpath=source_fullpath
			upload_script_path = os.path.join(ALLSKY_HOME, "scripts", "upload.sh")
			target_clean = target.replace("--", "")
			target_clean = target_clean.replace("-", " ")
			#run upload script
			upload_rc, out, err = self.__run_script(upload_script_path, target, source_fullpath, remote_dir, target_file)
			if upload_rc == 0:
				allsky_shared.log(1, f"INFO: {type} uploaded successfully to {target_clean}: {target_file}")
			else:
				allsky_shared.log(0, f"ERROR: Failed to upload {type} to {target_clean} (rc={upload_rc}). See stderr:\n{err}")
		up_thumb = False
		if type == "keogram":
			out_subdir = "keograms"
			if allsky_shared.getSetting("remoteserverkeogramdestinationname"):
				remoteserver_destination_name=allsky_shared.getSetting("remoteserverkeogramdestinationname")
			else:
				remoteserver_destination_name=filename
		if type == "startrails":
			out_subdir = "startrails"
			if allsky_shared.getSetting("remoteserverstartrailsdestinationname"):
				remoteserver_destination_name=allsky_shared.getSetting("remoteserverstartrailsdestinationname")
			else:
				remoteserver_destination_name=filename
		if type == "timelapse":
			out_subdir = "videos"
			if allsky_shared.getSetting("remoteserverimageuploadoriginalname"):
				remoteserver_destination_name=filename
			else:
				remoteserver_destination_name=allsky_shared.getSetting("remoteservertimelapsedestinationname")
			if up_thumb and thumbname and source_thumbpath:
				out_thumb_dir = "videos/thumbnails"
			else:
				up_thumb = False

		# local website
		if uselocalweb:
			target = "--local-web"
			remote_dir = os.path.join(ALLSKY_HOME, "html","allsky", out_subdir)

			upfile = call_upload_script(target, source_fullpath, remote_dir, target_file)
			if up_thumb:
				remote_thumb_dir = os.path.join(ALLSKY_HOME, "html", "allsky", out_thumb_dir)
				upthumb = call_upload_script(target, source_thumbpath, remote_thumb_dir, thumbname)

			#run upload script
			#upload_keo_rc, out, err = self.__run_script(upload_script_path, target, source_fullpath, remote_dir, target_file)
			#if upload_keo_rc == 0:
			#	allsky_shared.log(1, f"INFO: {type} uploaded successfully to local web: {os.path.join(output_dir, filename)}")
			#else:
			#	allsky_shared.log(0, f"ERROR: Failed to upload {type} to {target} (rc={create_keo_rc}). See stderr:\n{err}")

		if useremoteweb:
			target = "--remote-web"
			remote_dir = allsky_shared.getSetting("remotewebsiteimagedir")+"/"+out_subdir
			
			upfile=call_upload_script(target, source_fullpath, remote_dir, target_file)

			if up_thumb:
				remote_thumb_dir = allsky_shared.getSetting("remotewebsiteimagedir")+"/"+out_thumb_dir
				upthumb = call_upload_script(target, source_thumbpath, remote_thumb_dir, thumbname)

		# remote website need to check "upload with original name?"
		if useremoteserver:
			target = "--remote-server"
			remote_dir = allsky_shared.getSetting("remoteserverimagedir")+"/"+out_subdir
			target_file = remoteserver_destination_name

			upfile=call_upload_script(target, source_fullpath, remote_dir, target_file)
			
			if up_thumb:
				remote_thumb_dir = allsky_shared.getSetting("remoteserverimagedir")+"/"+out_thumb_dir
				upthumb = call_upload_script(target, source_thumbpath, remote_thumb_dir, thumbname)
	
		# delete temp file if it was created
		if os.path.exists(tmp_image_path):
			os.remove(tmp_image_path)

		return result

	def __make_imageprocessinglist(self,type, process_date, process_dir,output_file):
		'''
		type = "startrails" "timelapse" (?? "keogram")
		process_dirs [dir1, dir2]					designed for multiple for future capability (say timelapse noon - noon)

		make a text file in allsky tmp that contains a list of files to process.
		eg produced file can be passed on to a script like timelapse or startrails in lieu of processing a folder directly.
		need dirs (array), start limit, end limit, file ext, output filename
		returns full filepath of .txt file
		'''
		from datetime import datetime, timedelta

		def make_dtstr(date_str: str, time_str: str) -> datetime:
			combined_str = f"{date_str}{time_str}"
  			# Parse the combined string into a datetime object
			dt_object = datetime.strptime(combined_str, "%Y-%m-%d%H:%M:%S")		
			# Format the datetime object to the desired output format
			formatted_output = dt_object.strftime("%Y%m%d%H%M%S")
			return formatted_output

		type = type
		out_file = output_file

		if type =="startrails":
			use_day_images = self.get_param('startrails_dayimages', False, bool)
		else:
			return False
		

		# parse start /end date from first process_dir for sunwait
		#get this from passed array 
		start_dir = process_dir
		end_dir = process_dir		# placeholder for processing multiple dirs someday
		dirs = [start_dir]			# as array for future capbility (eg process two folders for noon-noon timelapse)

		start_date = process_date
		start_date_obj = datetime.strptime(start_date, "%Y%m%d").date()

		end_date_obj = start_date_obj + timedelta(days=1)		# Add one day
		end_date = str(end_date_obj.strftime("%Y%m%d"))		# Convert back to string
		
		# breakdown for sunwait
		y1 = start_date[2:4]	# year (2 characters)
		m1 = start_date[4:6]	# month (next 2 characters)
		d1 = start_date[6:8]	# day (last 2 characters)

		y2 = end_date[2:4]		# year (2 characters)
		m2 = end_date[4:6]		# month (next 2 characters)
		d2 = end_date[6:8]		# day (last 2 characters)
		
		if not use_day_images:
			filtered_file_list = True
			#use sunwait  to get start and stop times
			angle = allsky_shared.getSetting("angle")
			lat = allsky_shared.getSetting("latitude")
			lon = allsky_shared.getSetting("longitude")
			
			#call sunwait script
			sunwait = "/usr/bin/sunwait"
			night_st_params = [
				"list", "1", lat, lon, 
		  		"sunset",
				"y", y1, "m", m1, "d", d1,
				"angle", str(angle)
			]
			night_end_params = [
				"list", "1", lat, lon,
		  		"sunrise",
				"y", y2, "m", m2, "d", d2,
				"angle", str(angle)
			]
			
			rc, start_time, err = self.__run_script(sunwait, *night_st_params)
			start_time=start_time.strip()
			if rc == 0:
				st_time_obj = datetime.strptime(start_time, "%H:%M").time()
			
			rc, end_time, err = self.__run_script(sunwait, *night_end_params)
			end_time = end_time.strip()
			if rc == 0:
				end_time_obj = datetime.strptime(end_time, "%H:%M").time()

			#convert the date and time info into string like in filenames
			start_str=make_dtstr(start_date_obj,st_time_obj)
			end_str=make_dtstr(end_date_obj,end_time_obj)

		# Regex for the image filenames to match datetime for inclusion
		img_file_pattern = re.compile(r"^image-(\d{14})\." + EXT + r"$")

		# Process each directory, appending matches
		for dir_path in dirs:
			'''if not os.path.isdir(dir_path):
				print(f"Skipping non‑existent directory: {dir_path}")
				continue'''

			use_files = []
			for entry in os.listdir(dir_path):
				full_path = os.path.join(dir_path, entry)
				if not os.path.isfile(full_path):
					continue

				m = img_file_pattern.match(entry)
				
				if filtered_file_list:
					if m and start_str <= m.group(1) <= end_str:
						use_files.append(entry)
				else:
					if m:
						use_files.append(entry)

		# make the file and save
		if use_files:
			with open(out_file, "a", encoding="utf-8") as out_f:
				out_f.write("\n".join(use_files) + "\n")
			#TODO: should this be logged?
			print(f"Appended {len(use_files)} entries from {dir_path}")
			return True
		else:
			print(f"No matching files in {dir_path}")
			return False	

	def __create_thumbnail(self,original_image):

		thumb_w = allsky_shared.getSetting("thumbnailsizex")
		thumb_h = allsky_shared.getSetting("thumbnailsizey")

		img = cv2.imread(original_image)

		# Check if the image was loaded successfully
		if img is not None:
			thumbnail_size = (thumb_w, thumb_h)
			thumbnail = cv2.resize(img, thumbnail_size, interpolation=cv2.INTER_AREA)

			if thumbnail is not None:
				return thumbnail
			else:
				return 
		else:
			#error reading file. not sure what to do?
			return


			# Step 3: Save the thumbnail
			output_thumbnail_path = 'thumbnail_image.jpg'  # Path to save the thumbnail
			success = cv2.imwrite(output_thumbnail_path, thumbnail)

			# Check if the thumbnail was saved successfully
			if success:
				print(f"Thumbnail saved successfully at {output_thumbnail_path}")
				return True
			else:
				print("Error saving the thumbnail.")
				return False
					
	def __do_keogram(self):
		'''create keogram then upload 
		'''
		
		keo_settings = self.get_param('keogram_use_settings',"", str)

		if "Module" in keo_settings:
			generate = self.get_param('keogram_create', False, bool)
			expand = self.get_param('keogram_expand', False, bool)
			rotation = self.get_param('keogram_rotation', 0, int)
			resize = self.get_param('keogram_resize',"", str)
			show_labels = self.get_param('keogram_show_labels',"", str)
			font_name = self.get_param('keogram_font_name', "Simplex", str)
			font_color= self.get_param('keogram_font_color', "#ffffff", str)
			font_size = self.get_param('keogram_font_size', 2, float)
			font_thickness = self.get_param('keogram_font_thickness', 3, int)
			extra_params = self.get_param('keogram_extraparams', "", str)		# not used yet
		if "Allsky" in keo_settings:
			generate = allsky_shared.getSetting("keogramgenerate")
			expand = allsky_shared.getSetting("keogramexpand")
			font_name = allsky_shared.getSetting("keogramfontname")
			font_color= allsky_shared.getSetting("keogramfontcolor")
			font_size = allsky_shared.getSetting("keogramfontsize")
			font_thickness = allsky_shared.getSetting("keogramlinethickness")
			extra_params = allsky_shared.getSetting("keogramextraparameters")		# not used yet

		upload = allsky_shared.getSetting("keogramupload")			# from allsky website and server settings
		keogram_test = self.get_param('keogram_test', "", str)
		type = "keogram"

		result = ""

		#TODO: change this to use a list of files rather than a dir to pass to script??

		# set input directory and also upload setting
		if self.debugmode:
			generate = "generate" in keogram_test.lower()
			upload = "upload" in keogram_test.lower()		# returns boolean

		output_dir = os.path.join(process_dir, "keogram")
		output_dir_thumb = os.path.join(process_dir, "keogramthumbnail")
		os.makedirs(output_dir, exist_ok=True)  # make dir if not already present
		os.makedirs(output_dir_thumb, exist_ok=True)  # make dir if not already present

		keo_filename = f"keogram-{process_date}.{EXT}"
		keogram_fullpath = os.path.join(output_dir, keo_filename)

		# Create keogram
		if generate:
			# build info for running the script
			keo_script_path= os.path.join(ALLSKY_HOME, "bin", "keogram")
			create_params = [
				"-d", process_dir,
				"-e", EXT,  # 'jpg' (no leading dot)
				"-o", f"{output_dir}/{keo_filename}",
				"-N", font_name,         # e.g., "Simplex"
				"-S", str(font_size),    # e.g., "2.0"
				"-C", font_color,        # e.g., "#ffffff"
				"-L", str(font_thickness)
			]
			if expand:
				create_params.append("--image-expand")
			if "Module" in keo_settings:
				if rotation != 0:
					create_params.extend(["--rotate", str(rotation)])
				if show_labels == "Time Only":
					create_params.append("--no-date")
				if show_labels == "No Labels":
					create_params.append("--no-label")

				if extra_params:
					# Validate extra parameters against reserved flags controlled by module settings.
					blocked_flags = {
						"-d", "--directory",
						"-e", "--extension",
						"-o", "--output",
						"-N", "--fontname",
						"-S", "--fontsize",
						"-C", "--fontcolor",
						"-L", "--linethickness",
						"--image-expand",
						"--rotate",
						"--no-date",
						"--no-label",
					}
					try:
						extra_args = self.__check_extra_params(extra_params, blocked_flags, "Keogram")
						create_params.extend(extra_args)
					except ValueError as ex:
						result = f"Keogram process stopped: {ex}"
						allsky_shared.log(0, f"ERROR: {result}")
						return result

			# Execute keogram program
			create_keo_rc, out, err = self.__run_script(keo_script_path, *create_params)
			if create_keo_rc == 0:		# return code 0 means success
				allsky_shared.log(1, f"INFO: Keogram created successfully: {keogram_fullpath}")

				# create thumbnail using function & save returned image file
				thumbnail = self.__create_thumbnail(keogram_fullpath)
				if thumbnail is not None:
					thumb_fullpath = os.path.join(output_dir_thumb, keo_filename)
					cv2.imwrite(thumb_fullpath, thumbnail)

			else:
				allsky_shared.log(0, f"ERROR: Keogram creation failed (rc={create_keo_rc}). {out} See stderr:\n{err}")
		
			# FUTURE: could add stretch or other feature here by opening the new keogram file and doing stuff
			#if stretch:
			#	run script for that...etc

		# verify file exists before uploading
		if not os.path.isfile(keogram_fullpath):
				#log message 
				upload = False
		
		#TODO: move UPLOAD this to separate function and refactor so can be used by all three
		# send filename, full filepath, thumname, thumbpath

		if upload:
			tmp_image_path=""

			# resize upload file 
			if resize not in("","0"):			# user entered a resizing value
				image_resized,resize_plan = img_resize.resize(keogram_fullpath,resize)
				##allsky_shared.log(3,f"DEBUG: Keogram Resize Plan - {resize_plan}")

				tmp_image_path = os.path.join(ALLSKY_TMP, keo_filename)
				image_resized.save(tmp_image_path)
				keogram_fullpath = tmp_image_path

			# call upload 
			upkeo = self.__do_upload(type, keo_filename, keogram_fullpath)		#no thumbnail
			# delete temp file if it was created
			if os.path.exists(tmp_image_path):
				os.remove(tmp_image_path)

		result = "Daily Keogram process complete"
		
		allsky_shared.log(1, f"INFO:  {result}")
		#the end!
		return result

	def __do_startrails(self):

		stars_settings= self.get_param('startrails_use_settings',"", str)
		resize=""

		if "Module" in stars_settings:
			generate = self.get_param('startrails_create', False, bool)
			brightness_threshold = self.get_param('startrails_brightness', .2, float)
			apply_mask = self.get_param('startrails_mask',"", str)
			use_day_images = self.get_param('startrails_dayimages', False, bool)
			#resize = self.get_param('keogram_resize',"", str)
			extra_params = self.get_param('startrails_extraparams', "", str)			# not used yet
		if "Allsky" in stars_settings:
			generate = allsky_shared.getSetting("startrailsgenerate")
			brightness_threshold = self.get_param('startrailsbrightnessthreshold', .2, float)			
			extra_params = allsky_shared.getSetting("startrailsextraparameters")		

		upload = allsky_shared.getSetting("startrailsupload")			# from allsky website and server settings
		startrails_test = self.get_param('startrails_test', "", str)
		type = "startrails"
		result = ""

		# set input directory and also upload setting
		if self.debugmode:
			generate = "generate" in startrails_test.lower()
			upload = "upload" in startrails_test.lower()		# returns boolean
		
		output_dir = os.path.join(process_dir, "startrails")
		startrails_filename = f"startrails-{process_date}.{EXT}"
		startrails_fullpath = os.path.join(output_dir, startrails_filename)

		startrails_make_file = f"{ALLSKY_TMP}/startrailsfiles.txt"

		if not use_day_images:
			makelist = self.__make_imageprocessinglist("startrails", process_date, process_dir, startrails_make_file)
			#TODO: log issue if returns False??
			# or do we throw an error here, or just proceed and try to process the dir?
		else:
			makelist=False

		
		# Create startrails
		if generate:
			os.makedirs(output_dir, exist_ok=True)  # make dir if not already present

			# build info for running the script
			startrails_script_path= os.path.join(ALLSKY_HOME, "bin", "startrails")
			create_params = [
				"-b", str(brightness_threshold),
				"-e", EXT,  # 'jpg' (no leading dot)
				"-o", startrails_fullpath
			]
			
			if use_day_images and makelist:
				create_params.extend(["-i", startrails_make_file])		# to use input file
			else:	
				create_params.extend(["-d", process_dir])				# to use input dir

			if extra_params:
				# Validate extra parameters against reserved flags controlled by module settings.
				blocked_flags = {
					"-b", "--brightness",
					"-e", "--extension",
					"-o", "--output",
					"-d", "--directory",
					"-i", "--input",
				}
				try:
					extra_args = self.__check_extra_params(extra_params, blocked_flags, "Startrails")
					create_params.extend(extra_args)
				except ValueError as ex:
					result = f"Startrails process stopped: {ex}"
					allsky_shared.log(0, f"ERROR: {result}")
					if os.path.exists(startrails_make_file):
						os.remove(startrails_make_file)
					return result
					
			# Execute startrails program
			try:
				create_stars_rc, out, err = self.__run_script(startrails_script_path, *create_params)
				if create_stars_rc == 0:		# return code 0 means success
					allsky_shared.log(1, f"INFO: Startrails created successfully: {startrails_fullpath}")

					if apply_mask:
						img = cv2.imread(startrails_fullpath)
						masked_stars = allsky_shared.mask_image(img,apply_mask)
						##okaygo = True
						if masked_stars.any():
							#new_Stars = Image.fromarray(masked_stars)
							#mask_done=cv2.imwrite(startrails_fullpath, new_stars)
							mask_done=cv2.imwrite(startrails_fullpath, masked_stars)
							if mask_done:
								allsky_shared.log(1, f"INFO: Startrails mask applied")
							else:
								allsky_shared.log(0, f"ERROR: unable to save masked Startrails image.")
						else:
							allsky_shared.log(0, f"ERROR: unable to apply Startrails mask.")

					# create thumbanil using function & save
					thumbnail = self.__create_thumbnail(startrails_fullpath)
					if thumbnail is not None:
						output_dir_thumb = os.path.join(process_dir, "startrailsthumbnail")
						os.makedirs(output_dir_thumb, exist_ok=True)  # make dir if not already present
						thumb_fullpath = os.path.join(output_dir_thumb, startrails_filename)
						cv2.imwrite(thumb_fullpath, thumbnail)

				else:
					allsky_shared.log(0, f"ERROR: Startrails creation failed (rc={create_stars_rc}). {out} See stderr:\n{err}")
			finally:
			# delete temp list-of-files file
				if os.path.exists(startrails_make_file):
					os.remove(startrails_make_file)



		if upload:
			tmp_image_path=""

			# resize upload file 
			if resize not in("","0"):			# user entered a resizing value
				image_resized,resize_plan = img_resize.resize(startrails_fullpath,resize)
				##allsky_shared.log(3,f"DEBUG: Startrails Resize Plan - {resize_plan}")

				tmp_image_path = os.path.join(ALLSKY_TMP, startrails_filename)
				image_resized.save(tmp_image_path)
				startrails_fullpath = tmp_image_path

			# call upload 
			upstars = self.__do_upload(type, startrails_filename, startrails_fullpath)		#no thumbnail
			
			# delete temp file if it was created
			if os.path.exists(tmp_image_path):
				os.remove(tmp_image_path)

		result = "Daily Startrails process complete"
		allsky_shared.log(1, f"INFO:  {result}")
	
		return result

	def debug_log(self, message, level=1):
		"""Enhanced debug logging with multiple levels and debug mode control

		Args:
			message (str): The message to log
			level (int): Log level
		"""
		try:
			debug_enabled = debug_logging_timelapse

			if allsky_shared.LOGLEVEL < level and not debug_enabled:
				return

			# TODO: Only use allsky_shared.log() have have the invoker add ERROR, WARNING, and INFO to the messages.
			# Then prefix, print(), LOG_DIR, and log_file aren't needed.
			prefix = "ERROR" if level == 0 else "WARNING" if level == 1 else "INFO"

			if level == 0:
				print(f"KEOLAPSE {prefix}: {message}")    # TODO: where does this go?

			# Force allsky_shared.log() to display in debug mode.
			if debug_enabled and level > allsky_shared.LOGLEVEL:
				level = allsky_shared.LOGLEVEL

			allsky_shared.log(level, f"{prefix}: {message}")

		except Exception as e:
			print(f"KEOLAPSE LOGGING ERROR: {str(e)}")

	def get_timelapse_settings(self):
		"""Load timelapse settings from Allsky settings page."""
		try:
			timelapse_settings = {
				"width": allsky_shared.getSetting("timelapsewidth"),
				"height": allsky_shared.getSetting("timelapseheight"),
				"timelapse_bitrate": allsky_shared.getSetting("timelapsebitrate"),
				"fps": allsky_shared.getSetting("timelapsefps"),
				"vcodec": allsky_shared.getSetting("timelapsevcodec"),
				"pixfmt": allsky_shared.getSetting("timelapsepixfmt"),
				"fflog": allsky_shared.getSetting("timelapsefflog")
			}
			self.debug_log(f"Loaded Allsky's timelapse settings: {timelapse_settings}", level=4)
			return timelapse_settings
		except Exception as ex:
			self.debug_log(f"Unable to load timelapse settings: {ex}", level=0)
			return None

	def get_target_date(self):
		"""Get the processing date used for output naming."""
		global process_date

		if process_date:
			try:
				datetime.datetime.strptime(process_date, "%Y%m%d")
				self.debug_log(f"Using specified date: {process_date}", level=4)
				return process_date
			except ValueError:
				self.debug_log(f"Invalid process_date '{process_date}', using default", level=1)

		return default_date

	def get_source_directory(self):
		"""Get source image directory based on mode and test settings."""
		global process_dir
		global timelapse_debug_test

		if timelapse_debug_test and self.debugmode:
			source_dir = os.path.join(base_dir, "test")
		else:
			source_dir = process_dir

		if not source_dir or not os.path.exists(source_dir):
			self.debug_log(f"Directory not found: {source_dir}", level=0)
			return None

		return source_dir

	def get_source_images(self):
		"""Get sorted list of source images."""
		try:
			source_dir = self.get_source_directory()
			if source_dir is None:
				self.debug_log("Cannot proceed without valid source directory", level=0)
				return []

			self.debug_log(f"Searching for images in: {source_dir}", level=4)
			image_pattern = os.path.join(source_dir, f"image-*.{EXT}")
			images = sorted(glob.glob(image_pattern))

			if not images:
				self.debug_log("No images found", level=1)
				return []

			fps = int(self.params.get("timelapse_fps", "24"))
			estimated_length = len(images) / fps
			minutes = int(estimated_length // 60)
			seconds = int(estimated_length % 60)

			self.debug_log(f"Found {len(images)} images", level=4)
			self.debug_log(f"Estimated video length: {minutes}:{seconds:02d} at {fps} fps", level=4)

			return images
		except Exception as ex:
			self.debug_log(f"Failed to get source images: {ex}", level=1)
			return []

	def ensure_dir(self, path):
		if not os.path.exists(path):
			os.makedirs(path)
		return path

	def get_keogram_path(self):
		"""Find generated keogram for current source folder."""
		source_dir = self.get_source_directory()
		if source_dir is None:
			self.debug_log("Cannot locate keogram without valid source directory", level=0)
			return None

		keogram_dir = os.path.join(source_dir, "keogram")
		self.debug_log(f"Searching for keogram in: {keogram_dir}", level=4)
		if not os.path.exists(keogram_dir):
			self.debug_log(f"Keogram directory not found: {keogram_dir}", level=1)
			return None

		keogram_files = glob.glob(os.path.join(keogram_dir, f"keogram*.{EXT}"))
		if not keogram_files:
			keogram_files = glob.glob(os.path.join(keogram_dir, "keogram*.jpg"))

		if keogram_files:
			self.debug_log(f"Using keogram: {os.path.basename(sorted(keogram_files)[0])}", level=4)
			return sorted(keogram_files)[0]

		self.debug_log("No keogram found", level=1)
		return None

	def get_output_path(self, filename):
		"""Get output path for timelapse artifacts."""
		source_dir = self.get_source_directory()
		if source_dir is None:
			self.debug_log("Using fallback output path due to missing source directory", level=1)
			output_dir = self.ensure_dir(os.path.join(base_dir, "keolapse_output"))
		else:
			output_dir = source_dir

		return os.path.join(output_dir, filename)

	def generate_test_data(self):
		"""Generate short test input set from current target date."""
		try:
			target_date = self.get_target_date()
			source_dir = os.path.join(base_dir, target_date)
			test_dir = os.path.join(base_dir, "test")

			if not os.path.exists(source_dir):
				self.debug_log(f"Source directory not found: {source_dir}", level=0)
				return False

			if os.path.exists(test_dir):
				test_images = sorted(glob.glob(os.path.join(test_dir, f"image-*.{EXT}")))
				if test_images and self.test_date_is_current(test_images[0], target_date):
					return True
				shutil.rmtree(test_dir)

			os.makedirs(test_dir)

			night_pattern = os.path.join(source_dir, f"image-{target_date}23*.{EXT}")
			night_images = sorted(glob.glob(night_pattern))

			if not night_images:
				fallback_pattern = os.path.join(source_dir, f"image-*.{EXT}")
				night_images = sorted(glob.glob(fallback_pattern))[:120]

			if not night_images:
				self.debug_log("No source images found for test data", level=1)
				return False

			for img in night_images:
				shutil.copy2(img, os.path.join(test_dir, os.path.basename(img)))

			source_keogram = os.path.join(source_dir, "keogram")
			if os.path.exists(source_keogram):
				dest_keogram_dir = os.path.join(test_dir, "keogram")
				shutil.copytree(source_keogram, dest_keogram_dir)

				copied_keograms = sorted(glob.glob(os.path.join(dest_keogram_dir, f"keogram*.{EXT}")))
				if copied_keograms:
					os.replace(copied_keograms[0], os.path.join(dest_keogram_dir, f"keogram-test.{EXT}"))

			self.debug_log(f"Generated test data with {len(night_images)} images", level=3)
			return True
		except Exception as ex:
			self.debug_log(f"Error generating test data: {ex}", level=0)
			return False

	def test_date_is_current(self, test_image, target_date):
		try:
			test_date = os.path.basename(test_image).split("-")[1][:8]
			return test_date == target_date
		except Exception:
			return False

	def cleanup_test_data(self):
		if self.debugmode:
			return

		try:
			test_dir = os.path.join(base_dir, "test")
			if os.path.exists(test_dir):
				shutil.rmtree(test_dir)
				self.debug_log("Cleaned up test data", level=4)
		except Exception as ex:
			self.debug_log(f"Error cleaning test data: {ex}", level=1)

	def create_debug_image(self, images, params):
		"""Generate a debug frame with optional keogram overlay."""
		if not images:
			return False

		try:
			frame = cv2.imread(images[0])
			if frame is None:
				self.debug_log(f"Failed to read test image: {images[0]}", level=0)
				return False

			original_height, original_width = frame.shape[:2]
			new_width, new_height, scale_factor = self.calculate_scaled_dimensions(params, original_width, original_height)
			overlay_enabled = str(params.get("keolapse_overlay", "true")).lower() == "true"

			scaled_frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

			if not overlay_enabled:
				output_path = self.get_output_path("keolapse_debug.jpg")
				cv2.imwrite(output_path, scaled_frame)
				self.debug_log(f"Created debug image without overlay: {output_path}", level=4)
				return True

			generator = self.KeolapseGenerator(self, params, scale_factor)
			if not generator.detect_circle(scaled_frame):
				return False

			keogram_path = self.get_keogram_path()
			if not keogram_path:
				return False

			keogram_data = generator.prepare_keogram(keogram_path)
			if keogram_data[0] is None:
				return False

			result = generator.wrap_keogram(scaled_frame, keogram_data[0], keogram_data[1], 0, len(images))
			output_path = self.get_output_path("keolapse_debug.jpg")
			cv2.imwrite(output_path, result)
			self.debug_log(f"Created debug image: {output_path}", level=4)
			return True
		except Exception as ex:
			self.debug_log(f"Error creating debug image: {ex}", level=1)
			return False

	def optimize_video_params(self, images, params):
		min_fps = 5
		max_fps = 30
		target_duration = int(params.get("timelapse_max_length", "120"))

		current_fps = int(params.get("timelapse_fps", "24"))
		total_frames = len(images)
		current_duration = total_frames / current_fps

		if current_duration <= target_duration:
			return images, current_fps

		ideal_frame_count = max(1, int(target_duration * current_fps))
		skip_interval = max(1, total_frames // ideal_frame_count)
		optimized_images = images[::skip_interval]
		optimized_fps = min(max_fps, max(min_fps, len(optimized_images) / target_duration))

		return optimized_images, int(optimized_fps)

	def should_optimize_video(self, images, params):
		if len(images) < 300:
			return False

		global timelapse_use_AS_settings
		if timelapse_use_AS_settings:
			timelapse_settings = self.get_timelapse_settings()
			fps = int(timelapse_settings["fps"]) if timelapse_settings else int(params.get("timelapse_fps", "24"))
		else:
			fps = int(params.get("timelapse_fps", "24"))

		expected_duration = len(images) / fps
		timelapse_max_length = int(params.get("timelapse_max_length", "120"))
		return expected_duration > timelapse_max_length

	def calculate_scaled_dimensions(self, params, original_width, original_height):
		target_res = params.get("resolution", "720p")
		custom_res = int(params.get("timelapse_custom_resolution", 720))
		custom_res += custom_res % 2

		if custom_res > original_height and target_res == "Custom":
			raise ValueError(
				f"Custom resolution height ({custom_res}px) cannot be greater than original image height ({original_height}px)."
			)

		target_heights = {
			"720p": 720,
			"1080p": 1080,
			"4k": 2160,
			"Custom": custom_res,
			"No Resizing": original_height
		}

		target_height = target_heights.get(target_res, 720)
		if original_height < target_height:
			target_height = original_height

		scale_factor = target_height / original_height
		new_width = int(original_width * scale_factor)
		return new_width, target_height, scale_factor

	def check_ffmpeg_available(self):
		try:
			return shutil.which("ffmpeg") is not None
		except Exception:
			return False

	class KeolapseGenerator:
		"""Handles circular keogram preparation and per-frame overlay."""

		predefined_colors = {
			"White": (255, 255, 255),
			"Cyan": (255, 255, 0),
			"Red": (0, 0, 255),
			"Yellow": (0, 255, 255),
			"Green": (0, 255, 0),
			"Moon Glow": (218, 253, 250),
			"Blue Steel": (71, 48, 44),
			"Midnight": (48, 21, 23),
			"Black": (0, 0, 0)
		}

		def __init__(self, owner, params, scale_factor=1.0):
			self.owner = owner
			self.params = params
			self.scale_factor = scale_factor
			self.circle_center = None
			self.circle_radius = None
			self.keolapse_height = int(float(params.get("keolapse_height", 175)) * scale_factor)
			self.keolapse_edge_borders = int(float(params.get("keolapse_edge_borders", 3)) * scale_factor)
			self.keolapse_start_position = str(params.get("keolapse_start_position", "Bottom"))
			self.angle_offset = {
				"Top": 90,
				"Right": 0,
				"Bottom": 270,
				"Left": 180
			}[self.keolapse_start_position]

			if not params.get("keolapse_mask"):
				self.center_x_offset = 0
				self.center_y_offset = 0
				self.circle_radius_factor = 0.84
			else:
				mask_path = os.path.join(allsky_shared.ALLSKY_OVERLAY, "images", params.get("keolapse_mask"))
				self.read_mask_image(mask_path, scale_factor)

			self.expanded_image = None
			self.expansion = {"top": 0, "bottom": 0, "left": 0, "right": 0}
			self._ring_cache = None
			self._ring_cache_key = None

		def read_mask_image(self, mask_path, scale_factor):
			try:
				mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
				if mask is None:
					raise ValueError(f"Failed to load mask image: {mask_path}")

				circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1.0,
					minDist=100, param1=100, param2=100,
					minRadius=10, maxRadius=0)

				if circles is not None:
					cx, cy, r = np.round(circles[0, 0]).astype(int)
					self.circle_radius_factor = r / min(mask.shape)
					self.center_x_offset = int((cx - (mask.shape[1] // 2)) * scale_factor)
					self.center_y_offset = int((cy - (mask.shape[0] // 2)) * scale_factor)
					return True

				raise ValueError(f"No circle detected in mask image: {mask_path}")
			except Exception as ex:
				self.owner.debug_log(f"Error reading mask image: {ex}", level=0)
				return False

		def detect_circle(self, image):
			try:
				height, width = image.shape[:2]

				center_x = width // 2 + self.center_x_offset
				center_y = height // 2 + self.center_y_offset
				radius = int(min(width, height) * self.circle_radius_factor)

				required_space = radius + self.keolapse_height
				expansion_needed = False
				self.expansion = {"top": 0, "bottom": 0, "left": 0, "right": 0}

				if center_y - required_space < 0:
					self.expansion["top"] = abs(center_y - required_space) + self.keolapse_edge_borders
					expansion_needed = True
				if center_y + required_space >= height:
					self.expansion["bottom"] = (center_y + required_space) - height + self.keolapse_edge_borders
					expansion_needed = True
				if center_x - required_space < 0:
					self.expansion["left"] = abs(center_x - required_space) + self.keolapse_edge_borders
					expansion_needed = True
				if center_x + required_space >= width:
					self.expansion["right"] = (center_x + required_space) - width + self.keolapse_edge_borders
					expansion_needed = True

				if expansion_needed:
					self.expanded_image = cv2.copyMakeBorder(
						image,
						self.expansion["top"], self.expansion["bottom"],
						self.expansion["left"], self.expansion["right"],
						cv2.BORDER_CONSTANT, value=[0, 0, 0]
					)
					center_x += self.expansion["left"]
					center_y += self.expansion["top"]
				else:
					self.expanded_image = image.copy()

				self.circle_center = (center_x, center_y)
				self.circle_radius = radius
				self._ring_cache = None
				self._ring_cache_key = None
				return True
			except Exception as ex:
				self.owner.debug_log(f"Error setting circle parameters: {ex}", level=0)
				return False

		def convert_hex_to_bgr(self, hex_color):
			s = hex_color.lstrip("#")
			if len(s) == 3:
				s = "".join(ch * 2 for ch in s)
			if len(s) != 6:
				raise ValueError("Invalid hex color")
			r = int(s[0:2], 16)
			g = int(s[2:4], 16)
			b = int(s[4:6], 16)
			return (b, g, r)

		def prepare_keogram(self, keogram_path):
			try:
				keogram = cv2.imread(keogram_path)
				if keogram is None:
					raise ValueError(f"Failed to load keogram: {keogram_path}")

				circumference = 2 * np.pi * self.circle_radius
				new_width = int(circumference)
				keogram_resized = cv2.resize(keogram, (new_width, self.keolapse_height), interpolation=cv2.INTER_LANCZOS4)

				border_color = self.params.get("keolapse_border_color", "White")
				if border_color == "Custom":
					border_bgr = self.convert_hex_to_bgr(self.params.get("keolapse_border_color_custom", "#99a8c4"))
				else:
					border_bgr = self.predefined_colors.get(border_color, (255, 255, 255))

				border_thickness = int(self.params.get("keolapse_border_width", 2))
				border_thickness = min(border_thickness, keogram_resized.shape[0])
				keogram_resized[:border_thickness, :, :] = border_bgr
				keogram_resized[-border_thickness:, :, :] = border_bgr

				progress = np.zeros_like(keogram_resized)
				return keogram_resized, progress
			except Exception as ex:
				self.owner.debug_log(f"Error preparing keogram: {ex}", level=0)
				return None, None

		def _get_ring_cache(self, height, width, keogram_width, keogram_height):
			cache_key = (
				height,
				width,
				self.circle_center,
				self.circle_radius,
				self.keolapse_height,
				self.angle_offset,
				keogram_width,
				keogram_height,
			)

			if self._ring_cache is not None and self._ring_cache_key == cache_key:
				return self._ring_cache

			y, x = np.mgrid[:height, :width]
			dx = x - self.circle_center[0]
			dy = y - self.circle_center[1]
			radius = np.sqrt(dx ** 2 + dy ** 2)

			angle = np.degrees(np.arctan2(dy, dx))
			angle = np.where(angle < 0, angle + 360, angle)
			angle = (angle + self.angle_offset) % 360

			ring_mask = (radius > self.circle_radius) & (radius < (self.circle_radius + self.keolapse_height))

			keogram_x = ((angle[ring_mask] / 360) * keogram_width).astype(np.int32)
			keogram_y = ((radius[ring_mask] - self.circle_radius) * self.keolapse_height / self.keolapse_height).astype(np.int32)

			keogram_x = np.clip(keogram_x, 0, keogram_width - 1)
			keogram_y = np.clip(keogram_y, 0, keogram_height - 1)

			self._ring_cache = (ring_mask, keogram_x, keogram_y)
			self._ring_cache_key = cache_key
			return self._ring_cache

		def wrap_keogram(self, base_image, keogram, progress_indicator, frame_idx, total_frames):
			try:
				result = self.expanded_image.copy()
				height, width = result.shape[:2]

				progress_x = int((frame_idx / total_frames) * progress_indicator.shape[1])
				progress_copy = progress_indicator.copy()

				progress_color = self.params.get("keolapse_progress_color", "Red")
				if progress_color == "Custom":
					progress_color = self.convert_hex_to_bgr(self.params.get("keolapse_progress_color_custom", "#FFFFFF"))
				else:
					progress_color = self.predefined_colors.get(progress_color, (255, 255, 255))

				for i in range(4):
					marker_x = max(0, progress_x - i)
					intensity = 255 - (i * 50)
					fade_factor = max(0.0, intensity / 255.0)
					trail_color = tuple(int(channel * fade_factor) for channel in progress_color)
					cv2.line(progress_copy, (marker_x, 0), (marker_x, self.keolapse_height), trail_color, 2)

				cv2.line(progress_copy, (progress_x, 0), (progress_x, self.keolapse_height), progress_color, 3)

				ring_mask, keogram_x, keogram_y = self._get_ring_cache(height, width, keogram.shape[1], keogram.shape[0])

				combined = keogram.copy()
				progress_mask = np.any(progress_copy > 0, axis=2)
				if np.any(progress_mask):
					progress_alpha = 0.8
					combined[progress_mask] = (
						(1.0 - progress_alpha) * combined[progress_mask].astype(np.float32)
						+ progress_alpha * progress_copy[progress_mask].astype(np.float32)
					).astype(np.uint8)

				result[ring_mask] = combined[keogram_y, keogram_x]

				if self.owner.debugmode and timelapse_debug_test:
					debug_text = "DEBUG IMAGE"
					font = cv2.FONT_HERSHEY_SIMPLEX
					for i in range(3):
						x_pos = (result.shape[1] // 3) * i + 50
						cv2.putText(result, debug_text, (x_pos, height - 20), font, 1, (0, 0, 255), 2)

				return result
			except Exception as ex:
				self.owner.debug_log(f"Error wrapping keogram: {ex}", level=0)
				return base_image

	def create_video(self, images, params):
		"""Create timelapse video with optional keogram overlay."""
		if not images:
			self.debug_log("No images found to process", level=1)
			return False

		try:
			if not self.check_ffmpeg_available():
				self.debug_log("ffmpeg not found. Please install ffmpeg to create videos.", level=0)
				return False

			global timelapse_use_AS_settings
			timelapse_settings = None
			if timelapse_use_AS_settings:
				timelapse_settings = self.get_timelapse_settings()
				if timelapse_settings is None:
					self.debug_log("Failed to load timelapse settings, using module settings instead", level=1)
					timelapse_use_AS_settings = False
				else:
					self.debug_log("Using timelapse settings from Allsky Settings", level=4)

			first_frame = cv2.imread(images[0])
			if first_frame is None:
				self.debug_log(f"Failed to read first image: {os.path.basename(images[0])}", level=0)
				return False

			original_height, original_width = first_frame.shape[:2]
			overlay_enabled = str(params.get("keolapse_overlay", "true")).lower() == "true"

			if timelapse_use_AS_settings and timelapse_settings:
				new_width = timelapse_settings["width"] if timelapse_settings["width"] > 0 else original_width
				new_height = timelapse_settings["height"] if timelapse_settings["height"] > 0 else original_height
				scale_factor = min(new_width / original_width, new_height / original_height)
				new_width = int(original_width * scale_factor)
				new_height = int(original_height * scale_factor)
				self.debug_log(f"Using timelapse resolution: {new_width}x{new_height}, scale_factor={scale_factor}", level=4)
			else:
				new_width, new_height, scale_factor = self.calculate_scaled_dimensions(params, original_width, original_height)

			scaled_frame = cv2.resize(first_frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

			if overlay_enabled:
				generator = self.KeolapseGenerator(self, params, scale_factor)
				if not generator.detect_circle(scaled_frame):
					self.debug_log("Failed to detect circle parameters", level=0)
					return False

				keogram_path = self.get_keogram_path()
				if not keogram_path:
					self.debug_log("No keogram found", level=1)
					return False

				keogram_data = generator.prepare_keogram(keogram_path)
				if keogram_data[0] is None:
					return False

				if generator.expanded_image is not None:
					height, width = generator.expanded_image.shape[:2]
				else:
					height, width = scaled_frame.shape[:2]
			else:
				generator = None
				keogram_data = (None, None)
				height, width = scaled_frame.shape[:2]

			self.debug_log(f"Final frame dimensions: {width}x{height}", level=4)

			if self.should_optimize_video(images, params):
				self.debug_log("Video length exceeds maximum, optimizing...", level=4)
				images, fps = self.optimize_video_params(images, params)
			else:
				if timelapse_use_AS_settings and timelapse_settings:
					fps = int(timelapse_settings["fps"])
				else:
					fps = int(params.get("timelapse_fps", "24"))

			self.debug_log(f"Output video dimensions: {width}x{height} @ {fps}fps", level=4)

			if timelapse_use_AS_settings and timelapse_settings:
				timelapse_bitrate = timelapse_settings["timelapse_bitrate"]
				if timelapse_bitrate <= 3000:
					quality = 23
				elif timelapse_bitrate <= 6000:
					quality = 20
				else:
					quality = 18

				quality_params = {
					"timelapse_bitrate": f"{timelapse_bitrate}k",
					"quality": quality
				}
				self.debug_log(f"Using timelapse quality settings (bitrate: {timelapse_bitrate}k)", level=4)
			else:
				timelapse_bitrate = int(params.get("timelapse_bitrate", 2000))
				quality_params = {
					"timelapse_bitrate": f"{timelapse_bitrate}k",
					"quality": 20
				}
				self.debug_log(f"Using explicit bitrate from params: {timelapse_bitrate}k (CRF=20)", level=4)

			self.debug_log(f"Quality parameters: {quality_params}", level=4)

			global timelapse_debug_test
			is_test = timelapse_debug_test and self.debugmode
			if is_test:
				output_filename = "allsky-test.mp4"
				thumbnail_filename = "allsky-test.jpg"
			else:
				target_date = self.get_target_date()
				output_filename = f"allsky-{target_date}.mp4"
				thumbnail_filename = f"allsky-{target_date}.jpg"

			output_tmp_path = os.path.join(ALLSKY_TMP, output_filename)
			output_path = self.get_output_path(output_filename)

			if timelapse_use_AS_settings and timelapse_settings:
				vcodec = timelapse_settings["vcodec"]
				pixfmt = timelapse_settings["pixfmt"]
				fflog = timelapse_settings["fflog"]

				ffmpeg_cmd = [
					"ffmpeg", "-y",
					"-f", "rawvideo",
					"-pix_fmt", "bgr24",
					"-s", f"{width}x{height}",
					"-r", str(fps),
					"-i", "-",
					"-c:v", vcodec,
					"-preset", "medium",
					"-crf", str(quality_params["quality"]),
					"-b:v", quality_params["timelapse_bitrate"],
					"-maxrate", str(int(quality_params["timelapse_bitrate"].replace("k", "")) * 1.0) + "k",
					"-bufsize", str(int(quality_params["timelapse_bitrate"].replace("k", "")) * 2) + "k",
					"-pix_fmt", pixfmt,
					"-loglevel", fflog,
					"-movflags", "+faststart"
				]
			else:
				ffmpeg_preset = str(params.get("timelapse_preset", "medium"))
				scale_w = width - (width % 2)
				scale_h = height - (height % 2)

				ffmpeg_cmd = [
					"ffmpeg", "-y",
					"-f", "rawvideo",
					"-pix_fmt", "bgr24",
					"-s", f"{width}x{height}",
					"-r", str(fps),
					"-i", "-",
					"-c:v", str(params.get("timelapse_vcodec", "libx264")),
					"-vf", f"scale={scale_w}:{scale_h}",
					"-preset", ffmpeg_preset,
					"-crf", str(quality_params["quality"]),
					"-b:v", quality_params["timelapse_bitrate"],
					"-maxrate", str(int(quality_params["timelapse_bitrate"].replace("k", "")) * 1.0) + "k",
					"-bufsize", str(int(quality_params["timelapse_bitrate"].replace("k", "")) * 2) + "k",
					"-pix_fmt", str(params.get("timelapse_pixel_format", "yuv420p")),
					"-an",
					"-movflags", "+faststart"
				]

				extra_params = str(params.get("timelapse_extraparams", "")).strip()
				if extra_params:
					blocked_flags = {
						"-f", "-pix_fmt", "-s", "-r", "-i", "-c:v", "-vf", "-preset", "-crf", "-b:v",
						"-maxrate", "-bufsize", "-an", "-movflags", "-y"
					}
					try:
						extra_args = self.__check_extra_params(extra_params, blocked_flags, "Timelapse")
						ffmpeg_cmd.extend(extra_args)
					except ValueError as ex:
						self.debug_log(str(ex), level=0)
						return False

				self.debug_log(f"Module settings ffmpeg scale set to {scale_w}x{scale_h}; preset={ffmpeg_preset}", level=4)

			ffmpeg_cmd.append(output_tmp_path)
			self.debug_log("Starting direct ffmpeg encoding from processed frames...", level=4)

			ffmpeg_proc = subprocess.Popen(
				ffmpeg_cmd,
				stdin=subprocess.PIPE,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL
			)

			total_frames = len(images)
			keogram, progress = keogram_data
			initial_expansion = None
			initial_circle_center = None
			initial_circle_radius = None
			progress_interval = max(1, total_frames // (25 if total_frames > 500 else 20))
			start_time = datetime.datetime.now()

			for i, img_path in enumerate(images):
				if i % progress_interval == 0:
					progress_pct = (i + 1) / total_frames * 100
					elapsed_time = (datetime.datetime.now() - start_time).total_seconds()

					if i > 0:
						time_per_frame = elapsed_time / i
						time_remaining = (total_frames - i) * time_per_frame
						time_str = f"{time_remaining/60:.1f}min" if time_remaining > 60 else f"{time_remaining:.0f}s"
						self.debug_log(f"Progress: {progress_pct:.1f}% ({i+1}/{total_frames}) - Est. remaining: {time_str}", level=4)
					else:
						self.debug_log(f"Progress: {progress_pct:.1f}% ({i+1}/{total_frames})", level=4)

				frame = cv2.imread(img_path)
				if frame is None:
					self.debug_log(f"Failed to read frame: {os.path.basename(img_path)}", level=1)
					continue

				scaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

				if overlay_enabled:
					if i == 0:
						generator.detect_circle(scaled)
						initial_expansion = generator.expansion.copy()
						initial_circle_center = generator.circle_center
						initial_circle_radius = generator.circle_radius
					else:
						if any(initial_expansion.values()):
							generator.expansion = initial_expansion.copy()
							generator.expanded_image = cv2.copyMakeBorder(
								scaled,
								initial_expansion["top"], initial_expansion["bottom"],
								initial_expansion["left"], initial_expansion["right"],
								cv2.BORDER_CONSTANT, value=[0, 0, 0]
							)
							generator.circle_center = initial_circle_center
							generator.circle_radius = initial_circle_radius
						else:
							generator.expanded_image = scaled.copy()

					result = generator.wrap_keogram(scaled, keogram, progress, i, total_frames)
				else:
					result = scaled

				if ffmpeg_proc.stdin is None:
					self.debug_log("ffmpeg stdin is not available", level=0)
					return False

				ffmpeg_proc.stdin.write(result.tobytes())

			if ffmpeg_proc.stdin is not None:
				ffmpeg_proc.stdin.close()
			ffmpeg_proc.wait()

			if ffmpeg_proc.returncode != 0:
				self.debug_log(f"Timelapse encoding failed with code {ffmpeg_proc.returncode}", level=0)
				return False

			if not os.path.exists(output_tmp_path):
				self.debug_log(f"Encoded temp video not found: {output_tmp_path}", level=0)
				return False

			if os.path.exists(output_path):
				os.remove(output_path)

			shutil.move(output_tmp_path, output_path)

			thumbnail_path = os.path.join(os.path.dirname(output_path), "videothumbnail", thumbnail_filename)
			thumbnail_dir = os.path.dirname(thumbnail_path)
			if not os.path.exists(thumbnail_dir):
				try:
					os.makedirs(thumbnail_dir)
				except Exception as ex:
					self.debug_log(f"Failed to create thumbnail directory: {thumbnail_dir} - {ex}", level=1)
					return False

			cap = cv2.VideoCapture(output_path)
			ok, thumb_frame = cap.read()
			cap.release()

			if ok and thumb_frame is not None:
				h, w = thumb_frame.shape[:2]
				scale = min(100.0 / float(w), 75.0 / float(h))
				new_w = max(1, int(w * scale))
				new_h = max(1, int(h * scale))

				resized_thumb = cv2.resize(thumb_frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
				thumbnail_canvas = np.zeros((75, 100, 3), dtype=np.uint8)
				x_offset = (100 - new_w) // 2
				y_offset = (75 - new_h) // 2
				thumbnail_canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_thumb
				if not cv2.imwrite(thumbnail_path, thumbnail_canvas):
					self.debug_log(f"Failed to write thumbnail image: {thumbnail_path}", level=1)
			else:
				self.debug_log(f"Failed to read first frame for thumbnail: {output_path}", level=1)

			self.debug_log("Timelapse encoding completed successfully", level=4)
			end_time = datetime.datetime.now()
			total_time = (end_time - start_time).total_seconds()
			time_str = f"{total_time/60:.1f} minutes" if total_time > 60 else f"{total_time:.1f} seconds"
			self.debug_log(f"Timelapse creation completed in {time_str}, start={start_time}, end={end_time}", level=3)

			return output_path, thumbnail_path
		except Exception as ex:
			self.debug_log(f"Timelapse creation failed: {ex}", level=0)
			return False

	def __do_timelapse(self):
		"""Create/upload timelapse with optional keogram overlay."""
		result = ""
		allsky_shared.params = self.params

		global timelapse_use_AS_settings
		global timelapse_debug_test

		timelapse_use_AS_settings = str(self.get_param("timelapse_use_AS_settings", "Module Settings")) == "Allsky Settings Page"

		if self.debugmode:
			timelapse_test = self.get_param("timelapse_test", "None", str)
			timelapse_debug_test = "setup" in timelapse_test.lower()
			generate = "generate" in timelapse_test.lower() or timelapse_debug_test
			upload = "upload" in timelapse_test.lower() and allsky_shared.getSetting("timelapseupload")
			uploadthumbnail = allsky_shared.getSetting("timelapseuploadthumbnail")
		else:
			timelapse_debug_test = False
			generate = str(self.get_param("timelapse_create", "false")).lower() == "true"
			upload = allsky_shared.getSetting("timelapseupload")
			uploadthumbnail = allsky_shared.getSetting("timelapseuploadthumbnail")

		self.debug_log("=== Starting Keolapse Module ===", level=3)
		self.debug_log(f"Base directory: {base_dir}", level=4)
		self.debug_log(f"Event: {self.event}", level=4)
		self.debug_log(f"Module version: {ALLSKYKEOTIMELAPSESTARTRAILS.meta_data['version']}", level=4)
		self.debug_log(f"Testing mode: {'Enabled' if timelapse_debug_test else 'Disabled'}", level=4)

		try:
			output_path = None
			thumbnail_path = None

			##if not self.debugmode:
			##	self.cleanup_test_data()

			if timelapse_debug_test and self.debugmode:
				test_dir = os.path.join(base_dir, "test")
				target_date = self.get_target_date()
				if not os.path.exists(test_dir):
					self.debug_log("Test data folder not found, generating test data", level=3)
					if not self.generate_test_data():
						return "Failed to generate test data"
				else:
					test_images = sorted(glob.glob(os.path.join(test_dir, f"image-*.{EXT}")))
					if not test_images or not self.test_date_is_current(test_images[0], target_date):
						shutil.rmtree(test_dir)
						if not self.generate_test_data():
							return "Failed to refresh test data"

			if generate:
				images = self.get_source_images()
				if not images:
					source_dir = self.get_source_directory()
					if source_dir is None:
						return "ERROR: Source directory not found - cannot proceed"
					return "No images found to process"

				if timelapse_debug_test and self.debugmode and str(self.get_param("debug_generate", "Debug Image")).lower() == "debug image":
					self.debug_log("Creating debug image...", level=3)
					ok = self.create_debug_image(images, self.params)
					if not ok:
						return "Debug image creation failed"
					result = "Timelapse debug image created"
				else:
					self.debug_log("Creating keolapse video...", level=4)
					video_result = self.create_video(images, self.params)
					if not video_result:
						return "Failed to create timelapse video"
					output_path, thumbnail_path = video_result
					result = "Daily Timelapse process complete"
			else:
				self.debug_log("Timelapse creation not enabled, skipping video creation...", level=3)
				result = "Timelapse generation skipped"

			if upload:
				self.debug_log("Uploading video...", level=4)
				if not generate:
					self.debug_log("Upload Only mode: locating existing timelapse file", level=4)
					target_date = self.get_target_date()
					output_filename = f"allsky-{target_date}.mp4"
					output_path = self.get_output_path(output_filename)

					if not os.path.exists(output_path):
						self.debug_log(f"No existing timelapse found: {output_path}", level=1)
						return f"Upload Only selected but no existing timelapse found at {output_path}"

					thumbnail_filename = f"allsky-{target_date}.jpg"
					thumbnail_path = os.path.join(os.path.dirname(output_path), "videothumbnail", thumbnail_filename)

				if not output_path or not os.path.exists(output_path):
					self.debug_log("No timelapse file found to upload", level=1)
					return "No timelapse file found to upload"

				timelapse_filename = os.path.basename(output_path)
				timelapse_fullpath = output_path

				if uploadthumbnail and thumbnail_path and os.path.exists(thumbnail_path):
					tl_thumb_filename = os.path.basename(thumbnail_path)
					tl_thumb_fullpath = thumbnail_path
				else:
					tl_thumb_filename = None
					tl_thumb_fullpath = None

				self.__do_upload("timelapse", timelapse_filename, timelapse_fullpath, tl_thumb_filename, tl_thumb_fullpath)

			if not result:
				result = "Daily Timelapse process complete"

			return result
		except Exception as ex:
			self.debug_log(f"Timelapse module execution failed: {ex}", level=0)
			return f"Error: {ex}"
		finally:
			allsky_shared.params = None

	# Main Module Function
	def run(self):
		global default_date
		global debug_logging_timelapse
		global process_date
		global process_dir

		do_startrails = ""
		debug_logging_timelapse = str(self.get_param("debug_logging_timelapse", "false")).lower() == "true"

		if not self.debugmode:
				self.cleanup_test_data()

		# set a couple things if running from test button or not
		if self.debugmode:
			keogram_test = self.get_param('keogram_test', "None", str)
			timelapse_test = self.get_param('timelapse_test',"None",str)
			startrails_test =self.get_param('startrails_test', "None", str)
			
			# check test tab setting
			if "None" in keogram_test : do_keogram = False
			else: do_keogram = True
			if "None" in startrails_test : do_startrails = False
			else: do_startrails = True
			if "None" in timelapse_test : do_timelapse = False
			else:  do_timelapse = True
			
			if not do_keogram and not do_startrails and not do_timelapse:
				print("Nothing configured to process!!")
				##### TODO:  UPDATE HERE to log?
				return

			process_date = self.get_param('process_date', "", str)
			if process_date:
				if process_date.startswith("/"):
					process_dir = process_date
					#need to get just the date part for use in scripts
					process_date = process_date.split("/")[-1]
				else:
					process_dir = os.path.join(ALLSKY_IMAGES, process_date)
			else:
				process_dir = os.path.join(ALLSKY_IMAGES, default_date)	
				process_date = default_date
		else:
			do_keogram = self.get_param('keogram_create', False, bool)
			do_startrails = self.get_param('startrails_create', False, bool)
			do_timelapse = self.get_param('timelapse_create', False, bool)
			process_date = default_date
			process_dir = os.path.join(ALLSKY_IMAGES, default_date)		
	
		if do_keogram:
			# build parameters, run keogram script, upload if required
			keo_result=self.__do_keogram()
		
		if do_startrails:
			# build parameters, run startrails script, upload if required
			stars_result = self.__do_startrails()

		if do_timelapse:
			# build parameters, run timelapse script, upload if required
			timelapse_result = self.__do_timelapse()
		
		#result = "made it to end"
				
		return 

def keo_timelapse_startrails(params, event):
	allsky_keo_timelapse_startrails = ALLSKYKEOTIMELAPSESTARTRAILS(params, event)
	result = allsky_keo_timelapse_startrails.run()

	return result 
