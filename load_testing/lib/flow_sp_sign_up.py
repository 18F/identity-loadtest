from faker import Faker
from .flow_helper import (
    authenticity_token,
    do_request,
    get_env,
    confirm_link,
    otp_code,
    querystring_value,
    random_cred,
    random_phone,
    resp_to_dom,
    sp_signin_link,
    sp_signout_link,
    url_without_querystring,
)
import logging

LOG_NAME = __file__.split("/")[-1].split(".")[0]

"""
*** Service Provider Sign Up Flow ***

Using this flow requires that a Service Provider be running and configured to work with HOST.
"""


def do_sign_up(context):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly name for output
    resp = do_request(context, "get", sp_root_url, sp_root_url, "", {}, {}, sp_root_url)

    sp_signin_endpoint = sp_root_url + "/auth/request?aal=&ial=1"

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
        "/sign_up/completed",
        "",
        {"authenticity_token": auth_token},
    )

    auth_token = authenticity_token(resp)

    # Agree to share information with the service provider
    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/sign_up/completed",
        sp_root_url,
        "",
        {"authenticity_token": auth_token},
    )

    # We should now be at the SP root, with a "logout" link.
    # The test SP goes back to the root, so we'll test that for now
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
    # Does it include the you have been logged out text?
    if resp.text.find("You have been logged out") == -1:
        logging.error("The user has not been logged out")
        logging.error(f"resp.url = {resp.url}")
