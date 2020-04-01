import os
from locust import HttpLocust, TaskSet, task, between
from locust_helpers import *
from common_flows import *

class SignInLoad(TaskSet):
    def on_start(self):
        print("*** Starting Sign-In load tests with " + os.environ.get('NUM_USERS') + " users ***")

    def on_stop(self):
        print("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def sign_in_path(self):

        # Do Sign In
        resp = do_sign_in(self)

        # Get the /account page now
        resp = self.client.get("/account")

        # Now log out
        resp = self.client.get("/logout")


class WebsiteUser(HttpLocust):
    task_set = SignInLoad
    wait_time = between(5, 9)