from urllib.parse import urlparse
from .flow_helper import (
    authenticity_token,
    choose_cred,
    do_request,
    export_cookies,
    get_env,
    import_cookies,
    otp_code,
    random_cred,
    resp_to_dom,
    use_previous_visitor,
)
import logging

"""
*** DDOS Flow ***
"""

def do_ddos(context):
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users, None)

    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        "",
        {
            "user[email]": credentials["email"],
            "user[password]": "wrong pickles",
            "authenticity_token": auth_token,
        },
        headers={
            'X-Wargames': 'Wiseguy'
        }
    )

    return resp
