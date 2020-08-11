import os
from locust import HttpUser, TaskSet, task, between
from common_flows import flow_ial2_proofing, flow_sign_in, flow_sign_up, flow_helper

# Default ratios.  Sum should equal 10000.  (1 == 0.01%)
# These can be overridden by setting the corresponding environment
# variable.  Example:  RATIO_SIGN_UP will override RATIOS["SIGN_UP"]

# Defaults updated based on measurements from 2020-05-18
RATIOS = {
    "SIGN_IN": 7310,
    "SIGN_UP": 800,
    "SIGN_IN_AND_PROOF": 5,
    "SIGN_UP_AND_PROOF": 5,
    "SIGN_IN_USER_NOT_FOUND": 900,
    "SIGN_IN_INCORRECT_PASSWORD": 900,
    "SIGN_IN_INCORRECT_SMS_OTP": 80,
}

# For sign ins, what percentage should simulate a remembered device
REMEMBERED_PERCENT = int(os.getenv("REMEMBERED_PERCENT", 60))

# Runtime environment override with optional keys
for k in RATIOS.keys():
    rk = "RATIO_" + k
    if rk in os.environ:
        RATIOS[k] = int(os.getenv(rk))

# Visited user cookie cache
VISITED = {}


class ProdSimulator(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mont-front.jpeg")
    license_back = flow_helper.load_fixture("mont-back.jpeg")

    def on_start(self):
        self.num_users = int(flow_helper.get_env("NUM_USERS"))
        print(f"*** Production-like workload with {self.num_users} users ***")

        # Create a tracking dictionary to allow selection of previously logged
        # in users and restoration on specific cookies
        self.visited = VISITED

        # TODO - Make these tunable
        # Wait till this percentage of users have visited before enabling
        # random visited user selection.
        self.visited_min_pct = 1

        # Target percentage of remembered users for regular sign_in
        self.remembered_target = REMEMBERED_PERCENT

        # Calculate minimum number based on passed users
        self.visited_min = int(0.01 * self.visited_min_pct * self.num_users)

    def on_stop(self):
        print("*** Ending Production-like load tests ***")

    # Sum should equal 10000.  (1 == 0.01%)
    #
    @task(RATIOS["SIGN_IN"])
    def sign_in_remembered_load_test(self):
        print("=== Starting Sign IN w/remembered device ===")
        flow_sign_in.do_sign_in(
            self,
            remember_device=True,
            visited=self.visited,
            visited_min=self.visited_min,
            remembered_target=self.remembered_target,
        )
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_helper.do_request(self, "get", "/logout", "/")

    @task(RATIOS["SIGN_UP"])
    def sign_up_load_test(self):
        print("=== Starting Sign UP ===")
        flow_helper.do_request(self, "get", "/", "/")
        flow_sign_up.do_sign_up(self)
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_helper.do_request(self, "get", "/logout", "/logout")

    @task(RATIOS["SIGN_IN_AND_PROOF"])
    def sign_in_and_proof_load_test(self):
        flow_sign_in.do_sign_in(self)
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_ial2_proofing.do_ial2_proofing(self)
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_helper.do_request(self, "get", "/logout", "/")

    @task(RATIOS["SIGN_UP_AND_PROOF"])
    def sign_up_and_proof_load_test(self):
        flow_sign_up.do_sign_up(self)
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_ial2_proofing.do_ial2_proofing(self)
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_helper.do_request(self, "get", "/logout", "/")

    @task(RATIOS["SIGN_IN_USER_NOT_FOUND"])
    def sign_in_load_test_user_not_found(self):
        flow_sign_in.do_sign_in_user_not_found(self)

    @task(RATIOS["SIGN_IN_INCORRECT_PASSWORD"])
    def sign_in_load_test_incorrect_password(self):
        flow_sign_in.do_sign_in_incorrect_password(self)

    @task(RATIOS["SIGN_IN_INCORRECT_SMS_OTP"])
    def sign_in_load_test_incorrect_sms_otp(self):
        flow_sign_in.do_sign_in_incorrect_sms_otp(self)


class WebsiteUser(HttpUser):
    tasks = [ProdSimulator]
    wait_time = between(5, 9)
