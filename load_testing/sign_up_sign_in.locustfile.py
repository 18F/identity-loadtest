from locust import HttpUser, TaskSet, task, between
from lib import flow_sign_in, flow_sign_up, flow_helper
import logging


class SignUpSignInLoad(TaskSet):

    """ @task(<weight>) : value=3 executes 3x as often as value=1
        Things inside task are synchronous. Tasks are async """

    @task(8)
    def sign_in_load_test(self):
        logging.info("=== Starting Sign IN ===")
        # Do a Sign In
        flow_sign_in.do_sign_in(self)
        # Get account page, and stay there to prove authentication
        flow_helper.do_request(self, "get", "/account", "/account", "")
        flow_helper.do_request(self, "get", "/logout", "/", "")

    @task(1)
    def sign_up_load_test(self):
        logging.info("=== Starting Sign UP ===")
        flow_helper.do_request(self, "get", "/", "/", "")
        flow_sign_up.do_sign_up(self)
        flow_helper.do_request(self, "get", "/account", "/account", "")
        flow_helper.do_request(self, "get", "/logout", "/logout", "")


class WebsiteUser(HttpUser):
    tasks = [SignUpSignInLoad]
    wait_time = between(5, 9)
