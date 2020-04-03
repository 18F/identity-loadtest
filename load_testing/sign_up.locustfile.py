from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_sign_up, flow_helper


class SignUpLoad(TaskSet):
    def on_start(self):
        print("*** Starting Sign-Up load tests ***")

    def on_stop(self):
        print("*** Ending Sign-Up load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_up_load_test(self):
        # GET the root
        flow_helper.do_request(self, "get", "/", "/")

        # This performs the entire sign-up flow
        flow_sign_up.do_sign_up(self)

        # Should be able to get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account")

        # Now log out.
        # You'd think that this would leave you at "/", but it returns a 204 and leaves you be.
        flow_helper.do_request(self, "get", "/logout", "/logout")

class WebsiteUser(HttpLocust):
    task_set = SignUpLoad
    wait_time = between(5, 9) # number seconds simulated users wait between requests
