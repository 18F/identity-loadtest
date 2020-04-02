from faker import Faker
from random import randint
from .flow_helper import resp_to_dom, authenticity_token, random_cred
from .helper_phony import fake_phone_numbers
import os

"""
*** Sign Up Flow ***
"""

def do_sign_up(context):
    fake = Faker()
    phone_numbers = fake_phone_numbers()

    default_password = "salty pickles"

    # GET the new email page
    resp = context.client.get("/sign_up/enter_email")
    dom = resp_to_dom(resp)

    # Post fake email and get confirmation link (link shows up in "load test mode")
    new_email = "test+{}@test.com".format(fake.md5())
    resp = context.client.post("/sign_up/enter_email",
                               data={
                                   'user[email]': new_email,
                                   'authenticity_token': authenticity_token(resp),
                               },
                               catch_response=True)

    with resp as confirm_resp:
        dom = resp_to_dom(confirm_resp)
        try:
            confirmation_link = dom.find("#confirm-now")[0].attrib['href']
        except Exception:
            confirm_resp.failure(
                "Could not find CONFIRM NOW link, is IDP enable_load_testing_mode: 'true' ?")

    # Get confirmation token
    resp = context.client.get(
        confirmation_link, name="/sign_up/email/confirm?confirmation_token=")
    dom = resp_to_dom(resp)
    token = dom.find('[name="confirmation_token"]:first').attr('value')

    # Set user password
    resp = context.client.post("/sign_up/create_password",
                               data={
                                   'password_form[password]': default_password,
                                   'authenticity_token': authenticity_token(resp),
                                   'confirmation_token': token,
                               }
                               )

    # After password creation set up SMS 2nd factor
    phone_setup_url = "/phone_setup"
    resp = context.client.get(phone_setup_url)
    dom = resp_to_dom(resp)
    auth_token = authenticity_token(resp)

    resp = context.client.patch(
        phone_setup_url,
        data={
            'new_phone_form[international_code]': 'US',
            'new_phone_form[phone]': phone_numbers[randint(1, 1000)],
            'new_phone_form[otp_delivery_preference]': 'sms',
            'authenticity_token': auth_token,
            'commit': 'Send security code',
        },
        catch_response=True
    )

    with resp as otp_resp:
        dom = resp_to_dom(otp_resp)
        try:
            otp_code = dom.find('input[name="code"]')[0].attrib['value']
        except Exception:
            resp.failure(
                "Could not find pre-filled OTP code, is IDP telephony_disabled: 'true' ?")
            return

    # Visit security code page and submit pre-filled OTP
    resp = context.client.post(
        "/login/two_factor/sms",
        data={
            'code': otp_code,
            'authenticity_token': authenticity_token(resp),
        })

    return resp