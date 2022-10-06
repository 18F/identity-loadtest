 from random import choice, random, randint
from urllib.parse import parse_qs, urlparse
import locust
import logging
import os
import pyquery

# Utility functions that are helpful in various locust contexts
DEFAULT_COOKIE_SAVELIST = [
    "user_opted_remember_device_preference",
    "remember_device"
]
LOG_NAME = __file__.split('/')[-1].split('.')[0]


def do_request(
    context, method, path, expected_redirect=None, expected_text=None, data={}, files={}, name=None
):

    with getattr(context.client, method)(
        path,
        headers=desktop_agent_headers(),
        data=data,
        files=files,
        catch_response=True,
        name=name,
    ) as resp:
        if expected_redirect:
            if resp.url and expected_redirect not in resp.url:
                fail_response(resp, expected_redirect, expected_text)
                raise locust.exception.RescheduleTask
        if expected_text:
            if resp.text and expected_text not in resp.text:
                fail_response(resp, expected_redirect, expected_text)
                raise locust.exception.RescheduleTask
        return resp


def fail_response(response, expected_redirect, expected_text):
    if os.getenv("DEBUG"):
        message = f"""
        You wanted {expected_redirect}, but got {response.url} for a response.
        Request:
            Method: {response.request.method}
            Path: {response.url}
            Data: {response.request.body}
        Response:
            Body: {print(response.text)}"""

        response.failure(message)
    else:
        if expected_redirect:
            error_msg = f'You wanted {expected_redirect}, but got '\
                        f'{response.url} for a url.'
            if check_fail_text(response.text):
                error_msg += f' Found the following fail msg(s): ' + check_fail_text(
                    response.text)
            response.failure(error_msg)
        if expected_text:
            error_msg = f'"{expected_text}" is not in the response text.'
            if check_fail_text(response.text):
                error_msg += f' Found the following fail msg(s): ' + check_fail_text(
                    response.text)
            response.failure(error_msg)


def check_fail_text(response_text):
    known_failure_messages = [
        'For your security, your account is temporarily locked because you '
        'have entered the one-time security code incorrectly too many times.',
        'This is not a real email address. Make sure it includes an @ and a '
        'domain name',
        'Your login credentials were used in another browser. Please sign in '
        'again to continue in this browser',
        'This website is under heavy load (queue full)',
        'Need more time?',
        'Oops, something went wrong. Please try again.',
        # occurs under high load with async workers
        'The server took too long to respond. Please try again.',
    ]
    found_fail_msgs = []
    for msg in known_failure_messages:
        if msg in response_text:
            found_fail_msgs = msg
    if 'found_fail_msgs' in locals():
        return found_fail_msgs


def authenticity_token(response, index=0):
    """
    Retrieves the CSRF auth token from the DOM for submission.
    If you need to differentiate between multiple CSRF tokens on one page,
    pass the optional index of the CSRF on the page
    """
    selector = 'input[name="authenticity_token"]'

    dom = resp_to_dom(response)
    token = dom.find(selector).eq(index).attr("value")
    if not token:
        error = "Could not find authenticity_token on page"
        if os.getenv("DEBUG"):
            message = """
            {}
            Response:
                Body: {}
            """.format(
                error, response.text
            )
            response.failure(message)
        else:
            response.failure(error)
            logging.error(
                f'Failed to find authenticity token in {response.url}')
        raise locust.exception.RescheduleTask

    return token


def idv_phone_form_value(response):
    """
    Retrieves the phone number value from /verify/phone so the user does not
    have to verify a new phone number in the IAL2 flow.
    """
    selector = 'input[name="idv_phone_form[phone]"]'

    dom = resp_to_dom(response)
    value = dom.find(selector).eq(0).attr("value")

    if not value:
        error = "Could not find idv_phone_form value on page"
        if os.getenv("DEBUG"):
            message = """
            {}
            Response:
                Body: {}
            """.format(
                error, response.text
            )
            response.failure(message)
        else:
            response.failure(error)
        raise locust.exception.RescheduleTask

    return value


