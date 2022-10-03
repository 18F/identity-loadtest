from locust import HttpUser, TaskSet, task, between
from lib import flow_sp_ial2_sign_in_async, flow_helper
import logging


class SP_IAL2_SignInLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")
    num = flow_helper.get_env("NUM_USERS")
    logging.info(
        f'starting sp_sign_in_load_test with {num} users of entropy")')

    @task(1)
    def sp_sign_in_load_test(self):
        flow_sp_ial2_sign_in_async.ial2_sign_in_async(self)


class WebsiteUser(HttpUser):
    tasks = [SP_IAL2_SignInLoad]
    wait_time = between(5, 9)
