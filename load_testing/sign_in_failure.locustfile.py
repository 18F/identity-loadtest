from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_sign_in, flow_helper


class SignInFailureLoad(TaskSet):
    def on_start(self):
        print(
            "*** Starting Sign-In failure load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " users ***"
        )

    def on_stop(self):
        print("*** Ending Sign-In failure load tests ***")

    @task(1)
    def sign_in_load_test_user_not_found(self):

        # Do Sign In
        flow_sign_in.do_sign_in_user_not_found(self)

    @task(1)
    def sign_in_load_test_incorrect_password(self):

        # Do Sign In
        flow_sign_in.do_sign_in_incorrect_password(self)

    @task(1)
    def sign_in_load_test_incorrect_otp(self):

        # Do Sign In
        flow_sign_in.do_sign_in_incorrect_otp(self)


class WebsiteUser(HttpLocust):
    task_set = SignInFailureLoad
    wait_time = between(5, 9)
