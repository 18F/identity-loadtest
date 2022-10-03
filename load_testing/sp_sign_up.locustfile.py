from locust import HttpUser, TaskSet, task, between
from lib import flow_sp_sign_up


class SPSignUpLoad(TaskSet):
    @task(1)
    def sp_sign_up_load_test(self):
        # This flow does its own SP logout
        flow_sp_sign_up.do_sign_up(self)


class WebsiteUser(HttpUser):
    tasks = [SPSignUpLoad]
    wait_time = between(5, 9)
