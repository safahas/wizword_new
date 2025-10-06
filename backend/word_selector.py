import os
import json
import time
import random
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Tuple, Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from .fallback_words import get_fallback_word
from .openrouter_monitor import (
    update_quota_from_response,
    check_rate_limits,
    get_quota_warning,
    get_quota_status
)
import re
import base64
import traceback
from backend.monitoring import logger

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Looking for .env file at: {env_path.absolute()}")
load_dotenv(env_path)

# Add this before the WordSelector class
category_templates = {
    "general": {
        "table": [
            "This furniture piece typically measures 30 inches in height and supports 250 pounds of weight",
            "Modern versions cost between $200-$800 and last approximately 15 years",
            "Found in 98% of dining rooms and used exactly 3 times daily for meals",
            "Occupies approximately 15-20 square feet of floor space in average homes",
            "Production requires precisely 2.5 hours of assembly time in factories",
            "Available in over 1000 different styles and materials",
            "Average weight ranges from 25 to 75 pounds",
            "Standard dimensions include 30-inch height and 36-inch width",
            "Typically requires 4-6 chairs for complete dining set",
            "Lifespan extends to 20+ years with proper maintenance"
        ],
        "peace": [
            "Requires $500 billion in annual global initiatives to maintain",
            "Monitored by 100,000 international observers across 195 countries",
            "Reduces conflict-related costs by 75% in affected regions",
            "Diplomatic missions operate in 5,000 locations worldwide",
            "Saves approximately $350 billion yearly in military spending"
        ],
        "music": [
            "Vibrates at frequencies between 20 and 20,000 hertz for human hearing",
            "Traditionally divided into 12 semitones per octave in Western culture",
            "Recorded digitally at 44.1 kHz for CD-quality sound",
            "Travels through air at approximately 343 meters per second",
            "Requires at least 65 decibels for clear audibility in concert halls"
        ],
        "phone": [
            "Modern versions process data at 2.5 gigahertz and store 128GB of data",
            "Battery lasts exactly 12-15 hours and charges in 90 minutes",
            "Screen measures 6.1 inches diagonally with 460 pixels per inch",
            "Weighs precisely 174 grams and measures 5.78 inches in height",
            "Camera captures images at 48 megapixels with f/1.8 aperture"
        ],
        "light": [
            "Travels at precisely 299,792,458 meters per second in vacuum",
            "Visible spectrum ranges from 380 to 700 nanometers wavelength",
            "Solar version delivers approximately 1000 watts per square meter at noon",
            "LED versions last up to 50,000 hours of continuous operation",
            "Modern sensors detect as little as 0.00001 lux in darkness"
        ]
    },
    "animals": {
        "tiger": [
            "Adult males weigh exactly 420 pounds and measure 11 feet in length",
            "Runs at precisely 40 mph and jumps 20 feet horizontally",
            "Requires 15 pounds of meat daily and drinks 1 gallon of water",
            "Patrols territory of 40 square miles in natural habitat",
            "Lives between 20-25 years and sleeps 18 hours daily"
        ],
        "eagle": [
            "Spots prey from over 2 miles away with 20/4 vision acuity",
            "Dives at speeds exceeding 150 miles per hour during hunting",
            "Builds nests measuring up to 6 feet wide and 4 feet deep",
            "Wingspan typically ranges between 6 and 7.5 feet when fully grown",
            "Lives up to 30 years in natural habitats at elevations up to 10,000 feet"
        ],
        "shark": [
            "Swims continuously at 5 mph to push water through gills",
            "Detects blood in 1 part per million concentration from 0.25 miles",
            "Replaces 50,000 teeth in a lifetime spanning 70 years",
            "Dives to exactly 3,700 feet depth at 8 atmospheres pressure",
            "Maintains body temperature precisely 7°F above ambient water"
        ]
    },
    "food": {
        "pasta": [
            "Cooks for exactly 8-12 minutes in water at 212°F",
            "Contains 200 calories per 2-ounce serving and 42g carbohydrates",
            "Production exceeds 14.5 million tons annually worldwide",
            "Requires 4-6 quarts of water per pound for cooking",
            "Stores for 24 months at 70°F in airtight containers"
        ],
        "curry": [
            "Contains between 10 and 15 distinct spices in traditional recipes",
            "Preparation typically takes 45-60 minutes for authentic flavor",
            "Heat levels range from 500 to 50,000 Scoville units",
            "Originated over 4,000 years ago in South Asian cuisine",
            "Requires slow cooking at precisely 185°F for best results"
        ],
        "bread": [
            "Requires exactly 3 hours and 15 minutes for proper rising at 85°F",
            "Contains 150 calories per 2-ounce serving with 32g carbohydrates",
            "Bakes at precisely 375°F for 35 minutes until golden brown",
            "Uses 65% hydration ratio with 3% salt by flour weight",
            "Stays fresh for 48 hours when stored at 68°F"
        ]
    },
    "places": {
        "paris": [
            "Covers exactly 105.4 square kilometers with population density of 20,000 per km²",
            "Receives approximately 30 million tourists annually spending $21 billion",
            "Maintains average temperature of 15.5°C across 4 distinct seasons",
            "Houses precisely 296 metro stations spanning 214 kilometers of track",
            "Hosts 20,000 historic monuments dating back to 300 BCE"
        ],
        "tokyo": [
            "Spans precisely 2,194 square kilometers housing 37 million residents",
            "Processes 8.5 million commuters daily through 882 train stations",
            "Experiences 1,500 measurable earthquakes annually above 3.0 magnitude",
            "Maintains 36% green space across 11,000 hectares of urban area",
            "Operates transit system moving 40 million passengers per day"
        ]
    },
    "science": {
        "laser": [
            "Operates at precisely 1064 nanometers wavelength in industrial use",
            "Produces beam divergence of 0.5 milliradians at 100 meters",
            "Requires exactly 1.5 kilowatts power for continuous operation",
            "Achieves spot size of 25 microns for precise cutting",
            "Processes 1000 surface points per second in 3D scanning"
        ],
        "quark": [
            "Exists at temperatures above 2 trillion degrees Celsius",
            "Measures exactly 10^-18 meters in theoretical diameter",
            "Requires precisely 200 GeV of energy for separation",
            "Discovered in 1968 using 30 GeV particle accelerators",
            "Occurs in exactly 6 distinct types with specific charges"
        ],
        "atoms": [
            "Measures exactly 100 picometers in typical diameter",
            "Contains precisely 6.022 × 10^23 particles per mole",
            "Vibrates at frequencies of 10^13 hertz at room temperature",
            "Bonds at angles of 104.5 degrees in water molecules",
            "Requires 13.6 electron volts to ionize hydrogen"
        ],
        "force": [
            "Measures exactly 9.81 meters per second squared at sea level",
            "Generates 1000 newtons per square meter of pressure",
            "Requires 10 joules of energy for basic mechanical work",
            "Operates across distances of 10^-15 to 10^15 meters",
            "Produces acceleration of 3.27 meters per second squared"
        ],
        "light": [
            "Travels at exactly 299,792,458 meters per second in vacuum",
            "Wavelengths range from 380 to 700 nanometers precisely",
            "Requires 1.23 electron volts for visible photon energy",
            "Diffracts at angles of 0.5 degrees through 500nm slits",
            "Reflects at precisely equal angles from smooth surfaces"
        ],
        "cells": [
            "Divides every 24 hours under optimal conditions",
            "Maintains pH between 7.35-7.45 for proper function",
            "Contains exactly 37.2 trillion in human adult body",
            "Processes 1 billion ATP molecules per second",
            "Requires 0.1 millimeters minimum size for visibility"
        ],
        "brain": [
            "Processes information at 1016 operations per second",
            "Contains exactly 86 billion neurons in adult humans",
            "Requires 20% of body's oxygen at 15.4 liters per hour",
            "Maintains temperature at precisely 37.2°C normally",
            "Generates 10-23 watts of power during active thinking"
        ],
        "physics": [
            "Measures forces at precisely 9.81 m/s² on Earth",
            "Operates at temperatures of absolute zero (-273.15°C)",
            "Involves particles moving at 299,792,458 meters per second",
            "Generates magnetic fields of 2.5 tesla strength",
            "Requires precision to 0.000001 millimeters"
        ],
        "chemistry": [
            "Reactions occur at exactly 298.15 Kelvin standard temperature",
            "Solutions maintain pH between 6.5-7.5 precisely",
            "Molecules bind at angles of 104.5 degrees",
            "Requires exactly 6.022 × 10²³ particles per mole",
            "Achieves 99.9999% purity in laboratory conditions"
        ],
        "biology": [
            "Cells divide every 24 hours under optimal conditions",
            "Organisms maintain body temperature at exactly 37°C",
            "DNA contains precisely 3.2 billion base pairs",
            "Neurons fire at 200 times per second",
            "Requires exactly 20 different amino acids"
        ],
        "astronomy": [
            "Objects orbit at 7.67 kilometers per second",
            "Observes phenomena from 13.8 billion light-years away",
            "Detects radiation at wavelengths of 0.01 nanometers",
            "Measures stellar temperatures of 5,778 Kelvin",
            "Tracks objects moving at 2.1 million kilometers per hour"
        ],
        "research": [
            "Studies require exactly 1,000 test subjects",
            "Experiments run for precisely 36 months",
            "Data collection occurs every 15 minutes",
            "Analysis involves 50 terabytes of information",
            "Results achieve 95% confidence intervals"
        ]
    },
    "movies": {
        "drama": [
            "Generates approximately $15 billion in annual box office revenue",
            "Requires exactly 120 pages for standard screenplay format",
            "Films at 24 frames per second using 35mm digital equivalent",
            "Processes 4K resolution at 3840 x 2160 pixels per frame",
            "Records audio at precisely 48 kHz sample rate"
        ],
        "actor": [
            "Memorizes 850 words of dialogue per hour of content",
            "Performs under 5600K lighting at 100 foot-candles",
            "Requires 12-14 hours on set for 3-4 minutes of usable footage",
            "Maintains precise positions within 2 inch markers on set",
            "Syncs dialogue within 0.03 seconds for perfect lip sync"
        ]
    },
    "music": {
        "tempo": [
            "Measures precisely 120 beats per minute in common time",
            "Oscillates between 20 Hz and 20 kHz in audible range",
            "Records at exactly 44.1 kHz digital sampling rate",
            "Processes 32-bit floating point audio at 192 kHz",
            "Maintains timing accuracy within 0.5 milliseconds"
        ],
        "sound": [
            "Travels exactly 343 meters per second at sea level",
            "Requires minimum 60 dB for clear vocal reproduction",
            "Generates frequencies between 27.5 Hz and 4186 Hz on piano",
            "Processes 1,411,200 bits of data per second in CD quality",
            "Reflects off surfaces at precisely equal angles"
        ]
    },
    "sports": {
        "swim": [
            "Burns 500 calories per hour at moderate pace",
            "Moves through water at 2 meters per second",
            "Requires pool depth of 2 meters minimum",
            "Maintains heart rate at 140 beats per minute",
            "Uses 85% of body's muscle groups"
        ],
        "golf": [
            "Ball travels 250 meters maximum distance",
            "Club head speed reaches 160 kilometers per hour",
            "Course spans 6,500 meters total length",
            "Ball weighs exactly 45.93 grams",
            "Green slopes measured to 0.1 degree precision"
        ],
        "race": [
            "Sprints reach 45 kilometers per hour peak",
            "Track measures exactly 400 meters per lap",
            "Reaction time under 0.1 seconds at start",
            "Heart rate peaks at 180 beats per minute",
            "Stride length averages 2.5 meters at speed"
        ],
        "jump": [
            "Achieves heights of 2.45 meters in records",
            "Generates 4,000 newtons of force at takeoff",
            "Requires runway of 40 meters length",
            "Clears distances of 8.95 meters horizontally",
            "Takes 0.8 seconds from start to landing"
        ]
    },
    "tech": {
        "code": [
            "Processes 1 million lines per second",
            "Occupies 50 megabytes in compiled form",
            "Runs at 3.5 gigahertz clock speed",
            "Updates every 0.016 seconds for 60fps",
            "Handles 10,000 concurrent users"
        ],
        "data": [
            "Transfers at 10 gigabits per second",
            "Stores 1 petabyte across 1000 nodes",
            "Processes 1 million transactions hourly",
            "Compresses to 25% original size",
            "Backs up every 6 hours automatically"
        ],
        "chip": [
            "Operates at 5 gigahertz frequency",
            "Contains 50 billion transistors",
            "Consumes 125 watts at peak load",
            "Processes 15 trillion operations/second",
            "Measures 75 square millimeters"
        ],
        "wifi": [
            "Transmits at 5 gigahertz frequency",
            "Covers 50 meters indoor range",
            "Handles 1000 devices simultaneously",
            "Transfers 1 gigabit per second",
            "Uses 20 watts power consumption"
        ]
    },
    "food": {
        "cake": [
            "Bakes at precisely 180°C for 25 minutes",
            "Contains 350 calories per 100 gram serving",
            "Rises 2.5 centimeters during baking",
            "Requires 72% humidity for proper moisture",
            "Stores fresh for 120 hours at 4°C"
        ],
        "soup": [
            "Simmers at exactly 95°C for best results",
            "Contains 150 calories per 250ml serving",
            "Reduces by 25% volume in 30 minutes",
            "Requires 2 hours for flavor development",
            "Stores safely for 72 hours at 4°C"
        ],
        "meat": [
            "Cooks at 63°C for medium-rare doneness",
            "Contains 25 grams protein per 100 grams",
            "Rests 5 minutes per inch thickness",
            "Requires internal temperature of 75°C",
            "Stores safely for 3 days at 4°C"
        ]
    },
    "nature": {
        "tree": [
            "Grows 2.5 centimeters in height per year",
            "Absorbs 22 kilograms of CO2 annually",
            "Lives up to 500 years in optimal conditions",
            "Reaches heights of 100 meters maximum",
            "Processes 100 liters of water daily"
        ],
        "rain": [
            "Falls at 9 meters per second terminal velocity",
            "Delivers 25 millimeters per hour intensity",
            "Forms at 2,000 meters altitude typically",
            "Contains 0.5 milliliters per drop",
            "Covers 100 square kilometers per storm"
        ],
        "wind": [
            "Blows at 15 meters per second average",
            "Generates 250 watts per square meter",
            "Moves air masses across 1000 kilometers",
            "Changes direction every 6 hours typically",
            "Carries 25 grams water vapor per cubic meter"
        ],
        "soil": [
            "Contains 45% minerals by volume",
            "Holds 25% water at field capacity",
            "Supports 1 billion microorganisms per gram",
            "Takes 500 years to form 2.5 centimeters",
            "Stores 2,500 kilograms carbon per hectare"
        ],
        "wave": [
            "Oscillates at 20-20,000 hertz frequency range",
            "Travels at 343 meters per second in air",
            "Amplifies to 120 decibels maximum safe level",
            "Spans wavelengths from 17 meters to 17 millimeters",
            "Transfers 1 joule energy per oscillation"
        ],
        "dust": [
            "Measures 2.5-10 micrometers particle size",
            "Settles at 0.3 meters per second in still air",
            "Accumulates 2 grams per square meter daily",
            "Filters through 0.3 micron HEPA systems",
            "Reflects 15% of incident light particles"
        ],
        "seed": [
            "Germinates at 20°C optimal temperature",
            "Contains 45% protein by dry weight",
            "Requires 48 hours soaking for activation",
            "Stores viably for 10 years at 4°C",
            "Produces 2,000 offspring per parent plant"
        ]
    },
    "weather": {
        "snow": [
            "Falls at 1.5 meters per second speed",
            "Accumulates 2.5 centimeters per hour",
            "Forms at -2°C cloud temperature",
            "Contains 95% air by volume",
            "Reflects 90% of incident sunlight"
        ],
        "heat": [
            "Transfers at 100 watts per square meter",
            "Raises temperature 1°C per 4,184 joules",
            "Radiates at 460 nanometers wavelength",
            "Conducts through metal at 50 meters/second",
            "Dissipates at 15% rate in still air"
        ],
        "cold": [
            "Reduces temperature at 2°C per hour",
            "Freezes water at exactly 0°C",
            "Contracts materials by 0.1% per 10°C",
            "Requires 334 joules to freeze 1 gram water",
            "Preserves food 4 times longer per 10°C drop"
        ],
        "fog": [
            "Reduces visibility to 200 meters",
            "Forms at 100% relative humidity",
            "Contains 0.5 grams water per cubic meter",
            "Dissipates at 0.5°C temperature rise",
            "Covers area of 50 square kilometers"
        ]
    },
    "objects": {
        "book": [
            "Contains 250 pages of 75 gsm paper",
            "Measures 15 x 23 centimeters standard",
            "Weighs 350 grams on average",
            "Stores 80,000 words typically",
            "Lasts 100 years in proper conditions"
        ],
        "desk": [
            "Supports 100 kilograms maximum weight",
            "Measures 120 x 60 centimeters surface",
            "Stands 75 centimeters tall standard",
            "Weighs 25 kilograms assembled",
            "Lasts 15 years with normal use"
        ],
        "lamp": [
            "Produces 800 lumens of light output",
            "Consumes 9 watts LED power",
            "Lasts 50,000 hours operation",
            "Reaches 40°C surface temperature",
            "Illuminates 10 square meters area"
        ],
        "door": [
            "Measures 200 x 80 centimeters standard",
            "Weighs 25 kilograms installed",
            "Opens 90 degrees in 2 seconds",
            "Supports 150 kilograms hinges load",
            "Lasts 30 years with maintenance"
        ]
    },
    "transport": {
        "car": [
            "Accelerates 0-100 km/h in 8 seconds",
            "Consumes 7 liters fuel per 100 km",
            "Weighs 1,500 kilograms average",
            "Travels 500,000 kilometers lifetime",
            "Requires service every 15,000 km"
        ],
        "bike": [
            "Weighs 8 kilograms carbon frame",
            "Travels 25 kilometers per hour average",
            "Uses 700x23C tire dimensions",
            "Requires 50 watts power output",
            "Lasts 20,000 kilometers typical"
        ],
        "train": [
            "Reaches speeds of 300 kilometers per hour",
            "Carries 1000 passengers capacity",
            "Weighs 400 tons fully loaded",
            "Runs 18 hours daily schedule",
            "Consumes 5000 kWh electricity per trip"
        ],
        "ship": [
            "Carries 20,000 containers capacity",
            "Travels at 25 knots cruising speed",
            "Consumes 100 tons fuel per day",
            "Measures 400 meters length overall",
            "Displaces 200,000 tons water"
        ]
    }
}

# Default templates for categories without specific words
default_templates = {
    "general": [
        "Found in exactly 92.5% of modern households globally",
        "Weighs precisely between 2.5 and 10.2 pounds for standard use",
        "Lasts approximately 7.3 years with proper maintenance",
        "Used by 3.2 billion people daily across 195 countries",
        "Developed through 50 years of engineering improvements"
    ],
    "animals": [
        "Maintains body temperature between 35-42°C for optimal function",
        "Consumes exactly 12% of body weight in food daily",
        "Inhabits territories ranging from 2,500-4,000 feet elevation",
        "Travels precisely 22.5 miles daily for resources",
        "Produces sounds audible up to 1.2 miles in natural habitat"
    ],
    "food": [
        "Contains exactly 150 calories per 100-gram serving",
        "Requires precisely 45 minutes preparation time at 350°F",
        "Stores for 72 hours at 40°F in proper conditions",
        "Provides 15% daily value of essential nutrients",
        "Costs $3.50 per pound in standard markets"
    ],
    "places": [
        "Experiences average temperature of 22.5°C year-round",
        "Receives precisely 2.5 million visitors annually",
        "Covers exactly 150 square kilometers of land area",
        "Houses 500,000 residents with 95% occupancy rate",
        "Maintains 35% green space in urban planning"
    ],
    "science": [
        "Operates at exactly 1064 nanometers wavelength",
        "Processes 1000 data points per millisecond",
        "Requires precisely 2.5 kilowatts power input",
        "Achieves 99.99% accuracy in measurements",
        "Maintains temperature at -196°C using liquid nitrogen"
    ],
    "tech": [
        "Processes data at 3.2 gigahertz clock speed",
        "Stores exactly 1 terabyte of information",
        "Consumes 65 watts of power during operation",
        "Transfers data at 10 gigabits per second",
        "Updates every 2.5 milliseconds in real-time"
    ],
    "movies": [
        "Generates $500 million in global box office revenue",
        "Runs exactly 120 minutes in theatrical release",
        "Films using 8K cameras at 60 frames per second",
        "Employs 2500 visual effects artists for production",
        "Reaches 100 million viewers in first month"
    ],
    "music": [
        "Plays at precisely 120 beats per minute tempo",
        "Records at 192 kilohertz sample rate",
        "Reaches frequency range of 20-20,000 hertz",
        "Performs in venues seating 15,000 people",
        "Streams to 50 million listeners monthly"
    ],
    "brands": [
        "Values at precisely $100 billion market cap",
        "Serves 500 million customers annually",
        "Operates in exactly 150 countries worldwide",
        "Employs 250,000 people globally",
        "Generates $50 billion yearly revenue"
    ],
    "history": [
        "Occurred exactly 100 years ago in 1924",
        "Involved precisely 1 million participants",
        "Lasted exactly 5 years and 3 months",
        "Covered territory of 500,000 square miles",
        "Impacted 25% of global population"
    ]
}

