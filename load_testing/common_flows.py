from faker import Faker
from random import randint
from locust_helpers import authenticity_token, resp_to_dom, random_cred
import foney
import os

# Common flows that are used across tests

"""
*** Sign In Flow ***
"""


def do_sign_in(context):

    # This should match the number of users that were created for the DB with the rake task
    num_users = os.environ.get('NUM_USERS')
    credentials = random_cred(num_users)

    with context.client.get('/', catch_response=True) as resp:
        # If you're already logged in, it'll redirect to /account.
        # We need to handle this or you'll get all sorts of
        # downstream failures.
        if '/account' in resp.url:
            print("You're already logged in. We're going to quit sign-in.")
            return resp

        dom = resp_to_dom(resp)
        token = authenticity_token(resp)

        if not token:
            resp.failure(
                "Not a sign-in page. Current URL is {}.".format(resp.url)
            )

    resp = context.client.post(
        resp.url,
        data={
            'user[email]': credentials['email'],
            'user[password]': credentials['password'],
            'authenticity_token': authenticity_token(resp),
            'commit': 'Submit',
        },
        catch_response=True
    )
    dom = resp_to_dom(resp)
    code = dom.find("#code").attr('value')

    if not code:
        resp.failure(
            """
            No 2FA code found.
            Make sure {} is created and can log into the IDP
            """.format(credentials)
        )
        return

    code_form = dom.find("form[action='/login/two_factor/sms']")

    resp = context.client.post(
        code_form.attr('action'),
        data={
            'code': code,
            'authenticity_token': authenticity_token(resp),
            'commit': 'Submit'
        }
    )

    # We're not checking for post-login state here,
    # as it will vary depending on the SP.
    resp.raise_for_status()

    return resp


"""
*** Sign Up Flow ***
"""


def do_sign_up(context):
    fake = Faker()
    phone_numbers = foney.phone_numbers()
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