def querystring_value(url, key):
    # Get a querystring value from a url
    parsed = urlparse(url)
    try:
        return parse_qs(parsed.query)[key][0]
    except KeyError as e:
        logging.error(
            f'{LOG_NAME}: No querystring found for {key} in {response.url}')
        logging.debug(e)
        raise locust.exception.RescheduleTask


def url_without_querystring(url):
    # Return the url without a querystring
    return url.split("?")[0]


def otp_code(response):
    """
    Retrieves the auto-populated OTP code from the DOM for submission.
    """
    dom = resp_to_dom(response)
    selector = 'input[name="code"]'
    error_message = (
        "Could not find pre-filled OTP code, is IDP telephony_adapter: 'test' ?"
    )

    code = dom.find(selector).attr("value")

    if not code:
        response.failure(error_message)
        raise locust.exception.RescheduleTask

    return code


def confirm_link(response):
    """
    Retrieves the "CONFIRM NOW" link during the sign-up process.
    """

    dom = resp_to_dom(response)
    error_message = (
        "Could not find CONFIRM NOW link, is IDP enable_load_testing_mode: 'true' ?"
    )
    confirmation_link = dom.find("#confirm-now")[0].attrib["href"]
    if not confirmation_link:
        response.failure(error_message)
        raise locust.exception.RescheduleTask

    return confirmation_link


def sp_signin_link(response):
    """
    Gets a Sign-in link from the SP, raises an error if not found
    """

    dom = resp_to_dom(response)

    link = dom.find("div.sign-in-wrap a").eq(0)
    href = link.attr("href")

    if "/openid_connect/authorize" not in href:
        response.failure("Could not find SP Sign in link")
        raise locust.exception.RescheduleTask

    return href


def sp_signout_link(response):
    """
    Gets a Sign-in link from the SP, raises an error if not found
    """

    dom = resp_to_dom(response)
    link = dom.find("div.sign-in-wrap a").eq(0)

    failtext = "Your login credentials were used in another browser"
    if len(link) == 0 and failtext in response.text:
        logging.error(
            f'{LOG_NAME}: failed to find SP logout link. Redirected to IdP: "{failtext}"')
        response.failure(f"Redirected to IdP: {failtext}")
        raise locust.exception.RescheduleTask
    else:
        href = link.attr("href")
        try:
            if "/logout" not in href:
                response.failure("Could not find SP Log out link")
                raise locust.exception.RescheduleTask
            return href
        except TypeError as e:
            logging.debug(f'{LOG_NAME}: {e}')
            logging.debug(f'{LOG_NAME}: href = {href}')
            logging.error(f'{LOG_NAME}: status code = {response.status_code}')
            logging.error(f'{LOG_NAME}: url = {response.url}')

            raise locust.exception.RescheduleTask


def personal_key(response):
    """
    Gets a personal key from the /verify/confirmations page and raises an error
    if not found
    """
    dom = resp_to_dom(response)
    personal_key = ''
    try:
        for x in range(4):
            personal_key += dom.find("code.monospace")[x].text
    except IndexError as e:
        logging.error(f'{LOG_NAME}: No personal key found in {response.url}')
        logging.debug(e)
        raise locust.exception.RescheduleTask
    return personal_key


def resp_to_dom(resp):
    """
    Little helper to check response status is 200
    and return the DOM, cause we do that a lot.
    """
    return pyquery.PyQuery(resp.content)


