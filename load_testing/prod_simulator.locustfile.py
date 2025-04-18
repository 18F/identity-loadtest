from locust import HttpUser, TaskSet, task, between
from lib import (
    flow_ial2_proofing,
    flow_sp_ial2_sign_in,
    flow_sp_ial2_sign_up,
    flow_sign_in,
    flow_sp_sign_in,
    flow_sp_sign_up,
    flow_helper,
)
import os
import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root.addHandler(handler)

# Default ratios.  Sum should equal 10000.  (1 == 0.01%)
# These can be overridden by setting the corresponding environment
# variable.  Example:  RATIO_SIGN_UP will override RATIOS["SIGN_UP"]

# Defaults updated based on https://gitlab.login.gov/lg-teams/radia/TeamRadia/-/issues/320

RATIOS = {
    "SIGN_IN": 3812,
    "SIGN_UP": 275,
    "SIGN_IN_AND_PROOF": 0,
    "SIGN_UP_AND_PROOF": 4990,
    "SIGN_IN_USER_NOT_FOUND": 0,
    "SIGN_IN_INCORRECT_PASSWORD": 900,
    "SIGN_IN_INCORRECT_SMS_OTP": 23,
}

# For sign ins, what percentage should simulate a remembered device
REMEMBERED_PERCENT = int(os.getenv("REMEMBERED_PERCENT", 54))

# Runtime environment override with optional keys
for k in RATIOS.keys():
    rk = "RATIO_" + k
    if rk in os.environ:
        RATIOS[k] = int(os.getenv(rk))

# Visited user cookie cache
VISITED = {}


class ProdSimulator(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")

    def on_start(self):
        num_users = int(flow_helper.get_env("NUM_USERS"))
        logging.debug(f"*** Production-like workload with {num_users} users ***")

        # Create a tracking dictionary to allow selection of previously logged
        # in users and restoration on specific cookies
        self.visited = VISITED

        # TODO - Make these tunable
        # Wait till this percentage of users have visited before enabling
        # random visited user selection.
        self.visited_min_pct = 0.01

        # Target percentage of remembered users for regular sign_in
        self.remembered_target = REMEMBERED_PERCENT

        # Calculate minimum number based on passed users
        self.visited_min = int(0.01 * self.visited_min_pct * num_users)

    def on_stop(self):
        logging.debug("*** Ending Production-like load tests ***")

    # Sum should equal 10000.  (1 == 0.01%)
    #
    @task(RATIOS["SIGN_IN"])
    def sign_in_remembered_load_test(self):
        logging.debug("=== Starting Sign IN w/remembered device ===")
        flow_sp_sign_in.do_sign_in(
            self,
            remember_device=False,
            visited=self.visited,
            visited_min=self.visited_min,
            remembered_target=self.remembered_target,
        )

    @task(RATIOS["SIGN_UP"])
    def sign_up_load_test(self):
        logging.debug("=== Starting Sign UP ===")
        flow_sp_sign_up.do_sign_up(self)

    @task(RATIOS["SIGN_IN_AND_PROOF"])
    def sign_in_and_proof_load_test(self):
        flow_sp_ial2_sign_in.ial2_sign_in(self)

    @task(RATIOS["SIGN_UP_AND_PROOF"])
    def sign_up_and_proof_load_test(self):
        flow_sp_ial2_sign_up.ial2_sign_up(self)

    @task(RATIOS["SIGN_IN_USER_NOT_FOUND"])
    def sign_in_load_test_user_not_found(self):
        flow_sp_sign_in.do_sign_in_user_not_found(self)

    @task(RATIOS["SIGN_IN_INCORRECT_PASSWORD"])
    def sign_in_load_test_incorrect_password(self):
        flow_sp_sign_in.do_sign_in_incorrect_password(self)

    @task(RATIOS["SIGN_IN_INCORRECT_SMS_OTP"])
    def sign_in_load_test_incorrect_sms_otp(self):
        flow_sp_sign_in.do_sign_in_incorrect_sms_otp(self, visited=self.visited)


class WebsiteUser(HttpUser):
    tasks = [ProdSimulator]
    wait_time = between(5, 9)
