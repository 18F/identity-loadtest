from faker import Faker
from random import randint
from .flow_helper import (
    resp_to_dom,
    authenticity_token,
    random_cred,
    do_request,
    confirm_link,
)
from .helper_phony import fake_phone_numbers
import os

"""
*** Sign Up Flow ***
"""


def do_sign_up(context):
    fake = Faker()
    phone_numbers = fake_phone_numbers()
    new_email = "test+{}@test.com".format(fake.md5())
    default_password = "salty pickles"

    # GET the new email page
    resp = do_request(context, "get", "/sign_up/enter_email", "/sign_up/enter_email")
    auth_token = authenticity_token(resp)

    # Post fake email and get confirmation link (link shows up in "load test mode"
    resp = do_request(
        context,
        "post",
        "/sign_up/enter_email",
        "/sign_up/verify_email",
        {"user[email]": new_email, "authenticity_token": auth_token,},
    )

    conf_url = confirm_link(resp)

    # Get confirmation token
    resp = do_request(
        context,
        "get",
        conf_url,
        "/sign_up/enter_password?confirmation_token=",
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
        "/two_factor_options",
        {
            "password_form[password]": default_password,
            "authenticity_token": auth_token,
            "confirmation_token": token,
        },
    )

    # After password creation set up SMS 2nd factor
    resp = do_request(context, "get", "/phone_setup", "/phone_setup")
    auth_token = authenticity_token(resp)

    resp = do_request(
        context,
        "patch",
        "/phone_setup",
        "/login/two_factor/sms",
        {
            "new_phone_form[international_code]": "US",
            "new_phone_form[phone]": phone_numbers[randint(1, 1000)],
            "new_phone_form[otp_delivery_preference]": "sms",
            "authenticity_token": auth_token,
            "commit": "Send security code",
        },
    )
    auth_token = authenticity_token(resp)

    try:
        dom = resp_to_dom(resp)
        otp_code = dom.find('input[name="code"]')[0].attrib["value"]
    except Exception:
        resp.failure(
            "Could not find pre-filled OTP code, is IDP telephony_disabled: 'true' ?"
        )
        return

    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/account",
        {"code": otp_code, "authenticity_token": auth_token},
    )


    return resp
