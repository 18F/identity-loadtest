import pyquery
from random import randint

# Functions that are used across different locustfiles
def authenticity_token(dom, id=None):
    """
    Retrieves the CSRF auth token from the DOM for submission.
    If you need to differentiate between multiple CSRF tokens on one page,
    pass the optional ID of the parent form (with hash)
    """
    selector = 'input[name="authenticity_token"]:first'

    if id:
        selector = '{} {}'.format(id, selector)
    return dom.find(selector).attr('value')

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