import os
from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_ial2_proofing, flow_sign_in, flow_helper


class IAL2SignInLoad(TaskSet):
    def on_start(self):
        print(
            "*** Starting Sign-In and IAL2 proof load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " users ***"
        )

    def on_stop(self):
        print("*** Ending IAL2 Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_in_and_proof_load_test(self):

        #  Sign in flow
        flow_sign_in.do_sign_in(self)

        #  Get /account page
        flow_helper.do_request(self, "get", "/account", "/account")

        # IAL2 Proofing flow
        flow_ial2_proofing.do_ial2_proofing(self)

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/")


class WebsiteUser(HttpLocust):
    task_set = IAL2SignInLoad
    wait_time = between(5, 9)
