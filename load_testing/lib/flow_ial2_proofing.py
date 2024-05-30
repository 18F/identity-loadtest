from faker import Faker
from .flow_helper import do_request, authenticity_token, otp_code, random_phone, resp_to_dom
import os
import random
import sys
from urllib.parse import urlparse

"""
*** IAL2 Proofing Flow ***
"""


def do_ial2_proofing(context):
    """
    Requires following attributes on context:
    * license_front - Image data for front of driver's license
    * license_back - Image data for back of driver's license
    """
    # Request IAL2 Verification
    resp = do_request(context, "get", "/verify", "/verify/welcome")
    auth_token = authenticity_token(resp)

    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/welcome",
        "/verify/agreement",
        "",
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/agreement")
    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/agreement",
        "/verify/hybrid_handoff",
        '',
        {"doc_auth[idv_consent_given]": "1",
            "authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/hybrid_handoff",
        "/verify/document_capture",
        "",
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
        print("DEBUG: /api/verify/images")
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

    if os.getenv("DEBUG"):
        print("DEBUG: /verify/document_capture")
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

    ssn = f'900-12-{random.randint(0,9999):04}'
    if os.getenv("DEBUG"):
        print("DEBUG: /verify/ssn")
    resp = do_request(
        context,
        "put",
        "/verify/ssn",
        "/verify/verify_info",
        '',
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn, },
    )
    # There are three auth tokens on the response, get the second
    auth_token = authenticity_token(resp, 0)



    if os.getenv("DEBUG"):
        print("DEBUG: /verify/verify_info")
    # Verify
    resp = do_request(
        context,
        "put",
        "/verify/verify_info",
        None,
        '',
        {"authenticity_token": auth_token, },
    )

    # Wait until
    for i in range(12):
        if urlparse(resp.url).path == '/verify/phone':
            # success
            break
        if urlparse(resp.url).path == '/backup_code_reminder':
            # verify backup codes
            if os.getenv("DEBUG"):
               print("DEBUG: /backup_code_reminder")
            auth_token = authenticity_token(resp)
            resp = do_request(
                context,
                "get",
                "/account?",
                None,
                '',
                {"authenticity_token": auth_token, },
            )
            break
        elif urlparse(resp.url).path == '/verify/verify_info':
            # keep waiting
            time.sleep(2)
        else:
            raise ValueError(
                f"Verification expected /verify/phone but received unexpected URL of {resp.url}")

        resp = do_request(
            context,
            "get",
            "/verify/verify_info",
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
            if "login credentials used in another browser" in resp.text:
                resp.failure(
                    'Your login credentials were used in another browser.')
            else:
                raise ValueError(
                    f"Verification expected /verify/phone_confirmation but received unexpected URL of {resp.url}")

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
        "/verify/enter_password",
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
        "/verify/enter_password",
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
        "/account",
        '',
        {
            "authenticity_token": auth_token,
            "acknowledgment": "1",
        },
    )
    auth_token = authenticity_token(resp)

    ial2_sig = "ACR: http://idmanagement.gov/ns/assurance/ial/2"
    # Does it include the IAL2 text signature?
    if resp.text.find(ial2_sig) == -1:
        print("ERROR: this does not appear to be an IAL2 auth")

    # Re-Check verification activated
    do_request(context, "get", "/verify", "/verify/activated", "")

    return resp
