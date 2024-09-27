import os
from dotenv import load_dotenv

def load_environment_variables():
    load_dotenv()
    local_env_path = '.env.local'
    if os.path.exists(local_env_path):
        load_dotenv(local_env_path, override=True)

load_environment_variables()

class Config:
    ZONE_PATH = '/var/lib/bind/'
    ZONE_BASE_IP = '127.0.0.1'
    ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
    CONFIG_ZONE_PATH = '/var/lib/bind/zones.conf'

class DevelopmentConfig(Config):
   ZONE_PATH = '/var/lib/bind/'

class ProductionConfig(Config):
   ZONE_PATH = '/var/lib/bind/'