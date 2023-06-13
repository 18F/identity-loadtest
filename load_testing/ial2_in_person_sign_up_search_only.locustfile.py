from locust import HttpUser, TaskSet, task, between
from lib import flow_ial2_in_person_proofing_search_only, flow_sign_up, flow_helper
import logging


class IAL2SignUpLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")

    def on_start(self):
        logging.info("*** Starting Sign-Up and IAL2 proof load tests ***")

    def on_stop(self):
        logging.info("*** Ending IAL2 Sign-Up load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_up_and_proof_load_test(self):

        #  Sign up flow
        flow_sign_up.do_sign_up(self)

        #  Get /account page
        flow_helper.do_request(self, "get", "/account", "/account", "")

        # IAL2 Proofing flow
        flow_ial2_in_person_proofing_search_only.do_ial2_proofing(self)

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account", "")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/", "")


class WebsiteUser(HttpUser):
    tasks = [IAL2SignUpLoad]
    wait_time = between(5, 9)
