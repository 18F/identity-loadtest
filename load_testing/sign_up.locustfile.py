from locust import HttpLocust, TaskSet, task, between
from common_flows import do_sign_up

class SignUpLoad(TaskSet):
    def on_start(self):
        print("*** Starting Sign-Up load tests ***")

    def on_stop(self):
        print("*** Ending Sign-Up load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def sign_up_path(self):
        # GET the root
        self.client.get("/")

        # This performs the entire sign-up flow
        do_sign_up(self) 

        # Should be able to get the /account page now
        self.client.get("/account")

        # Now log out
        self.client.get("/logout")

class WebsiteUser(HttpLocust):
    task_set = SignUpLoad
    wait_time = between(5, 9)