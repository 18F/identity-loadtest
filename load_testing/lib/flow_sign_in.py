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
        logging.debug(f"remember_device and use_previous_visitor")
        # Choose a specific previous user
        credentials = choose_cred(visited.keys())
        logging.debug(f"CREDENTIALS: {credentials}")
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
        "",
        "",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    if "/backup_code_reminder" in resp.url:
        logging.debug(f"WHAT IS BACKUP CODE REMINDER DOING THIS EARLY IN THE FLOW???")
    # rescue from /backup_code_reminder
    # TODO

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
    logging.debug(f"/login/two_factor/sms")
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "",
        "",
        {
            "code": code,
            "authenticity_token": auth_token,
            "remember_device": remember_device_value(remember_device),
        },
    )

    # also need to rescue from /backup_code_reminder and /second_mfa_reminder
    logging.debug(f"/backup_code_reminder conditional")
    if "/backup_code_reminder" in resp.url:
        logging.debug(f"/backup_code_reminder")
        resp = do_request(
            context,
            "get",
            "/account",
            "/account",
        )
    elif "/second_mfa_reminder" in resp.url:
        logging.debug(f"/second_mfa_reminder")
        auth_token = authenticity_token(resp)
        resp = do_request(
            context,
            "post",
            "/second_mfa_reminder",
            "",
            '',
            {
                "authenticity_token": auth_token,
            },
        )
    else:
      logging.debug(f"No backup code reminder or second MFA reminder, normal login so far")
      if "/account" in resp.url:
          logging.debug(f"Successful login")
      else:
          logging.debug(f"Failed login. Not at /account as expected")
          resp.failure("Not at account page")

    logging.debug(f"Export Cookies")
    # Mark user as visited and save remembered device cookies
    visited[usernum] = export_cookies(
urlparse(resp.url).netloc, context.client.cookies)

    return resp


def remember_device_value(value):
    if value:
        return "true"
    else:
        return "false"


def do_sign_in_user_not_found(context):
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users, None)

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
        "",
        {
            "user[email]": "actually-not-" + credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    return resp


def do_sign_in_incorrect_password(context):
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users, None)

    if get_env("DEBUG"):
        f"incorrect password CREDENTIALS: {credentials}"

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
        "",
        {
            "user[email]": credentials["email"],
            "user[password]": "bland pickles",
            "authenticity_token": auth_token,
        },
    )

    return resp


def do_sign_in_incorrect_sms_otp(context):
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users, None)

    logging.debug(f"incorrect OTP CREDENTIALS: {credentials}")

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
