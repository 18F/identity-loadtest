import os
from locust import HttpLocust, TaskSet, task, between
from faker import Factory
import pyquery
import foney
from random import randint

""" Globals """
fake = Factory.create()
phone_numbers = foney.phone_numbers()
default_password = "salty pickles"

""" Helper functions """
def authenticity_token(dom, id=None):
    """
    Retrieves the CSRF auth token from the DOM for submission.
    If you need to differentiate between multiple CSRF tokens on one page,
    pass the optional ID of the parent form (with hash)
    """
    selector = 'input[name="authenticity_token"]:first'

    if id:
        selector = '{} {}'.format(id, selector)
    return dom.find(selector).attr('value')

def resp_to_dom(resp):
    """
    Little helper to check response status is 200
    and return the DOM, cause we do that a lot.
    """
    resp.raise_for_status()
    return pyquery.PyQuery(resp.content)


""" The main Locust script """
class CovidReliefLoad(TaskSet):
    def on_start(self):
        print("*** Starting load tests ***")

    def on_stop(self):
        print("*** Ending load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def full_synchronous_path(self):
        # GET the root
        self.client.get("/")

        # GET the new email page
        resp = self.client.get("/sign_up/enter_email")
        dom = resp_to_dom(resp)

        # Post fake email and get confirmation link (link shows up in "load test mode")
        new_email = "test+{}@test.com".format(fake.md5())
        resp = self.client.post("/sign_up/enter_email",
                  data={
                    'user[email]': new_email,
                    'authenticity_token': authenticity_token(dom),
                  },
                  catch_response=True)

        with resp as confirm_resp:
            dom = resp_to_dom(confirm_resp)
            try:
                confirmation_link = dom.find("#confirm-now")[0].attrib['href']
            except Exception as err:
                resp.failure(
                    "Could not find CONFIRM NOW link, is IDP enable_load_testing_mode: 'true' ?")
                return 
        
        # Get confirmation token
        resp = self.client.get(confirmation_link, name="/sign_up/email/confirm?confirmation_token=")
        dom = resp_to_dom(resp)
        token = dom.find('[name="confirmation_token"]:first').attr('value')

        # Set user password
        resp = self.client.post("/sign_up/create_password",
                  data={
                      'password_form[password]': default_password,
                      'authenticity_token': authenticity_token(dom),
                      'confirmation_token': token,
                  }
              )

        # After password creation set up SMS 2nd factor
        phone_setup_url = "/phone_setup"
        resp = self.client.get(phone_setup_url)
        dom = resp_to_dom(resp)
        auth_token = authenticity_token(dom)

        resp = self.client.post(
          phone_setup_url,
          data={
            '_method': 'patch',
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
            except Exception as err:
                resp.failure(
                    "Could not find pre-filled OTP code, is IDP telephony_disabled: 'true' ?")
                return

        # Visit security code page and submit pre-filled OTP
        resp = self.client.post(
            "/login/two_factor/sms",
            data={
                'code': otp_code,
                'authenticity_token': authenticity_token(dom),
            })

        # Should be able to get the /account page now
        resp = self.client.get("/account")

        # Now log out
        resp = self.client.get("/logout")


class WebsiteUser(HttpLocust):
    task_set = CovidReliefLoad
    wait_time = between(5, 9)