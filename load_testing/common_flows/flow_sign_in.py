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
*** Sign In Flow ***
"""


def do_sign_in(
    context,
    remember_device=False,
    visited={},
    visited_min=0,
    remembered_target=0,
):
    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    remembered = False

    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

    # Crossed minimum visited user threshold AND passed random selector
    if remember_device and use_previous_visitor(
        len(visited), visited_min, remembered_target
    ):
        # Choose a specific previous user
        credentials = choose_cred(visited.keys())
        # Restore remembered device cookies to client jar
        import_cookies(context.client, visited[credentials["number"]])
        remembered = True
    else:
        # remove the first 6% of visited users if more than 66% of the users
        # have signed in. Note: this was picked arbitrarily and seems to work.
        # We may want to better tune this per NUM_USERS.
        if float(len(visited))/float(num_users) > 0.66:
            logging.info(
                'You have used more than two thirds of the userspace.')
            removal_range = int(0.06 * float(num_users))
            count = 0
            for key in list(visited):
                logging.debug(f'removing user #{key}')
                if count < removal_range:
                    visited.pop(key)
        # grab an random and unused credential
        credentials = random_cred(num_users, visited)

    usernum = credentials["number"]
    expected_path = "/login/two_factor/sms" if remember_device is False else "/"

    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        expected_path,
        "",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    if "/account" in resp.url:
        if not remembered:
            logging.error(f"You're already logged in. Quitting sign-in for "
                          f"{usernum}")
        return resp

    if remembered and "/login/two_factor/sms" in resp.url:
        logging.error(
            f"Unexpected SMS prompt for remembered user {usernum}")
        return resp

    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/account",
        "",
        {
            "code": code,
            "authenticity_token": auth_token,
            "remember_device": remember_device_value(remember_device),
        },
    )

    # Mark user as visited and save remembered device cookies
    visited[usernum] = export_cookies(
        urlparse(resp.url).netloc, context.client.cookies)

    return resp


def remember_device_value(value):
    if value:
        return "true"
    else:
        return "false"


def do_sign_in_with_params(context, param="user_not_found"):

    resp = do_request(context, "get", "/", "/")
    if "/account" in resp.url:
        print("You're already logged in. Quitting sign-in.")
        return resp

    num_users = get_env("NUM_USERS")
    auth_token = authenticity_token(resp)
    credentials = random_cred(num_users, None)

    if param == "user_not_found":
    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        "",
        {
            "user[email]": "actually-not-" + credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )
    elif param == "incorrect_password":
    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        "",
        {
            "user[email]": credentials["email"],
            "user[password]": "bland pickles",
            "authenticity_token": auth_token,
        },
    )
    elif param == "incorrect_sms_otp":
    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/login/two_factor/sms",
        "",
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
        "",
        {"code": "000000", "authenticity_token": auth_token},
    )

    return resp



def do_sign_in_user_not_found(context):
    
    resp = do_sign_in_with_params(context,"user_not_found")

    return resp


def do_sign_in_incorrect_password(context):
    
    resp = do_sign_in_with_params(context, "incorrect_password")

    return resp


def do_sign_in_incorrect_sms_otp(context):
    
    resp = do_sign_in_with_params(context, "incorrect_sms_otp")

    return resp
