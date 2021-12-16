from locust import HttpUser, TaskSet, task, between
from common_flows import flow_sp_ial2_sign_up, flow_helper


class SP_IAL2_SignUpLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")

    @task(1)
    def sp_sign_in_load_test(self):
        flow_sp_ial2_sign_up.ial2_sign_up(self)


class WebsiteUser(HttpUser):
    tasks = [SP_IAL2_SignUpLoad]
    wait_time = between(5, 9)
