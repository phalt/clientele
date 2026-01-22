"""
API Client functions.
"""

from __future__ import annotations

from clientele import api
from tests.api_clients.test_basic_client.config import config

client = api.APIClient(config=config)

# Declare your API functions here.
