from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_sign_in, flow_helper

# Singletons... everyone's fav!
VISITED = {}


class SignInRememberMeLoad(TaskSet):
    def on_start(self):

        num_users = int(flow_helper.get_env("NUM_USERS"))

        print(f"*** Starting Sign-In Remember Me load tests with {num_users} users ***")

        # Create a tracking dictionary to allow selection of previously logged
        # in users and restoration on specific cookies
        self.visited = VISITED

        # TODO - Make these tunable
        # Wait till this percentage of users have visited before enabling
        # random visited user selection.
        self.visited_min_pct = 1

        # Target percentage of remembered users
        self.remembered_target = 90

        # Calculate minimum number based on passed users
        self.visited_min = int(0.01 * self.visited_min_pct * num_users)

    def on_stop(self):
        print("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def sign_in_load_test(self):

        # Do Sign In and make sure to check "Remember Device"
        flow_sign_in.do_sign_in(
            self,
            remember_device=True,
            visited=self.visited,
            visited_min=self.visited_min,
            remembered_target=self.remembered_target,
        )

        # Get the /account page now
        flow_helper.do_request(self, "get", "/account", "/account")

        # Now log out
        flow_helper.do_request(self, "get", "/logout", "/")


class WebsiteUser(HttpLocust):
    task_set = SignInRememberMeLoad
    wait_time = between(5, 9)
