from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_ial2_proofing, flow_sign_up, flow_helper


class IAL2SignUpLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mont-front.jpeg")
    license_back = flow_helper.load_fixture("mont-back.jpeg")

    def on_start(self):
        print("*** Starting Sign-Up and IAL2 proof load tests ***")

    def on_stop(self):
        print("*** Ending IAL2 Sign-Up load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_up_and_proof_load_test(self):

        #  Sign up flow
        flow_sign_up.do_sign_up(self)

        #  Get /account page
        flow_helper.do_request(self, "get", "/account", "/account")

        # IAL2 Proofing flow
        flow_ial2_proofing.do_ial2_proofing(self)

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/")


class WebsiteUser(HttpLocust):
    task_set = IAL2SignUpLoad
    wait_time = between(5, 9)