# Fallback hints for specific words
WORD_HINTS = {
    "truth": [
        "Courts spend $50 billion annually to verify claims",
        "Scientific journals require 95% confidence level for publication",
        "Lie detectors measure pulse variations of 5-10 beats per minute",
        "Legal proceedings take 180 days on average to establish facts",
        "Digital fact-checking algorithms process 1 terabyte of data hourly"
    ],
    "dance": [
        "Professional training requires 6,000 hours over 10 years",
        "Performance spaces maintain 72°F temperature for optimal movement",
        "Dancers burn 450 calories per hour during rehearsals",
        "Stage lights generate 2,500 watts of illumination",
        "Competition venues span 2,000 square feet of sprung flooring"
    ],
    "storm": [
        "Generates winds at 120 kilometers per hour",
        "Drops 100 millimeters rain per hour",
        "Spans 100 kilometers diameter typical",
        "Creates lightning at 300 million volts",
        "Lasts 2-4 hours at peak intensity"
    ],
    "power": [
        "Global grid generates 25,000 terawatt-hours annually",
        "High-voltage lines carry 765,000 volts across continents",
        "Solar installations convert 20% of sunlight at 1,000 watts per square meter",
        "Batteries store 100 kilowatt-hours at 98% efficiency",
        "Distribution networks span 5 million kilometers worldwide"
    ],
    "heart": [
        "Pumps 7,500 liters of blood daily through vessels",
        "Maintains pressure of 120/80 millimeters of mercury",
        "Generates 1-5 watts of continuous electrical power",
        "Processes 2,000 gallons of blood in 24 hours",
        "Achieves 65% ejection fraction at peak performance"
    ],
    "space": [
        "Extends 93 billion light-years across observable universe",
        "Maintains temperature of -270.45°C in cosmic voids",
        "Contains dark energy density of 10^-29 grams per cubic centimeter",
        "Expands at 73.3 kilometers per second per megaparsec",
        "Electromagnetic waves travel 299,792 kilometers per second"
    ],
    "voice": [
        "Produces frequencies between 85-255 Hertz in adults",
        "Carries through air at 343 meters per second",
        "Generates sound pressure of 60 decibels in conversation",
        "Vocal cords vibrate 100-1000 times per second",
        "Transmits 1000 bits of information per second"
    ],
    "peace": [
        "Global initiatives cost $500 billion annually",
        "Humanitarian aid reaches 150 million people across 195 countries",
        "Reduces military spending by 75% in affected regions",
        "Diplomatic missions operate in 5,000 locations worldwide",
        "Peacekeeping forces cover 500,000 square kilometers"
    ],
    "brain": [
        "Processes information at 1016 operations per second",
        "Consumes 20% of body's oxygen at 15.4 liters per hour",
        "Contains exactly 86 billion neurons in adult humans",
        "Maintains temperature precisely at 37.2°C",
        "Generates 23 watts of power during active thinking"
    ],
    "light": [
        "Travels at exactly 299,792,458 meters per second",
        "Visible spectrum spans 380-700 nanometers wavelength",
        "LED bulbs last 50,000 hours at 90% efficiency",
        "Solar radiation delivers 1,000 watts per square meter",
        "Fiber optics transmit 1 terabit per second"
    ],
    "water": [
        "Covers 71% of Earth's surface at average depth 3,700 meters",
        "Boils at exactly 100°C at sea level pressure",
        "Reaches maximum density at precisely 4°C",
        "Processes 500 trillion liters through global water cycle daily",
        "Surface tension measures 72 dynes per centimeter at 20°C"
    ],
    "sound": [
        "Travels through air at 343 meters per second at 20°C",
        "Concert halls maintain 85 decibels average volume",
        "Human ear detects frequencies 20-20,000 Hertz",
        "Professional audio samples at 192 kilohertz",
        "Theater systems output 1,500 watts of acoustic power"
    ],
    "earth": [
        "Rotates at 1,037 miles per hour equator",
        "Orbits at 107,000 kilometers per hour",
        "Measures 12,742 kilometers diameter",
        "Maintains 14.7 PSI at sea level",
        "Tilts at 23.5 degrees on axis"
    ],
    "table": [
        "This furniture piece typically measures 30 inches in height and supports 250 pounds of weight",
        "Modern versions cost between $200-$800 and last approximately 15 years",
        "Found in 98% of dining rooms and used exactly 3 times daily for meals",
        "Occupies approximately 15-20 square feet of floor space in average homes",
        "Production requires precisely 2.5 hours of assembly time in factories"
    ],
    "phone": [
        "Modern versions process data at 2.5 gigahertz and store 128GB of data",
        "Battery lasts exactly 12-15 hours and charges in 90 minutes",
        "Screen measures 6.1 inches diagonally with 460 pixels per inch",
        "Weighs precisely 174 grams and measures 5.78 inches in height",
        "Camera captures images at 48 megapixels with f/1.8 aperture"
    ],
    "tiger": [
        "Adult males weigh exactly 420 pounds and measure 11 feet in length",
        "Runs at precisely 40 mph and jumps 20 feet horizontally",
        "Requires 15 pounds of meat daily and drinks 1 gallon of water",
        "Patrols territory of 40 square miles in natural habitat",
        "Lives between 20-25 years and sleeps 18 hours daily"
    ],
    "eagle": [
        "Spots prey from over 2 miles away with 20/4 vision acuity",
        "Dives at speeds exceeding 150 miles per hour during hunting",
        "Builds nests measuring up to 6 feet wide and 4 feet deep",
        "Wingspan typically ranges between 6 and 7.5 feet when fully grown",
        "Lives up to 30 years in natural habitats at elevations up to 10,000 feet"
    ],
    "shark": [
        "Swims continuously at 5 mph to push water through gills",
        "Detects blood in 1 part per million concentration from 0.25 miles",
        "Replaces 50,000 teeth in a lifetime spanning 70 years",
        "Dives to exactly 3,700 feet depth at 8 atmospheres pressure",
        "Maintains body temperature precisely 7°F above ambient water"
    ],
    "pasta": [
        "Cooks for exactly 8-12 minutes in water at 212°F",
        "Contains 200 calories per 2-ounce serving and 42g carbohydrates",
        "Production exceeds 14.5 million tons annually worldwide",
        "Requires 4-6 quarts of water per pound for cooking",
        "Stores for 24 months at 70°F in airtight containers"
    ],
    "paris": [
        "Covers exactly 105.4 square kilometers with population density of 20,000 per km²",
        "Receives approximately 30 million tourists annually spending $21 billion",
        "Maintains average temperature of 15.5°C across 4 distinct seasons",
        "Houses precisely 296 metro stations spanning 214 kilometers of track",
        "Hosts 20,000 historic monuments dating back to 300 BCE"
    ],
    "tokyo": [
        "Spans precisely 2,194 square kilometers housing 37 million residents",
        "Processes 8.5 million commuters daily through 882 train stations",
        "Experiences 1,500 measurable earthquakes annually above 3.0 magnitude",
        "Maintains 36% green space across 11,000 hectares of urban area",
        "Operates transit system moving 40 million passengers per day"
    ],
    "laser": [
        "Operates at precisely 1064 nanometers wavelength in industrial use",
        "Produces beam divergence of 0.5 milliradians at 100 meters",
        "Requires exactly 1.5 kilowatts power for continuous operation",
        "Achieves spot size of 25 microns for precise cutting",
        "Processes 1000 surface points per second in 3D scanning"
    ],
    "drama": [
        "Generates approximately $15 billion in annual box office revenue",
        "Requires exactly 120 pages for standard screenplay format",
        "Films at 24 frames per second using 35mm digital equivalent",
        "Processes 4K resolution at 3840 x 2160 pixels per frame",
        "Records audio at precisely 48 kHz sample rate"
    ],
    "actor": [
        "Memorizes 850 words of dialogue per hour of content",
        "Performs under 5600K lighting at 100 foot-candles",
        "Requires 12-14 hours on set for 3-4 minutes of usable footage",
        "Maintains precise positions within 2 inch markers on set",
        "Syncs dialogue within 0.03 seconds for perfect lip sync"
    ],
    "tempo": [
        "Measures precisely 120 beats per minute in common time",
        "Oscillates between 20 Hz and 20 kHz in audible range",
        "Records at exactly 44.1 kHz digital sampling rate",
        "Processes 32-bit floating point audio at 192 kHz",
        "Maintains timing accuracy within 0.5 milliseconds"
    ],
    "curry": [
        "Contains between 10 and 15 distinct spices in traditional recipes",
        "Preparation typically takes 45-60 minutes for authentic flavor",
        "Heat levels range from 500 to 50,000 Scoville units",
        "Originated over 4,000 years ago in South Asian cuisine",
        "Requires slow cooking at precisely 185°F for best results"
    ],
    "bread": [
        "Requires exactly 3 hours and 15 minutes for proper rising at 85°F",
        "Contains 150 calories per 2-ounce serving with 32g carbohydrates",
        "Bakes at precisely 375°F for 35 minutes until golden brown",
        "Uses 65% hydration ratio with 3% salt by flour weight",
        "Stays fresh for 48 hours when stored at 68°F"
    ],
    "cells": [
        "Divides every 24 hours under optimal conditions",
        "Maintains pH between 7.35-7.45 for proper function",
        "Contains exactly 37.2 trillion in human adult body",
        "Processes 1 billion ATP molecules per second",
        "Requires 0.1 millimeters minimum size for visibility"
    ],
    "quark": [
        "Exists at temperatures above 2 trillion degrees Celsius",
        "Measures exactly 10^-18 meters in theoretical diameter",
        "Requires precisely 200 GeV of energy for separation",
        "Discovered in 1968 using 30 GeV particle accelerators",
        "Occurs in exactly 6 distinct types with specific charges"
    ],
    "force": [
        "Measures exactly 9.81 meters per second squared at sea level",
        "Generates 1000 newtons per square meter of pressure",
        "Requires 10 joules of energy for basic mechanical work",
        "Operates across distances of 10^-15 to 10^15 meters",
        "Produces acceleration of 3.27 meters per second squared"
    ],
    "astronomy": [
        "Objects orbit at 7.67 kilometers per second",
        "Observes phenomena from 13.8 billion light-years away",
        "Detects radiation at wavelengths of 0.01 nanometers",
        "Measures stellar temperatures of 5,778 Kelvin",
        "Tracks objects moving at 2.1 million kilometers per hour"
    ],
    "research": [
        "Studies require exactly 1,000 test subjects",
        "Experiments run for precisely 36 months",
        "Data collection occurs every 15 minutes",
        "Analysis involves 50 terabytes of information",
        "Results achieve 95% confidence intervals"
    ],
    "house": [
        "Average construction requires 16,000 board feet of lumber",
        "Maintains internal temperature at 72°F year-round",
        "Consumes 28.5 kilowatt-hours of electricity daily",
        "Occupies 2,500 square feet of living space typically",
        "Costs $300,000 median price in current market"
    ],
    "world": [
        "Population exceeds 8 billion people across 195 countries",
        "Surface area measures 510.1 million square kilometers",
        "Rotates at 1,037 miles per hour at the equator",
        "Atmosphere extends 100 kilometers above sea level",
        "Contains 1.386 billion cubic kilometers of water"
    ],
    "happy": [
        "Releases 50 nanograms of serotonin per emotional event",
        "Increases heart rate by 15 beats per minute on average",
        "Activates 12 distinct facial muscles for genuine smiles",
        "Boosts productivity by 31% in workplace studies",
        "Extends lifespan by approximately 7.5 years statistically"
    ],
    "smart": [
        "Processes information at 1016 operations per second",
        "Requires 20% of body's glucose at 5.6 mmol/L",
        "Activates 100 billion neurons simultaneously",
        "Achieves 130+ score on standardized IQ tests",
        "Learns new concepts in 1.5 hours average time"
    ],
    "dream": [
        "Occurs during REM sleep at 90-minute intervals",
        "Brain waves oscillate at 4-7 Hz theta frequency",
        "Lasts precisely 20 minutes per episode typically",
        "Consumes 65% less glucose than waking state",
        "Activates hippocampus at 30% above baseline"
    ],
    "faith": [
        "Influences 84% of global population's decisions",
        "Reduces stress hormones by 23% in studies",
        "Practiced in 4,200 organized religions worldwide",
        "Involves 2.5 hours weekly in organized gatherings",
        "Spans historical records dating back 6,000 years"
    ],
    "grace": [
        "Dancers maintain balance at 0.1 degree precision",
        "Movements flow at 2.5 meters per second",
        "Training requires 5,000 hours of practice",
        "Performance scores average 9.5 out of 10",
        "Muscles respond within 0.1 seconds to adjustments"
    ],
    "music": [
        "Frequencies range from 20 Hz to 20,000 Hz",
        "Digital audio samples at 44,100 times per second",
        "Concert halls maintain 85 decibel average volume",
        "Notes divide octaves into 12 equal intervals",
        "Professional recordings use 24-bit resolution"
    ],
    "ocean": [
        "Covers 361.9 million square kilometers",
        "Reaches depths of 11,034 meters maximum",
        "Contains 1.335 billion cubic kilometers water",
        "Maintains 3.5% salinity average",
        "Processes 48% of carbon dioxide emissions"
    ],
    "cloud": [
        "Forms at 1,000-3,000 meters altitude",
        "Contains 0.5 grams water per cubic meter",
        "Moves at 30 kilometers per hour average",
        "Covers 67% of Earth's surface typically",
        "Reflects 80% of incident sunlight upward"
    ],
    "quiet": [
        "Measures below 30 decibels in sound level",
        "Reduces heart rate by 6 beats per minute",
        "Decreases cortisol levels by 35% in 15 minutes",
        "Sound waves attenuate to 0.1 pascal pressure",
        "Creates spaces with RT60 below 0.5 seconds"
    ],
    "smile": [
        "Activates 17 facial muscles simultaneously",
        "Releases 50 nanograms of endorphins",
        "Visible from 300 feet distance clearly",
        "Lasts 1/3 second in typical expression",
        "Improves mood by 25% in clinical studies"
    ],
    "youth": [
        "Cells regenerate every 24-36 hours",
        "Metabolism runs 15% faster than adult rate",
        "Growth occurs at 2.5 inches per year peak",
        "Brain processes information 1.5x adult speed",
        "Requires 2,800 calories daily for development"
    ],
    "flame": [
        "Burns at precisely 1,100°C in typical conditions",
        "Consumes 2 cubic feet of oxygen per minute",
        "Emits light at 555 nanometers wavelength peak",
        "Generates 4 kilowatts of heat energy",
        "Rises at 4.5 meters per second naturally"
    ],
    "camel": [
        "Stores 80 pounds of fat in each hump for energy",
        "Travels 100 miles without water in desert conditions",
        "Maintains body temperature between 34-41°C efficiently",
        "Runs at speeds up to 40 miles per hour in bursts",
        "Lives 40-50 years in natural habitat conditions"
    ],
    "horse": [
        "Gallops at speeds up to 55 miles per hour",
        "Sleeps 2-3 hours daily while standing upright",
        "Consumes 20-25 pounds of food daily",
        "Lives 25-30 years in domesticated settings",
        "Heart weighs 8.5 pounds and pumps 40 liters per minute"
    ],
    "koala": [
        "Sleeps 20-22 hours daily in eucalyptus trees",
        "Eats 2.5 pounds of leaves every 24 hours",
        "Maintains body temperature at 36.6°C constantly",
        "Lives 13-18 years in natural habitat",
        "Weighs 15-30 pounds when fully grown"
    ],
    "beach": [
        "Extends 12.5 kilometers shoreline length",
        "Slopes at 2-3 degrees typical grade",
        "Contains 98% pure silica sand content",
        "Changes 1 meter tidal range daily",
        "Erodes 2.5 meters annually average"
    ],
    "hotel": [
        "Occupies 150,000 square feet of building space",
        "Maintains 72°F temperature throughout 500 rooms",
        "Processes 1,000 guests daily during peak season",
        "Consumes 100 kilowatt-hours per room monthly",
        "Employs 250 staff members across 3 shifts"
    ],
    "store": [
        "Covers 50,000 square feet of retail space",
        "Processes 2,500 transactions daily",
        "Maintains inventory worth $2.5 million",
        "Employs 75 staff members across shifts",
        "Operates 14 hours daily at 72°F"
    ],
    "atoms": [
        "Measures 100 picometers in typical diameter",
        "Vibrates at 10^13 hertz at room temperature",
        "Contains exactly 6.022 × 10^23 particles per mole",
        "Bonds at angles of 104.5 degrees in molecules",
        "Requires 13.6 electron volts to ionize"
    ],
    "cells": [
        "Divides every 24 hours in optimal conditions",
        "Maintains pH between 7.35-7.45 precisely",
        "Contains 37.2 trillion in human adult body",
        "Processes 1 billion ATP molecules per second",
        "Measures 0.1 millimeters minimum size"
    ],
    "brain": [
        "Processes 1016 operations per second",
        "Consumes 20% of body's oxygen supply",
        "Contains 86 billion neurons exactly",
        "Maintains 37.2°C temperature precisely",
        "Generates 23 watts during active thinking"
    ],
    "sport": [
        "Athletes burn 800 calories per hour of activity",
        "Training requires 20 hours weekly for professionals",
        "Heart rate increases to 160 beats per minute",
        "Reaction time improves to 0.15 seconds",
        "Generates $500 billion in global revenue annually"
    ],
    "track": [
        "Measures exactly 400 meters per lap",
        "Surface maintains 10mm thickness for cushioning",
        "Temperature affects speed by 0.3% per degree Celsius",
        "Runners achieve speeds of 23 miles per hour",
        "Requires $500,000 for professional installation"
    ],
    "rugby": [
        "Match lasts exactly 80 minutes of play time",
        "Ball weighs 410-460 grams when properly inflated",
        "Field measures 100 meters by 70 meters",
        "Players run average of 7 kilometers per game",
        "Tackles impact with 1,600 newtons of force"
    ],
    "skate": [
        "Wheels rotate at 5,000 RPM at top speed",
        "Bearings rated at ABEC-7 precision grade",
        "Achieves speeds up to 30 miles per hour",
        "Requires 85A durometer hardness wheels",
        "Supports up to 250 pounds of weight"
    ],
    "score": [
        "Updates within 0.1 seconds of event",
        "Displays on screens 100 feet wide",
        "Processes 1,000 data points per game",
        "Tracks statistics with 99.9% accuracy",
        "Syncs across 50 display boards simultaneously"
    ],
    "chaos": [
        "Systems diverge at 2.5 units per second",
        "Patterns repeat every 256 iterations",
        "Generates 1 million unique states",
        "Processes variables at 100 Hz frequency",
        "Predicts outcomes with 65% accuracy"
    ],
    "guess": [
        "Probability equals 0.0016 for random success",
        "Takes 7 attempts on average to succeed",
        "Brain processes options in 2.5 seconds",
        "Accuracy improves 15% with each attempt",
        "Success rate reaches 95% by 10th try"
    ],
    "lucky": [
        "Odds calculate to exactly 1 in 1,000,000",
        "Occurs in 0.1% of random events",
        "Generates $150 billion in gambling revenue",
        "Influences decisions within 2.5 seconds",
        "Affects outcomes in 5% of cases studied"
    ],
    "quirky": [
        "Behavior deviates 2.5 standard deviations",
        "Occurs in 4.3% of population samples",
        "Processes information 15% differently",
        "Reaction times vary by 0.3 seconds",
        "Creates 30% more neural connections"
    ],
    "twist": [
        "Rotates exactly 360 degrees in one turn",
        "Generates torque of 50 newton-meters",
        "Completes motion in 0.5 seconds",
        "Requires 25 pounds of force to initiate",
        "Changes direction at 1,000 RPM maximum"
    ],
    "cat": [
        "Purrs at frequencies between 25-150 Hz for healing",
        "Sleeps exactly 16 hours per day on average",
        "Runs at speeds up to 30 miles per hour",
        "Has whiskers measuring 3-4 inches in length",
        "Maintains body temperature at 102°F"
    ],
    "dog": [
        "Detects odors at concentrations of 1 part per trillion",
        "Hears frequencies up to 45,000 Hz",
        "Runs at speeds reaching 45 miles per hour",
        "Has a bite force of 230-250 pounds per square inch",
        "Maintains body temperature at 101.5°F"
    ],
    "hat": [
        "Blocks 98% of harmful UV radiation",
        "Weighs approximately 150-200 grams",
        "Reduces head temperature by 10°F in sunlight",
        "Lasts 2-3 years with regular use",
        "Costs $25-45 on average in retail stores"
    ],
    "run": [
        "Burns 100 calories per mile",
        "Impacts feet with 2.5 times body weight",
        "Maintains 160 beats per minute heart rate",
        "Covers 26.2 miles in marathon distance",
        "Takes 2,000 steps per mile average"
    ],
    "sky": [
        "Appears blue due to 400-700 nanometer wavelengths",
        "Contains 78% nitrogen at sea level",
        "Extends 62 miles above Earth's surface",
        "Filters 75% of harmful UV radiation",
        "Changes color at precisely 90° viewing angle"
    ],
    "art": [
        "Values reach $450 million for famous pieces",
        "Uses pigments lasting 100+ years",
        "Requires 10,000 hours to master techniques",
        "Contains 16.7 million possible colors digitally",
        "Occupies 65% of museum exhibition space"
    ],
    "ant": [
        "Lifts 50 times its body weight",
        "Lives in colonies of 250,000 members",
        "Walks 700 meters per hour",
        "Survives underwater for 14 days",
        "Communicates using 10-20 pheromone signals"
    ],
    "bee": [
        "Flies at 20 miles per hour average speed",
        "Visits 5,000 flowers per day",
        "Beats wings 200 times per second",
        "Lives 4-5 weeks in summer",
        "Produces 1/12 teaspoon of honey in lifetime"
    ],
    "owl": [
        "Rotates head 270 degrees",
        "Spots prey from 100 meters away",
        "Flies silently at 40 miles per hour",
        "Lives 20-25 years in wild",
        "Hears frequencies up to 12,000 Hz"
    ],
    "pie": [
        "Bakes at exactly 375°F for 45 minutes",
        "Contains 300-400 calories per slice",
        "Uses 2.5 cups of flour in crust",
        "Serves 6-8 portions per 9-inch dish",
        "Stays fresh for 4 days at 40°F"
    ],
    "ham": [
        "Cures for 15-20 days in salt",
        "Contains 23 grams of protein per serving",
        "Smokes at 225°F for 6 hours",
        "Weighs 15-18 pounds on average",
        "Stores safely for 7 days at 40°F"
    ],
    "egg": [
        "Contains 6 grams of protein each",
        "Boils in exactly 7 minutes for medium",
        "Weighs 50-60 grams on average",
        "Stays fresh for 35 days refrigerated",
        "Requires 70°F to start incubation"
    ],
    "dna": [
        "Contains 3 billion base pairs in humans",
        "Measures 2 nanometers in diameter",
        "Replicates at 50 nucleotides per second",
        "Forms double helix at 10.5 base pairs per turn",
        "Stores 750 megabytes of genetic data"
    ],
    "ion": [
        "Carries charge of 1.6 × 10⁻¹⁹ coulombs",
        "Moves at 75 meters per second in solution",
        "Forms in plasma at 5,000°C",
        "Conducts 96,485 coulombs per mole",
        "Exists in solutions at 10⁻⁷ molar concentration"
    ],
    "gas": [
        "Expands 1% per 3°C temperature rise",
        "Moves at 500 meters per second at room temperature",
        "Occupies 22.4 liters per mole at STP",
        "Exerts 14.7 pounds per square inch at sea level",
        "Contains 6.022 × 10²³ molecules per mole"
    ],
    "app": [
        "Downloads at 25 megabytes per second",
        "Updates every 2-3 weeks on average",
        "Occupies 150MB of storage space",
        "Processes data at 60 frames per second",
        "Serves 1 million users daily"
    ],
    "cpu": [
        "Processes 3 billion instructions per second",
        "Operates at 3.5 gigahertz frequency",
        "Consumes 65 watts at full load",
        "Reaches temperatures of 90°C maximum",
        "Contains 7 billion transistors"
    ],
    "ram": [
        "Transfers data at 3200 megahertz",
        "Accesses in 10 nanoseconds",
        "Holds 16 gigabytes per module",
        "Consumes 1.2 volts during operation",
        "Processes 25.6 gigabytes per second"
    ],
    "ski": [
        "Descends at 60 miles per hour maximum",
        "Requires -2°C snow temperature minimum",
        "Uses 170-190cm length equipment",
        "Burns 400 calories per hour",
        "Operates on 15-30 degree slopes"
    ],
    "box": [
        "Delivers 1,000 pounds of force per punch",
        "Lasts exactly 3 minutes per round",
        "Burns 800 calories per hour training",
        "Requires 16-ounce gloves regulation",
        "Maintains 85% maximum heart rate"
    ],
    "bay": [
        "Extends 15 kilometers inland average",
        "Reaches depths of 100 meters typically",
        "Covers 400 square kilometers area",
        "Experiences 2-meter tidal range daily",
        "Maintains 20°C water temperature"
    ],
    "sea": [
        "Contains 35 grams of salt per liter",
        "Reaches depths of 3,688 meters average",
        "Covers 361 million square kilometers",
        "Produces 70% of Earth's oxygen",
        "Absorbs 2.2 billion tons of CO₂ yearly"
    ],
    "zoo": [
        "Houses 750 species on average",
        "Occupies 100 acres of land typically",
        "Attracts 2.5 million visitors annually",
        "Maintains 70°F temperature indoors",
        "Spends $50,000 daily on operations"
    ],
    "plant": [
        "Grows at precisely 2.5 millimeters per day in optimal conditions",
        "Requires 6 hours of direct sunlight at 5000 lumens intensity",
        "Processes 100 grams of CO2 into oxygen daily",
        "Maintains internal temperature within 2°C of ambient air",
        "Reaches maturity after 90 days of controlled growth"
    ],
    "clock": [
        "Measures time with 0.001 second precision per day",
        "Operates at 32,768 Hz crystal frequency",
        "Consumes 1.5 volts from standard battery",
        "Displays across 7 square centimeters of face area",
        "Functions reliably for 5 years between services"
    ],
    "paint": [
        "Dries in exactly 30 minutes at 23°C and 50% humidity",
        "Covers 400 square feet per gallon at 4 mils thickness",
        "Contains 45% solids by volume in latex formulation",
        "Resists fading for 15 years under normal conditions",
        "Achieves full cure strength after 168 hours"
    ],
    "sugar": [
        "Dissolves at 200 grams per 100ml at 20°C",
        "Contains exactly 16 calories per 4-gram teaspoon",
        "Crystallizes at precisely 154°C during candy making",
        "Stores safely for 2 years at 20°C and 60% humidity",
        "Requires 1000 liters of water per kilogram produced"
    ],
    "metal": [
        "Conducts electricity at 6.0×10⁷ siemens per meter",
        "Melts at temperatures above 1,538°C for steel",
        "Expands 1.2% per 100°C temperature increase",
        "Resists 200 megapascals of tensile stress",
        "Weighs 7.874 grams per cubic centimeter"
    ],
    "grass": [
        "Grows 2-6 millimeters daily spring rate",
        "Covers 40.5% of land surface naturally",
        "Produces 5 grams oxygen per square meter",
        "Requires 25 millimeters water weekly",
        "Reaches 15 centimeters root depth"
    ],
    "steam": [
        "Expands 1,600 times from water at 100°C",
        "Carries 2,257 kilojoules per kilogram of heat",
        "Reaches pressures of 15 pounds per square inch",
        "Condenses at 373.15 Kelvin at sea level",
        "Flows through pipes at 30 meters per second"
    ],
    "glass": [
        "Melts at temperatures above 1,500°C",
        "Transmits 90% of visible light wavelengths",
        "Withstands 50 megapascals of pressure",
        "Insulates with R-value of 0.95 per inch",
        "Weighs 2.58 grams per cubic centimeter"
    ],
    "paper": [
        "Weighs 75 grams per square meter standard",
        "Contains 90% cellulose fiber by mass",
        "Absorbs 0.1 milliliters water per square cm",
        "Resists tearing up to 5 newtons force",
        "Degrades over 2-5 months in landfills"
    ],
    "music": [
        "Vibrates air at 20-20,000 hertz frequency",
        "Travels through air at 343 meters per second",
        "Requires minimum 60 decibels for performance",
        "Processes 1,411,200 bits per second digitally",
        "Fills concert halls of 10,000 cubic meters"
    ],
    "radio": [
        "Broadcasts at 88-108 megahertz FM band",
        "Reaches 100 kilometers radius coverage",
        "Transmits at 100,000 watts maximum power",
        "Processes audio at 44.1 kilohertz sample rate",
        "Operates 24 hours consuming 5 kilowatts hourly"
    ],
    "wheat": [
        "Grows to heights of 1.2 meters in 120 days",
        "Requires 450mm annual rainfall for cultivation",
        "Produces 50 bushels per acre on average",
        "Contains 13% protein by dry weight measure",
        "Stores for 25 years at 10°C and 12% moisture"
    ],
    "honey": [
        "Contains 17.1 grams of carbohydrates per tablespoon",
        "Requires 2 million flower visits for 500 grams",
        "Never spoils when stored at 20°C in sealed containers",
        "Crystallizes naturally at 10°C after 6 months",
        "Measures 76 on the Brix scale of sugar content"
    ],
    "lemon": [
        "Contains 64 milligrams vitamin C per 100 grams",
        "Maintains pH level of 2.2 in juice form",
        "Grows on trees producing 600 fruits annually",
        "Stores for 21 days at 4°C and 85% humidity",
        "Requires 15 square meters space per tree"
    ],
    "olive": [
        "Contains 120 calories per 100 gram serving",
        "Requires 7 years for trees to reach full production",
        "Produces 45 kilograms of fruit per tree annually",
        "Stores for 18 months at 15°C in brine solution",
        "Processes into 15% oil by weight when pressed"
    ],
    "grape": [
        "Grows in clusters of 75 berries on average",
        "Contains 17 grams of sugar per 100 grams",
        "Requires 1,400 growing degree days to ripen",
        "Produces 12 tons per hectare in vineyards",
        "Ferments at 25°C for 14 days into wine"
    ],
    "peach": [
        "Ripens at exactly 25 days after fruit set",
        "Contains 39 calories per 100 gram serving",
        "Grows on trees yielding 150 pounds annually",
        "Requires 850 chill hours below 7°C",
        "Stores for 14 days at 0°C and 90% humidity"
    ],
    "sheep": [
        "Weighs 150 pounds at full adult size",
        "Produces 8 pounds of wool annually",
        "Grazes 2.5 acres per animal sustainably",
        "Lives productively for 10-12 years",
        "Maintains body temperature at 39°C"
    ],
    "horse": [
        "Runs at speeds up to 88 kilometers per hour",
        "Weighs 500 kilograms on average when adult",
        "Requires 20 liters of water daily",
        "Lives 25-30 years in domestic care",
        "Sleeps 3 hours per day standing up"
    ],
    "snake": [
        "Moves at speeds up to 5 meters per second",
        "Detects heat variations of 0.002°C",
        "Strikes prey from 1.5 meters distance",
        "Digests meals over 5-7 days period",
        "Sheds skin every 40-100 days cycle"
    ],
    "mouse": [
        "Weighs precisely 20 grams when adult",
        "Runs at 13 kilometers per hour maximum",
        "Lives 12-18 months in natural habitat",
        "Consumes 3 grams of food daily",
        "Maintains heart rate of 632 beats/minute"
    ],
    "whale": [
        "Dives to depths of 2,800 meters maximum",
        "Weighs up to 200,000 kilograms when adult",
        "Migrates 16,000 kilometers annually",
        "Lives 90 years on average naturally",
        "Consumes 3,600 kilograms of food daily"
    ],
    "coral": [
        "Grows 1.5 centimeters annually upward",
        "Covers 284,300 square kilometers reef",
        "Hosts 1,500 fish species per system",
        "Requires 23-29°C water temperature",
        "Lives 400+ years in optimal conditions"
    ],
    "pearl": [
        "Forms over 2-4 years in oysters",
        "Measures 7-8 millimeters diameter typically",
        "Requires 25°C water temperature optimal",
        "Reflects light at 90% efficiency rate",
        "Values at $300 per perfect specimen"
    ],
    "amber": [
        "Forms over 25-40 million years naturally",
        "Measures 2-3 on Mohs hardness scale",
        "Melts at precisely 375°C temperature",
        "Contains 79% carbon by atomic weight",
        "Transmits 90% of incident light through"
    ],
    "quill": [
        "Writes for 50 meters before refilling",
        "Measures 20 centimeters in length average",
        "Lasts 5 years with proper maintenance",
        "Produces lines 0.5 millimeters wide",
        "Holds 0.5 milliliters of ink capacity"
    ],
    "robot": [
        "Processes commands at 2.4 gigahertz speed",
        "Moves at precisely 1.5 meters per second",
        "Operates for 8 hours on single charge",
        "Lifts payloads up to 50 kilograms weight",
        "Navigates within 0.1 millimeter precision"
    ],
    "laser": [
        "Emits light at 650 nanometers wavelength",
        "Operates at 5 milliwatts continuous power",
        "Focuses to 0.2 millimeter spot diameter",
        "Reaches targets at 1000 meters distance",
        "Pulses at 1000 hertz repetition rate"
    ],
    "radar": [
        "Detects objects at 100 kilometers range",
        "Operates at 10 gigahertz frequency band",
        "Processes 1000 pulses per second",
        "Consumes 500 watts of power continuous",
        "Achieves 1 meter range resolution"
    ],
    "solar": [
        "Converts light at 20% efficiency rate",
        "Generates 250 watts per square meter",
        "Operates 25 years at rated output",
        "Requires 1000 volts DC systems",
        "Produces 2000 kilowatt-hours annually"
    ],
    "motor": [
        "Spins at 3600 revolutions per minute",
        "Draws 15 amperes at full load",
        "Produces 5 horsepower mechanical output",
        "Operates at 90% efficiency rating",
        "Weighs exactly 25 kilograms assembled"
    ],
    "phone": [
        "Processes data at 2.8 gigahertz speed",
        "Stores 256 gigabytes of information",
        "Displays 460 pixels per inch density",
        "Lasts 15 hours on single charge",
        "Connects at 1 gigabit per second"
    ],
    "drone": [
        "Flies at 70 kilometers per hour maximum",
        "Carries 2.5 kilograms payload capacity",
        "Operates for 25 minutes per charge",
        "Reaches 500 meters control range",
        "Captures 4K video at 60 frames/second"
    ],
    "clock": [
        "Keeps time within 1 second per year",
        "Oscillates at 32,768 hertz precisely",
        "Displays across 100 square centimeters",
        "Runs for 5 years on single battery",
        "Chimes at 85 decibels volume level"
    ],
    "watch": [
        "Measures time to 0.1 second precision",
        "Weighs exactly 45 grams assembled",
        "Resists water to 100 meters depth",
        "Operates for 2 years on battery",
        "Displays on 3.5 square centimeters"
    ],
    "pixel": [
        "Measures 0.2 millimeters square size",
        "Refreshes at 144 hertz frequency",
        "Produces 16.7 million color combinations",
        "Consumes 0.1 watts power each",
        "Lasts 50,000 hours operation time"
    ],
    "cable": [
        "Transfers data at 10 gigabits/second",
        "Spans lengths up to 100 meters copper",
        "Carries 600 volts maximum rating",
        "Weighs 50 grams per meter length",
        "Bends at minimum 4 centimeter radius"
    ],
    "audio": [
        "Samples at 48 kilohertz frequency",
        "Processes 24-bit depth resolution",
        "Outputs 100 watts per channel power",
        "Responds from 20-20,000 hertz range",
        "Achieves 100 decibel dynamic range"
    ],
    "flash": [
        "Illuminates for 1/1000 second duration",
        "Outputs 100 watt-seconds of energy",
        "Recycles in 2.5 seconds between uses",
        "Covers 80 degree beam angle area",
        "Triggers at 1/250 second sync speed"
    ],
    "drive": [
        "Stores 2 terabytes of data capacity",
        "Transfers at 550 megabytes/second",
        "Spins at 7200 revolutions/minute",
        "Consumes 6 watts during operation",
        "Accesses in 4.2 milliseconds average"
    ],
    "chips": [
        "Processes 5 billion transistors each",
        "Operates at 4 gigahertz frequency",
        "Consumes 95 watts at full power",
        "Measures 75 square millimeters die",
        "Produces 75 degrees Celsius heat"
    ],
    "river": [
        "Flows at 1.6 meters per second average",
        "Carries 200 million tons sediment yearly",
        "Spans 6,650 kilometers longest length",
        "Drains 7.05 million square kilometers",
        "Discharges 209,000 cubic meters/second"
    ],
    "desert": [
        "Receives less than 250mm rain yearly",
        "Covers 50.2 million square kilometers",
        "Reaches 57°C surface temperature max",
        "Contains 20% Earth's land surface",
        "Experiences 40°C daily temperature range"
    ],
    "frost": [
        "Forms at 0°C surface temperature",
        "Grows 1-2 millimeters per hour",
        "Requires 90% relative humidity minimum",
        "Damages crops at -2°C exposure",
        "Lasts 2-3 hours after sunrise typical"
    ],
    "flood": [
        "Rises 1 meter per hour at peak flow",
        "Carries 2,800 cubic meters per second",
        "Covers 100 square kilometers area",
        "Causes $40 billion annual damage",
        "Lasts 48-72 hours typical duration"
    ],
    "ozone": [
        "Absorbs 97-99% ultraviolet radiation",
        "Concentrates at 25 kilometers altitude",
        "Measures 300 Dobson units thickness",
        "Depletes 4% per decade currently",
        "Protects from 240-320nm wavelengths"
    ],
    "smog": [
        "Reduces visibility to 2 kilometers",
        "Contains 150 micrograms/m³ particles",
        "Forms above 20°C temperature inversion",
        "Traps pollutants below 1000 meters",
        "Persists 4-5 days during episodes"
    ],
    "wind": [
        "Blows at 15 meters per second average",
        "Generates 250 watts per square meter",
        "Carries 25 micrograms/m³ particles",
        "Changes direction 15 degrees hourly",
        "Gusts to 40 meters per second maximum"
    ],
    "chair": [
        "Supports 150 kilograms maximum weight",
        "Measures 45 centimeters seat height",
        "Occupies 0.6 square meters floor space",
        "Weighs 4.5 kilograms assembled",
        "Lasts 10 years average lifespan"
    ],
    "table": [
        "Measures 75 centimeters standard height",
        "Supports 100 kilograms distributed load",
        "Covers 2 square meters surface area",
        "Weighs 15 kilograms assembled",
        "Requires 4 square meters usage space"
    ],
    "paper": [
        "Measures 210x297 millimeters A4 size",
        "Weighs 80 grams per square meter",
        "Holds 21.6 kilograms tensile strength",
        "Contains 90% wood pulp composition",
        "Lasts 200 years acid-free storage"
    ],
    "glass": [
        "Contains 250 milliliters capacity",
        "Weighs 200 grams empty weight",
        "Withstands 100°C temperature change",
        "Measures 15 centimeters height",
        "Breaks at 30 newtons impact force"
    ],
    "knife": [
        "Measures 20 centimeters total length",
        "Weighs 150 grams balanced weight",
        "Cuts with 15 degree edge angle",
        "Holds edge for 100 hours use",
        "Contains 0.5% carbon steel content"
    ],
    "shoes": [
        "Weighs 300 grams per shoe average",
        "Lasts 500 miles walking distance",
        "Provides 1.5 centimeters cushioning",
        "Measures EU size 42 (26.5cm)",
        "Withstands 400 newtons impact force"
    ],
    "shirt": [
        "Measures 75 centimeters chest width",
        "Weighs 180 grams cotton material",
        "Contains 150 threads per inch",
        "Shrinks 2% after first wash",
        "Lasts 50 wash cycles typical"
    ],
    "pants": [
        "Measures 82 centimeters inseam length",
        "Weighs 400 grams denim material",
        "Contains 98% cotton composition",
        "Stretches 3% with wear",
        "Withstands 25 newtons tear force"
    ],
    "brush": [
        "Contains 2,500 bristles per head",
        "Measures 20 centimeters handle length",
        "Weighs 50 grams total weight",
        "Lasts 3 months average use",
        "Spans 3 centimeters bristle width"
    ],
    "soap": [
        "Weighs 100 grams per bar",
        "Contains 80% fatty acids content",
        "Lasts 30 days normal usage",
        "Measures pH 9.5 alkalinity",
        "Dissolves 0.5 grams per wash"
    ],
    "lamp": [
        "Produces 800 lumens light output",
        "Consumes 9 watts LED power",
        "Lasts 25,000 hours operation",
        "Measures 30 centimeters height",
        "Illuminates 10 square meters area"
    ],
    "book": [
        "Contains 300 pages average length",
        "Measures 15x23 centimeters size",
        "Weighs 450 grams paperback",
        "Uses 90 grams/m² paper weight",
        "Requires 7.2 megabytes storage digital"
    ],
    "keys": [
        "Measures 5.7 centimeters length each",
        "Weighs 15 grams per key brass",
        "Contains 6 pins per cylinder",
        "Requires 1.5 nm torque to turn",
        "Lasts 100,000 cycles lifetime"
    ],
    "bowl": [
        "Holds 500 milliliters capacity",
        "Measures 15 centimeters diameter",
        "Weighs 300 grams ceramic empty",
        "Withstands 150°C temperature",
        "Stacks to 5 centimeters height"
    ],
    "pen": [
        "Writes 2 kilometers line length",
        "Contains 0.7 millimeters ball tip",
        "Holds 0.3 milliliters ink volume",
        "Measures 14 centimeters length",
        "Lasts 2 years average use"
    ],
    "golf": [
        "Drives ball 250 meters maximum distance",
        "Uses 45.93 grams ball weight",
        "Requires 18 holes standard course",
        "Takes 4 hours average round time",
        "Covers 6,500 meters course length"
    ],
    "swim": [
        "Burns 500 calories per hour activity",
        "Moves at 2 meters per second speed",
        "Requires 25 meter pool minimum",
        "Takes 20 strokes per pool length",
        "Uses 85% muscle groups engaged"
    ],
    "bike": [
        "Travels 25 kilometers per hour average",
        "Weighs 8 kilograms road model",
        "Uses 700x23C tire dimensions",
        "Requires 50 watts power output",
        "Covers 40 kilometers typical ride"
    ],
    "jump": [
        "Reaches 0.5 meters vertical height",
        "Takes 0.5 seconds airborne time",
        "Uses 900 newtons ground force",
        "Burns 100 calories per 100 jumps",
        "Requires 2 square meters space"
    ],
    "run": [
        "Covers 10 kilometers per hour pace",
        "Burns 100 calories per kilometer",
        "Takes 180 steps per minute rate",
        "Uses 75% maximum heart rate",
        "Requires 2.5 liters water hourly"
    ],
    "ski": [
        "Travels 40 kilometers per hour average",
        "Uses 170 centimeters ski length",
        "Requires -5°C snow temperature",
        "Covers 20 kilometers daily distance",
        "Burns 400 calories per hour"
    ],
    "surf": [
        "Rides waves 2 meters height average",
        "Uses 6 foot board length typical",
        "Requires 10 knots wind minimum",
        "Takes 2 hours session length",
        "Catches 20 waves per session"
    ],
    "yoga": [
        "Burns 250 calories per hour practice",
        "Holds poses 30 seconds each",
        "Requires 4 square meters mat space",
        "Takes 60 minutes class length",
        "Uses 30% maximum heart rate"
    ],
    "box": [
        "Throws 60 punches per minute rate",
        "Burns 800 calories per hour",
        "Uses 12 ounce glove weight",
        "Takes 3 minute rounds standard",
        "Requires 16 square feet ring space"
    ],
    "dance": [
        "Burns 400 calories per hour activity",
        "Takes 120 beats per minute tempo",
        "Uses 70% maximum heart rate",
        "Requires 4 square meters space",
        "Lasts 2 hours typical session"
    ],
    "climb": [
        "Ascends 10 meters per minute rate",
        "Uses 10 millimeters rope diameter",
        "Requires 5.5 grade minimum skill",
        "Takes 30 minutes average route",
        "Burns 600 calories per hour"
    ],
    "hike": [
        "Covers 5 kilometers per hour pace",
        "Climbs 300 meters elevation gain",
        "Burns 440 calories per hour",
        "Takes 4 hours average trip",
        "Requires 2 liters water carried"
    ],
    "sail": [
        "Travels 15 knots maximum speed",
        "Uses 50 square meters sail area",
        "Requires 8 knots wind minimum",
        "Takes 4 hours typical trip",
        "Covers 30 nautical miles range"
    ],
    "bowl": [
        "Rolls ball at 20 miles per hour",
        "Uses 16 pounds ball weight",
        "Requires 60 feet lane length",
        "Takes 2 hours game duration",
        "Scores 300 points perfect game"
    ],
    "fish": [
        "Casts 30 meters line distance",
        "Uses 10 pound test line strength",
        "Requires 4 hours session time",
        "Takes 2.5 meters rod length",
        "Catches 5 fish average trip"
    ],
    "bake": [
        "Heats oven to 180°C standard",
        "Takes 45 minutes average time",
        "Uses 350 watts power consumption",
        "Requires 60% humidity optimal",
        "Loses 10% moisture during process"
    ],
    "grill": [
        "Heats to 230°C cooking surface",
        "Takes 12 minutes per side meat",
        "Uses 2000 watts electric power",
        "Covers 1600 square centimeters",
        "Marks 1 centimeter char lines"
    ],
    "boil": [
        "Reaches 100°C water temperature",
        "Takes 8 minutes per liter heat",
        "Uses 2400 watts electric power",
        "Evaporates 5% volume per hour",
        "Requires 2.2 kilojoules per gram"
    ],
    "fry": [
        "Heats oil to 180°C optimal",
        "Takes 3-5 minutes per batch",
        "Uses 1500 watts power typical",
        "Requires 2 liters oil minimum",
        "Absorbs 15% oil by food weight"
    ],
    "stew": [
        "Simmers at 85°C temperature",
        "Takes 2 hours cooking time",
        "Reduces liquid by 25% volume",
        "Serves 6 portions average",
        "Contains 500 calories per serve"
    ],
    "rice": [
        "Cooks for 20 minutes duration",
        "Absorbs 200% water by weight",
        "Contains 130 calories per 100g",
        "Expands 300% when cooked",
        "Requires 2:1 water ratio"
    ],
    "meat": [
        "Cooks at 63°C medium rare",
        "Contains 25 grams protein/100g",
        "Shrinks 25% during cooking",
        "Rests 5 minutes after heat",
        "Stores 5 days at 4°C"
    ],
    "fish": [
        "Cooks at 63°C internal temp",
        "Contains 20 grams protein/100g",
        "Takes 10 minutes per inch",
        "Stores 2 days at 4°C max",
        "Yields 45% edible portion"
    ],
    "soup": [
        "Simmers at 95°C temperature",
        "Takes 45 minutes preparation",
        "Contains 100 calories per cup",
        "Serves 8 portions typical",
        "Reduces 20% during cooking"
    ],
    "cake": [
        "Bakes at 175°C temperature",
        "Takes 35 minutes in oven",
        "Contains 350 calories per slice",
        "Rises 50% during baking",
        "Serves 12 portions standard"
    ],
    "salt": [
        "Dissolves in 2.8 ml water/gram",
        "Contains 2300mg sodium/teaspoon",
        "Melts at 801°C temperature",
        "Weighs 5 grams per teaspoon",
        "Stores indefinitely sealed"
    ],
    "milk": [
        "Contains 3.25% fat content",
        "Provides 150 calories per cup",
        "Weighs 1.03 grams per ml",
        "Stores 7 days at 4°C",
        "Contains 8 grams protein/cup"
    ],
    "eggs": [
        "Weighs 50 grams standard size",
        "Contains 6 grams protein each",
        "Cooks at 63°C soft boiled",
        "Takes 3 minutes to boil",
        "Stores 30 days refrigerated"
    ],
    "bread": [
        "Contains 80 calories per slice",
        "Rises for 60 minutes time",
        "Bakes at 200°C temperature",
        "Takes 30 minutes in oven",
        "Stores 5 days room temperature"
    ],
    "sugar": [
        "Dissolves in 0.5 ml water/gram",
        "Contains 16 calories per teaspoon",
        "Melts at 186°C temperature",
        "Weighs 4 grams per teaspoon",
        "Stores indefinitely sealed"
    ],
    "wave": [
        "Oscillates at 20-20,000 hertz frequency range",
        "Travels at 343 meters per second in air",
        "Amplifies to 120 decibels maximum safe level",
        "Spans wavelengths from 17 meters to 17 millimeters",
        "Transfers 1 joule energy per oscillation"
    ],
    "dust": [
        "Measures 2.5-10 micrometers particle size",
        "Settles at 0.3 meters per second in still air",
        "Accumulates 2 grams per square meter daily",
        "Filters through 0.3 micron HEPA systems",
        "Reflects 15% of incident light particles"
    ],
    "seed": [
        "Germinates at 20°C optimal temperature",
        "Contains 45% protein by dry weight",
        "Requires 48 hours soaking for activation",
        "Stores viably for 10 years at 4°C",
        "Produces 2,000 offspring per parent plant"
    ],
    "leaf": [
        "Absorbs 90% of incident red light",
        "Processes 0.5 grams CO2 per hour",
        "Maintains 25°C internal temperature",
        "Contains 70% water by fresh weight",
        "Spans 150 square centimeters area"
    ],
    "root": [
        "Grows 2.5 centimeters per day maximum",
        "Reaches depths of 2 meters typical",
        "Absorbs 500 milliliters water daily",
        "Supports 50 kilograms soil pressure",
        "Lives 20 years in perennial plants"
    ],
    "star": [
        "Radiates 3.828×10²⁶ watts energy",
        "Burns at 5,778 Kelvin surface temperature",
        "Measures 1.4 million kilometers diameter",
        "Contains 1.989×10³⁰ kilograms mass",
        "Fuses 600 million tons hydrogen hourly"
    ],
    "moon": [
        "Orbits at 384,400 kilometers distance",
        "Measures 3,475 kilometers diameter",
        "Reflects 12% of incident sunlight",
        "Cycles every 29.5 days precisely",
        "Influences tides by 2 meters height"
    ],
    "rain": [
        "Falls at 9 meters per second terminal velocity",
        "Measures 2 millimeters droplet diameter",
        "Delivers 25 millimeters per hour intensity",
        "Forms at 2,000 meters cloud height",
        "Covers 100 square kilometers per storm"
    ],
    "snow": [
        "Falls at 1.5 meters per second speed",
        "Accumulates 2.5 centimeters per hour",
        "Forms at -2°C cloud temperature",
        "Contains 95% air by volume",
        "Reflects 90% of incident sunlight"
    ],
    "wind": [
        "Blows at 15 meters per second average",
        "Generates 250 watts per square meter",
        "Moves air masses across 1000 kilometers",
        "Changes direction every 6 hours typically",
        "Carries 25 grams water vapor per cubic meter"
    ],
    "fire": [
        "Burns at 1,100°C typical temperature",
        "Consumes 2 cubic meters oxygen per minute",
        "Spreads at 10 meters per minute uphill",
        "Generates 4 kilowatts heat energy",
        "Emits light at 555 nanometers peak wavelength"
    ],
    "iron": [
        "Melts at precisely 1,538°C temperature",
        "Conducts 80 watts per meter-kelvin",
        "Weighs 7.874 grams per cubic centimeter",
        "Resists 200 megapascals tensile stress",
        "Contains 98% pure metal content"
    ],
    "gold": [
        "Melts at exactly 1,064°C temperature",
        "Conducts 318 watts per meter-kelvin",
        "Weighs 19.32 grams per cubic centimeter",
        "Stretches to 0.1 micrometers thickness",
        "Trades at $2000 per troy ounce"
    ],
    "sand": [
        "Measures 0.0625-2 millimeters grain size",
        "Weighs 1,600 kilograms per cubic meter",
        "Filters water at 0.45 microns effective",
        "Heats to 60°C in direct sunlight",
        "Supports 25 kilopascals bearing pressure"
    ],
    "rock": [
        "Withstands 200 megapascals compression",
        "Weighs 2,700 kilograms per cubic meter",
        "Forms over 1 million years typically",
        "Contains 65% silica by composition",
        "Erodes 1 millimeter per century"
    ]
}

