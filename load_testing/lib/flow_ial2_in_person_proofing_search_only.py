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
        {"doc_auth[ial2_consent_given]": "1",
            "authenticity_token": auth_token, },
    )
    auth_token = authenticity_token(resp)

    # Choose Desktop flow
    resp = do_request(
        context,
        "put",
        "/verify/doc_auth/upload?type=desktop",
        "/verify/document_capture",
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
        "/verify/document_capture",
        None,
        "",
        {"authenticity_token": auth_token, },
        files
    )
    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "post",
        "/api/addresses",
        None,
        data={"address":"1600 Pennsylvania Avenue NW, Washington, DC 20500"}
    )
    auth_token = authenticity_token(resp)

    return resp
