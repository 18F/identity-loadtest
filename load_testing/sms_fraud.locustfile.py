from locust import HttpUser, TaskSet, task, between
from lib import flow_sign_in, flow_sign_up, flow_sms_fraud, flow_helper
import logging


class SignUpLoad(TaskSet):
    def on_start(self):
        logging.info("*** Starting SMS Fraud load tests ***")

    def on_stop(self):
        logging.info("*** Ending SMS Fraud load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

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

    @task(1)
    def sms_fraud_load_test(self):
        flow_helper.do_request(self, "get", "/", "/", "")
        flow_sms_fraud.do_sign_up(self)
        resp = flow_helper.do_request(self, "get", "/sign_up/cancel", "/sign_up/cancel", "")
        auth_token = flow_helper.authenticity_token(resp)
        flow_helper.do_request(self, "post", "/sign_up/cancel", "/logout", "", {
            "_method": "delete",
            "authenticity_token": auth_token,
        },
)


class WebsiteUser(HttpUser):
    tasks = [SignUpLoad]
    # number seconds simulated users wait between requests
    wait_time = between(5, 9)
