import pytest
import os
import re
import test_helper

# Import load_testing files using a sad hack to support running from anywhere
import sys

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "load_testing")
    )
)

from lib.flow_helper import (
    authenticity_token,
    choose_cred,
    confirm_link,
    desktop_agent_headers,
    export_cookies,
    get_env,
    import_cookies,
    load_fixture,
    otp_code,
    querystring_value,
    random_cred,
    random_phone,
    resp_to_dom,
    sp_signin_link,
    sp_signout_link,
    url_without_querystring,
    use_previous_visitor,
)

"""
*** Unit test simple flow helpers
"""


def test_querystring_value():
    url = "http://one.two?three=four&five=six"
    assert querystring_value(url, "three") == "four"
    assert querystring_value(url, "five") == "six"


def test_url_without_querystring():
    assert (
        url_without_querystring("http://one.two?three=four&five=six")
        == "http://one.two"
    )
    assert url_without_querystring("http://one.two") == "http://one.two"


def test_random_cred():
    cred = random_cred(1, {})
    assert cred["number"] == 0
    assert cred["email"] == "testuser0@example.com"
    assert cred["password"] == "salty pickles"


def test_choose_cred():
    choices = [777, 424242, 90210]
    cred = choose_cred(choices)
    number = cred["number"]
    assert number in choices
    assert cred["email"] == "testuser{}@example.com".format(number)
    assert cred["password"] == "salty pickles"


def test_use_previous_visitor():
    # Under threshold should always be false
    assert use_previous_visitor(0, 1, 0) is False

    # Over threshold with a 100% limit should always be true
    assert use_previous_visitor(1, 0, 100) is True

    # Nondeterministic test with 75% target +/- 10% and 1000 samples
    trues = 0
    for i in range(1000):
        if use_previous_visitor(1, 0, 75):
            trues = trues + 1

    assert (
        trues >= 650 and trues <= 850
    ), "use_previous_visitor with target of 75% +/- 10 was out of spec"


def test_random_phone():
    for i in range(5):
        assert re.match(r"202555\d{4}", random_phone())


def test_desktop_agent_headers():
    agent = desktop_agent_headers()
    assert "Firefox" in agent["user-agent"]


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

    assert (
        authenticity_token(resp)
        == "WPhfbuwqPzfbpB2+aTHWR93t0/7O88iK5nYdL/RaZoLEPH63Cjf4yKAkHw6CUDyaXw6O5oi4Nc2NHzC6stEdwA=="
    )
    assert (
        authenticity_token(resp, 0)
        == "WPhfbuwqPzfbpB2+aTHWR93t0/7O88iK5nYdL/RaZoLEPH63Cjf4yKAkHw6CUDyaXw6O5oi4Nc2NHzC6stEdwA=="
    )
    assert (
        authenticity_token(resp, 1)
        == "I7WOA3x24rsZVj56R9QtCNVNlXapxqo2A9MOkU2sHPIsAi99KMzwSzD3Y89H710hluHXCoKOYt8VkT77f9U/Kg=="
    )
    assert (
        authenticity_token(resp, 2)
        == "679gwHHowpDvKlzyBL4Cw2MYZC1NYLqWaAEz+Nze6ZJZELBdu1t7BTlGmVkvqfBh713/xc0oCkbndTMoOlpLRg=="
    )

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

def test_export_import_cookies():
    # Late load requests to avoid monkeypatch warning:
    #  https://github.com/gevent/gevent/issues/1016
    from requests import Session

    domain = "oh.yea"

    r = Session()

    # Cookie that should be exported
    r.cookies.set("remember_device", "Sure", domain=domain)
    r.cookies.set("user_opted_remember_device_preference", "Yep", domain=domain)

    # Cookies that should not be exported
    r.cookies.set("remember_device", "Wrong_Domain", domain="other.place")
    r.cookies.set("wrong_domain_and_name", "me", domain="sumthing")
    r.cookies.set("wrong_name", "me", domain=domain)

    ## Export tests
    e = export_cookies(domain, r.cookies)

    assert len(e) == 2, "Wrong number of cookies exported"
    assert set([i.name for i in e]) == set(
        ["remember_device", "user_opted_remember_device_preference"]
    )
    assert e[0].domain == domain

    e2 = export_cookies(domain, r.cookies, savelist=["wrong_name"])
    assert len(e2) == 1
    assert e2[0].name == "wrong_name"

    assert export_cookies("foo.bar", r.cookies) == []

    r.cookies.clear()

    assert len(export_cookies(domain, r.cookies)) == 0

    ## Import tests
    assert (
        r.cookies.get("remember_device", domain=domain) is None
    ), "Cookies did not clear"

    import_cookies(r, e)

    assert r.cookies.get("remember_device", domain=domain) == "Sure"
    assert r.cookies.get("user_opted_remember_device_preference") == "Yep"
    assert r.cookies.get("remember_device", domain="other_place") is None
