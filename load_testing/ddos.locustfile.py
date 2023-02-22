from lib import flow_ddos, flow_helper
from locust import HttpUser, TaskSet, task, between
import logging


class DDOSLoad(TaskSet):
    def on_start(self):
        logging.info(
            "*** Starting DDOS load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " users ***"
        )

    def on_stop(self):
        logging.info("*** Ending Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """

    @task(1)
    def ddos(self):
        # Do Sign In
        flow_ddos.do_ddos(self)


class WebsiteUser(HttpUser):
    tasks = [DDOSLoad]
    wait_time = between(5, 9)
