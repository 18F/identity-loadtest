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
import logging
import os
import random
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
    resp = do_request(context, "get", sp_root_url, sp_root_url, "", {}, {}, sp_root_url)

    sp_signin_endpoint = sp_root_url + "/auth/request?aal=&ial=2"
    # submit signin form
    resp = do_request(
        context, "get", sp_signin_endpoint, "", "", {}, {}, sp_signin_endpoint
    )
    auth_token = authenticity_token(resp)

    # GET the new email page
    resp = do_request(context, "get", "/sign_up/enter_email", "/sign_up/enter_email")
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
        "",
        {
            "user[email]": new_email,
            "authenticity_token": auth_token,
            "user[terms_accepted]": "1",
        },
    )

    conf_url = confirm_link(resp)

    # Get confirmation token
    resp = do_request(
        context,
        "get",
        conf_url,
        "/sign_up/enter_password?confirmation_token=",
        "",
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
        "",
        {
            "password_form[password]": default_password,
            "password_form[password_confirmation]": default_password,
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
            "new_phone_form[international_code]": "US",
            "new_phone_form[phone]": random_phone(),
            "new_phone_form[otp_delivery_preference]": "sms",
            "new_phone_form[recaptcha_token]": "",
            "authenticity_token": auth_token,
            "commit": "Send security code",
        },
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    logging.debug("/login/two_factor/sms")

    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/auth_method_confirmation",
        "",
        {"code": code, "authenticity_token": auth_token},
    )

    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "post",
        "/auth_method_confirmation/skip",
        "/verify/welcome",
        "",
        {"authenticity_token": auth_token},
    )
    auth_token = authenticity_token(resp)

    logging.debug("/verify/welcome")
    auth_token = authenticity_token(resp)
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/welcome",
        "/verify/agreement",
        "",
        {
            "authenticity_token": auth_token,
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug("/verify/agreement")
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/agreement",
        "/verify/hybrid_handoff",
        "",
        {
            "doc_auth[idv_consent_given]": "1",
            "authenticity_token": auth_token,
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug("/verify/hybrid_handoff")
    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/hybrid_handoff",
        "/verify/document_capture",
        "",
        {
            "authenticity_token": auth_token,
        },
    )

    dom = resp_to_dom(resp)

    selector = 'meta[name="csrf-token"]'
    auth_token = dom.find(selector).eq(0).attr("content")

    selector = 'input[id="doc_auth_document_capture_session_uuid"]'
    dcs_uuid = dom.find(selector).eq(0).attr("value")

    second_auth_token = authenticity_token(resp)

    files = {
        "front": context.license_front,
        "back": context.license_back,
    }

    logging.debug("/api/verify/images")
    # Post the license images
    resp = do_request(
        context,
        "post",
        "/api/verify/images",
        None,
        None,
        {"flow_path": "standard", "document_capture_session_uuid": dcs_uuid},
        files,
        None,
        {"X-CSRF-Token": auth_token},
    )

    logging.debug("/verify/document_capture")
    resp = do_request(
        context,
        "put",
        "/verify/document_capture",
        "/verify/ssn",
        None,
        {
            "_method": "patch",
            "doc_auth[document_capture_session_uuid]": dcs_uuid,
            "authenticity_token": second_auth_token,
        },
    )
    auth_token = authenticity_token(resp)

    ssn = f"900-12-{random.randint(0,9999):04}"

    logging.debug("/verify/ssn")
    resp = do_request(
        context,
        "put",
        "/verify/ssn",
        "/verify/verify_info",
        "",
        {
            "authenticity_token": auth_token,
            "doc_auth[ssn]": ssn,
        },
    )
    auth_token = authenticity_token(resp, 0)

    logging.debug("/verify/verify_info")
    # Verify
    resp = do_request(
        context,
        "put",
        "/verify/verify_info",
        None,
        "",
        {
            "authenticity_token": auth_token,
        },
    )

    # Wait until
    for i in range(12):
        if urlparse(resp.url).path == "/verify/phone":
            # success
            break
        if urlparse(resp.url).path == "/backup_code_reminder":
            # verify backup codes
            logging.debug("/backup_code_reminder")
            auth_token = authenticity_token(resp)
            resp = do_request(
                context,
                "get",
                "/account?",
                None,
                "",
                {
                    "authenticity_token": auth_token,
                },
            )
            break
        elif urlparse(resp.url).path == "/verify/verify_info":
            # keep waiting
            time.sleep(2)
        else:
            raise ValueError(
                f"Verification expected /verify/phone but received unexpected URL of {resp.url}"
            )

        resp = do_request(
            context,
            "get",
            "/verify/verify_info",
        )

    logging.debug("/verify/phone")
    # Enter Phone
    auth_token = authenticity_token(resp)
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        None,
        "",
        {
            "authenticity_token": auth_token,
            "idv_phone_form[phone]": random_phone(),
        },
    )
    for i in range(12):
        if urlparse(resp.url).path == "/verify/phone_confirmation":
            # success
            break
        elif urlparse(resp.url).path == "/verify/phone":
            # keep waiting
            time.sleep(5)
        else:
            raise ValueError(
                f"Phone verification received unexpected URL of {resp.url}"
            )

        resp = do_request(
            context,
            "get",
            "/verify/phone",
        )

    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    logging.debug("/verify/phone_confirmation")
    # Verify SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/phone_confirmation",
        "/verify/enter_password",
        "",
        {
            "authenticity_token": auth_token,
            "code": code,
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug("/verify/review")
    # Re-enter password
    resp = do_request(
        context,
        "put",
        "/verify/enter_password",
        "/verify/personal_key",
        "",
        {
            "authenticity_token": auth_token,
            "user[password]": "salty pickles",
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug("/verify/personal_key")
    # Re-enter password
    resp = do_request(
        context,
        "post",
        "/verify/personal_key",
        "/sign_up/completed",
        "",
        {
            "authenticity_token": auth_token,
            "acknowledgment": "1",
        },
    )
    auth_token = authenticity_token(resp)

    logging.debug("/sign_up/completed")
    # Sign Up Completed
    resp = do_request(
        context,
        "post",
        "/sign_up/completed",
        None,
        "",
        {"authenticity_token": auth_token, "commit": "Agree and continue"},
    )

    ial2_sig = "ACR: http://idmanagement.gov/ns/assurance/ial/2"
    # Does it include the IAL2 text signature?
    if resp.text.find(ial2_sig) == -1:
        logging.error("this does not appear to be an IAL2 auth")

    logout_link = sp_signout_link(resp)
    resp = do_request(
        context,
        "get",
        logout_link,
        "",
        "Do you want to sign out of",
        {},
        {},
        "/openid_connect/logout?client_id=...",
    )

    auth_token = authenticity_token(resp)
    state = querystring_value(resp.url, "state")
    # Confirm the logout request on the IdP
    resp = do_request(
        context,
        "post",
        "/openid_connect/logout",
        sp_root_url,
        "You have been logged out",
        {
            "authenticity_token": auth_token,
            "_method": "delete",
            "client_id": "urn:gov:gsa:openidconnect:sp:sinatra",
            "post_logout_redirect_uri": f"{sp_root_url}/logout",
            "state": state,
        },
    )
    # Does it include the logged out text signature?
    if resp.text.find("You have been logged out") == -1:
        logging.error("user has not been logged out")
