import os
from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_helper


class SPSignInLoad(TaskSet):
    @task(1)
    def sp_sign_in_load_test(self):

        #TODO: make this an ENV variable.  Others too?
        sp_root_url = "http://localhost:9292"

        # GET the SP root, which should contain a login link
        resp = flow_helper.do_request(
            self, "get", sp_root_url, sp_root_url, {}, {}, sp_root_url
        )
        dom = flow_helper.resp_to_dom(resp)
        sp_signin_link = dom.find("div.sign-in-wrap a").eq(0).attr("href")
        if not sp_signin_link:
            resp.failure("We could not find a signin link at {}".format(resp.url))

        # GET the signin link we found
        redirect_match = self.parent.host + "/?request_id="
        resp = flow_helper.do_request(
            self, "get", sp_signin_link, redirect_match, {}, {}, redirect_match
        )
        auth_token = flow_helper.authenticity_token(resp)
        request_id = flow_helper.querystring_value(resp.url, "request_id")

        print("*** *** *** Request ID {}".format(request_id))

        #TODO: this doesn't work from locust like it does when I do it manually.
        # POST to the sign-in page
        num_users = os.environ.get("NUM_USERS")
        credentials = flow_helper.random_cred(num_users)
        resp = flow_helper.do_request(
            self,
            "post",
            "/",
            "/login/two_factor/authenticator",
            {
                "user[email]": credentials["email"],
                "user[password]": credentials["password"],
                "user[request_id]": request_id,
                "authenticity_token": auth_token,
            },
        )
        print(resp.text)
        auth_token = flow_helper.authenticity_token(resp)
        code = flow_helper.otp_code(resp)

        # POST to 2FA authenticator
        resp = flow_helper.do_request(
            self,
            "post",
            "/login/two_factor/authenticator",
            "/account",
            {"code": code, "authenticity_token": auth_token,},
        )

        # Get /account to prove login, then log out
        flow_helper.do_request(self, "get", "/account", "/account")
        flow_helper.do_request(self, "get", "/logout", "/")


class WebsiteUser(HttpLocust):
    task_set = SPSignInLoad
    wait_time = between(5, 9)
