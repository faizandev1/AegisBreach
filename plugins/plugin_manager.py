import os
import importlib.util
from utils.logger import logger

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = plugin_dir
        self.plugins = {}

    def load_plugins(self):
        for file in os.listdir(self.plugin_dir):
            if file.endswith(".py") and file != "__init__.py" and file != "plugin_manager.py":
                name = file[:-3]
                path = os.path.join(self.plugin_dir, file)
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, 'run'):
                    self.plugins[name] = mod
                    logger.info(f"Loaded plugin: {name}")
        return self.plugins

    def run_plugin(self, name, *args):
        if name in self.plugins:
            self.plugins[name].run(*args)