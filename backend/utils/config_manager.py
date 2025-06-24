from utils.path_utils import get_data_folder
from utils.logging_config import get_logger
import os
import json

logger = get_logger('utils.config')

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance
    
    def initialize(self):
        """Initialize the configuration manager"""
        self.data_folder = get_data_folder()
        self.config_files = {
            'blacklist': os.path.join(self.data_folder, 'blacklist.json'),
            'whitelist': os.path.join(self.data_folder, 'whitelist.json'),
            'mode': os.path.join(self.data_folder, 'mode.json')
        }
        
        # Ensure all config files exist with default values
        self._initialize_config_files()
    
    def _initialize_config_files(self):
        """Initialize all configuration files with default values if they don't exist"""
        default_configs = {
            'blacklist': {
                'Wan_Interface': 'eth0',
                'Limit_Rate': '50mbit',
                'Full_Rate': '1000mbit'
            },
            'whitelist': {
                'Wan_Interface': 'eth0',
                'Limit_Rate': '50mbit',
                'Full_Rate': '1000mbit'
            },
            'mode': {
                'mode': 'none'
            }
        }
        
        for config_name, default_config in default_configs.items():
            config_path = self.config_files[config_name]
            if not os.path.exists(config_path):
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                logger.info(f"Initialized {config_name} config with default values")
    
    def load_config(self, config_name):
        """
        Load a configuration file
        
        Args:
            config_name (str): Name of the configuration to load
            
        Returns:
            dict: The configuration data
            
        Raises:
            ValueError: If the configuration name is invalid
        """
        if config_name not in self.config_files:
            raise ValueError(f"Invalid configuration name: {config_name}")
            
        try:
            with open(self.config_files[config_name], 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading {config_name} config: {str(e)}", exc_info=True)
            raise
    
    def save_config(self, config_name, config_data):
        """
        Save configuration data to a file
        
        Args:
            config_name (str): Name of the configuration to save
            config_data (dict): The configuration data to save
            
        Raises:
            ValueError: If the configuration name is invalid
        """
        if config_name not in self.config_files:
            raise ValueError(f"Invalid configuration name: {config_name}")
            
        try:
            with open(self.config_files[config_name], 'w') as f:
                json.dump(config_data, f, indent=4)
            logger.info(f"Saved {config_name} configuration")
        except Exception as e:
            logger.error(f"Error saving {config_name} config: {str(e)}", exc_info=True)
            raise

# Create a singleton instance
config_manager = ConfigManager() 