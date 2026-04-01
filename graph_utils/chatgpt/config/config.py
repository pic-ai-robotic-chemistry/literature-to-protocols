import json
from typing import List,Literal
import yaml
import os
import logging

def get_config():
    with open(os.path.join(DIR_PATH,CONFIG_PATH), 'r', encoding='utf-8') as config_file:
        CONFIG = yaml.safe_load(config_file)
    return CONFIG

def get_prompts():
    prompts_path = OPENAI_CONFIG['prompts_path']
    with open(os.path.join(DIR_PATH,prompts_path), 'rb') as prompts_file:
        PROMPTS = json.load(prompts_file)
    return PROMPTS

DIR_PATH = os.path.dirname(os.path.abspath(__file__)) 
LOGGER_MODES:Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
# LOGGER_MODES:Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "ERROR"
CONFIG_PATH = './config.yaml'
CONFIG = get_config()
OPENAI_CONFIG = CONFIG['openai']
DEEPSEEK_CONFIG = CONFIG['deepseek']
QWEN_CONFIG = CONFIG['qwen']
TTS_CONFIG = CONFIG['tts']
SPLIT_CONFIG = CONFIG['split']

PROMPTS = get_prompts()
APPLICATION_PROMPTS = PROMPTS['application_prompts']

