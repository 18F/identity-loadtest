import os
from locust import HttpLocust, TaskSet, task, between
from faker import Factory
import pyquery
import foney
from random import randint

""" Globals """
fake = Factory.create()
phone_numbers = foney.phone_numbers()
usagov_url = "https://www.cdc.gov"
login_url = "http://localhost:3000"
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
        """
        USA.gov : just make one request
        """
        self.client.get(usagov_url + "/coronavirus/2019-ncov/about/index.html", name="USA.gov/covid19")

        """
        Login.gov : Create new user, set up SMS, log out
        """
        self.client.get(login_url + "/")

        # GET the new email page
        resp = self.client.get(login_url + "/sign_up/enter_email", name="Login/sign_up/enter_email")
        dom = resp_to_dom(resp)

        # Post fake email and get confirmation link (link shows up in "load test mode")
        new_email = "test+{}@test.com".format(fake.md5())
        resp = self.client.post(login_url + "/sign_up/enter_email",
                  data={
                    'user[email]': new_email,
                    'authenticity_token': authenticity_token(dom),
                  },
                  catch_response=True, name="Login/sign_up/enter_email")
        dom = resp_to_dom(resp)
        confirmation_link = dom.find("#confirm-now")[0].attrib['href']
        
        # Get confirmation token
        resp = self.client.get(confirmation_link, name="Login/sign_up/email/confirm")
        dom = resp_to_dom(resp)
        token = dom.find('[name="confirmation_token"]:first').attr('value')

        # Set user password
        resp = self.client.post(login_url + "/sign_up/create_password",
                  data={
                      'password_form[password]': default_password,
                      'authenticity_token': authenticity_token(dom),
                      'confirmation_token': token,
                  }
              )

        # After password creation set up SMS 2nd factor
        phone_setup_url = login_url + "/phone_setup"
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
        dom = resp_to_dom(resp)
        otp_code = dom.find('input[name="code"]')[0].attrib['value']

        # Visit security code page and submit pre-filled OTP
        resp = self.client.post(
            login_url + "/login/two_factor/sms",
            data={
                'code': otp_code,
                'authenticity_token': authenticity_token(dom),
            })

        # Should be able to get the /account page now
        resp = self.client.get(
          login_url + "/account"
        )

        # Now log out
        resp = self.client.get(
          login_url + "/logout"
        )


class WebsiteUser(HttpLocust):
    task_set = CovidReliefLoad
    wait_time = between(5, 9)