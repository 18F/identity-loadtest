from locust import HttpUser, TaskSet, task, between
from lib import flow_sp_sign_in


class SPSignInLoad(TaskSet):
    @task(1)
    def sp_sign_in_load_test(self):
        # This flow does its own SP logout
        flow_sp_sign_in.do_sign_in(self)


class WebsiteUser(HttpUser):
    tasks = [SPSignInLoad]
    wait_time = between(5, 9)
