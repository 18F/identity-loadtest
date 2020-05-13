from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_sign_in, flow_helper


class SignInRememberMeLoad(TaskSet):
    def on_start(self):
        print(
            "*** Starting Sign-In Remember Me load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " users ***"
        )

    def on_stop(self):
        print("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_in_load_test(self):

        # Do Sign In and make sure to check "Remember Device"
        flow_sign_in.do_sign_in(self, remember_device = True)

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/")


class WebsiteUser(HttpLocust):
    task_set = SignInRememberMeLoad
    wait_time = between(5, 9)
