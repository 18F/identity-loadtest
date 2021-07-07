from faker import Faker
from .flow_helper import do_request, authenticity_token, otp_code, random_phone
import sys

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
    resp = do_request(context, "get", "/verify", "/verify/doc_auth")
    auth_token = authenticity_token(resp)

    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/welcome",
        "/verify/doc_auth/agreement",
        "",
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/agreement",
        "/verify/doc_auth/upload",
        "",
        {"ial2_consent_given": "true", "authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/upload?type=desktop",
        "/verify/doc_auth/document_capture",
        "",
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    files = {"doc_auth[front_image]": context.license_front,
             "doc_auth[back_image]": context.license_back}

    # Post the license images
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/document_capture",
        "/verify/doc_auth/ssn",
        "",
        {"authenticity_token": auth_token, },
        files
    )
    auth_token = authenticity_token(resp)

    # SSN - use faker to get unique SSNs
    fake = Faker()
    ssn = fake.ssn()
    # print("*** Using ssn: " + ssn)
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/ssn",
        "/verify/doc_auth/verify",
        "",
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn, },
    )
    # There are three auth tokens on the response, get the second
    auth_token = authenticity_token(resp, 1)

    # Verify
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/verify",
        "/verify/phone",
        "",
        {"authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    # Enter Phone
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        "/verify/otp_delivery_method",
        "",
        {"authenticity_token": auth_token,
            "idv_phone_form[phone]": random_phone(), },
    )
    auth_token = authenticity_token(resp)

    # Select SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/otp_delivery_method",
        "/verify/phone_confirmation",
        "",
        {"authenticity_token": auth_token, "otp_delivery_preference": "sms", },
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    # Verify SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/phone_confirmation",
        "/verify/review",
        "",
        {"authenticity_token": auth_token, "code": code, },
    )
    auth_token = authenticity_token(resp)

    # Re-enter password
    resp = do_request(
        context,
        "put",
        "/verify/review",
        "/verify/confirmations",
        "",
        {"authenticity_token": auth_token,
            "user[password]": "salty pickles", },
    )
    auth_token = authenticity_token(resp)

    # Confirmations
    do_request(
        context,
        "post",
        "/verify/confirmations",
        "/account",
        "",
        {"authenticity_token": auth_token, },
    )

    # Re-Check verification activated
    do_request(context, "get", "/verify", "/verify/activated", "")

    return resp
