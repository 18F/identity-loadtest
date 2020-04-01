import pyquery
from random import randint

# Utility functions that are used across different locustfiles

def do_request(context, method, path, expected_redirect=None, data={}, files={}):
   with getattr(context.client, method)(
        path, 
        headers=desktop_agent_headers(),
        data=data, 
        files=files,
        catch_response=True) as resp:
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
    token = dom.find(selector).eq(index).attr('value')
    # print("Returning authenticity_token: {}".format(token))

    return token

def otp_code(response):
    """
    Retrieves the auto-populated OTP code from the DOM for submission.
    """
    selector = 'input[name="code"]'

    dom = resp_to_dom(response)
    code = dom.find(selector).attr('value')
    # print("Returning OTP code: {}".format(code))

    return code

def resp_to_dom(resp):
    """
    Little helper to check response status is 200
    and return the DOM, cause we do that a lot.
    """
    resp.raise_for_status()
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
        'email': 'testuser{}@example.com'.format(randint(1, int(num_users)-1)),
        'password': "salty pickles"
    }

    return credential

"""
Format a common error message with full content attached
"""
def err_msg(msg, resp):
    return """"
           {}
           Our current URL is: {}
           Content is: {}.
           """.format(msg, resp.url, resp.content)

"""
Use this in headers to act as a Desktop
"""
def desktop_agent_headers():
    return {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1"}

"""
Raise errors when you are not at the expected page
"""
def verify_resp_url(url, resp):
    if url not in resp.url:
        resp.failure("You wanted {}, but got {} for a url".format(url, resp.url))