def random_cred(num_users, used_nums):
    """
    Given the rake task:
    rake dev:random_users NUM_USERS=1000'

    We should have 1000 existing users with credentials matching:
    * email address testuser1@example.com through testuser1000@example.com
    * the password "salty pickles"
    * a phone number between +1 (415) 555-0001 and +1 (415) 555-1000.

    This will generate a set of credentials to match one of those entries.
    Note that YOU MUST run the rake task to put these users in the DB before using them.
    """
    user_num = randint(0, int(num_users) - 1)

    if used_nums != None:
        while user_num in used_nums:
            logging.debug(
                f'{LOG_NAME}: User #{user_num} has already been used. Retrying.')
            user_num = randint(0, int(num_users) - 1)
        else:
            logging.debug(
                f'{LOG_NAME}: User #{user_num} ready for service.')

    credential = {
        "number": user_num,
        "email": f"testuser{user_num}@example.com",
        "password": "salty pickles",
    }

    logging.debug(f'{LOG_NAME}: {credential["email"]}')
    return credential


def choose_cred(choose_from):
    """
    Same as random_cred but selects from a list of user IDs numbers.
    """
    # Coerce to list to make random.choice happy
    user_num = choice(list(choose_from))

    credential = {
        "number": user_num,
        "email": f"testuser{user_num}@example.com",
        "password": "salty pickles",
    }

    return credential


def use_previous_visitor(visited_count, visited_min, remembered_target):
    """
    Helper to decide if a specific sign in should use a previously used user
    number.

    Args:
        visited_count (int)       - Number of previously visited users
        visited_min (int)         - Lower threshold of visited users before reuse
        remembered_target (float) - Target percentage of reuse

    Returns:
        bool
    """
    if visited_count > visited_min and random() * 100 <= remembered_target:
        return True

    return False


def random_phone():
    """
    IdP uses Phonelib.valid_for_country? to test phone numbers to make sure
    they look very real
    """
    digits = "%0.4d" % randint(0, 9999)
    return "202555" + digits


def desktop_agent_headers():
    """
    Use this in headers to act as a Desktop
    """
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"
    }


def get_env(key):
    """
    Get an ENV value, and raise an error if it's not there
    """
    value = os.getenv(key)
    if not value:
        raise Exception("You must pass in Environment Variable {}".format(key))
    return value


def load_fixture(filename, path="./load_testing"):
    """
    Preload data for use by tests.

    Args:
        filename (str) - File to load, relative to path
        path (str)     - (Optional)  Path files are under
                        (Default: ./load_testing)
    Returns:
        bytes
    """
    fullpath = os.path.join(path, filename)

    try:
        with open(fullpath, "rb") as infile:
            fixture = infile.read()
    except FileNotFoundError:
        # Be a little more helpful
        raise RuntimeError(f"Could not find fixture {fullpath}")

    return fixture


def export_cookies(domain, cookies, savelist=None, sp_domain=None):
    """
    Export cookies used for remembered device/other non-session use
    as list of Cookie objects.  Only looks in jar matching host name.

    Args:
        domain (str) - Domain to select cookies from
        cookies (requests.cookies.RequestsCookieJar) - Cookie jar object
        savelist (list(str)) - (Optional) List of cookies to export

    Returns:
        list(Cookie) - restorable using set_device_cookies() function
    """
    if savelist is None:
        savelist = DEFAULT_COOKIE_SAVELIST

    # Pulling directly from internal data structure as there is
    # no get_cookies method.
    cookies_dict = cookies._cookies.get(domain, {}).get('/', None)
    # if they exist, add sp cookies to idp cookies
    if 'sp_domain' in locals() and sp_domain is not None:
        cookies_dict.update(cookies._cookies.get(sp_domain, {}).get('/', None))

    if cookies_dict is None:
        return []

    return [c for c in [cookies_dict.get(si) for si in savelist] if c is not None]


def import_cookies(client, cookies):
    """
    Restore saved cookies to the referenced client's cookie jar.

    Args:
        client (requests.session) - Client to store cookies in
        cookies (list(Cookie)) - Saved list of Cookie objects

    Returns:
        None
    """

    for c in cookies:
        client.cookies.set_cookie(c)
