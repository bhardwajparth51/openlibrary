"""Infobase extension for Open Library."""

from ..plugins import ol_infobase
from . import events


def init_plugin():
    from infogami import config
    import web
    # Infogami's parse_db_parameters strictly filters keys and strips out the 'driver' 
    # key. We re-inject it here if it exists in the original infobase config so psycopg3
    # is picked up by web.py instead of the default psycopg2.
    if hasattr(config, "db_parameters") and config.db_parameters and "driver" in config.db_parameters:
        web.config.db_parameters["driver"] = config.db_parameters["driver"]

    ol_infobase.init_plugin()
    events.setup()
