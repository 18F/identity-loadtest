from faker import Faker
from random import randint
import os
from .flow_helper import random_cred, resp_to_dom, authenticity_token

"""
*** Sign In Flow ***
"""


def do_sign_in(context):

    # This should match the number of users that were created for the DB with the rake task
    num_users = os.environ.get("NUM_USERS")
    credentials = random_cred(num_users)

    with context.client.get("/", catch_response=True) as resp:
        # If you're already logged in, it'll redirect to /account.
        # We need to handle this or you'll get all sorts of
        # downstream failures.
        if "/account" in resp.url:
            print("You're already logged in. We're going to quit sign-in.")
            return resp

        dom = resp_to_dom(resp)
        token = authenticity_token(resp)

        if not token:
            resp.failure("Not a sign-in page. Current URL is {}.".format(resp.url))

    resp = context.client.post(
        resp.url,
        data={
            "user[email]": credentials["email"],
            "user[password]": credentials["password"],
            "authenticity_token": authenticity_token(resp),
            "commit": "Submit",
        },
        catch_response=True,
    )
    dom = resp_to_dom(resp)
    code = dom.find("#code").attr("value")

    if not code:
        resp.failure(
            """
            No 2FA code found.
            Make sure {} is created and can log into the IDP
            """.format(
                credentials
            )
        )
        return

    code_form = dom.find("form[action='/login/two_factor/sms']")

    resp = context.client.post(
        code_form.attr("action"),
        data={
            "code": code,
            "authenticity_token": authenticity_token(resp),
            "commit": "Submit",
        },
    )

    # We're not checking for post-login state here,
    # as it will vary depending on the SP.
    resp.raise_for_status()

    return resp
