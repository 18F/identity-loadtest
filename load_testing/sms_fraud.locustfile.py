from locust import HttpUser, TaskSet, task, between
from lib import flow_sms_fraud, flow_helper
import logging


class SignUpLoad(TaskSet):
    def on_start(self):
        logging.info("*** Starting SMS Fraud load tests ***")

    def on_stop(self):
        logging.info("*** Ending SMS Fraud load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_up_load_test(self):
        # GET the root
        flow_helper.do_request(self, "get", "/", "/", "")

        # This performs the entire sms fraud flow
        flow_sms_fraud.do_sign_up(self)

        # Should be able to get the /account page now
        resp = flow_helper.do_request(self, "get", "/sign_up/cancel", "/sign_up/cancel", "")

        auth_token = flow_helper.authenticity_token(resp)
        # Now log out.
        # You'd think that this would leave you at "/", but it returns a 204 and leaves you be.
        flow_helper.do_request(self, "post", "/sign_up/cancel", "/logout", "", {
            "_method": "delete",
            "authenticity_token": auth_token,
        },
)


class WebsiteUser(HttpUser):
    tasks = [SignUpLoad]
    # number seconds simulated users wait between requests
    wait_time = between(5, 9)
