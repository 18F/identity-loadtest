from faker import Faker
from .flow_helper import (
    resp_to_dom,
    authenticity_token,
    random_cred,
    do_request,
    confirm_link,
    otp_code,
    random_phone
)
import time


"""
*** Sign Up Flow ***
"""


def do_sign_up(context):
    context.client.cookies.clear()
    fake = Faker()
    new_email = "test+{}@test.com".format(fake.md5())
    default_password = "salty pickles"

    # GET the new email page
    resp = do_request(context, "get", "/sign_up/enter_email",
                      "/sign_up/enter_email")
    auth_token = authenticity_token(resp)

    # Post fake email and get confirmation link (link shows up in "load test mode")
    resp = do_request(
        context,
        "post",
        "/sign_up/enter_email",
        "/sign_up/verify_email",
        "",
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

    for i in range(30):
      resp =  do_request(
          context,
          "get",
          "/otp/send?otp_delivery_selection_form%5Botp_delivery_preference%5D=sms&otp_delivery_selection_form%5Bresend%5D=true",
          "/login/two_factor/sms",
          "",
      )
      time.sleep(10)

    return resp
