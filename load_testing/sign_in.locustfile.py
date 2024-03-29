from lib import flow_sign_in, flow_helper
from locust import HttpUser, TaskSet, task, between
import logging


class SignInLoad(TaskSet):
    def on_start(self):
        logging.info(
            "*** Starting Sign-In load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " users ***"
        )

    def on_stop(self):
        logging.info("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_in_load_test(self):

        # Do Sign In
        flow_sign_in.do_sign_in(self)

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account", "")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/", "")


class WebsiteUser(HttpUser):
    tasks = [SignInLoad]
    wait_time = between(5, 9)
