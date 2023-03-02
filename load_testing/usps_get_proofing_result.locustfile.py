from lib import flow_helper
from locust import HttpUser, TaskSet, task, between
import logging
import psycopg2

class USPSGetProofingResultTest(TaskSet):
    env = flow_helper.get_env("ENV")
    ENDPOINT = "/ivs-ippaas-api/IPPRest/resources/rest/getProofingResults"
    DB = "identity_idp_development"
    USER = ""
    PASSWORD = ""
    DBHOST = "127.0.0.1"

    def on_start(self):
        logging.info(
            "*** Starting USPS CAT load tests with "
            + flow_helper.get_env("NUM_USERS")
            + " calls ***"
            + " to "
            + self.env
        )

    def on_stop(self):
        logging.info("*** Ending USPS CAT load tests ***")


    @task(1)
    def USPS_enrollment_check_test(self):
        conn = psycopg2.connect(
            database=self.DB, user=self.USER, password=self.PASSWORD, host=self.DBHOST
        )
               
        cursor = conn.cursor()

        cursor.execute("SELECT enrollment_code, unique_id FROM in_person_enrollments;")

        # for initial testing, fetch one.
        result = cursor.fetchone()

        # post to enrollment
        resp = flow_helper.do_request(
            self,
            "post",
            self.env + self.ENDPOINT,
            "",
            "",
            {
                "sponsorID": 3,
                "uniqueID": result[1],
                "enrollmentCode": result[0],
                "activationCode": "30457833"
            }
        )

        conn.close()


class WebsiteUser(HttpUser):
    tasks = [USPSGetProofingResultTest]
    wait_time = between(5, 9)
