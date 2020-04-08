from faker import Faker
from .flow_helper import do_request, authenticity_token, otp_code, random_phone
import os
import sys

"""
*** IAL2 Proofing Flow ***
"""


def do_ial2_proofing(context):

    # Request IAL2 Verification
    resp = do_request(context, "get", "/verify", "/verify/doc_auth")
    auth_token = authenticity_token(resp)

    # Post consent to Welcome
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/welcome",
        "/verify/doc_auth/upload",
        {"ial2_consent_given": "true", "authenticity_token": auth_token,},
    )
    auth_token = authenticity_token(resp)

    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/upload?type=desktop",
        "/verify/doc_auth/front_image",
        {"authenticity_token": auth_token,},
    )
    auth_token = authenticity_token(resp)

    # Post the Front Image of the license
    front_path = sys.path[0] + "/load_testing/mont-front.jpeg"
    image = open(front_path, "rb")
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/front_image",
        "/verify/doc_auth/back_image",
        {"authenticity_token": auth_token,},
        {"doc_auth[image]": image},
    )
    auth_token = authenticity_token(resp)

    # Post the Back Image of the license
    back_path = sys.path[0] + "/load_testing/mont-back.jpeg"
    image = open(back_path, "rb")
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/back_image",
        "/verify/doc_auth/ssn",
        {"authenticity_token": auth_token,},
        {"doc_auth[image]": image},
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
        {"authenticity_token": auth_token, "doc_auth[ssn]": ssn,},
    )
    # There are three auth tokens on the response, get the second
    auth_token = authenticity_token(resp, 1)

    # You can debug by issuing a GET and checking the expected path
    # resp = get_request(context, "/verify", "/verify/doc_auth/verify")
    # auth_token = authenticity_token(resp)

    # Verify
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/verify",
        "/verify/doc_auth/doc_success",
        {"authenticity_token": auth_token,},
    )
    auth_token = authenticity_token(resp)

    # Continue after doc success
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/doc_success",
        "/verify/phone",
        {"authenticity_token": auth_token,},
    )
    auth_token = authenticity_token(resp)

    # Enter Phone
    resp = do_request(
        context,
        "put",
        "/verify/phone",
        "/verify/otp_delivery_method",
        {"authenticity_token": auth_token, "idv_phone_form[phone]": random_phone(),},
    )
    auth_token = authenticity_token(resp)

    # Select SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/otp_delivery_method",
        "/verify/phone_confirmation",
        {"authenticity_token": auth_token, "otp_delivery_preference": "sms",},
    )
    auth_token = authenticity_token(resp)
    code = otp_code(resp)

    # Verify SMS Delivery
    resp = do_request(
        context,
        "put",
        "/verify/phone_confirmation",
        "/verify/review",
        {"authenticity_token": auth_token, "code": code,},
    )
    auth_token = authenticity_token(resp)

    # Re-enter password
    resp = do_request(
        context,
        "put",
        "/verify/review",
        "/verify/confirmations",
        {"authenticity_token": auth_token, "user[password]": "salty pickles",},
    )
    auth_token = authenticity_token(resp)

    # Confirmations
    do_request(
        context,
        "post",
        "/verify/confirmations",
        "/account",
        {"authenticity_token": auth_token,},
    )

    # Re-Check verification activated
    do_request(context, "get", "/verify", "/verify/activated")

    return resp
