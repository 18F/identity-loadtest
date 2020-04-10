from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_sp_sign_in


class SPSignInLoad(TaskSet):
    @task(1)
    def sp_sign_in_load_test(self):
        # This flow does its own SP logout
        flow_sp_sign_in.do_sp_sign_in(self)


class WebsiteUser(HttpLocust):
    task_set = SPSignInLoad
    wait_time = between(5, 9)
