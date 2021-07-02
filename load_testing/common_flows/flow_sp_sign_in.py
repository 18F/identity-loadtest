from urllib.parse import urlparse
from .flow_helper import (
    authenticity_token,
    choose_cred,
    do_request,
    export_cookies,
    get_env,
    import_cookies,
    otp_code,
    querystring_value,
    random_cred,
    resp_to_dom,
    sp_signin_link,
    sp_signout_link,
    url_without_querystring,
    use_previous_visitor,
)

"""
*** Service Provider Sign In Flow ***

Using this flow requires that a Service Provider be running and configured to work with HOST. It
also requires that users are pre-generated in the IdP database.
"""


def do_sign_in(
    context,
    remember_device=False,
    visited={},
    visited_min=0,
    remembered_target=0,
):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()
    # print(f"cookie count for user: {len(context.client.cookies)}")

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        {},
        {},
        sp_root_url
    )

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=1'
    # submit signin form
    resp = do_request(
        context,
        "get",
        sp_signin_endpoint,
        '',
        {},
        {},
        sp_signin_endpoint
    )
    auth_token = authenticity_token(resp)
    request_id = querystring_value(resp.url, "request_id")

    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    remembered = False

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
    auth_token = authenticity_token(resp)
    expected_path = "/login/two_factor/sms" if remember_device is False else None

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        expected_path,
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )

    if remembered and "/login/two_factor/sms" in resp.url:
        print(f"Unexpected SMS prompt for remembered user {usernum}")

    auth_token = authenticity_token(resp)
    code = otp_code(resp)
    idp_domain = urlparse(resp.url).netloc

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        None,
        {
            "code": code,
            "authenticity_token": auth_token,
            "remember_device": remember_device_value(remember_device),
        },
    )

    if "/sign_up/completed" in resp.url:
        # POST to completed, should go back to the SP
        auth_token = authenticity_token(resp)
        resp = do_request(
            context,
            "post",
            "/sign_up/completed",
            sp_root_url,
            {"authenticity_token": auth_token, },
        )

    sp_domain = urlparse(resp.url).netloc

    # We should now be at the SP root, with a "logout" link.
    # The test SP goes back to the root, so we'll test that for now
    logout_link = sp_signout_link(resp)
    resp = do_request(
        context,
        "get",
        logout_link,
        sp_root_url,
        {},
        {},
        url_without_querystring(logout_link),
    )
    # Does it include the you have been logged out text?
    if resp.text.find('You have been logged out') == -1:
        print("ERROR: user has not been logged out")

    # Mark user as visited and save remembered device cookies
    visited[usernum] = export_cookies(
        idp_domain, context.client.cookies, None, sp_domain)


def remember_device_value(value):
    if value:
        return "true"
    else:
        return "false"


def do_sign_in_user_not_found(context):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        {},
        {},
        sp_root_url
    )

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=1'
    # submit signin form
    resp = do_request(
        context,
        "get",
        sp_signin_endpoint,
        '',
        {},
        {},
        sp_signin_endpoint
    )
    auth_token = authenticity_token(resp)
    request_id = querystring_value(resp.url, "request_id")

    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )
    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

    # Post login credentials
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        {
            "user[email]":  "actually-not-" + credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )

    # Validate that we got the expected response and were not redirect back for
    # some other reason.
    if resp.text.find('The email or password you’ve entered is wrong') == -1:
        print("ERROR: the expected response for incorrect l/p is not present")

    return resp


def do_sign_in_incorrect_password(context):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        {},
        {},
        sp_root_url
    )

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=1'
    # submit signin form
    resp = do_request(
        context,
        "get",
        sp_signin_endpoint,
        '',
        {},
        {},
        sp_signin_endpoint
    )
    auth_token = authenticity_token(resp)
    request_id = querystring_value(resp.url, "request_id")

    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )
    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

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

    # Validate that we got the expected response and were not redirect back for
    # some other reason.
    if resp.text.find('The email or password you’ve entered is wrong') == -1:
        print("ERROR: the expected response for incorrect l/p is not present")

    return resp


def do_sign_in_incorrect_sms_otp(context):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        {},
        {},
        sp_root_url
    )

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=1'
    # submit signin form
    resp = do_request(
        context,
        "get",
        sp_signin_endpoint,
        '',
        {},
        {},
        sp_signin_endpoint
    )
    auth_token = authenticity_token(resp)
    request_id = querystring_value(resp.url, "request_id")

    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    credentials = random_cred(num_users)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )
    resp = do_request(context, "get", "/", "/")
    auth_token = authenticity_token(resp)

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

    # Validate that we got the expected response and were not redirect back for
    # some other reason.
    if resp.text.find('That security code is invalid.') == -1:
        print("ERROR: the expected response for incorrect OTP is not present")

    return resp
