from faker import Faker
from .flow_helper import (
    authenticity_token,
    do_request,
    get_env,
    otp_code,
    personal_key,
    querystring_value,
    random_cred,
    random_phone,
    resp_to_dom,
    sp_signout_link,
    url_without_querystring,
)
from urllib.parse import urlparse
import os
import sys
import time

"""
*** SP IAL2 Sign In Flow ***
"""


def ial2_sign_in(context):
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

    if os.getenv("DEBUG"):
        print("DEBUG: /login/two_factor/sms")

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

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/welcome")
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

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/agreement")
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/agreement",
        "/verify/doc_auth/upload",
        '',
        {"doc_auth[ial2_consent_given]": "1",
            "authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/upload?type=desktop")
    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/upload?type=desktop",
        "/verify/doc_auth/document_capture",
        '',
        {"authenticity_token": auth_token, },
    )

    dom = resp_to_dom(resp)
    selector = 'meta[name="csrf-token"]'
    auth_token = dom.find(selector).eq(0).attr("content")

    selector = 'input[id="doc_auth_document_capture_session_uuid"]'
    dcs_uuid = dom.find(selector).eq(0).attr("value")

    second_auth_token = authenticity_token(resp)

    files = {"front": context.license_front,
             "back": context.license_back,
             }

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/document_capture")
    # Post the license images
    resp = do_request(
        context,
        "post",
        "/api/verify/images",
        None,
        None,
        {
         "flow_path": "standard",
         "document_capture_session_uuid": dcs_uuid},
        files,
        None,
        {"X-CSRF-Token": auth_token},
    )

    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/document_capture",
        "/verify/doc_auth/ssn",
        None,
        {
            "_method": "patch",
            "doc_auth[document_capture_session_uuid]": dcs_uuid,
            "authenticity_token": second_auth_token,
        },
    )
    auth_token = authenticity_token(resp)

    ssn = '900-12-3456'
    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/ssn")
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/ssn",
        "/verify/doc_auth/verify",
        '',
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn, },
    )
    # There are three auth tokens on the response, get the second
    auth_token = authenticity_token(resp, 2)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/doc_auth/verify")
    # Verify
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/verify",
        None,
        '',
        {"authenticity_token": auth_token, },
    )

    # Wait until
    for i in range(12):
        print(i)
        if urlparse(resp.url).path == '/verify/phone':
            # success
            break
        elif urlparse(resp.url).path == '/verify/doc_auth/verify_wait':
            # keep waiting
            time.sleep(5)
        else:
            raise ValueError(f'Verification received unexpected URL of {resp.url}')

        resp = do_request(
            context,
            "get",
            "/verify/doc_auth/verify_wait",
        )
    if os.getenv("DEBUG"):
        print("DEBUG: /verify/phone")
    # Enter Phone
    auth_token = authenticity_token(resp)
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        None,
        '',
        {"authenticity_token": auth_token,
            "idv_phone_form[phone]": random_phone(), },
    )
    for i in range(12):
        if urlparse(resp.url).path == '/verify/otp_delivery_method':
            # success
            break
        elif urlparse(resp.url).path == '/verify/phone':
            # keep waiting
            time.sleep(5)
        else:
            raise ValueError(f'Phone verification received unexpected URL of {resp.url}')
        resp = do_request(
            context,
            "get",
            "/verify/phone",
        )
    auth_token = authenticity_token(resp)
    if os.getenv("DEBUG"):
        print("DEBUG: /verify/otp_delivery_method")
    # Select SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/otp_delivery_method",
        "/verify/phone_confirmation",
        '',
        {"authenticity_token": auth_token, "otp_delivery_preference": "sms", },
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/phone_confirmation")
    # Verify SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/phone_confirmation",
        "/verify/review",
        '',
        {"authenticity_token": auth_token, "code": code, },
    )
    auth_token = authenticity_token(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/review")
    # Re-enter password
    resp = do_request(
        context,
        "put",
        "/verify/review",
        "/verify/personal_key",
        '',
        {
            "authenticity_token": auth_token,
            "user[password]": "salty pickles",
        },
    )
    auth_token = authenticity_token(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/confirmations")
    # Confirmations
    resp = do_request(
        context,
        "post",
        "/verify/personal_key",
        "/sign_up/completed",
        '',
        {
            "authenticity_token": auth_token,
            "acknowledgment": "1",
        },
    )
    auth_token = authenticity_token(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /sign_up/completed")
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
        print("ERROR: this does not appear to be an IAL2 auth")

    logout_link = sp_signout_link(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /sign_up/completed")
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
