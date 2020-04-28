
import pytest
import os
import re
import test_helper

# Import load_testing files
# :/ this kind of import only works when you run `pytest` from the root of the project.
import sys
sys.path.append('./load_testing')
from common_flows.flow_helper import (
    authenticity_token,
    confirm_link,
    desktop_agent_headers,
    get_env,
    load_fixture,
    otp_code,
    querystring_value,
    random_cred,
    random_phone,
    resp_to_dom,
    sp_signin_link,
    sp_signout_link,
    url_without_querystring,
)

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
    assert cred["email"] == "testuser0@example.com"
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

def test_resp_to_dom():
    resp = test_helper.mock_response("doc_auth_verify.html")
    assert resp_to_dom(resp)

def test_authentication_token():
    resp = test_helper.mock_response("doc_auth_verify.html")

    assert authenticity_token(resp) == "WPhfbuwqPzfbpB2+aTHWR93t0/7O88iK5nYdL/RaZoLEPH63Cjf4yKAkHw6CUDyaXw6O5oi4Nc2NHzC6stEdwA=="
    assert authenticity_token(resp, 0)  == "WPhfbuwqPzfbpB2+aTHWR93t0/7O88iK5nYdL/RaZoLEPH63Cjf4yKAkHw6CUDyaXw6O5oi4Nc2NHzC6stEdwA=="
    assert authenticity_token(resp, 1) == "I7WOA3x24rsZVj56R9QtCNVNlXapxqo2A9MOkU2sHPIsAi99KMzwSzD3Y89H710hluHXCoKOYt8VkT77f9U/Kg=="
    assert authenticity_token(resp, 2) == "679gwHHowpDvKlzyBL4Cw2MYZC1NYLqWaAEz+Nze6ZJZELBdu1t7BTlGmVkvqfBh713/xc0oCkbndTMoOlpLRg=="

    with pytest.raises(Exception):
        authenticity_token("a response without a token in it")

def test_otp_code():
    resp = test_helper.mock_response("two_factor_sms.html")

    assert otp_code(resp) == "543662"

    with pytest.raises(Exception):
        otp_code("a response without a code in it")

def test_confirm_link():
    resp = test_helper.mock_response("verify_email.html")

    assert "/sign_up/email/confirm?confirmation_token=" in confirm_link(resp)
    
    with pytest.raises(Exception):
        confirm_link("a response without a token in it")

def test_sp_signin_link():
    resp = test_helper.mock_response("sp_without_session.html")
    
    assert "openid_connect/authorize?" in sp_signin_link(resp)

    with pytest.raises(Exception):
        sp_signin_link("a response without a signin link in it")

def test_sp_signout_link():
    resp = test_helper.mock_response("sp_with_session.html")

    assert "openid_connect/logout?" in sp_signout_link(resp)

    with pytest.raises(Exception):
        sp_signout_link("A response without a sign-out link")

def test_load_file():
    orig = open("README.md", "rb").read()

    assert load_fixture("README.md", ".") == orig

    with pytest.raises(RuntimeError):
        load_fixture("NotReallyThere")
