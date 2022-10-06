from locust import HttpUser, TaskSet, task, between
from lib import flow_sign_up, flow_helper
import logging


class SignUpLoad(TaskSet):
    def on_start(self):
        logging.info("*** Starting Sign-Up load tests ***")

    def on_stop(self):
        logging.info("*** Ending Sign-Up load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_up_load_test(self):
        # GET the root
        flow_helper.do_request(self, "get", "/", "/", "")

        # This performs the entire sign-up flow
        flow_sign_up.do_sign_up(self)

        # Should be able to get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account", "")

        # Now log out.
        # You'd think that this would leave you at "/", but it returns a 204 and leaves you be.
        flow_helper.do_request(self, "get", "/logout", "/logout", "")


class WebsiteUser(HttpUser):
    tasks = [SignUpLoad]
    # number seconds simulated users wait between requests
    wait_time = between(5, 9)
