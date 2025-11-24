"""Constants for the VVS integration."""
from datetime import timedelta

DOMAIN = "vvs"

CONF_DESTINATION = "destination"
CONF_START = "start"
CONF_OFFSET = "offset"
CONF_ROUTE_TYPE = "route_type"
CONF_MAX_CONNECTIONS = "max_connections"
CONF_Limit = "limit"

# Default update interval
SCAN_INTERVAL = timedelta(minutes=2)

# Mapping for the UI
ROUTE_TYPE_OPTIONS = {
    "leasttime": "Fastest (Least Time)",
    "leastinterchange": "Least Interchanges",
    "leastwalking": "Least Walking",
}

DEFAULT_OFFSET = 0
DEFAULT_MAX_CONNECTIONS = 3
DEFAULT_ROUTE_TYPE = "leasttime"
