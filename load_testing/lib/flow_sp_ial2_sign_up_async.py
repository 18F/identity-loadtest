from faker import Faker
from .flow_helper import (
    authenticity_token,
    confirm_link,
    do_request,
    get_env,
    otp_code,
    personal_key,
    querystring_value,
    random_phone,
    resp_to_dom,
    sp_signout_link,
    url_without_querystring,
)
from urllib.parse import urlparse
import logging
import os
import time

"""
*** SP IAL2 Sign Up Flow ***
"""


def ial2_sign_up_async(context):
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
            # this is in sign in, not needed here?
            #  "user[request_id]": request_id,
            "authenticity_token": auth_token,
            "user[terms_accepted]": '1'},
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
        "",
        {
            "_method": "patch",
            "new_phone_form[international_code]": "US",
            "new_phone_form[phone]": random_phone(),
            "new_phone_form[otp_delivery_preference]": "sms",
            "authenticity_token": auth_token,
            "commit": "Send security code",
        },
    )

    # After password creation set up SMS 2nd factor
    resp = do_request(context, "get", "/phone_setup", "/phone_setup")
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

    logging.debug('/login/two_factor/sms')
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
        {"doc_auth[ial2_consent_given]": "1",
            "authenticity_token": auth_token, },
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

    logging.debug('verify/doc_auth/document_capture')
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

    logging.debug('/verify/doc_auth/ssn')
    ssn = '900-12-3456'
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/ssn",
        "/verify/doc_auth/verify",
        '',
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn, },
    )
    # There are three auth tokens on the response, get the second
    auth_token = authenticity_token(resp, 1)

    logging.debug('/verify/doc_auth/verify')
    # Verify
    expected_text = 'This might take up to a minute'
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/verify",
        "/verify/doc_auth/verify_wait",
        expected_text,
        {"authenticity_token": auth_token, },
    )
    while resp.url == 'https://idp.pt.identitysandbox.gov/verify/doc_auth/verify_wait':
        time.sleep(3)
        logging.debug(
            f"SLEEPING IN /verify_wait WHILE LOOP with {new_email}")
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
                f"STILL IN /verify_wait WHILE LOOP with {new_email}")
        else:
            auth_token = authenticity_token(resp)

    logging.debug("/verify/phone")
    # Enter Phone
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        "/verify/phone",
        'This might take up to a minute',
        {"authenticity_token": auth_token,
            "idv_phone_form[phone]": random_phone(), },
    )

    wait_text = 'This might take up to a minute. We’ll load the next step '\
        'automatically when it’s done.'
    while wait_text in resp.text:
        time.sleep(3)
        logging.debug(
            f"SLEEPING IN /verify/phone WHILE LOOP with {new_email}")
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
                f"STILL IN /verify/phone WHILE LOOP with {new_email}")
        else:
            auth_token = authenticity_token(resp)

    logging.debug('/verify/otp_delivery_method')
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

    logging.debug('/verify/phone_confirmation')
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

    logging.debug('/verify/review')
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

    logging.debug('/verify/confirmations')
    # Confirmations
    resp = do_request(
        context,
        "post",
        "/verify/personal_key",
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

    logging.debug('/sign_up/completed')
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
