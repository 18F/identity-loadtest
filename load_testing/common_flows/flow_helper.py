import locust
import os
import pyquery
from random import randint

# Utility functions that are helpful in various locust contexts


def do_request(
    context, method, path, expected_redirect=None, data={}, files={}, name=None
):

    if os.getenv("DEBUG"):
        print(
            """
            *** Doing Request ***
            Method: {}
            Path: {}
            Data: {}
            """.format(
                method, path, data
            )
        )

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
            verify_resp_url(expected_redirect, resp)

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
        response.failure("Could not find authenticity_token on page")
        raise locust.exception.RescheduleTask

    return token


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
    credential = {
        "email": "testuser{}@example.com".format(randint(1, int(num_users) - 1)),
        "password": "salty pickles",
    }

    return credential


"""
Use this in headers to act as a Desktop
"""


def desktop_agent_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"
    }


"""
Raise errors when you are not at the expected page
"""


def verify_resp_url(url, resp):
    if resp.url and url not in resp.url:
        if os.getenv("DEBUG"):
            message = """
            You wanted {}, but got {} for a response.
            
            Body: {}
            """.format(
                url, resp.url, resp.text
            )
            resp.failure(message)
        else:
            resp.failure("You wanted {}, but got {} for a url".format(url, resp.url))

        raise locust.exception.RescheduleTask
