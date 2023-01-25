from faker import Faker
from .flow_helper import (
    authenticity_token,
    confirm_link,
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
*** SP IAL2 Sign Up Flow ***
"""


def ial2_sign_up(context):
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
    request_id = querystring_value(resp.url, "request_id")

    # GET the new email page
    resp = do_request(context, "get", "/sign_up/enter_email",
                      "/sign_up/enter_email")
    auth_token = authenticity_token(resp)

    # Post fake email and get confirmation link (link shows up in "load test mode")
    fake = Faker()
    new_email = "test+{}@test.com".format(fake.md5())
    default_password = "salty pickles"

    resp = do_request(
        context,
        "post",
        "/sign_up/enter_email",
        "/sign_up/verify_email",
        '',
        {
            "user[email]": new_email,
            "authenticity_token": auth_token,
            "user[terms_accepted]": '1'
        },
    )

    conf_url = confirm_link(resp)

    # Get confirmation token
    resp = do_request(
        context,
        "get",
        conf_url,
        "/sign_up/enter_password?confirmation_token=",
        '',
        {},
        {},
        "/sign_up/email/confirm?confirmation_token=",
    )
    auth_token = authenticity_token(resp)
    dom = resp_to_dom(resp)
    token = dom.find('[name="confirmation_token"]:first').attr("value")

    # Set user password
    resp = do_request(
        context,
        "post",
        "/sign_up/create_password",
        "/authentication_methods_setup",
        '',
        {
            "password_form[password]": default_password,
            "authenticity_token": auth_token,
            "confirmation_token": token,
        },
    )

    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "post",
        "/authentication_methods_setup",
        "/phone_setup",
        "",
        {
            "_method": "patch",
            "two_factor_options_form[selection][]": "phone",
            "authenticity_token": auth_token,
        },
    )

    # After password creation set up SMS 2nd factor
    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "post",
        "/phone_setup",
        "/login/two_factor/sms",
        '',
        {
            "_method": "patch",
            "new_phone_form[international_code]": "US",
            "new_phone_form[phone]": random_phone(),
            "new_phone_form[otp_delivery_preference]": "sms",
            "authenticity_token": auth_token,
            "commit": "Send security code",
        },
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /login/two_factor/sms")

    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/auth_method_confirmation",
        '',
        {"code": code, "authenticity_token": auth_token},
    )

    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "post",
        "/auth_method_confirmation/skip",
        "/verify/doc_auth/welcome",
        "",
        {"authenticity_token": auth_token},
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
        {
            "doc_auth[ial2_consent_given]": "1",
            "authenticity_token": auth_token,
        },
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
    # There are three auth tokens on the response, get the third
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
        if urlparse(resp.url).path == '/verify/phone':
            # success
            break
        elif urlparse(resp.url).path == '/verify/doc_auth/verify_wait':
            # keep waiting
            time.sleep(5)
        else:
            raise ValueError(
                f'Verification received unexpected URL of {resp.url}')

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
        if urlparse(resp.url).path == '/verify/phone_confirmation':
            # success
            break
        elif urlparse(resp.url).path == '/verify/phone':
            # keep waiting
            time.sleep(5)
        else:
            raise ValueError(
                f'Phone verification received unexpected URL of {resp.url}')

        resp = do_request(
            context,
            "get",
            "/verify/phone",
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
        print("DEBUG: /verify/review")
    # Re-enter password
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
        {
            "authenticity_token": auth_token,
            "commit": "Agree and continue"
        },
    )

    ial2_sig = "ACR: http://idmanagement.gov/ns/assurance/ial/2"
    # Does it include the IAL2 text signature?
    if resp.text.find(ial2_sig) == -1:
        print("ERROR: this does not appear to be an IAL2 auth")

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
            "post_logout_redirect_uri": f"{sp_root_url}/logout",
            "state": state
        }
    )
    # Does it include the logged out text signature?
    if resp.text.find('You have been logged out') == -1:
        print("ERROR: user has not been logged out")
