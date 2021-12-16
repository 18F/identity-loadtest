from locust import HttpUser, TaskSet, task, between
from common_flows import flow_sp_ial2_sign_up_async, flow_helper
import logging


class SP_IAL2_SignUpLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")
    logging.info('starting sp_sign_up_load_test')

    @task(1)
    def sp_sign_up_load_test(self):
        flow_sp_ial2_sign_up_async.ial2_sign_up_async(self)


class WebsiteUser(HttpUser):
    tasks = [SP_IAL2_SignUpLoad]
    wait_time = between(5, 9)
