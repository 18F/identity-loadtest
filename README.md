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
telephony_disabled: 'true'
```

## Running Locust

You can only run one locustfile at a time, there are many to choose from that end in `.locustfile.py`.

- `clients` is the total number of concurrent Locust users.
- `hatch-rate` is the number of users to spawn per second, starting from zero.

### Sign-Up load test

- This will create lots of users in your database

```sh
locust --host http://localhost:3000 --clients=1 --hatch-rate 1 --locustfile load_testing/sign_up.locustfile.py --no-web
```

### Sign-In load test

- You must run a rake task in the IdP before using this test, something like: `rake dev:random_users NUM_USERS=100 SCRYPT_COST='800$8$1$'` [(source)](https://github.com/18F/identity-idp/blob/master/lib/tasks/dev.rake)
- You also must pass in a matching `NUM_USERS=100` to the locust call.

```sh
NUM_USERS=100 locust --host http://localhost:3000 --clients=1 --hatch-rate 1 --locustfile load_testing/sign_in.locustfile.py --no-web
```

Or omit `--no-web` and open <http://localhost:8089> for a UI.

### IAL2 load tests

- Same rules as above, but use `ial2_sign_*` filenames.
- Uses "desktop proofing" experience, not mobile.
- Requires `mont-front.jpeg` and `mont-back.jpeg` drivers license images

```sh
NUM_USERS=100 locust --host http://localhost:3000 --clients=1 --hatch-rate 1 --locustfile load_testing/ial2_sign_in.locustfile.py --no-web
```

## Debugging Locust scripts

The python debugger _should_ just work. [Here are some commands](https://docs.python.org/3/library/pdb.html#debugger-commands) The following will drop you into a debugger:

```py
import pdb; pdb.set_trace()
```
