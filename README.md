# `identity-loadtest`

Load testing scripts and tooling for the Login.gov, currently using [`locust`](http://locust.io).

## Local setup

### Python and Locust

Install python3 and dependencies

```sh
brew install python
pip3 install -r requirements.txt
```

### Login.gov IdP

Login IdP must be running with these settings in `application.yml`

```yml
disable_email_sending: 'true'
enable_load_testing_mode: 'true'
telephony_adapter: 'test'
```

## Running Locust

You can only run one locustfile at a time, there are many to choose from that end in `.locustfile.py`.

- `clients` is the total number of concurrent Locust users.
- `hatch-rate` is the number of users to spawn per second, starting from zero.

### Common `locust` cmd line arguments

```sh
--host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

Or omit `--no-web` and open <http://localhost:8089> for a UI.

Add `--csv=<base-name>` to generate CSV output

## Adding new tests

Add new `*.loucstfile.py` files to the project for new test scenarios.

### Sign-Up load test

- This will create lots of users in your database

```sh
locust --locustfile load_testing/sign_up.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### Sign-In load test

- You must run a rake task in the IdP before using this test, something like: `rake dev:random_users NUM_USERS=100 SCRYPT_COST='800$8$1$'` [(source)](https://github.com/18F/identity-idp/blob/master/lib/tasks/dev.rake)
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --locustfile load_testing/sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### Sign up + Sign-In load test

- This test mixes Sign-up and Sign-in together
- You must run the same rake task as above in the IdP before using this test
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --locustfile load_testing/sign_up_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### IAL2 load tests

- Same rules as above, but use `ial2_sign_*` filenames.
- Uses "desktop proofing" experience, not mobile.
- Requires `mont-front.jpeg` and `mont-back.jpeg` drivers license images

```sh
NUM_USERS=100 locust --locustfile load_testing/ial2_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

```sh
NUM_USERS=100 locust --locustfile load_testing/ial2_sign_up.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

### SP Sign in load test

- This requires that [`identity-oidc-sinatra`](https://github.com/18F/identity-oidc-sinatra) be running as an SP

```sh
NUM_USERS=100 locust --locustfile load_testing/sp_sign_in.locustfile.py --host http://localhost:3000 --clients 1 --hatch-rate 1 --run-time 15m --no-web
```

## Debugging Locust scripts

The HTTP Library is called Requests: <https://requests.readthedocs.io/en/master/>

The python debugger _should_ just work. [Here are some commands](https://docs.python.org/3/library/pdb.html#debugger-commands) The following will drop you into a debugger:

```py
import pdb; pdb.set_trace()
```
