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
import locust
import logging

# TODO: add code to set this via env var or CLI flag
# import locust.stats
# locust.stats.CONSOLE_STATS_INTERVAL_SEC = 15

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

    logging.debug(f"cookie count for user: {len(context.client.cookies)}")

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        '',
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
        '/',
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

    expected_path = "/login/two_factor/sms" if remember_device is False else None
    if remembered:
        expected_path = sp_root_url

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        expected_path,
        '',
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )

    if remembered and "/login/two_factor/sms" in resp.url:
        logging.error(f'Unexpected SMS prompt for remembered user {usernum}')
        logging.error(f'resp.url = {resp.url}')

    auth_token = authenticity_token(resp)
    code = otp_code(resp)
    idp_domain = urlparse(resp.url).netloc

    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        None,
        '',
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
            'You are logged in',
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
        '',
        'Do you want to sign out of',
        {},
        {},
        '/openid_connect/logout?client_id=...'
    )

    auth_token = authenticity_token(resp)
    state = querystring_value(resp.url, 'state')
    # Confirm the logout request on the IdP
    resp = do_request(
        context,
        "post",
        "/openid_connect/logout",
        sp_root_url,
        'You have been logged out',
        {
            "authenticity_token": auth_token,
            "_method": "delete",
            "client_id": "urn:gov:gsa:openidconnect:sp:sinatra",
            "post_logout_redirect_uri": "https://oidc-sinatra2.loadtest.identitysandbox.gov/logout",
            "state": state
        }
    )
    # Does it include the you have been logged out text?
    if resp.text.find('You have been logged out') == -1:
        logging.error('The user has not been logged out')
        logging.error(f'resp.url = {resp.url}')
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
        '',
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
    credentials = random_cred(num_users, None)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        '',
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
        'The email or password you’ve entered is wrong',
        {
            "user[email]":  "actually-not-" + credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": auth_token,
        },
    )
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
        '',
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
    credentials = random_cred(num_users, None)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        '',
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
        'The email or password you’ve entered is wrong',
        {
            "user[email]": credentials["email"],
            "user[password]": "bland pickles",
            "authenticity_token": auth_token,
        },
    )


def do_sign_in_incorrect_sms_otp(context, visited={}):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly
    # name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        '',
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
    credentials = random_cred(num_users, visited)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/",
        '',
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
        '',
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
        'That security code is invalid',
        {"code": "000000", "authenticity_token": auth_token},
    )

    # Validate that we got the expected response and were not redirect back for
    # some other reason.
    if resp.text.find('That security code is invalid.') == -1:

        # handle case when account is locked
        account_locked_string = 'For your security, your account is '\
            'temporarily locked because you have entered the one-time '\
            'security code incorrectly too many times.'
        if resp.text.find(account_locked_string):
            error = 'sign in with incorrect sms otp failed because the '\
                f'account for testuser{credentials["number"]} has been locked.'
            logging.error(error)
            resp.failure(error)
        # handle other errors states yet to be discovered
        else:
            error = f'The expected response for incorrect OTP is not '\
                'present. resp.url: {resp.url}'
            logging.error(error)
            resp.failure(error)

    # Mark user as visited and save remembered device cookies
    visited[credentials["number"]] = export_cookies(
        urlparse(resp.url).netloc, context.client.cookies, None, None)
