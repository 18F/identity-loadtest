from faker import Faker
from .flow_helper import (
    authenticity_token,
    do_request,
    get_env,
    idv_phone_form_value,
    otp_code,
    personal_key,
    querystring_value,
    random_cred,
    sp_signout_link,
    url_without_querystring,
)
from urllib.parse import urlparse
import logging
import time

"""
*** SP IAL2 Sign In Flow ***
"""


def ial2_sign_in_async(context):
    """
    Requires following attributes on context:
    * license_front - Image data for front of driver's license
    * license_back - Image data for back of driver's license
    """
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

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=2'
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

    # TODO add debugging around this statement to further investigate
    # https://github.com/18F/identity-loadtest/issues/25
    request_id = querystring_value(resp.url, "request_id")

    # This should match the number of users that were created for the DB with
    # the rake task
    num_users = get_env("NUM_USERS")
    # Choose a random user
    credentials = random_cred(num_users, None)

    # POST username and password
    resp = do_request(
        context,
        "post",
        "/",
        "/login/two_factor/sms",
        '',
        {
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "user[request_id]": request_id,
            "authenticity_token": auth_token,
        }
    )

    auth_token = authenticity_token(resp)
    code = otp_code(resp)
    idp_domain = urlparse(resp.url).netloc

    logging.debug('/login/two_factor/sms')
    # Post to unauthenticated redirect
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/verify/doc_auth/welcome",
        '',
        {
            "code": code,
            "authenticity_token": auth_token,
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug('/verify/doc_auth/welcome')
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/welcome",
        "/verify/doc_auth/agreement",
        '',
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    logging.debug('/verify/doc_auth/agreement')
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/agreement",
        "/verify/doc_auth/upload",
        '',
        {"ial2_consent_given": "1", "authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    logging.debug('/verify/doc_auth/upload?type=desktop')
    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/upload?type=desktop",
        "/verify/doc_auth/document_capture",
        '',
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    files = {"doc_auth[front_image]": context.license_front,
             "doc_auth[back_image]": context.license_back}

    logging.debug('/verify/doc_auth/document_capture')
    # Post the license images
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/document_capture",
        "/verify/doc_auth/ssn",
        '',
        {"authenticity_token": auth_token, },
        files
    )
    auth_token = authenticity_token(resp)

    ssn = '900-12-3456'
    logging.debug('/verify/doc_auth/ssn')
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/ssn",
        "/verify/doc_auth/verify",
        '',
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn, },
    )
    # There are three auth tokens in the response text, get the second
    auth_token = authenticity_token(resp, 1)

    logging.debug('/verify/doc_auth/verify')
    # Verify
    expected_text = 'This might take up to a minute. We’ll load the next step '\
        'automatically when it’s done.'
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/verify",
        '/verify/doc_auth/verify_wait',
        expected_text,
        {"authenticity_token": auth_token, },)

    while resp.url == 'https://idp.pt.identitysandbox.gov/verify/doc_auth/verify_wait':
        time.sleep(3)
        logging.debug(
            f"SLEEPING IN /verify_wait WHILE LOOP with #{credentials['email']}")
        resp = do_request(
            context,
            "get",
            "/verify/doc_auth/verify_wait",
            '',
            '',
            {},
        )
        if resp.url == 'https://idp.pt.identitysandbox.gov/verify/doc_auth/verify_wait':
            logging.debug(
                f"STILL IN /verify_wait WHILE LOOP with #{credentials['email']}")
        else:
            auth_token = authenticity_token(resp)

    logging.debug("/verify/phone")
    # Enter Phone
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        '/verify/phone',
        'This might take up to a minute',
        {"authenticity_token": auth_token,
            "idv_phone_form[phone]": idv_phone_form_value(resp), },
    )

    wait_text = 'This might take up to a minute. We’ll load the next step '\
        'automatically when it’s done.'
    while wait_text in resp.text:
        time.sleep(3)
        logging.debug(
            f"SLEEPING IN /verify/phone WHILE LOOP with {credentials['email']}")
        resp = do_request(
            context,
            "get",
            "/verify/phone",
            '',
            '',
            {},
        )
        if resp.url == 'https://idp.pt.identitysandbox.gov/verify/phone':
            logging.debug(
                f"STILL IN /verify/phone WHILE LOOP with {credentials['email']}")
        else:
            auth_token = authenticity_token(resp)

    logging.debug('/verify/review')
    # Re-enter password
    resp = do_request(
        context,
        "put",
        "/verify/review",
        "/verify/confirmations",
        '',
        {"authenticity_token": auth_token,
            "user[password]": "salty pickles", },
    )
    auth_token = authenticity_token(resp)

    logging.debug('/verify/confirmations')
    # Confirmations
    resp = do_request(
        context,
        "post",
        "/verify/confirmations",
        "/sign_up/completed",
        '',
        {
            "authenticity_token": auth_token,
            "personal_key": personal_key(resp)
        },
    )

    auth_token = authenticity_token(resp)

    logging.debug('/sign_up/completed')
    # Sign Up Completed
    resp = do_request(
        context,
        "post",
        "/sign_up/completed",
        None,
        '',
        {"authenticity_token": auth_token,
         "commit": "Agree and continue"},
    )

    ial2_sig = "ACR: http://idmanagement.gov/ns/assurance/ial/2"
    # Does it include the IAL2 text signature?
    if resp.text.find(ial2_sig) == -1:
        logging.error('this does not appear to be an IAL2 auth')

    logout_link = sp_signout_link(resp)

    logging.debug('SP /logout')
    resp = do_request(
        context,
        "get",
        logout_link,
        sp_root_url,
        '',
        {},
        {},
        url_without_querystring(logout_link),
    )
    # Does it include the logged out text signature?
    if resp.text.find('You have been logged out') == -1:
        print("ERROR: user has not been logged out")