class WordSelector:
    # Define available categories
    CATEGORIES = [
        "general",
        "animals",
        "food",
        "places",
        "science",
        "tech",
        "sports",
        "movies",
        "music",
        "brands",
        "history",
        "random",
        "4th_grade",
        "flashcard"
    ]

    # Available models in order of preference
    MODELS = [
        "anthropic/claude-3-sonnet",
        "mistralai/mistral-small-24b-instruct-2501:free",
        "openai/gpt-4",
        "google/gemini-pro"
    ]

    # Change from a single set to a dict of sets for per-category tracking
    _recently_used_words_by_category = {}
    _max_recent_words = int(os.getenv("RECENT_WORDS_LIMIT", "50"))  # Set by .env or default to 50

    def _add_recent_word(self, word: str, username: str = "global"):
        if username not in self._recently_used_words_by_user:
            self._recently_used_words_by_user[username] = []
        recent = self._recently_used_words_by_user[username]
        if word in recent:
            recent.remove(word)
        recent.insert(0, word)
        if len(recent) > self._max_recent_words:
            recent.pop()

    def get_recently_used_words(self, username: str = "global") -> list:
        return list(self._recently_used_words_by_user.get(username, []))

    def clear_recent_words(self, username: str = "global"):
        self._recently_used_words_by_user[username] = []
        logger.info(f"Cleared recently used words list for user: {username}")

    def _select_word_from_dictionary(self, word_length: int = 5, subject: str = "general", username: str = "global") -> str:
        logger.debug(f"Entered _select_word_from_dictionary with subject='{subject}', word_length='{word_length}', username='{username}' (length will be ignored)")
        # Get all possible words from hints.json for the subject
        hints_file = os.path.join('backend', 'data', 'hints.json')
        try:
            with open(hints_file, 'r', encoding='utf-8') as f:
                hints_data = json.load(f)
            templates = hints_data.get('templates', {})
            # Case-insensitive subject resolution
            ci_key_map = {k.lower(): k for k in templates.keys()}
            subject_key = ci_key_map.get(str(subject).lower()) or ci_key_map.get('general', 'general')
            all_words = list(templates.get(subject_key, {}).keys())
            # Normalize keys to their original displayed form but compare in lowercase
            all_words = [w for w in all_words if isinstance(w, str)]
        except Exception as e:
            logger.error(f"Error loading hints.json: {e}")
            all_words = []

        # Track recent words per user+subject
        recent_key = f"{username}:{(subject_key if 'subject_key' in locals() else subject)}"
        if not hasattr(self, "_recently_used_words_by_combo"):
            self._recently_used_words_by_combo = {}
        recent = set(self._recently_used_words_by_combo.get(recent_key, []))
        logger.debug(f"Recent word list for {recent_key}: {list(recent)}")
        # logger.info(f"[DEBUG] All recent word lists: {self._recently_used_words_by_combo}")

        # Block immediate repeat of last word
        if not hasattr(self, "_last_word_by_combo"):
            self._last_word_by_combo = {}
        last_word = self._last_word_by_combo.get(recent_key)

        # Exclude recently used words and last word for this combo
        candidates = [w for w in all_words if w not in recent and w != last_word]
        logger.debug(f"Candidate word list for {recent_key} (after filtering): {candidates}")
        if not candidates:
            # If all words used, allow repeats but still block immediate repeat
            candidates = [w for w in all_words if w != last_word]
            logger.debug(f"Candidate word list for {recent_key} (allowing repeats, still blocking last word): {candidates}")
        if not candidates:
            logger.error(f"No candidate words available for subject '{subject}' (length ignored, all would be immediate repeats)")
            return None

        word = random.choice(candidates)
        logger.debug(f"Selected fallback word: {word}")
        # Do NOT update last word here
        return word

    def _select_word_from_flashcard(self, username: str) -> str:
        """Pick a word from the user's FlashCard pool, building it from flash_text if needed."""
        try:
            from backend.bio_store import get_flash_text, get_flash_pool, set_flash_pool, get_active_flash_set_name, get_flash_set_pool
        except Exception:
            return None
        try:
            text = (get_flash_text(username) or '')[: self.flash_text_max]
            try:
                _active_name = get_active_flash_set_name(username) or 'flashcard'
                pool = get_flash_set_pool(username, _active_name)
                # If this is an imported/reference set, the per-set pool may be empty.
                # Fall back to the active set's resolved pool (which dereferences ref_token).
                if not isinstance(pool, list) or not pool:
                    try:
                        pool = get_flash_pool(username)
                    except Exception:
                        pool = []
            except Exception:
                pool = get_flash_pool(username)
            # If pool exceeds current target size (env lowered), trim and persist
            try:
                if pool and len(pool) > self.flash_words_count:
                    trimmed = list(pool)[: self.flash_words_count]
                    set_flash_pool(username, trimmed)
                    try:
                        logger.info(f"[FLASH_BUILD] trimmed pool from {len(pool)} to {len(trimmed)} user={username}")
                        print(f"[FLASH_BUILD][trim] {len(pool)}=>{len(trimmed)} user={username}")
                    except Exception:
                        pass
                    pool = trimmed
            except Exception:
                pass
            # Do not rebuild if a pool exists, even if smaller than target (e.g., document-generated pools)
            if not pool:
                try:
                    logger.info(f"[FLASH_BUILD] start user={username} pool_curr={len(pool) if pool else 0} target={self.flash_words_count} text_bytes={len((text or '').encode('utf-8','ignore'))}")
                    print(f"[FLASH_BUILD][start] user={username} curr={len(pool) if pool else 0} target={self.flash_words_count}")
                except Exception:
                    pass
                import time as _t
                _start = _t.time()
                # API-first pool builder from source text for nouns + contextual hints (env-gated)
                lst = []
                use_api_flash = os.getenv('FLASHCARD_API_FIRST', 'false').strip().lower() in ('1','true','yes','on')
                api_items = self._generate_flash_pool_api(text, max_items=self.flash_words_count) if use_api_flash else []
                if api_items:
                    # Deduplicate and limit to flash_words_count
                    seenw = set()
                    dedup = []
                    for it in api_items:
                        wl = str(it.get('word','')).strip().lower()
                        if not wl or wl in seenw:
                            continue
                        seenw.add(wl)
                        dedup.append(it)
                        if len(dedup) >= self.flash_words_count:
                            break
                    lst = dedup
                else:
                    words = self._extract_flash_words(text, max_items=self.flash_words_count)
                # Build map of existing API hints to reuse when text changes
                try:
                    prev_pool = get_flash_pool(username)
                except Exception:
                    prev_pool = []
                prev_api = {}
                try:
                    prev_api = { str(it.get('word','')).strip().lower(): it for it in (prev_pool or []) if str(it.get('hint_source','')) == 'api' and str(it.get('hint','')).strip() }
                except Exception:
                    prev_api = {}
                # First pass: one API attempt per word, then save immediately
                try:
                    import os as _os
                    _max_att = int(_os.getenv('PERSONAL_POOL_API_ATTEMPTS', '3'))
                except Exception:
                    _max_att = 3
                built_words = [it.get('word') for it in lst] if lst and isinstance(lst[0], dict) and 'word' in lst[0] else words
                # Runtime API usage toggle for FlashCard pool building (default: disabled)
                try:
                    _fc_runtime_api = os.getenv('FLASHCARD_RUNTIME_API', 'false').strip().lower() in ('1','true','yes','on')
                except Exception:
                    _fc_runtime_api = False
                for w in built_words:
                    if not w:
                        continue
                    wl = str(w).strip().lower()
                    # Reuse existing API hint if we have it
                    prev_item = prev_api.get(wl)
                    if prev_item and str(prev_item.get('hint','')).strip():
                        lst.append({"word": w, "hint": str(prev_item.get('hint')), 'hint_source': 'api', 'api_attempts': int(prev_item.get('api_attempts', 1)) or 1})
                        continue
                    hint_text = None
                    hint_source = 'local'
                    api_attempts = 0
                    # If API pool already provided hint for this word
                    try:
                        if isinstance(api_items, list):
                            for it in api_items:
                                if str(it.get('word','')).strip().lower() == wl and str(it.get('hint','')).strip():
                                    hint_text = str(it.get('hint')).strip()
                                    api_attempts = int(it.get('api_attempts', 1)) or 1
                                    hint_source = 'api'
                                    break
                    except Exception:
                        pass
                    # Otherwise attempt single API hint call (only if explicitly enabled)
                    if not hint_text and _fc_runtime_api:
                        try:
                            api_h = self.get_api_hints_force(w, 'flashcard', n=1, attempts=1)
                            hint_text = str(api_h[0]) if api_h else None
                            api_attempts = 1
                            hint_source = 'api' if hint_text else 'local'
                        except Exception:
                            hint_text = None
                    if not hint_text:
                        hint_text = self._make_flash_hint(w, text) or self._first_letter_hint(w)
                        hint_source = 'local'
                    # Append if not already present
                    if str(w).strip().lower() not in {it.get('word','').lower() for it in lst}:
                        lst.append({"word": w, "hint": hint_text or '', 'hint_source': hint_source, 'api_attempts': api_attempts})
                    # Respect time budget but try to reach target size; break if both time exceeded and we have enough
                    if (_t.time() - _start) >= getattr(self, 'flash_rebuild_max_secs', 5.0) and len(lst) >= self.flash_words_count:
                        break
                # If still short, top up with offline extraction beyond initial words to reach target size
                if len(lst) < self.flash_words_count:
                    try:
                        more = self._extract_flash_words(text, max_items=self.flash_words_count * 2)
                        existing = {it.get('word','').lower() for it in lst}
                        for w in more:
                            if len(lst) >= self.flash_words_count:
                                break
                            if not w or w.lower() in existing:
                                continue
                            hint_text = self._make_flash_hint(w, text) or self._first_letter_hint(w)
                            lst.append({"word": w, "hint": hint_text, 'hint_source': 'local', 'api_attempts': 0})
                            existing.add(w.lower())
                    except Exception:
                        pass
                set_flash_pool(username, lst)
                try:
                    logger.info(f"[FLASH_BUILD] saved items={len(lst)} user={username}")
                    print(f"[FLASH_BUILD][saved] items={len(lst)} user={username}")
                except Exception:
                    pass
                pool = lst
            # Maintenance pass: reattempt API hints only if explicitly enabled via FLASHCARD_RUNTIME_API
            try:
                import time as _t2
                import os as _os2
                changed = False
                budget = getattr(self, 'flash_rebuild_max_secs', 5.0)
                start = _t2.time()
                max_attempts = int(_os2.getenv('PERSONAL_POOL_API_ATTEMPTS', '3'))
                enable_runtime_api = _os2.getenv('FLASHCARD_RUNTIME_API', 'false').strip().lower() in ('1','true','yes','on')
                new_pool = []
                for it in (pool or []):
                    if (_t2.time() - start) >= budget:
                        new_pool.extend(pool[len(new_pool):])
                        break
                    w = str(it.get('word','')).strip()
                    hint = it.get('hint', '')
                    src = it.get('hint_source', 'local')
                    tries = int(it.get('api_attempts', 0))
                    if w and enable_runtime_api and (src != 'api') and (tries < max_attempts):
                        # one attempt this call
                        got = None
                        try:
                            ah = self.get_api_hints_force(w, 'flashcard', n=1, attempts=1)
                            got = str(ah[0]) if ah else None
                        except Exception:
                            got = None
                        tries += 1
                        if got:
                            it = {"word": w, "hint": got, 'hint_source': 'api', 'api_attempts': tries}
                            changed = True
                        else:
                            it = {"word": w, "hint": hint, 'hint_source': src, 'api_attempts': tries}
                            changed = True
                    new_pool.append(it)
                if changed:
                    set_flash_pool(username, new_pool)
                    try:
                        logger.info(f"[FLASH_BUILD] maintenance_updated items={len(new_pool)} user={username}")
                        print(f"[FLASH_BUILD][maint] items={len(new_pool)} user={username}")
                    except Exception:
                        pass
                    pool = new_pool
            except Exception:
                pass
            # Scope recents by active FlashCard token to avoid cross-set interference
            try:
                from backend.bio_store import get_active_flash_set_name, get_flash_set_token
                _active_name = get_active_flash_set_name(username) or 'flashcard'
                _active_tok = get_flash_set_token(username, _active_name) or ''
                recent_key = f"{username}:flashcard:{_active_tok or _active_name}"
            except Exception:
                recent_key = f"{username}:flashcard"
            if not hasattr(self, "_recently_used_words_by_combo"):
                self._recently_used_words_by_combo = {}
            recent = set(self._recently_used_words_by_combo.get(recent_key, []))
            candidates = [it for it in (pool or []) if str(it.get('word','')).lower() not in recent]
            if not candidates:
                candidates = pool or []
            if not candidates:
                return None
            import random as _rnd
            choice = _rnd.choice(candidates)
            # Soft-mark selection into the recents for FlashCard using token-scoped key
            try:
                if str(self.current_category).strip().lower() == 'flashcard':
                    from backend.bio_store import get_active_flash_set_name, get_flash_set_token
                    _active_name2 = get_active_flash_set_name(username) or 'flashcard'
                    _active_tok2 = get_flash_set_token(username, _active_name2) or ''
                    rk2 = f"{username}:flashcard:{_active_tok2 or _active_name2}"
                    if not hasattr(self, "_recently_used_words_by_combo"):
                        self._recently_used_words_by_combo = {}
                    lst2 = self._recently_used_words_by_combo.get(rk2, [])
                    w_lc2 = str(choice.get('word') or '').strip().lower()
                    if w_lc2 and w_lc2 not in lst2:
                        lst2.insert(0, w_lc2)
                        self._recently_used_words_by_combo[rk2] = lst2[: self._max_recent_words]
                    if not hasattr(self, "_last_word_by_combo"):
                        self._last_word_by_combo = {}
                    self._last_word_by_combo[rk2] = w_lc2
            except Exception:
                pass
            return str(choice.get('word') or '')
        except Exception:
            return None

    def _extract_flash_words(self, text: str, max_items: int = 10) -> list:
        """Extract words from FlashCard text using Personal-style allow/deny and scoring."""
        try:
            import re
            toks = re.findall(r"[A-Za-z0-9]+", text or "")
            # Expanded stopwords to avoid function words in FlashCard extraction
            stop = {
                "and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as",
                "while","every","then","etc","also","because","however","therefore","thus","very","really","quite","maybe","often","sometimes","usually","always","never","again","still",
                "than","into","onto","until","within","without","across","through","during","before","after","between","against","among","about","like","just","even","both","either","neither","each","per","via",
                # Common verb forms to exclude
                "called","call","calls","calling","has","have","had","can","could","make","makes","made","show","shows","showed","showing","talk","talks","talking"
            }
            number_words = {"zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen","twenty"}
            deny = {"people","person","thing","things","stuff","place","time","year","years","work","works","worked","working","live","lived","living","like","likes","liked","watch","watched","watching","join","joined","joining","use","used","using","since","have","been","most","many","life","day","days","good","bad","nice","great","hello","thanks","team"} | number_words
            def valid_word(w: str) -> bool:
                if not w or len(w) < 3 or len(w) > 15:
                    return False
                wl = w.lower()
                if wl in stop or wl in deny:
                    return False
                if wl.isdigit():
                    return False
                letters = ''.join([c for c in wl if c.isalpha()])
                if len(letters) < 2 or not any(c in 'aeiou' for c in letters):
                    return False
                return True
            scores = {}
            for t in toks:
                tl = t.lower()
                if not valid_word(tl):
                    continue
                rel = 1.0
                L = len(tl)
                if 5 <= L <= 9:
                    rel += 0.5
                if t[:1].isupper():
                    rel += 0.5
                scores[tl] = max(scores.get(tl, 0.0), rel)
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return [w for w,_ in ranked[:max_items]]
        except Exception:
            return []

    def _first_letter_hint(self, word: str) -> str:
        try:
            c = next((ch for ch in (word or '') if ch.isalpha()), None)
            return f"Starts with '{c.upper()}'" if c else "Starts with a letter"
        except Exception:
            return "Starts with a letter"

    def _build_flash_pool_prompt(self, text: str, max_items: int) -> dict:
        """Build an API prompt to extract nouns/proper nouns from text and a comprehension-style hint per word.

        The model must return strict JSON with shape:
        {"items": [{"word": "...", "pos": "noun", "hint": "..."}, ...]}
        """
        instr = (
            "You are extracting vocabulary for flashcards. Read the source text. "
            "Return only nouns or proper nouns that actually appear in the text (no verbs or function words). "
            "Favor meaningful entities and concepts over generic words. "
            "For each selected word, produce EXACTLY three short hints that test comprehension, ALL grounded in THIS text, and NEVER include the word itself (no substrings, case-insensitive): "
            "Hint A: plain-meaning or role in context. "
            "Hint B: where/why it matters in THIS text (policy, actor, action, section, outcome, etc.). "
            "Hint C: a concise related idea (synonym, consequence, example) that still fits THIS text. "
            "Keep hints simple and clear. Avoid generic filler. Do NOT leak the answer word in any hint. "
            "Respond ONLY with compact JSON object of the form: {\"items\": [{\"word\":\"\", \"pos\":\"noun\", \"hints\":[\"A\",\"B\",\"C\"]}, ...]} "
            f"Limit to {max_items} unique items."
        )
        return {
            "model": os.getenv("OPENROUTER_MODEL", "gpt-4o"),
            "messages": [
                {"role": "system", "content": instr},
                {"role": "user", "content": f"Source text:\n{text or ''}"},
            ]
        }

    def _generate_flash_pool_api(self, text: str, max_items: int = 10) -> list:
        """Call the API to extract noun words and contextual hints from the given text.

        Returns list of {word, hint, hint_source, api_attempts}.
        """
        try:
            if not text or not getattr(self, 'api_key_valid', False) or not getattr(self, 'api_key', None):
                return []
            messages = self._build_flash_pool_prompt(text, max_items)
            response = self._make_api_request_with_retry(messages)
            content = response["choices"][0]["message"]["content"].strip()
            # Strip code fences if any
            if content.startswith('```'):
                content = content.lstrip('`').strip()
                if content.startswith('json'):
                    content = content[4:].strip()
            import re as _re, json as _json
            data = None
            # Try JSON object directly
            try:
                data = _json.loads(content)
            except Exception:
                # Try to extract first JSON object
                m = _re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, _re.DOTALL)
                if m:
                    try:
                        data = _json.loads(m.group(0))
                    except Exception:
                        data = None
            # Build stop/deny sets to reject function words like 'called'
            stop = {
                "and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as",
                "while","every","then","etc","also","because","however","therefore","thus","very","really","quite","maybe","often","sometimes","usually","always","never","again","still",
                "than","into","onto","until","within","without","across","through","during","before","after","between","against","among","about","like","just","even","both","either","neither","each","per","via",
                # common verbs/auxiliaries/participles to exclude
                "called","call","calls","calling","has","have","had","can","could","make","makes","made","show","shows","showed","showing","talk","talks","talking"
            }
            deny = {"people","person","thing","things","stuff","place","time","year","years","work","works","worked","working","live","lived","living","like","likes","liked","use","used","using","since","most","many","life","day","days","good","bad","nice","great","hello","thanks","team"}
            import re as _re
            def _in_text_word(w: str) -> bool:
                try:
                    pattern = r"(?i)(?<![A-Za-z])" + _re.escape(w) + r"(?![A-Za-z])"
                    return _re.search(pattern, text or "") is not None
                except Exception:
                    return (w or '').lower() in (text or '').lower()

            # Prepare a set of content words from the text for grounding check
            content_words = set([t.lower() for t in _re.findall(r"[A-Za-z]{3,}", text or "")]) - stop - deny
            # Never allow certain verbs even if present
            hard_exclude = {"called","call","calls","calling"}

            items = []
            if isinstance(data, dict) and isinstance(data.get('items'), list):
                seen = set()
                for it in data['items']:
                    try:
                        w = str((it.get('word') or '')).strip()
                        hints_arr = it.get('hints')
                        h = str((it.get('hint') or '')).strip() if hints_arr is None else ''
                        if not w:
                            continue
                        wl = w.lower()
                        # Reuse FlashCard validity rules
                        letters = ''.join([c for c in wl if c.isalpha()])
                        if not (2 <= len(letters) <= 15) or not any(c in 'aeiou' for c in letters):
                            continue
                        # Exclude stop/deny/hard_exclude and ensure appears in text
                        if wl in stop or wl in deny or wl in hard_exclude or not _in_text_word(wl):
                            continue
                        if wl in seen:
                            continue
                        seen.add(wl)
                        # Build candidate hints list (prefer 3 from LLM if provided)
                        cand_hints = []
                        if isinstance(hints_arr, list):
                            for hh in hints_arr:
                                if isinstance(hh, str) and hh.strip():
                                    cand_hints.append(hh.strip())
                        elif h:
                            cand_hints.append(h)

                        # Sanitize candidates: remove answer leakage (substring, case-insensitive) and score groundedness
                        sanitized_scored = []
                        for hh in cand_hints:
                            try:
                                leak_pat = _re.compile(_re.escape(wl), _re.IGNORECASE)
                                if leak_pat.search(hh):
                                    continue
                                hint_tokens = set(t.lower() for t in _re.findall(r"[A-Za-z]{3,}", hh))
                                ground_score = len(hint_tokens & content_words)
                                if ground_score <= 0:
                                    continue
                                sanitized_scored.append((hh, ground_score))
                            except Exception:
                                continue

                        # Sort by groundedness (desc) so the first is most document-grounded
                        sanitized_scored.sort(key=lambda x: x[1], reverse=True)
                        sanitized = [hh for hh,_s in sanitized_scored]

                        # Ensure exactly 3 for optional storage; choose one primary for pool
                        while len(sanitized) < 3:
                            sanitized.append(f"Related to {wl}")

                        if sanitized:
                            hint_text = sanitized[0]
                            extra_hints = sanitized[:3]
                        else:
                            hint_text = None
                            extra_hints = []

                        if not hint_text:
                            hint_text = self._make_flash_hint(w, text)
                            extra_hints = [hint_text]
                        if not hint_text:
                            hint_text = self._first_letter_hint(w)
                            extra_hints = [hint_text]

                        items.append({
                            'word': w,
                            'hint': hint_text,
                            'hints': extra_hints,
                            'hint_source': 'api',
                            'api_attempts': 1,
                        })
                        if len(items) >= max_items:
                            break
                    except Exception:
                        continue
            # If API returned too few, fill with offline extractor to reach target
            if len(items) < max_items:
                try:
                    fillers = self._extract_flash_words(text, max_items=max_items)
                    fillers = [w for w in fillers if w and w.lower() not in {it['word'].lower() for it in items}]
                    for w in fillers:
                        if len(items) >= max_items:
                            break
                        hint_text = self._make_flash_hint(w, text) or self._first_letter_hint(w)
                        items.append({'word': w, 'hint': hint_text, 'hint_source': 'local', 'api_attempts': 0})
                except Exception:
                    pass
            return items
        except Exception:
            return []

    def _make_flash_hint(self, word: str, text: str) -> str:
        """Create a comprehension-style hint from nearby context; fallback to first letter."""
        try:
            w = (word or '').strip()
            src = (text or '')
            idx = src.lower().find(w.lower())
            # Helper: choose up to 2 meaningful keywords near the word
            def _keywords(window: str, target: str) -> list:
                import re as _re
                # Match extraction stopwords for keyword selection too
                stop = {
                    "and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as",
                    "while","every","then","etc","also","because","however","therefore","thus","very","really","quite","maybe","often","sometimes","usually","always","never","again","still",
                    "than","into","onto","until","within","without","across","through","during","before","after","between","against","among","about","like","just","even","both","either","neither","each","per","via",
                    "called","call","calls","calling"
                }
                toks = _re.findall(r"[A-Za-z]{3,}", window)
                scores = []
                for t in toks:
                    tl = t.lower()
                    if tl == target.lower() or tl in stop:
                        continue
                    score = 1
                    if tl.endswith(('tion','sion','ment','ness','ity','ism','ing','ed','ship','ance','ence')):
                        score += 1
                    if t[:1].isupper():
                        score += 1
                    scores.append((t, score))
                scores.sort(key=lambda x: x[1], reverse=True)
                out = []
                for t,_ in scores:
                    if t.lower() not in {o.lower() for o in out}:
                        out.append(t)
                    if len(out) >= 2:
                        break
                return out

            if idx != -1:
                start = max(0, idx - 80)
                end = min(len(src), idx + 80)
                ctx = src[start:end]
                kws = _keywords(ctx, w)
                first = next((ch for ch in w if ch.isalpha()), None)
                # Try to phrase as a question that checks understanding
                if kws:
                    if len(kws) == 1:
                        return f"In the passage, which term is closely tied to {kws[0]}?"
                    return f"Which concept in the text connects {kws[0]} and {kws[1]}?"
            # Fallback: first letter prompt
            return self._first_letter_hint(w)
        except Exception:
            return self._first_letter_hint(word)

    def __init__(self):
        """Initialize the word selector."""
        self.use_fallback = False
        self.current_category = None  # Track current word category
        
        # Try to load API key from environment
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        logger.debug(f"Loaded OPENROUTER_API_KEY from environment: {self.api_key[:8]}...{'*' * (len(self.api_key)-8) if self.api_key else ''}")
        if not self.api_key:
            logger.info("Looking for .env file at: " + os.path.abspath(".env"))
            load_dotenv()
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            logger.debug(f"Loaded OPENROUTER_API_KEY from .env: {self.api_key[:8]}...{'*' * (len(self.api_key)-8) if self.api_key else ''}")
        if not self.api_key:
            logger.info("No valid API key found. Using fallback mode.")
            self.use_fallback = True
            self.api_key_valid = False
        else:
            # Validate format
            valid = self._validate_api_key()
            logger.debug(f"API key validation result: {valid}")
            self.api_key_valid = valid
            if not valid:
                logger.info("API key format invalid. Using fallback mode.")
                self.use_fallback = True
        
        # Remove all words.json loading
        # self.words_data = {}
        # Set up headers according to OpenRouter requirements
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cursor",
            "X-Title": "Word Guess Game",
            "User-Agent": "Cursor/1.0.0",
            "Accept": "application/json"
        }

        # Initialize model list in order of preference
        self.models = [
            "mistralai/mistral-small-24b-instruct-2501:free",  # Free tier model
            "openai/gpt-4",
            "anthropic/claude-3-sonnet",
            "google/gemini-pro"
        ]
        
        # Track recently used words
        self._recently_used_words = set()
        self._max_recent_words = int(os.getenv("RECENT_WORDS_LIMIT", "50"))  # Set by .env or default to 50

        # Email configuration
        self.admin_email = os.getenv("ADMIN_EMAIL")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")

        # Track recently used words per user
        self._recently_used_words_by_user = {}
        self._max_recent_words = int(os.getenv("RECENT_WORDS_LIMIT", "50"))  # Set by .env or default to 50

        # Personal pool env knobs
        try:
            self.personal_pool_max = int(os.getenv("PERSONAL_POOL_MAX", "60"))
        except Exception:
            self.personal_pool_max = 60
        try:
            self.personal_pool_batch_size = int(os.getenv("PERSONAL_POOL_BATCH_SIZE", "10"))
        except Exception:
            self.personal_pool_batch_size = 10
        try:
            self.personal_pool_api_attempts = int(os.getenv("PERSONAL_POOL_API_ATTEMPTS", "3"))
        except Exception:
            self.personal_pool_api_attempts = 3

        # Check for .env variable to bypass API word selection
        self.bypass_api_word_selection = os.getenv("BYPASS_API_WORD_SELECTION", "false").lower() == "true"
        logger.debug(f"BYPASS_API_WORD_SELECTION is set to: {self.bypass_api_word_selection}")
        if self.bypass_api_word_selection:
            logger.debug("Bypassing API for word selection due to BYPASS_API_WORD_SELECTION setting. Using fallback/dictionary only (except 'personal' and 'flashcard').")
            self.use_fallback = True  # default to fallback

        self._api_hint_cache = {}

        # Read OpenRouter model names from .env
        self.primary_model = os.getenv("OPENROUTER_MODEL_PRIMARY", "mistralai/mistral-small-24b-instruct-2501:free")
        self.fallback_model = os.getenv("OPENROUTER_MODEL_FALLBACK", "openai/gpt-4o")
        # Available models in order of preference (for other uses)
        self.models = [self.primary_model, self.fallback_model]
        # FlashCard env knobs (aligned with Personal)
        try:
            self.flash_text_max = int(os.getenv("FLASHCARD_TEXT_MAX", "500"))
        except Exception:
            self.flash_text_max = 500
        try:
            # Single source of truth: FLASHCARD_POOL_MAX (fallback default 10)
            self.flash_words_count = int(os.getenv("FLASHCARD_POOL_MAX", "10"))
        except Exception:
            self.flash_words_count = 10
        try:
            self.flash_rebuild_max_secs = float(os.getenv("PERSONAL_POOL_REBUILD_MAX_SECS", "5"))
        except Exception:
            self.flash_rebuild_max_secs = 5.0
        try:
            # Use Personal's batch size/attempts for FlashCard, for symmetry
            self.flash_batch_size = int(os.getenv("PERSONAL_POOL_BATCH_SIZE", "10"))
        except Exception:
            self.flash_batch_size = 10
        try:
            self.flash_api_attempts = int(os.getenv("PERSONAL_POOL_API_ATTEMPTS", "3"))
        except Exception:
            self.flash_api_attempts = 3

    def _load_users_db(self) -> dict:
        try:
            from streamlit_app import load_users  # local import to avoid cycles
            users = load_users()
            return users if isinstance(users, dict) else {}
        except Exception:
            return {}

    def _save_users_db(self, users: dict) -> None:
        try:
            from streamlit_app import save_users  # local import to avoid cycles
            if isinstance(users, dict):
                save_users(users)
        except Exception:
            pass

    def _infer_role_for_name(self, word: str, bio_text: str) -> str:
        try:
            w = (word or '').strip()
            if not w:
                return ''
            # Reject obvious generic/function words for name inference
            wl = w.lower()
            generic = {
                'have','since','and','the','this','that','these','those','with','without','about','into','onto',
                'from','by','for','as','at','to','in','of','on','a','an','is','are','was','were','be','been','am',
                'i','you','your','my','our','their','his','her','it','they','we','me','him','her','them'
            }
            if wl in generic:
                return ''
            idx = bio_text.lower().find(w.lower())
            if idx == -1:
                return ''
            # Require likely proper name capitalization in original text segment
            orig_seg = bio_text[idx: idx + len(w)]
            if not (orig_seg[:1].isupper() and (len(orig_seg) == 1 or not orig_seg[1:].isupper())):
                # Not titlecased like a proper name → avoid mapping to family role
                return ''
            window = bio_text[max(0, idx - 80): idx + 80]
            if 'wife' in window:
                return 'your wife'
            if 'daughter' in window:
                return 'your daughter'
            if 'son' in window or 'sons' in window:
                return 'your son'
            if 'teacher' in window:
                return 'a teacher'
            if 'pharmacist' in window:
                return 'a pharmacist'
            if 'marketing' in window:
                return 'in digital marketing'
            if 'student' in window:
                return 'a student'
            return ''
        except Exception:
            return ''

    def _make_profile_hint(self, word: str, rec: dict) -> str:
        """Create a clearer one-line hint based on profile context rather than a generic label.

        Enhanced: if the bio contains the exact word, extract a local context window and
        surface up to two meaningful neighboring keywords, mirroring FlashCard behavior.
        Falls back to role/location/occupation heuristics and finally first-letter.
        """
        try:
            wl = (word or '').strip().lower()
            bio_text = str(rec.get('bio') or '')
            # Inline helper for first letter
            def _first_letter_hint(w: str) -> str:
                try:
                    for c in (w or ''):
                        if c.isalpha():
                            return f"Starts with '{c.upper()}'"
                    return "Starts with a letter"
                except Exception:
                    return "Starts with a letter"
            # If the bio contains the exact word, build a context-based hint
            try:
                idx = bio_text.lower().find(wl)
                if idx != -1:
                    start = max(0, idx - 80)
                    end = min(len(bio_text), idx + 80)
                    window = bio_text[start:end]
                    import re as _re
                    stop = {"and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as"}
                    toks = _re.findall(r"[A-Za-z]{3,}", window)
                    scores = []
                    for t in toks:
                        tl = t.lower()
                        if tl == wl or tl in stop:
                            continue
                        score = 1
                        if tl.endswith(('tion','sion','ment','ness','ity','ism','ing','ed','ship','ance','ence')):
                            score += 1
                        if t[:1].isupper():
                            score += 1
                        scores.append((t, score))
                    scores.sort(key=lambda x: x[1], reverse=True)
                    neigh = []
                    for t,_ in scores:
                        if t.lower() not in {o.lower() for o in neigh}:
                            neigh.append(t)
                        if len(neigh) >= 2:
                            break
                    first = next((ch for ch in (word or '') if ch.isalpha()), None)
                    if neigh and first:
                        if len(neigh) == 1:
                            return f"Starts with '{first.upper()}'. Related to {neigh[0]}"
                        return f"Starts with '{first.upper()}'. Related to {neigh[0]} and {neigh[1]}"
            except Exception:
                pass
            # Early guard for generic tokens
            generic = {
                'have','since','and','the','this','that','these','those','with','without','about','into','onto',
                'from','by','for','as','at','to','in','of','on','a','an','is','are','was','were','be','been','am',
                'i','you','your','my','our','their','his','her','it','they','we','me','him','her','them'
            }
            if wl in generic:
                return _first_letter_hint(word)
            # Location first (avoid misclassifying 'Jose')
            addr_str = str(rec.get('address') or '')
            if wl in {'almaden','jose','san','california'} or (addr_str and wl in addr_str.lower()):
                if wl == 'jose' and 'san jose' in (bio_text or '').lower():
                    return 'Related to where you live'
                return 'Related to where you live'
            # Specific token 'high' → prefer first-letter hint to avoid awkward phrasing
            if wl == 'high':
                return _first_letter_hint(word)
            # Named entities from bio (family members)
            role = self._infer_role_for_name(word, bio_text)
            if role:
                if role.startswith('your'):
                    return f"Name of {role}"
                return f"Related to {role}"
            # Occupation keywords
            if wl in {'engineer','teacher','pharmacist'}:
                if wl == 'engineer':
                    return 'Your profession'
                return 'A family occupation'
            # Work and apps
            if wl in {'software','ai','wizword','powered','developing','develop'}:
                if wl == 'wizword':
                    return 'An app you develop'
                if wl == 'ai':
                    return 'A field you work with'
                if wl in {'powered'}:
                    return 'About the AI-powered apps you build'
                if wl in {'develop','developing'}:
                    return 'About building apps you work on'
                return 'Your field of work'
            # Company / networks
            if wl in {'juniper','network','networks'}:
                return 'Related to your previous company'
            # Location
            if wl in {'almaden','jose','san'} or (rec.get('address') and wl in rec.get('address','').lower()):
                return 'Related to where you live'
            # High-tech phrase
            if wl == 'high' and 'high tech' in (bio_text or '').lower():
                return "From 'high tech' in your bio"
            # Sports
            if wl in {'soccer','basketball'}:
                return 'A sport you like to watch'
            # Family roles
            if wl in {'wife','daughter','son','sons','family'}:
                return 'A family relationship'
            # Education
            if wl in {'student','study','college','school'}:
                return 'Tied to education'
            # Default to a helpful first-letter hint
            return _first_letter_hint(word)
        except Exception:
            return "Starts with a letter"

    def get_user_personal_pool(self, username: str) -> list:
        # Prefer users_bio.json store
        try:
            from backend import bio_store
            pool = bio_store.get_personal_pool(username)
        except Exception:
            users = self._load_users_db()
            rec = users.get((username or '').lower(), {}) if isinstance(users, dict) else {}
            pool = rec.get('personal_pool') or []
        # Normalize to list of {word, hint}
        norm = []
        for item in pool:
            try:
                w = str(item.get('word', '')).strip()
                h = str(item.get('hint', '')).strip()
                if w:
                    norm.append({'word': w, 'hint': h})
            except Exception:
                continue
        return norm

    def set_user_personal_pool(self, username: str, pool: list) -> None:
        try:
            from backend import bio_store
            bio_store.set_personal_pool(username, pool)
        except Exception:
            users = self._load_users_db()
            key = (username or '').lower()
            if key not in users or not isinstance(users[key], dict):
                users[key] = {}
            users[key]['personal_pool'] = pool
            self._save_users_db(users)

    def add_or_update_personal_hint(self, username: str, word: str, hint: str) -> None:
        """Ensure the user's personal_pool contains the word with a hint (update or append)."""
        try:
            # Skip writes in guest demo mode
            import streamlit as _st  # type: ignore
            if _st.session_state.get('guest_mode'):
                return
        except Exception:
            pass
        try:
            from backend import bio_store
            pool = bio_store.get_personal_pool(username)
            updated = False
            wl = (word or '').strip().lower()
            for it in pool:
                if (it.get('word') or '').strip().lower() == wl:
                    if hint and hint.strip():
                        it['hint'] = hint.strip()
                    updated = True
                    break
            if not updated and wl:
                pool.append({'word': word, 'hint': (hint or '').strip()})
            bio_store.set_personal_pool(username, pool)
        except Exception:
            pass

    def generate_personal_pool(self, username: str, n: int = 10, avoid: list = None) -> list:
        """Generate a list of personal words with a single hint each for a user.
        Optionally avoid words already present in the user's pool. When API returns fewer than
        requested, keep partial results and request only the remainder up to 3 short attempts,
        then top-up with the offline generator. Filters remove low-value tokens (e.g., 'since', 'have').
        """
        # Normalize avoidance set (lowercased words)
        avoid_set = {str(w).strip().lower() for w in (avoid or []) if str(w).strip()}
        # Early capacity guard: if pool already at or above 60, do not call API
        try:
            existing_pool = self.get_user_personal_pool(username or 'global')
            if existing_pool and len(existing_pool) >= self.personal_pool_max:
                logger.info(f"[PERSONAL] Pool at capacity (>={self.personal_pool_max}); skipping API/offline generation")
                return []
        except Exception:
            pass
        # If API key is missing/invalid, use offline generator directly
        if not getattr(self, 'api_key_valid', False) or not getattr(self, 'api_key', None):
            logger.warning("[PERSONAL] Using offline generator for personal pool (no valid API key)")
            return self._generate_personal_pool_offline(username, n=n, avoid_set=avoid_set)
        profile_parts = []
        try:
            # Bio + occupation + education + address from users_bio/users.json
            from backend import bio_store
            bio_text = bio_store.get_bio(username)
            if bio_text:
                profile_parts.append(f"bio: {bio_text.strip()}")
            users = self._load_users_db()
            rec = users.get((username or '').lower(), {})
            occ = (rec.get('occupation') or '').strip()
            edu = (rec.get('education') or '').strip()
            addr = (rec.get('address') or '').strip()
            if occ:
                profile_parts.append(f"occupation: {occ}")
            if edu:
                profile_parts.append(f"education: {edu}")
            if addr:
                profile_parts.append(f"address: {addr}")
        except Exception:
            pass
        persona = "; ".join(profile_parts) or f"username: {username}"
        avoid_list = ", ".join(sorted({w for w in (avoid_set or set())}))
        prompt = (
            "Generate a JSON array of {n} items for a personal word pool based on this profile: '" + persona + "'. "
            "Each item must be an object with keys 'word' (single alphanumeric noun) and 'hint' (a short one-line clue). "
            + (f"Avoid these words: [{avoid_list}]. " if avoid_list else "") +
            "Return STRICT JSON only (no prose)."
        )
        # Build allowed terms from profile tokens (bio-only)
        def _tok(s: str) -> list:
            import re
            return [t.lower() for t in re.findall(r"[A-Za-z0-9]+", s or "") if t]
        try:
            from backend import bio_store
            users = self._load_users_db()
            rec = users.get((username or '').lower(), {})
            occ = (rec.get('occupation') or '')
            edu = (rec.get('education') or '')
            addr = (rec.get('address') or '')
            allowed_terms = set(_tok(bio_store.get_bio(username))) | set(_tok(occ)) | set(_tok(edu)) | set(_tok(addr))
        except Exception:
            allowed_terms = set()
        
        def _parse_json_array_safely(raw: str):
            """Attempt to parse a JSON array from raw text with best-effort repairs.
            Returns a Python list or [].
            """
            import json, re, logging
            log = logging.getLogger("backend.word_selector")
            if not isinstance(raw, str):
                return []
            text = raw.strip()
            # Strip code fences
            if text.startswith('```'):
                text = text.lstrip('`').strip()
                if text.startswith('json'):
                    text = text[4:].strip()
            # Normalize newlines and smart quotes
            text = text.replace('\r', ' ').replace('\n', ' ')
            text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', '"').replace('\u2019', '"')
            text = text.replace('“', '"').replace('”', '"').replace('’', '"').replace('‘', '"')
            # Fix trailing commas
            text = text.replace(', ]', ']').replace(',]', ']')
            # If the whole array is quoted like "[ {...} ]", unquote it
            if text.startswith('"[') and text.endswith(']"'):
                text = text[1:-1]
            # Remove empty string elements in array like ["", {...}] or [{...}, ""]
            text = re.sub(r'\[\s*""\s*,', '[', text)
            text = re.sub(r',\s*""\s*\]', ']', text)
            text = re.sub(r',\s*""\s*,', ',', text)
            # Unwrap accidentally quoted objects inside the array: "{...}" -> {...}
            # Common malformed pattern seen in provider payloads
            text = text.replace('""{', '{').replace('}""', '}')
            text = text.replace('"{', '{').replace('}"', '}')
            # Extract array region if possible
            m = re.search(r'\[[\s\S]*\]', text)
            candidate = m.group(0).strip() if m else text
            # Try direct load
            try:
                return json.loads(candidate)
            except Exception:
                pass
            # Attempt to convert single quotes to double quotes in a targeted way
            try:
                # Replace single-quoted keys: 'key': -> "key":
                candidate2 = re.sub(r"'([A-Za-z0-9_]+)'\s*:\s*", r'"\1": ', candidate)
                # Replace single-quoted string values after colon or comma
                candidate2 = re.sub(r":\s*'([^']*)'", r': "\1"', candidate2)
                candidate2 = re.sub(r",\s*'([^']*)'\s*([,\]])", r', "\1"\2', candidate2)
                return json.loads(candidate2)
            except Exception:
                pass
            # As a last resort, build array from object snippets
            try:
                objs = re.findall(r'\{[^{}]*\}', text)
                if objs:
                    arr = '[' + ','.join(objs) + ']'
                    return json.loads(arr)
            except Exception:
                pass
            # Log truncated payload for diagnostics and return []
            try:
                log.warning(f"[PERSONAL] JSON repair failed. Raw payload (truncated): {text[:200]}")
            except Exception:
                pass
            return []
        try:
            import json, re
            collected = []
            collected_set = set()
            remaining = n
            attempt = 0
            max_attempts = 3
            # Common validity checks (avoid low-value words)
            stop = {"and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as","have","since"}
            deny = {"people","person","thing","things","stuff","place","time","year","years","work","works","worked","working","life","day","days","good","bad","nice","great","hello","thanks","team","many","most"}
            def _valid_api_word(wl: str) -> bool:
                if not wl or len(wl) < 3 or len(wl) > 15:
                    return False
                if wl in stop or wl in deny:
                    return False
                if wl.isdigit():
                    return False
                letters = ''.join([c for c in wl if c.isalpha()])
                if len(letters) < 2 or not any(c in 'aeiou' for c in letters):
                    return False
                return True
            while remaining > 0 and attempt < max_attempts:
                req = remaining
                msg = prompt.replace("{n}", str(req))
                messages = {"messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": msg}
                ]}
                response = self._make_api_request_with_retry(messages, max_retries=1, base_delay=0.5, max_delay=1.0)
                content = response["choices"][0]["message"]["content"].strip()
                data = _parse_json_array_safely(content)
                added = 0
                for it in (data or []):
                    try:
                        w = str(it.get('word', '')).strip()
                        h = str(it.get('hint', '')).strip()
                        wl = w.lower()
                        if not w or wl in avoid_set or wl in collected_set:
                            continue
                        if not _valid_api_word(wl):
                            continue
                        if not h:
                            h = 'From your bio'
                        collected.append({'word': w, 'hint': h, 'hint_source': 'api', 'api_attempts': 1})
                        collected_set.add(wl)
                        added += 1
                        if added >= remaining:
                            break
                    except Exception:
                        continue
                if added == 0:
                    attempt += 1
                remaining = max(0, n - len(collected))
            if remaining > 0:
                logger.info(f"[PERSONAL] API returned {len(collected)} items; topping up offline to reach {n}.")
                offline = self._generate_personal_pool_offline(username, n=remaining, avoid_set=avoid_set.union(collected_set))
                if offline:
                    collected.extend(offline)
            return collected[:n]
        except Exception as e:
            logger.warning(f"[PERSONAL] Pool generation failed: {e}")
            return self._generate_personal_pool_offline(username, n=n, avoid_set=avoid_set)

    def _generate_personal_pool_offline(self, username: str, n: int = 10, avoid_set: set = None) -> list:
        """Deterministically synthesize a personal pool from users.json profile fields (offline),
        with source weighting, basic allow/deny lists, and a relevance score to the profile topics.
        """
        avoid_set = avoid_set or set()
        users = self._load_users_db()
        rec = users.get((username or '').lower(), {}) if isinstance(users, dict) else {}
        # Extract tokens (bio + occupation + education + address)
        import re
        def tokenize(text: str) -> list:
            if not text:
                return []
            toks = re.findall(r"[A-Za-z0-9]+", str(text))
            return [t for t in toks if t]
        bio_toks = tokenize(rec.get('bio', ''))
        occ_toks = tokenize(rec.get('occupation', ''))
        edu_toks = tokenize(rec.get('education', ''))
        addr_toks = tokenize(rec.get('address', ''))
        # Derive age token and location short token for weighting
        age_tok = []
        try:
            import datetime as _dt
            b = rec.get('birthday')
            if isinstance(b, str) and b:
                try:
                    dob = _dt.date.fromisoformat(b)
                except Exception:
                    try:
                        dob = _dt.datetime.fromisoformat(b).date()
                    except Exception:
                        dob = None
                if dob:
                    today = _dt.date.today()
                    age_val = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    if 5 <= age_val <= 120:
                        age_tok = [str(age_val)]
        except Exception:
            pass
        loc_tok = []
        try:
            addr = (rec.get('address') or '').strip()
            if addr:
                loc_short = addr.split(',')[0].strip()
                if loc_short and len(loc_short) > 2:
                    loc_tok = tokenize(loc_short)
        except Exception:
            pass
        # Scoring and selection
        stop = {"and","the","with","for","you","your","at","to","in","of","on","a","an","is","are","was","were","be","been","am","from","by","or","as"}
        # Deny-list of overly-generic words and common verbs/numbers
        number_words = {"zero","one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve","thirteen","fourteen","fifteen","sixteen","seventeen","eighteen","nineteen","twenty"}
        deny = {"people","person","thing","things","stuff","place","time","year","years","work","works","worked","working","live","lived","living","like","likes","liked","watch","watched","watching","join","joined","joining","use","used","using","since","have","been","most","many","life","day","days","good","bad","nice","great","hello","thanks","team"} | number_words
        def valid_word(w: str) -> bool:
            if not w or len(w) < 3 or len(w) > 15:
                return False
            wl = w.lower()
            if wl in stop:
                return False
            if wl in deny:
                return False
            if wl.isdigit():
                return False
            letters = ''.join([c for c in wl if c.isalpha()])
            if len(letters) < 2 or not any(c in 'aeiou' for c in letters):
                return False
            return True
        # Build profile topic keywords (weighted by source)
        topic_weights = {}
        def bump(tokens, weight):
            for t in tokens:
                tl = t.lower()
                if valid_word(tl):
                    topic_weights[tl] = topic_weights.get(tl, 0.0) + weight
        # Bio-only weighting
        bump(bio_toks, 2.0)
        # Age token is numeric, not a candidate word itself, but influences topic proximity implicitly
        # Candidate list with source preference order
        candidates = []
        def add_candidates(tokens, source, base_weight):
            for t in tokens:
                if not valid_word(t):
                    continue
                tl = t.lower()
                if tl in avoid_set:
                    continue
                # Relevance heuristic: base weight + topic match + length normalization
                rel = base_weight + topic_weights.get(tl, 0.0)
                # Slight bonus for mid-length words (5-9 chars)
                L = len(tl)
                if 5 <= L <= 9:
                    rel += 0.5
                candidates.append((t, source, rel))
        add_candidates(bio_toks, 'bio', 1.5)
        # De-duplicate keeping best score per word
        best = {}
        for t, src, score in candidates:
            tl = t.lower()
            if (tl not in best) or (score > best[tl][1]):
                best[tl] = (src, score)
        # Sort by score descending
        ranked = sorted([(w, src, sc) for w, (src, sc) in best.items()], key=lambda x: x[2], reverse=True)
        unique = [(w, src) for (w, src, _) in ranked]
        # If still short, add from a small fixed vocabulary
        fallback_vocab = [
            ('family', 'From your bio'), ('project', 'From your bio'), ('health', 'From your bio'),
            ('finance', 'From your bio'), ('music', 'From your bio'), ('teacher', 'From your bio')
        ]
        for w, src in fallback_vocab:
            if len(unique) >= n:
                break
            wl = w.lower()
            if wl not in best and wl not in avoid_set and valid_word(wl):
                unique.append((w, 'fallback'))
        # Build pool with one-line hints based on source
        pool = []
        for w, src in unique[:n]:
            if src == 'fallback':
                hint = 'From a general theme'
            else:
                # Generate a clearer, contextual hint based on the user's profile
                hint = self._make_profile_hint(w, rec)
            pool.append({'word': w, 'hint': hint})
        return pool

    def _validate_api_key(self) -> bool:
        """Validate the API key format."""
        if not self.api_key:
            return False
        try:
            # Simple format validation
            parts = self.api_key.split('-')
            return len(parts) >= 3 and parts[0] == 'sk' and parts[1] == 'or'
        except:
            return False

    def generate_all_hints(self, word: str, subject: str) -> List[str]:
        """Generate up to 10 hints for a word based on difficulty level."""
        hints = []
        logger.info(f"[HINT SOURCE] Starting hint generation for word '{word}' in subject '{subject}'")
        
        # Map categories to general if needed
        
        if subject in ["tech", "movies", "music", "brands", "history"]:
            subject = "general"
        
        # Try hints.json first
        try:
            hints_file = os.path.join('backend', 'data', 'hints.json')
            logger.info(f"[HINT SOURCE] Looking for hints in: {hints_file}")
            with open(hints_file, 'r', encoding='utf-8') as f:
                hints_data = json.load(f)
                
                
                # Try specific category first
                if "templates" in hints_data and subject in hints_data["templates"] and word in hints_data["templates"][subject]:
                    logger.info(f"[HINT SOURCE] Found hints in hints.json for '{word}' in category '{subject}'")
                    hints = hints_data["templates"][subject][word][:10]  # Take up to 10 hints
                    logger.info(f"[HINT SOURCE] Using {len(hints)} hints from hints.json")
                    for i, hint in enumerate(hints, 1):
                        logger.info(f"[HINT SOURCE] Hint {i}: {hint} (Source: hints.json)")
                    return hints
                # Fall back to 'general' if not found in specific category
                elif "templates" in hints_data and "general" in hints_data["templates"] and word in hints_data["templates"]["general"]:
                    logger.info(f"[HINT SOURCE] Found hints in hints.json for '{word}' in fallback category 'general'")
                    hints = hints_data["templates"]["general"][word][:10]
                    logger.info(f"[HINT SOURCE] Using {len(hints)} hints from hints.json (general fallback)")
                    for i, hint in enumerate(hints, 1):
                        logger.info(f"[HINT SOURCE] Hint {i}: {hint} (Source: hints.json/general fallback)")
                    return hints
                else:
                    logger.warning(f"[HINT SOURCE] Word '{word}' not found in hints.json templates for category '{subject}' or 'general'")
        except FileNotFoundError:
            logger.warning(f"[HINT SOURCE] hints.json file not found at {hints_file}")
        except json.JSONDecodeError:
            logger.warning("[HINT SOURCE] Error decoding hints.json")
        except Exception as e:
            logger.warning(f"[HINT SOURCE] Error reading hints.json: {e}")
        
        
        # If no hints in hints.json, try word-specific hints from WORD_HINTS
        if word in WORD_HINTS:
            logger.info(f"[HINT SOURCE] Found word-specific hints in WORD_HINTS for '{word}'")
            hints = WORD_HINTS[word][:10]  # Take up to 10 hints
            logger.info(f"[HINT SOURCE] Using {len(hints)} hints from WORD_HINTS")
            for i, hint in enumerate(hints, 1):
                logger.info(f"[HINT SOURCE] Hint {i}: {hint} (Source: WORD_HINTS)")
            return hints
        
        logger.info(f"[HINT SOURCE] No word-specific hints found in WORD_HINTS for '{word}'")
        
        # If no word-specific hints, try category templates
        subject = subject.lower()
        if subject == "tech":
            subject = "science"  # Map tech to science category
        elif subject in ["movies", "music", "brands", "history"]:
            subject = "general"  # Map entertainment categories to general
            
        logger.info(f"[HINT SOURCE] Mapped subject '{subject}' for template lookup")
        
        # Try to get hints from templates
        if subject in category_templates:
            logger.info(f"[HINT SOURCE] Found templates for subject '{subject}'")
            template_hints = []
            for template in category_templates[subject]:
                hint = template.format(word=word)
                template_hints.append(hint)
                logger.info(f"[HINT SOURCE] Generated hint from template: {hint}")
            hints.extend(template_hints[:10])
            logger.info(f"[HINT SOURCE] Added {len(template_hints)} template-based hints")
        else:
            logger.info(f"[HINT SOURCE] No templates found for subject '{subject}'")
            
        # If we still need more hints, try fallback hints
        if len(hints) < 10:
            logger.info(f"[HINT SOURCE] Need {10 - len(hints)} more hints, using fallback hints")
            fallback_hints = [
                f"This {subject} term has {len(word)} letters",
                f"This word is related to {subject}",
                f"The first letter is '{word[0]}'",
                f"The last letter is '{word[-1]}'",
            ]
            remaining_slots = 10 - len(hints)
            hints.extend(fallback_hints[:remaining_slots])
            for i, hint in enumerate(fallback_hints[:remaining_slots], len(hints) + 1):
                logger.info(f"[HINT SOURCE] Hint {i}: {hint} (Source: Fallback)")
                
        logger.info(f"[HINT SOURCE] Final hint count: {len(hints)}")
        return hints

    def _add_recent_word_combo(self, word: str, username: str, subject: str):
        recent_key = f"{username}:{subject}"
        # For FlashCard, scope recents by active set token to avoid cross-set repetition
        try:
            if str(subject).strip().lower() == 'flashcard':
                from backend.bio_store import get_active_flash_set_name, get_flash_set_token
                _active_name = get_active_flash_set_name(username) or 'flashcard'
                _active_tok = get_flash_set_token(username, _active_name) or ''
                recent_key = f"{username}:flashcard:{_active_tok or _active_name}"
        except Exception:
            pass
        if not hasattr(self, "_recently_used_words_by_combo"):
            self._recently_used_words_by_combo = {}
        if recent_key not in self._recently_used_words_by_combo:
            self._recently_used_words_by_combo[recent_key] = []
        recent = self._recently_used_words_by_combo[recent_key]
        wl = (word or '').strip().lower()
        # Normalize existing list to lower once
        self._recently_used_words_by_combo[recent_key] = [str(w).strip().lower() for w in recent]
        recent = self._recently_used_words_by_combo[recent_key]
        if wl in recent:
            recent.remove(wl)
        recent.insert(0, wl)
        max_recent = getattr(self, "_max_recent_words", 50)
        self._recently_used_words_by_combo[recent_key] = recent[:max_recent]

    def select_word(self, word_length: int = 5, subject: str = "general", username: str = "global") -> str:
        """Select a word based on subject, using per-user recent word tracking. Ignores word length for repeat logic. Blocks immediate repeats."""
        self.current_category = subject.lower()

        # FlashCard category: pull from user's flash text pool
        if self.current_category == "flashcard":
            word = self._select_word_from_flashcard(username or 'global')
            if word:
                return word

        # Personal category: honor ENABLE_PERSONAL_CATEGORY gate
        _enable_personal = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
        # Personal category: prefer user's saved personal_pool; fallback to generating a batch
        if self.current_category == "personal" and _enable_personal:
            try:
                pool = self.get_user_personal_pool(username or 'global')
                # Auto top-up: if pool exists but < max, add batch more (API or offline) avoiding duplicates
                try:
                    if pool and len(pool) < self.personal_pool_max:
                        existing_words = [str(it.get('word','')).strip() for it in pool]
                        target_total = min(self.personal_pool_max, len(pool) + self.personal_pool_batch_size)
                        attempts = 0
                        while len(pool) < target_total and attempts < self.personal_pool_api_attempts:
                            batch = self.generate_personal_pool(username or 'global', n=self.personal_pool_batch_size, avoid=existing_words)
                            added = 0
                            if batch:
                                seen = { (it.get('word') or '').strip().lower() for it in pool }
                                for it in batch:
                                    w = (it.get('word') or '').strip()
                                    if w and w.lower() not in seen:
                                        pool.append(it)
                                        seen.add(w.lower())
                                        added += 1
                            if added == 0:
                                attempts += 1
                            existing_words = [str(it.get('word','')).strip() for it in pool]
                        if added > 0:
                            self.set_user_personal_pool(username or 'global', pool[: self.personal_pool_max])
                except Exception:
                    pass
                # Rank pool words with keyword boosts
                if pool:
                    import random as _r
                    recent_key = f"{username}:{self.current_category}"
                    recent = set(getattr(self, "_recently_used_words_by_combo", {}).get(recent_key, []))
                    last_word = getattr(self, "_last_word_by_combo", {}).get(recent_key)
                    # Custom boosts
                    boost_keywords = {"juniper": 3.0, "software": 2.5, "engineer": 2.0, "san": 1.5, "jose": 1.5, "almaden": 2.0}
                    candidates = []
                    for it in pool:
                        w = str(it.get('word','')).strip()
                        wl = w.lower()
                        if not w or not wl.isalnum():
                            continue
                        if wl in recent or wl == (last_word or '').lower():
                            continue
                        score = 1.0
                        for k, b in boost_keywords.items():
                            if k in wl:
                                score += b
                        # Bonus for mid-length
                        if 5 <= len(wl) <= 9:
                            score += 0.3
                        candidates.append((w, score))
                    if not candidates:
                        # If all were filtered by recency, relax to any pool item not equal to last_word
                        for it in pool:
                            w = str(it.get('word','')).strip()
                            if w and w.lower() != (last_word or '').lower():
                                candidates.append((w, 1.0))
                    if candidates:
                        candidates.sort(key=lambda x: x[1], reverse=True)
                        # Add small variability: sample among top 5 if available
                        top_k = candidates[:max(1, min(5, len(candidates)))]
                        chosen = _r.choice(top_k)[0]
                        # Soft-mark as last word to avoid immediate repeats even if not played yet
                        try:
                            if not hasattr(self, "_last_word_by_combo"):
                                self._last_word_by_combo = {}
                            self._last_word_by_combo[recent_key] = chosen
                            if not hasattr(self, "_recently_used_words_by_combo"):
                                self._recently_used_words_by_combo = {}
                            lst = self._recently_used_words_by_combo.get(recent_key, [])
                            if chosen.lower() not in lst:
                                lst.insert(0, chosen.lower())
                                # Clamp size
                                self._recently_used_words_by_combo[recent_key] = lst[: self._max_recent_words]
                        except Exception:
                            pass
                        return chosen
                # If pool empty, try to generate a new batch offline (or API if available)
                # Re-check gate before any generation
                _enable_personal2 = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
                if not _enable_personal2:
                    batch = []
                else:
                    batch = self.generate_personal_pool(username or 'global', n=self.personal_pool_batch_size, avoid=[it.get('word') for it in pool] if pool else [])
                if batch:
                    self.set_user_personal_pool(username or 'global', (pool or []) + batch)
                    # Pick best from new batch
                    # Re-run selection from the updated pool (will apply boosts and recency)
                    pool2 = self.get_user_personal_pool(username or 'global')
                    if pool2:
                        import random as _r
                        recent_key = f"{username}:{self.current_category}"
                        recent = set(getattr(self, "_recently_used_words_by_combo", {}).get(recent_key, []))
                        last_word = getattr(self, "_last_word_by_combo", {}).get(recent_key)
                        boost_keywords = {"juniper": 3.0, "software": 2.5, "engineer": 2.0, "san": 1.5, "jose": 1.5, "almaden": 2.0}
                        candidates2 = []
                        for it in pool2:
                            w = str(it.get('word','')).strip()
                            wl = w.lower()
                            if not w or not wl.isalnum():
                                continue
                            if wl in recent or wl == (last_word or '').lower():
                                continue
                            score = 1.0
                            for k, b in boost_keywords.items():
                                if k in wl:
                                    score += b
                            if 5 <= len(wl) <= 9:
                                score += 0.3
                            candidates2.append((w, score))
                        if candidates2:
                            candidates2.sort(key=lambda x: x[1], reverse=True)
                            # Reduce bias: sample among top 5 if available
                            chosen2 = _r.choice(candidates2[:max(1, min(5, len(candidates2)))])[0]
                            # Soft-mark selection
                            if not hasattr(self, "_last_word_by_combo"):
                                self._last_word_by_combo = {}
                            self._last_word_by_combo[recent_key] = chosen2
                            if not hasattr(self, "_recently_used_words_by_combo"):
                                self._recently_used_words_by_combo = {}
                            lst = self._recently_used_words_by_combo.get(recent_key, [])
                            if chosen2.lower() not in lst:
                                lst.insert(0, chosen2.lower())
                                self._recently_used_words_by_combo[recent_key] = lst[: self._max_recent_words]
                            return chosen2
                    # Fallback to first new batch word
                    return batch[0].get('word')
            except Exception as e:
                logger.warning(f"[PERSONAL] Pool selection failed: {e}")
            # As a last resort, fall back to general selection
            self.current_category = "general"

        # Map tech to science and other categories to general
      #  if self.current_category == "tech":
      #      self.current_category = "science"
      #  if self.current_category in ["movies", "music", "brands", "history"]:
    #     self.current_category = "general"

        def is_valid_word(word: str) -> bool:
            """Validate if a word meets all criteria."""
            if not word or not isinstance(word, str):
                logger.warning(f"Invalid word type or empty word: {type(word)}")
                return False
            # Accept alphanumeric words (letters and digits only)
            if not word.isalnum():
                logger.warning(f"Word contains non-alphanumeric characters: {word}")
                return False
            # Use the combo recent list for repeat check (ignore length)
            recent_key = f"{username}:{self.current_category}"
            recent = set(getattr(self, "_recently_used_words_by_combo", {}).get(recent_key, []))
            # Block immediate repeat
            last_word = getattr(self, "_last_word_by_combo", {}).get(recent_key)
            if word in recent:
                logger.warning(f"Word was recently used: {word}")
                return False
            if word == last_word:
                logger.warning(f"Word would be an immediate repeat: {word}")
                return False
            # Apply letter-based checks on letters-only view
            _letters_only = ''.join(c for c in word if c.isalpha())
            if len(set(_letters_only.lower())) < 2:  # At least 2 different letters
                logger.warning(f"Word has too few unique letters (letters-only view): {word}")
                return False
            if not any(c in 'aeiou' for c in _letters_only.lower()):  # Must contain at least one vowel
                logger.warning(f"Word contains no vowels (letters-only view): {word}")
                return False
            return True

        # Try API first if not in fallback mode, or if category is personal/flashcard (always allow)
        if (not self.use_fallback) or (self.current_category in ("personal", "flashcard")):
            max_api_retries = 3
            for attempt in range(max_api_retries):
                try:
                    messages = self._build_prompt(word_length, subject)
                    # Add recent words to the user message for context
                    recent_key = f"{username}:{self.current_category}"
                    recent_words = getattr(self, "_recently_used_words_by_combo", {}).get(recent_key, [])
                    if isinstance(messages, dict) and "messages" in messages:
                        messages["messages"].append({
                            "role": "user",
                            "content": f"Avoid these words: {', '.join(recent_words)}"
                        })
                    response = self._make_api_request_with_retry(messages)
                    content = response["choices"][0]["message"]["content"].strip()
                    
                    # Handle code block formatting (triple backticks)
                    if content.startswith('```'):
                        content = content.lstrip('`').strip()
                        # Remove language tag if present (e.g., 'json')
                        if content.startswith('json'):
                            content = content[4:].strip()
                    
                    # Try to extract JSON object from the content
                    word = ""
                    
                    # First, try to find JSON object in the content
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(0)
                        try:
                            word_obj = json.loads(json_content)
                            word = word_obj.get("selected_word", "").lower()
                        except json.JSONDecodeError:
                            pass
                    
                    # If no JSON object found or parsing failed, try direct JSON parsing
                    if not word:
                        try:
                            word_obj = json.loads(content)
                            word = word_obj.get("selected_word", "").lower()
                        except json.JSONDecodeError:
                            pass
                    
                    # If still no word, try regex extraction
                    if not word:
                        match = re.search(r'"selected_word"\s*:\s*"([^"]+)"', content)
                        if match:
                            word = match.group(1).lower()
                        else:
                            # Last resort: try to extract any word-like content
                            word_match = re.search(r'"([a-zA-Z]+)"', content)
                            if word_match:
                                word = word_match.group(1).lower()
                            else:
                                logger.warning(f"Could not extract valid word from content: {content}")
                                continue  # Skip this attempt instead of using raw content
                    
                    if is_valid_word(word):
                        # Do NOT add to recent list here
                        logger.info(f"Selected word '{word}' from API for user '{username}'")
                        return word
                    
                except Exception as e:
                    import traceback
                    logger.error(f"Error getting word from API: {e}")
                    logger.debug(traceback.format_exc())
                    self.use_fallback = True
            logger.warning(f"API failed to provide a valid word after {max_api_retries} attempts.")

        # Always try dictionary if present, even in fallback mode
        word = self._select_word_from_dictionary(word_length, self.current_category, username=username)
        if word and is_valid_word(word):
            # Do NOT add to recent list here
            return word

        # If dictionary yielded nothing but hints.json has this subject, pick from that subject explicitly
        try:
            hints_file = os.path.join('backend', 'data', 'hints.json')
            with open(hints_file, 'r', encoding='utf-8') as f:
                hints_data = json.load(f)
            templates = hints_data.get('templates', {})
            ci_key_map = {k.lower(): k for k in templates.keys()}
            subject_key = ci_key_map.get(str(self.current_category).lower())
            if subject_key and isinstance(templates.get(subject_key), dict) and templates[subject_key]:
                subject_words = list(templates[subject_key].keys())
                if subject_words:
                    import random as _random
                    picked = _random.choice(subject_words)
                    if is_valid_word(picked):
                        return picked
        except Exception:
            pass

        # Only use fallback pool if both API and dictionary fail
        word = get_fallback_word(word_length, self.current_category)
        if word and isinstance(word, str):
            # Accept alphanumeric from fallback too
            word = word.strip()
            if is_valid_word(word):
                # Do NOT add to recent list here
                return word
        
        logger.error("Failed to get a valid word from any source")
        raise ValueError("Could not select a valid word after exhausting all options")

    def _answer_question_fallback(self, word: str, question: str, subject: str = "general") -> str:
        """Generate a fallback answer when API is not available."""
        import re
        question = question.lower()

        # Handle category questions
        category_patterns = [
            r"what (?:category|type|kind|group) (?:is|of word is) (?:it|this|the word)",
            r"(?:is|does) (?:it|the word) (?:belong|related) to (?:the )?(\w+) category",
            r"(?:is|does) (?:it|this|the word) (?:a|an) (\w+) word",
            r"(?:is|does) (?:it|this|the word) from (?:the )?(\w+) category",
            r"(?:is|does) (?:it|this|the word) in (?:the )?(\w+) category",
            r"what (?:is|about) (?:the )?category",
            r"which category",
            r"tell me (?:the )?category"
        ]
        for pattern in category_patterns:
            if re.search(pattern, question):
                return f"This word belongs to the {subject} category."

        # Check for letter presence (improved, allow whitespace)
        letter_presence_patterns = [
            r"(?:contain|have|include|has|with).*letter\s*['\"]?([a-z])['\"]?",
            r"letter\s*['\"]?([a-z])['\"]? (?:in|inside|within) (?:it|the word)",
            r"is there a\s*['\"]?([a-z])['\"]? (?:in|inside|within) (?:it|the word)",
            r"does (?:it|the word) have\s*['\"]?([a-z])['\"]?",
            r"does (?:it|the word) contain\s*['\"]?([a-z])['\"]?",
            r"any\s*['\"]?([a-z])['\"]? in (?:it|the word)"
        ]
        for pattern in letter_presence_patterns:
            match = re.search(pattern, question)
            if match:
                letter = match.group(1).lower()
                # Always strip and lowercase the word for robust checking
                return "Yes" if letter in word.strip().lower() else "No"

        # Check for word length
        if "how many letters" in question:
            return f"The word has {len(word)} letters"

        # Robust first letter patterns
        first_letter_patterns = [
            r"(?:is|does|has|contains?).*(?:first|1st|start|begin).*(?:letter|character).*['\"]?(\w)['\"]?",
            r"(?:is|does) (?:it|the word) start (?:with|using) ['\"]?(\w)['\"]?",
            r"(?:does|is) ['\"]?(\w)['\"]? (?:the|its) first letter",
            r"(?:is|does) the first letter ['\"]?(\w)['\"]?",
            r"first letter ['\"]?(\w)['\"]?",
            r"(?:is|does) ['\"]?(\w)['\"]? (?:the )?first",
            r"start with ['\"]?(\w)['\"]?",
            r"begins? with ['\"]?(\w)['\"]?",
            r"^first ['\"]?(\w)['\"]?$"
        ]
        for pattern in first_letter_patterns:
            match = re.search(pattern, question)
            if match:
                letter = match.group(1).lower()
                return f"Yes, the first letter is '{word[0]}'" if word[0] == letter else f"No, the first letter is not '{letter}'"
        if "first letter" in question:
            return f"The first letter is '{word[0]}'"

        # Robust last letter patterns
        last_letter_patterns = [
            r"(?:is|does|has|contains?).*(?:last|final|end).*(?:letter|character).*['\"]?(\w)['\"]?",
            r"(?:is|does) (?:it|the word) end (?:with|in) ['\"]?(\w)['\"]?",
            r"(?:does|is) ['\"]?(\w)['\"]? (?:the|its) last letter",
            r"(?:is|does) the last letter ['\"]?(\w)['\"]?",
            r"last letter ['\"]?(\w)['\"]?",
            r"(?:is|does) ['\"]?(\w)['\"]? (?:the )?last",
            r"end with ['\"]?(\w)['\"]?",
            r"ends? with ['\"]?(\w)['\"]?",
            r"^last ['\"]?(\w)['\"]?$"
        ]
        for pattern in last_letter_patterns:
            match = re.search(pattern, question)
            if match:
                letter = match.group(1).lower()
                return f"Yes, the last letter is '{word[-1]}'" if word[-1] == letter else f"No, the last letter is not '{letter}'"
        if "last letter" in question:
            return f"The last letter is '{word[-1]}'"

        # Default response
        return "I can only answer questions about letters and word length in fallback mode"

    def get_semantic_hint(self, word: str, subject: str, previous_hints: list = None, max_hints: int = 10) -> str:
        import logging
        logger = logging.getLogger("backend.word_selector")
        if previous_hints is None:
            previous_hints = []
        word = word.lower().strip()
        subject = subject.lower().strip()
        hints = []
        # Debug logging for subject and keys
        logger.info(f"[HINT DEBUG] Requested subject: '{subject}' for word: '{word}'")
        if hasattr(self, 'hints_data'):
            logger.info(f"[HINT DEBUG] Top-level keys in hints_data: {list(self.hints_data.keys())}")
            if 'categories' in self.hints_data:
                logger.info(f"[HINT DEBUG] Category keys in hints_data['categories']: {list(self.hints_data['categories'].keys())}")
        # 1. Check top-level subject section FIRST (e.g., 4th_grade)
        if (
            hasattr(self, 'hints_data') and
            subject in self.hints_data and
            word in self.hints_data[subject]
        ):
            hints = self.hints_data[subject][word]
            logger.info(f"[HINT DEBUG] Found hints for word '{word}' in top-level '{subject}': {hints}")
            print(f"[HINT DEBUG] Found hints for word '{word}' in top-level '{subject}': {hints}")
        # 2. If not found, check categories section
        elif (
            hasattr(self, 'hints_data') and
            'categories' in self.hints_data and
            subject in self.hints_data['categories'] and
            word in self.hints_data['categories'][subject]
        ):
            hints = self.hints_data['categories'][subject][word]
            logger.info(f"[HINT DEBUG] Found hints for word '{word}' in categories['{subject}']: {hints}")
            print(f"[HINT DEBUG] Found hints for word '{word}' in categories['{subject}']: {hints}")
        else:
            logger.info(f"[HINT DEBUG] No pre-generated hints found for word '{word}' in subject '{subject}'")
            print(f"[HINT DEBUG] No pre-generated hints found for word '{word}' in subject '{subject}'")
            # Use cached API hints if available, otherwise call API
            cache_key = (word, subject)
            if cache_key in self._api_hint_cache:
                api_hints = self._api_hint_cache[cache_key]
            else:
                api_hints = self.get_api_hints(word, subject, n=max_hints)
                if api_hints:
                    self._api_hint_cache[cache_key] = api_hints
            if api_hints:
                hints = api_hints
        # 3. Fallback to dynamic hints if still not found
        if hints:
            for hint in hints:
                if hint not in previous_hints:
                    return hint
        return self._generate_dynamic_hint(word, subject, previous_hints)

    def verify_guess(self, word: str, guess: str) -> bool:
        """Verify if the guessed word matches the actual word."""
        return word.lower() == guess.lower()

    def answer_question(self, word: str, question: str, subject: str = "general") -> str:
        """Answer a question about the word."""
        import re
        # Patterns for simple fallback questions
        letter_presence_patterns = [
            r"(?:contain|have|include|has|with)[^a-zA-Z]*['\"]?([a-z])['\"]?",
            r"letter[^a-zA-Z]*['\"]?([a-z])['\"]?",
            r"is there[^a-zA-Z]*['\"]?([a-z])['\"]?",
            r"any[^a-zA-Z]*['\"]?([a-z])['\"]?",
            r"does (?:it|the word)[^a-zA-Z]*['\"]?([a-z])['\"]?",
            r"is ['\"]?([a-z])['\"]? present",
            r"['\"]?([a-z])['\"]? in (?:it|the word)",
            r"does it have ['\"]?([a-z])['\"]?",
            r"does the word have ['\"]?([a-z])['\"]?",
            r"has ['\"]?([a-z])['\"]?",
            r"include ['\"]?([a-z])['\"]?",
            r"with ['\"]?([a-z])['\"]?",
        ]
        first_letter_patterns = [
            r"(?:is|does|has|contains?).*(?:first|1st|start|begin).*(?:letter|character).*['\"]?(\w)['\"]?",
            r"(?:is|does) (?:it|the word) start (?:with|using) ['\"]?(\w)['\"]?",
            r"(?:does|is) ['\"]?(\w)['\"]? (?:the|its) first letter",
            r"(?:is|does) the first letter ['\"]?(\w)['\"]?",
            r"first letter ['\"]?(\w)['\"]?",
            r"(?:is|does) ['\"]?(\w)['\"]? (?:the )?first",
            r"start with ['\"]?(\w)['\"]?",
            r"begins? with ['\"]?(\w)['\"]?",
            r"^first ['\"]?(\w)['\"]?$"
        ]
        last_letter_patterns = [
            r"(?:is|does|has|contains?).*(?:last|final|end).*(?:letter|character).*['\"]?(\w)['\"]?",
            r"(?:is|does) (?:it|the word) end (?:with|in) ['\"]?(\w)['\"]?",
            r"(?:does|is) ['\"]?(\w)['\"]? (?:the|its) last letter",
            r"(?:is|does) the last letter ['\"]?(\w)['\"]?",
            r"last letter ['\"]?(\w)['\"]?",
            r"(?:is|does) ['\"]?(\w)['\"]? (?:the )?last",
            r"end with ['\"]?(\w)['\"]?",
            r"ends? with ['\"]?(\w)['\"]?",
            r"^last ['\"]?(\w)['\"]?$"
        ]
        category_patterns = [
            r"what (?:category|type|kind|group) (?:is|of word is) (?:it|this|the word)",
            r"(?:is|does) (?:it|the word) (?:belong|related) to (?:the )?(\w+) category",
            r"(?:is|does) (?:it|this|the word) (?:a|an) (\w+) word",
            r"(?:is|does) (?:it|this|the word) from (?:the )?(\w+) category",
            r"(?:is|does) (?:it|this|the word) in (?:the )?(\w+) category",
            r"what (?:is|about) (?:the )?category",
            r"which category",
            r"tell me (?:the )?category"
        ]
        # Simple fallback: letter presence
        for pattern in letter_presence_patterns:
            if re.search(pattern, question.lower()):
                return self._answer_question_fallback(word, question, subject)
        # Simple fallback: word length
        if "how many letters" in question.lower():
            return self._answer_question_fallback(word, question, subject)
        # Simple fallback: first letter
        for pattern in first_letter_patterns:
            if re.search(pattern, question.lower()):
                return self._answer_question_fallback(word, question, subject)
        if "first letter" in question.lower():
            return self._answer_question_fallback(word, question, subject)
        # Simple fallback: last letter
        for pattern in last_letter_patterns:
            if re.search(pattern, question.lower()):
                return self._answer_question_fallback(word, question, subject)
        if "last letter" in question.lower():
            return self._answer_question_fallback(word, question, subject)
        # Simple fallback: category
        for pattern in category_patterns:
            if re.search(pattern, question.lower()):
                return self._answer_question_fallback(word, question, subject)
        # If fallback mode but API is available, try API for complex questions
        if self.use_fallback and self.api_key and self.api_key_valid:
            try:
                messages = [
                    {
                        "role": "system",
                        "content": "You are a word guessing game assistant. Answer any yes/no question about the word as helpfully as possible. Do not reveal, confirm, or mention the word itself in your response. Only provide a yes/no answer and a brief explanation if relevant. Never include the word or any part of it in your answer."
                    },
                    {
                        "role": "user",
                        "content": f"The word is: {word}\nPlayer's question: {question}\n"
                    }
                ]
                response = self._make_api_request_with_retry(messages)
                logger.debug(f"API response type: {type(response)}, content: {response}")
                answer = response["choices"][0]["message"]["content"].strip()
                return answer
            except Exception as e:
                logger.error(f"[Fallback-API] Failed to get answer from API: {str(e)}")
                return self._answer_question_fallback(word, question, subject)
        # Fallback mode, no API or API failed: fallback logic
        if self.use_fallback:
            return self._answer_question_fallback(word, question, subject)
        # API mode: allow any question style
        try:
            messages = [
                {
                    "role": "system",
                    "content": "You are a word guessing game assistant. Answer any yes/no question about the word as helpfully as possible. Do not reveal, confirm, or mention the word itself in your response. Only provide a yes/no answer and a brief explanation if relevant. Never include the word or any part of it in your answer."
                },
                {
                    "role": "user",
                    "content": f"The word is: {word}\nPlayer's question: {question}\n"
                }
            ]
            response = self._make_api_request_with_retry(messages)
            logger.debug(f"API response type: {type(response)}, content: {response}")
            answer = response["choices"][0]["message"]["content"].strip()
            return answer
        except Exception as e:
            logger.error(f"Failed to get answer from API: {str(e)}")
            return self._answer_question_fallback(word, question, subject)

    def _generate_dynamic_hint(self, word: str, subject: str, previous_hints: list = None, max_hints: int = 10) -> str:
        """Generate a dynamic fallback hint for the word and subject."""
        import random
        if previous_hints is None:
            previous_hints = []
        word = word.lower().strip()
        subject = subject.lower().strip()
        word_length = len(word or '')
        if word_length <= 0:
            return "Preparing word…",
        vowel_count = sum(1 for c in word if c in 'aeiou')
        consonant_count = word_length - vowel_count
        dynamic_hints = [
            f"This {subject} word has {vowel_count} vowels and {consonant_count} consonants.",
            f"In this {subject} word, {round(vowel_count/word_length * 100)}% of letters are vowels.",
            f"This {subject} word follows a {'-'.join('C' if c not in 'aeiou' else 'V' for c in word)} pattern.",
            f"This {subject} word has {len(set(word))} unique letters.",
            f"This {subject} word has {sum(1 for i, c in enumerate(word[:-1]) if c == word[i+1])} repeated consecutive letters.",
            f"The letters in this {subject} word are {round(len(set(word))/word_length * 100)}% unique."
        ]
        available_hints = [h for h in dynamic_hints if h not in previous_hints]
        if available_hints:
            return random.choice(available_hints)
        # Final fallback
        return f"This is a {word_length}-letter word in the category '{subject}'."

    def _build_prompt(self, word_length: int, subject: str) -> dict:
        """Build the prompt for word selection with strict JSON formatting and no extra text."""
        grade_level = ''
        subj = subject.lower()
        if subj == 'general':
            grade_level = ' The word should be suitable for a 10th grade English student.'
        elif subj == '4th_grade':
            grade_level = ' The word should be suitable for a 4th grade English student.'
        return {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        'You are a word guessing game assistant. '
                        'Respond with ONLY a JSON object using double quotes, in this exact format: {"selected_word": "WORD"}. '
                        'Do NOT include any explanations, code blocks, or extra text. '
                        'The word must be a valid English word, not recently used, and match the required length.'
                        + grade_level
                    )
                },
                {
                    "role": "user",
                    "content": f'Choose a {word_length}-letter English word under the subject "{subject}". Respond with ONLY the JSON object using double quotes.'
                }
            ]
        }

    def _make_api_request_with_retry(self, messages, max_retries=3, base_delay=1.0, max_delay=10.0):
        """
        Make an API request with retries, exponential backoff, and jitter.
        Also update quota info and trigger fallback if quota is exhausted.
        """
        url = "https://openrouter.ai/api/v1/chat/completions"
        if isinstance(messages, dict) and "messages" in messages:
            payload = {"model": self.primary_model, "messages": messages["messages"]}
        else:
            payload = {"model": self.primary_model, "messages": messages}
        headers = self.headers
        last_warning = None
        # Allow tuning via env
        try:
            import os
            base_delay = float(os.getenv('OPENROUTER_RETRY_BASE_DELAY_S', str(base_delay)))
            max_delay = float(os.getenv('OPENROUTER_RETRY_MAX_DELAY_S', str(max_delay)))
            max_retries = int(os.getenv('OPENROUTER_RETRY_MAX_ATTEMPTS', str(max_retries)))
            cooldown_429 = float(os.getenv('OPENROUTER_429_COOLDOWN_S', '8'))
        except Exception:
            cooldown_429 = 8.0
        # Try primary model up to max_retries times
        for attempt in range(max_retries):
            try:
                import requests
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                from .openrouter_monitor import update_quota_from_response, get_quota_warning
                update_quota_from_response(response.headers)
                warning = get_quota_warning()
                if warning:
                    last_warning = warning
                    try:
                        _msg = str(warning['message']).encode('ascii', 'backslashreplace').decode('ascii')
                    except Exception:
                        _msg = str(warning.get('message', ''))
                    logger.warning(f"Quota warning: {_msg}")
                    if warning['level'] == 'error':
                        self.use_fallback = True
                        logger.error("Critical quota reached. Switching to fallback mode.")
                        raise RuntimeError(warning['message'])
                # Special handling: if 429, observe cooldown
                if response.status_code == 429:
                    time.sleep(cooldown_429)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 1)
                try:
                    _err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
                except Exception:
                    _err = str(e)
                logger.warning(f"API request failed (primary, attempt {attempt+1}/{max_retries}): {_err}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
        # If all primary model attempts fail, try fallback model up to max_retries times
        payload["model"] = self.fallback_model
        for attempt in range(max_retries):
            try:
                import requests
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                from .openrouter_monitor import update_quota_from_response, get_quota_warning
                update_quota_from_response(response.headers)
                warning = get_quota_warning()
                if warning:
                    last_warning = warning
                    try:
                        _msg2 = str(warning['message']).encode('ascii', 'backslashreplace').decode('ascii')
                    except Exception:
                        _msg2 = str(warning.get('message', ''))
                    logger.warning(f"Quota warning: {_msg2}")
                    if warning['level'] == 'error':
                        self.use_fallback = True
                        logger.error("Critical quota reached. Switching to fallback mode.")
                        raise RuntimeError(warning['message'])
                if response.status_code == 429:
                    time.sleep(cooldown_429)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                wait = min(max_delay, base_delay * (2 ** attempt)) + random.uniform(0, 1)
                try:
                    _err2 = str(e).encode('ascii', 'backslashreplace').decode('ascii')
                except Exception:
                    _err2 = str(e)
                logger.warning(f"API request failed (fallback, attempt {attempt+1}/{max_retries}): {_err2}. Retrying in {wait:.1f}s...")
                time.sleep(wait)
        if last_warning:
            raise RuntimeError(last_warning['message'])
        raise RuntimeError("API request failed after multiple retries")

    def get_api_hints_force(self, word: str, subject: str, n: int = 10, attempts: int | None = None) -> list:
        """Force API hint generation regardless of fallback flag (used for Personal/FlashCard).
        Optional 'attempts' allows callers to override the retry count.
        """
        saved = getattr(self, 'use_fallback', False)
        try:
            self.use_fallback = False
            return self.get_api_hints(word, subject, n, attempts=attempts)
        except Exception:
            return []
        finally:
            self.use_fallback = saved

    def get_quota_warning_for_ui(self):
        """Get the current quota warning for the UI/frontend to display."""
        from .openrouter_monitor import get_quota_warning
        warning = get_quota_warning()
        if warning:
            return warning['message']
        return None

    def get_api_hints(self, word: str, subject: str, n: int = 10, attempts: int | None = None) -> list:
        """Use the API to generate n meaningful, diverse hints about the word, with improved prompt and post-processing.
        Optional 'attempts' controls retry loops (default 3).
        """
        if self.use_fallback:
            return []
        import time
        import logging
        import re
        import json
        logger = logging.getLogger("backend.word_selector")
        max_attempts = attempts if isinstance(attempts, int) and attempts > 0 else 3
        blacklist = [
            'crime', 'assail', 'attack', 'stance', 'deficit', 'direction a signal',
            'contentious verbal exchange', 'successfully', 'assuming a stance',
            'oppositely', 'point deduction', 'assail', 'verbal exchange', 'consequence',
            'committed', 'successfully', 'assume', 'assail', 'attack', 'crime', 'deficit',
            'direction', 'signal', 'stance', 'exchange', 'consequence', 'professional',
            'particularly', 'point deduction', 'applied', 'deduction', 'hint', 'player', 'game',
            'guess', 'word itself', 'letters', 'synonym', 'antonym', 'definition', 'spelling',
            'anagram', 'scramble', 'reverse', 'jumbled', 'directly', 'opposite', 'not related',
            'irrelevant', 'unrelated', 'generic', 'nonsense', 'meaningless', 'random', 'unknown',
            'no further clues', 'no more hints', 'no additional hints', 'no hints', 'no clue',
            'cannot provide', 'not available', 'not applicable', 'not possible', 'not enough',
            'not sure', 'do not know', 'unsure', 'uncertain', 'unavailable', 'not given', 'not provided',
            'not specified', 'not stated', 'not mentioned', 'not described', 'not explained', 'not defined',
            'not listed', 'not included', 'not found', 'not present', 'not shown', 'not displayed',
            'not revealed', 'not disclosed', 'not shared', 'not told', 'not said', 'not written', 'not shown',
            'not shown', 'not shown', 'not shown', 'not shown', 'not shown', 'not shown', 'not shown', 'not shown',
        ]
        def is_meaningful_hint(hint: str, word: str) -> bool:
            if not isinstance(hint, str) or len(hint) < 10 or len(hint) > 120:
                return False
            if word.lower() in hint.lower():
                return False
            for bad in blacklist:
                if bad in hint.lower():
                    return False
            # Must be a complete English sentence (simple check)
            if not hint[0].isupper() or not hint.strip().endswith('.'):
                return False
            # Should not be a question
            if '?' in hint:
                return False
            # Should not be a direct definition or meta-statement
            if 'this word' in hint.lower() or 'the word' in hint.lower():
                return False
            return True
        for attempt in range(max_attempts):
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            f"You are a word guessing game assistant. Generate exactly {n} short, clear, meaningful, and diverse English hints for the secret word in the category '{subject}'. "
                            f"Each hint must be a single, self-contained, non-question sentence that helps a player guess the word, but you must NEVER mention, reveal, or confirm the word or any part of it (including its letters, synonyms, antonyms, or definition). "
                            f"Avoid generic, unrelated, or meta statements. Do not include explanations, code blocks, or any extra text. Respond with ONLY a JSON array of {n} unique, high-quality English sentences, nothing else."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"The word is: {word}\nGenerate exactly {n} hints as described."
                    }
                ]
                response = self._make_api_request_with_retry(messages)
                content = response["choices"][0]["message"]["content"].strip()
                # Remove code block formatting if present
                if content.startswith('```'):
                    content = content.lstrip('`').strip()
                    if content.startswith('json'):
                        content = content[4:].strip()
                try:
                    hints = json.loads(content)
                except Exception:
                    # Try to extract JSON array using regex
                    match = re.search(r'(\[.*\])', content, re.DOTALL)
                    if match:
                        try:
                            hints = json.loads(match.group(1))
                        except Exception:
                            hints = []
                    else:
                        hints = []
                # Post-process: filter for meaningful, relevant hints
                filtered_hints = [h for h in hints if is_meaningful_hint(h, word)]
                # Remove duplicates
                filtered_hints = list(dict.fromkeys(filtered_hints))
                if len(filtered_hints) >= min(5, n):
                    try:
                        _safe_hints = json.dumps(filtered_hints, ensure_ascii=True)
                    except Exception:
                        _safe_hints = str(filtered_hints)
                    try:
                        _safe_word = word.encode('ascii', 'backslashreplace').decode('ascii')
                    except Exception:
                        _safe_word = str(word)
                    logger.debug(f"API returned {len(filtered_hints)} valid hints for '{_safe_word}': {_safe_hints}")
                    return filtered_hints[:n]
                try:
                    _safe_hints2 = json.dumps(filtered_hints, ensure_ascii=True)
                except Exception:
                    _safe_hints2 = str(filtered_hints)
                logger.debug(f"API returned insufficient valid hints, retrying (attempt {attempt+1}/{max_attempts}): {_safe_hints2}")
                time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                try:
                    _safe_err = str(e).encode('ascii', 'backslashreplace').decode('ascii')
                except Exception:
                    _safe_err = str(e)
                logger.debug(f"Failed to get hints from API (attempt {attempt+1}): {_safe_err}")
                time.sleep(1.5 * (attempt + 1))
        try:
            _safe_word2 = word.encode('ascii', 'backslashreplace').decode('ascii')
        except Exception:
            _safe_word2 = str(word)
        logger.debug(f"API failed to provide valid hints after {max_attempts} attempts for word '{_safe_word2}'")
        return []

    def mark_word_played(self, word: str, username: str, subject: str):
        """Mark a word as played (add to recent list, ignoring length). Also update last word for immediate repeat logic."""
        self._add_recent_word_combo(word, username, subject)
        # Update last word for this combo
        if not hasattr(self, "_last_word_by_combo"):
            self._last_word_by_combo = {}
        recent_key = f"{username}:{subject}"
        self._last_word_by_combo[recent_key] = word
        # Log the recent list after update
        logger.debug(f"[AFTER UPDATE] Recent word list for {recent_key}: {self._recently_used_words_by_combo.get(recent_key, [])}")
        # logger.info(f"[DEBUG] (AFTER UPDATE) All recent word lists: {self._recently_used_words_by_combo}")
