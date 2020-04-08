import os
from locust import HttpLocust, TaskSet, task, between
from common_flows import flow_helper


class SPSignInLoad(TaskSet):
    @task(1)
    def sp_sign_in_load_test(self):

        sp_root_url = flow_helper.get_env("SP_HOST")

        # GET the SP root, which should contain a login link, give it a friendly name for output
        resp = flow_helper.do_request(
            self, "get", sp_root_url, sp_root_url, {}, {}, sp_root_url
        )
        signin_link = flow_helper.sp_signin_link(resp)

        # GET the signin link we found
        resp = flow_helper.do_request(
            self,
            "get",
            signin_link,
            "/?request_id=",
            {},
            {},
            flow_helper.url_without_querystring(signin_link),
        )
        auth_token = flow_helper.authenticity_token(resp)
        request_id = flow_helper.querystring_value(resp.url, "request_id")

        # POST username and password
        num_users = flow_helper.get_env("NUM_USERS")
        credentials = flow_helper.random_cred(num_users)
        resp = flow_helper.do_request(
            self,
            "post",
            "/",
            "/login/two_factor/sms",
            {
                "user[email]": credentials["email"],
                "user[password]": credentials["password"],
                "user[request_id]": request_id,
                "authenticity_token": auth_token,
            },
        )

        auth_token = flow_helper.authenticity_token(resp)
        code = flow_helper.otp_code(resp)

        # POST to 2FA
        # If first time for user, this redirects to "completed", otherwise to the SP root.
        resp = flow_helper.do_request(
            self,
            "post",
            "/login/two_factor/sms",
            None,
            {"code": code, "authenticity_token": auth_token,},
        )
        auth_token = flow_helper.authenticity_token(resp)

        if "/sign_up/completed" in resp.url:
            # POST to completed, should go back to the SP
            resp = flow_helper.do_request(
                self,
                "post",
                "/sign_up/completed",
                sp_root_url,
                {"authenticity_token": auth_token,},
            )

        # We should now be at the SP root, with a "logout" link.
        # Test SP goes back to the root, so we'll test that for now
        logout_link = flow_helper.sp_signout_link(resp)
        flow_helper.do_request(
            self,
            "get",
            logout_link,
            sp_root_url,
            {},
            {},
            flow_helper.url_without_querystring(logout_link),
        )


class WebsiteUser(HttpLocust):
    task_set = SPSignInLoad
    wait_time = between(5, 9)
