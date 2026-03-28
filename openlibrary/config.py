"""Utility for loading config file."""

import os
import sys
import yaml

import infogami
from infogami import config
from infogami.infobase import server as infobase_server


# Patch infogami to handle partial db_parameters (like just a driver hint)
# and ensure the 'driver' key is preserved during configuration parsing.
def _patch_infogami():
    _orig_parse = infobase_server.parse_db_parameters
    if getattr(_orig_parse, "_is_patched", False):
        return

    def _new_parse(d):
        if d is None:
            return None
        # Support both <engine, database, username, password, port> and <dbn, db, user, pw, port>.
        # If it's a partial dict (e.g. only contains 'driver' from openlibrary.yml),
        # return it as-is to avoid a KeyError('db') and ensure the driver survives.
        if isinstance(d, dict) and 'database' not in d and 'db' not in d:
            return d
        
        result = _orig_parse(d)
        if result and isinstance(d, dict) and 'driver' in d:
            result['driver'] = d['driver']
        return result

    _new_parse._is_patched = True
    infobase_server.parse_db_parameters = _new_parse


_patch_infogami()


runtime_config = {}


def load(config_file):
    """legacy function to load openlibary config.

    The loaded config will be available via runtime_config var in this module.
    This doesn't affect the global config.

    WARNING: This function is deprecated, please use load_config instead.
    """
    if "pytest" in sys.modules:
        # During pytest ensure we're not using like olsystem or something
        assert config_file == "conf/openlibrary.yml"
    # for historic reasons
    global runtime_config
    with open(config_file) as in_file:
        runtime_config = yaml.safe_load(in_file)


def load_config(config_file):
    """Loads the config file.

    The loaded config will be available via infogami.config.
    """
    if "pytest" in sys.modules:
        # During pytest ensure we're not using like olsystem or something
        assert config_file == "conf/openlibrary.yml"
    infogami.load_config(config_file)
    setup_infobase_config(config_file)

    # This sets web.config.db_parameters
    infobase_server.update_config(config.infobase)


def setup_infobase_config(config_file):
    """Reads the infobase config file and assign it to config.infobase.
    The config_file is used as base to resolve relative path, if specified in the config.
    """
    if config.get("infobase_config_file"):
        dir = os.path.dirname(config_file)
        path = os.path.join(dir, config.infobase_config_file)
        with open(path) as in_file:
            config.infobase = yaml.safe_load(in_file)
    else:
        config.infobase = {}
