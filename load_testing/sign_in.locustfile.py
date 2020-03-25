import os
from locust import HttpLocust, TaskSet, task, between
from locust_helpers import *

class SignInLoad(TaskSet):
    def on_start(self):
        print("*** Starting Sign-In load tests with " + os.environ.get('NUM_USERS') + " users ***")

    def on_stop(self):
        print("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def sign_in_path(self):

        # This should match the number of users that were created for the DB with the rake task
        num_users = os.environ.get('NUM_USERS')
        credentials = random_cred(num_users)

        with self.client.get('/', catch_response=True) as resp:
            # If you're already logged in, it'll redirect to /account.
            # We need to handle this or you'll get all sorts of
            # downstream failures.
            if '/account' in resp.url:
                print("You're already logged in. We're going to quit sign-in.")
                return resp

            dom = resp_to_dom(resp)
            token = authenticity_token(dom)

            if not token:
                resp.failure(
                    "Not a sign-in page. Current URL is {}.".format(resp.url)
                )

        resp = self.client.post(
            resp.url,
            data={
                'user[email]': credentials['email'],
                'user[password]': credentials['password'],
                'authenticity_token': authenticity_token(dom),
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
        
        resp = self.client.post(
            code_form.attr('action'),
            data={
                'code': code,
                'authenticity_token': authenticity_token(dom),
                'commit': 'Submit'
            }
        )

        # We're not checking for post-login state here,
        # as it will vary depending on the SP.
        resp.raise_for_status()

        # Get the /account page now
        resp = self.client.get("/account")

        # Now log out
        resp = self.client.get("/logout")


class WebsiteUser(HttpLocust):
    task_set = SignInLoad
    wait_time = between(5, 9)