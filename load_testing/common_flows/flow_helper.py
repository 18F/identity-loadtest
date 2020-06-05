import locust
import os
import pyquery
from urllib.parse import parse_qs, urlparse
from random import choice, random, randint

# Utility functions that are helpful in various locust contexts
DEFAULT_COOKIE_SAVELIST = [
    "user_opted_remember_device_preference",
    "remember_device"
]

def do_request(
    context, method, path, expected_redirect=None, data={}, files={}, name=None
):

    with getattr(context.client, method)(
        path,
        headers=desktop_agent_headers(),
        data=data,
        files=files,
        catch_response=True,
        name=name,
    ) as resp:
        resp.raise_for_status()

        if expected_redirect:
            if resp.url and expected_redirect not in resp.url:
                if os.getenv("DEBUG"):
                    message = """
                    You wanted {}, but got {} for a response.
                    Request:
                        Method: {}
                        Path: {}
                        Data: {}
                    Response:
                        Body: {}
                    """.format(
                        expected_redirect, resp.url, method, path, data, resp.text
                    )
                    resp.failure(message)
                else:
                    resp.failure(
                        "You wanted {}, but got {} for a url".format(
                            expected_redirect, resp.url
                        )
                    )

                raise locust.exception.RescheduleTask

        return resp


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
        raise locust.exception.RescheduleTask

    return token


def querystring_value(url, key):
    # Get a querystring value from a url
    parsed = urlparse(url)
    return parse_qs(parsed.query)[key][0]


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
    href = link.attr("href")

    if "/logout" not in href:
        response.failure("Could not find SP Log out link")
        raise locust.exception.RescheduleTask

    return href


def resp_to_dom(resp):
    """
    Little helper to check response status is 200
    and return the DOM, cause we do that a lot.
    """
    return pyquery.PyQuery(resp.content)


def random_cred(num_users):
    """
    Given the rake task:
    rake dev:random_users NUM_USERS=1000 SCRYPT_COST='800$8$1$'

    We should have 1000 existing users with credentials matching:
    * email address testuser1@example.com through testuser1000@example.com
    * the password "salty pickles"
    * a phone number between +1 (415) 555-0001 and +1 (415) 555-1000.

    This will generate a set of credentials to match one of those entries.
    Note that YOU MUST run the rake task to put these users in the DB before using them.
    """
    user_num = randint(0, int(num_users) - 1)

    credential = {
        "number": user_num,
        "email": f"testuser{user_num}@example.com",
        "password": "salty pickles",
    }

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


def export_cookies(domain, cookies, savelist=None):
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
    dcookies = cookies._cookies.get(domain, {}).get('/', None)

    if dcookies is None:
        return []

    return [c for c in [dcookies.get(si) for si in savelist] if c is not None]


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
