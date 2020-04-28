from .flow_helper import (
    random_cred,
    resp_to_dom,
    authenticity_token,
    do_request,
    otp_code,
    get_env,
)

"""
*** Sign In Flow ***
"""

def do_sign_in(context):

    # This should match the number of users that were created for the DB with the rake task
    num_users = get_env("NUM_USERS")
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

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/account",
        {"code": code, "authenticity_token": auth_token,},
    )

    return resp


def do_sign_in_user_not_found(context):
    num_users = get_env("NUM_USERS")
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
        "/",
        {
            "user[email]": "actually-not-" + credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    return resp


def do_sign_in_incorrect_password(context):
    num_users = get_env("NUM_USERS")
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
        "/",
        {
            "user[email]": credentials["email"],
            "user[password]": "bland pickles",
            "authenticity_token": auth_token,
        },
    )

    return resp


def do_sign_in_incorrect_otp(context):
    num_users = get_env("NUM_USERS")
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

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/login/two_factor/sms",
        {"code": "000000", "authenticity_token": auth_token,},
    )

    return resp
