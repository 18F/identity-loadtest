from locust import HttpUser, TaskSet, task, between
from lib import flow_sp_ial2_sign_in, flow_helper


class SP_IAL2_SignInLoad(TaskSet):
    # Preload drivers license data
    license_front = flow_helper.load_fixture("mock-front.jpeg")
    license_back = flow_helper.load_fixture("mock-back.jpeg")

    @task(1)
    def sp_sign_in_load_test(self):
        flow_sp_ial2_sign_in.ial2_sign_in(self)


class WebsiteUser(HttpUser):
    tasks = [SP_IAL2_SignInLoad]
    wait_time = between(5, 9)
