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
LOG_NAME = __file__.split('/')[-1].split('.')[0]

"""
*** Service Provider Sign Up Flow ***

Using this flow requires that a Service Provider be running and configured to work with HOST.
"""


def do_sign_up(context):
    sp_root_url = get_env("SP_HOST")
    context.client.cookies.clear()

    # GET the SP root, which should contain a login link, give it a friendly name for output
    resp = do_request(
        context,
        "get",
        sp_root_url,
        sp_root_url,
        {},
        {},
        sp_root_url
    )

    sp_signin_endpoint = sp_root_url + '/auth/request?aal=&ial=1'

    # submit signin form
    resp = do_request(
        context,
        "get",
        sp_signin_endpoint,
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
        {
            "user[email]": new_email,
            "authenticity_token": auth_token,
            "user[terms_accepted]": 'true'},
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
        "post",
        "/phone_setup",
        "/login/two_factor/sms",
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

    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/login/two_factor/sms",
        "/sign_up/completed",
        {"code": code, "authenticity_token": auth_token},
    )
    auth_token = authenticity_token(resp)

    # Agree to share information with the service provider
    # Visit security code page and submit pre-filled OTP
    resp = do_request(
        context,
        "post",
        "/sign_up/completed",
        "https://sp-oidc-sinatra.pt.identitysandbox.gov/",
        {"authenticity_token": auth_token},
    )

    # We should now be at the SP root, with a "logout" link.
    # The test SP goes back to the root, so we'll test that for now
    logout_link = sp_signout_link(resp)
    resp = do_request(
        context,
        "get",
        logout_link,
        sp_root_url,
        {},
        {},
        url_without_querystring(logout_link),
    )

    # Does it include the logged out text signature?
    if resp.text.find('You have been logged out') == -1:
        logging.error(f"{LOG_NAME}: user has not been logged out")
