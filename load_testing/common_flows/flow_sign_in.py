from requests.utils import urlparse
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


"""
*** Sign In Flow ***
"""


def do_sign_in(
    context, remember_device=False, visited={}, visited_min=0, remembered_target=0,
):
    remembered = False
    # This should match the number of users that were created for the DB with the rake task
    num_users = get_env("NUM_USERS")

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
        # Choose a random user
        credentials = random_cred(num_users)

    usernum = credentials["number"]

    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

    if "/account" in resp.url:
        print(f"You're already logged in. Quitting sign-in for {usernum}")
        return resp

    expected_path = "/login/two_factor/sms" if remember_device is False else None

    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        expected_path,
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    if "/account" in resp.url:
        if not remembered:
            print(f"You're already logged in. Quitting sign-in for {usernum}")
        return resp

    remembered and print(f"Unexpected SMS prompt for remembered user {usernum}")

    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/account",
        {
            "code": code,
            "authenticity_token": auth_token,
            "remember_device": remember_device_value(remember_device),
        },
    )

    # Mark user as visited and save remembered device cookies
    visited[usernum] = export_cookies(urlparse(resp.url).netloc, context.client.cookies)

    return resp


def remember_device_value(value):
    if value:
        return "true"
    else:
        return "false"


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


def do_sign_in_incorrect_sms_otp(context):
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
        {"code": "000000", "authenticity_token": auth_token},
    )

    return resp
