from faker import Faker
from random import randint
import os
from .flow_helper import (
    random_cred,
    resp_to_dom,
    authenticity_token,
    do_request,
    otp_code,
)

"""
*** Sign In Flow ***
"""


def do_sign_in(context):

    # This should match the number of users that were created for the DB with the rake task
    num_users = os.environ.get("NUM_USERS")
    credentials = random_cred(num_users)

    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

    if "/account" in resp.url:
        print("You're already logged in. Quitting sign-in.")
        return resp

    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/login/two_factor/sms",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    if not code:
        resp.failure(
            """
            No 2FA code found.
            Make sure {} is created and can log into the IDP
            """.format(
                credentials
            )
        )
        return

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/account",
        {"code": code, "authenticity_token": auth_token,},
    )
    auth_token = authenticity_token(resp)

    resp.raise_for_status()

    return resp
