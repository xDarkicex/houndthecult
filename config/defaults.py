import json
import logging

def load_config(config_file="config.json"):
    """
    Load the configuration file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: Loaded configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file is not valid JSON.
        KeyError: If required keys are missing in the config file.
    """
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        
        # Ensure required keys are present in the twitter_api section
        required_keys = ["API_KEY", "API_SECRET", "ACCESS_TOKEN", "ACCESS_SECRET", "BEARER_TOKEN"]
        twitter_api_config = config.get("twitter_api", {})
        
        for key in required_keys:
            if key not in twitter_api_config:
                raise KeyError(f"Missing required key: {key}")
        
        return config
    except FileNotFoundError:
        logging.critical(f"Config file '{config_file}' not found. Please create it with API keys.")
        raise
    except json.JSONDecodeError:
        logging.critical(f"Config file '{config_file}' is not valid JSON. Please check its format.")
        raise
    except KeyError as e:
        logging.critical(f"Config file '{config_file}' is missing required keys: {str(e)}")
        raise
