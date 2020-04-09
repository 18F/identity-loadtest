
import pytest
import os
import re
import test_helpers

# Import load_testing files
# :/ this kind of import only works when you run `pytest` from the root of the project.
import sys
sys.path.append('./load_testing')
from common_flows.flow_helper import *

"""
*** Unit test simple flow helpers
"""
def test_querystring_value():
    url = "http://one.two?three=four&five=six"
    assert querystring_value(url, "three") == "four"
    assert querystring_value(url, "five") == "six"


def test_url_without_querystring():
    assert url_without_querystring("http://one.two?three=four&five=six") == "http://one.two"
    assert url_without_querystring("http://one.two") == "http://one.two"

def test_random_cred():
    cred = random_cred(1)
    assert cred["email"] == "testuser1@example.com"
    assert cred["password"] == "salty pickles"

def test_random_phone():
    for i in range(5):
        assert re.match(r"202555\d{4}", random_phone())

def test_desktop_agent_headers():
    agent = desktop_agent_headers()
    assert "Firefox" in agent["User-Agent"]

def test_get_env():
    os.environ["TESTKEY"] = "testvalue"
    assert get_env("TESTKEY") == "testvalue"

    with pytest.raises(Exception):
        get_env("UNSETKEY")


