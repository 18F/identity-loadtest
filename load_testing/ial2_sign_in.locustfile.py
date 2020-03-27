import os
import sys
from locust import HttpLocust, TaskSet, task, between
from locust_helpers import *
from common_flows import do_sign_in
from faker import Faker

class IAL2SignInLoad(TaskSet):
    def on_start(self):
        print("*** Starting IAL2 Sign-In load tests with " + os.environ.get('NUM_USERS') + " users ***")

    def on_stop(self):
        print("*** Ending IAL2 Sign-In load tests ***")

    """ @task(<weight>) : value=3 executes 3x as often as value=1 """
    """ Things inside task are synchronous. Tasks are async """
    @task(1)
    def sign_in_and_verify_path(self):

      """
      Here's the flow:
      1.  Login flow
      2.  GET  /verify
      3.  POST /verify/doc_auth/welcome
      4.  POST /verify/doc_auth/upload?type=desktop
      5.  POST /verify/doc_auth/front_image
      6.  POST /verify/doc_auth/back_image
      7.  POST /verify/doc_auth/ssn
      8.  POST /verify/doc_auth/verify
      9.  POST /verify/doc_auth/doc_success
      10. POST /verify/doc_auth/phone
      11. POST /verify/otp_delivery_method
      12. POST /verify/phone_confirmation
      13. POST /verify/review
      14. POST /verify/confirmations
      15. GET  /verify (redirects -> /verify/activated)
      """


      #  Sign in
      do_sign_in(self)

      #  Get /account page
      dom, auth_token = get_request(self, "/account", "/account")

      # Request IAL2 Verification
      dom, auth_token = get_request(self, "/verify", "/verify/doc_auth")
      
      # Post consent to Welcome
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/welcome",
        { '_method': 'put',
          'ial2_consent_given': 'true',
          'authenticity_token': auth_token,
        },
        "/verify/doc_auth/upload")

      # Choose Desktop flow
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/upload?type=desktop",
        { '_method': 'put',
          'authenticity_token': auth_token,
        },
        "/verify/doc_auth/front_image")

      # Post the Front Image of the license
      front_path = sys.path[0] + "/load_testing/mont-front.jpeg"
      with open(front_path, 'rb') as image, self.client.post(
        "/verify/doc_auth/front_image",
        headers= desktop_agent_headers(),
        data={
          '_method': 'put',
          'authenticity_token': auth_token,
          }, 
        files={'doc_auth[image]': image},
        catch_response=True) as resp:
          verify_resp_url("/verify/doc_auth/back_image", resp)
          dom = resp_to_dom(resp)
          auth_token = authenticity_token(dom)
      
      # Post the Back Image of the license
      back_path = sys.path[0] + "/load_testing/mont-back.jpeg"
      with open(back_path, 'rb') as image, self.client.post(
        "/verify/doc_auth/back_image",
        headers= desktop_agent_headers(),
        data={
          '_method': 'put',
          'authenticity_token': auth_token,
          }, 
        files={'doc_auth[image]': image},
        catch_response=True) as resp:
          verify_resp_url("/verify/doc_auth/ssn", resp)
          dom = resp_to_dom(resp)
          auth_token = authenticity_token(dom)

      # SSN - use faker to get unique SSNs
      fake = Faker()
      ssn = fake.ssn()
      print("*** Using ssn: " + ssn)
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/ssn",
        { '_method': 'put',
          'authenticity_token': auth_token,
          'doc_auth[ssn]': ssn,
        },
        "/verify/doc_auth/verify")

      # Verify
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/verify",
        { '_method': 'put',
          'authenticity_token': auth_token,
        },
        "/verify/doc_auth/doc_success")

      # Continue after doc success
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/doc_success",
        { '_method': 'put',
          'authenticity_token': auth_token,
        },
        "/verify/doc_auth/phone")

      # Enter Phone
      dom, auth_token = post_request(self, 
        "/verify/doc_auth/phone",
        { '_method': 'put',
          'authenticity_token': auth_token,
          'idv_phone_form[phone]': '8888888888',
        },
        "/verify/otp_delivery_method")

      # Select SMS Delivery
      dom, auth_token = post_request(self, 
        "/verify/otp_delivery_method",
        { '_method': 'put',
          'authenticity_token': auth_token,
          'otp_delivery_preference': 'sms',
        },
        "/verify/phone_confirmation") 
      try:
          otp_code = dom.find('input[name="code"]')[0].attrib['value']
      except Exception:
          resp.failure(
              "Could not find pre-filled OTP code, is IDP telephony_disabled: 'true' ?")

      # Verify SMS Delivery
      dom, auth_token = post_request(self, 
        "/verify/phone_confirmation",
        { '_method': 'put',
          'authenticity_token': auth_token,
          'code': otp_code,
        },
        "/verify/review")

      # Re-enter password
      dom, auth_token = post_request(self, 
        "/verify/review",
        { '_method': 'put',
          'authenticity_token': auth_token,
          'user[password]': 'salty pickles',
        },
        "/verify/confirmations")

      # Confirmations
      dom, auth_token = post_request(self, 
        "/verify/confirmations",
        { 'authenticity_token': auth_token,
        },
        "/verify/account")

      # Re-Check verification activated
      dom, auth_token = get_request(self, "/verify", "/verify/activated")

      # Now log out
      resp = self.client.get("/logout")


class WebsiteUser(HttpLocust):
    task_set = IAL2SignInLoad
    wait_time = between(5, 9)