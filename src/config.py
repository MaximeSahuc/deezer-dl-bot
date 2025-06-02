import yaml
import os


CONFIG_DEFAULT_TEMPLATE = {
    "deezer": {
        "bot_arl_cookie": "12345678901234567890123456789012345678901234567890"
    },
    "downloads": {
        "music_download_path": "/path/to/jellyfin/data/media/Music/"
    },
    "jellyfin": {
        "server_url": "https://jellyfin.foo",
        "api_key": "11de10c9368627286f0377f69f42c7d4"
    }
}


class ConfigManager:
    def __init__(self, file_path):
        global CONFIG_DEFAULT_TEMPLATE
        self.file_path = file_path
        self.default_template = CONFIG_DEFAULT_TEMPLATE
        self._load_config()


    def _load_config(self):
        """Loads the configuration from the file, or initializes with a default template."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
            except yaml.YAMLError as e:
                print(f"Error parsing YAML file: {e}. Initializing with empty config or default template.")
                self.config = {}
                self._apply_default_template_if_empty()
        else:
            self.config = {}
            self._apply_default_template_if_empty()
        self.save() # Ensure the file exists and is populated if a template was used


    def _apply_default_template_if_empty(self):
        """Applies the default template if the configuration is empty."""
        if not self.config and self.default_template:
            self.config = self.default_template.copy()
            self.save()
            print(f"Config file not found or empty. Initializing with default template.")
            print(f"Please edit the config file: {self.file_path}")
            exit(1)


    def add_section(self, section):
        """Adds a new section to the config if it does not exist."""
        if section not in self.config:
            self.config[section] = {}
            self.save()


    def add_item(self, section, key, value):
        """Adds an item to a section in the config. Creates the section if it does not exist."""
        if section not in self.config:
            self.add_section(section)
        self.config[section][key] = value
        self.save()


    def get_value(self, section, key, default=None):
        """Gets the value of a key in a section. Returns default if not found and saves it to the config."""
        if section not in self.config or key not in self.config.get(section, {}):
            if default is not None:
                self.set_value(section, key, default)
            return default
        return self.config[section][key]


    def set_value(self, section, key, value):
        """Sets the value of a key in a section. Creates the section if it does not exist."""
        if section not in self.config:
            self.add_section(section)
        self.config[section][key] = value
        self.save()


    def save(self):
        """Writes the current configuration to the file."""
        with open(self.file_path, 'w') as file:
            yaml.safe_dump(self.config, file, default_flow_style=False)
