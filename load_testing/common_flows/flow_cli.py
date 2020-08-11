from locust import events

# Defaults
RATIOS = {
    "SIGN_IN": 7310,
    "SIGN_UP": 800,
    "SIGN_IN_AND_PROOF": 5,
    "SIGN_UP_AND_PROOF": 5,
    "SIGN_IN_USER_NOT_FOUND": 900,
    "SIGN_IN_INCORRECT_PASSWORD": 900,
    "SIGN_IN_INCORRECT_SMS_OTP": 80,
}
REMEMBERED_PERCENT = 60


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "-n",
        "--prepopulated-users",
        type=int,
        default=0,
        help=f"(prod_simulator, sign_in_*) Number of pre-populated (fixture) users in database",
        env_var=f"NUM_USERS",
    )

    parser.add_argument(
        "--remembered-percent",
        type=int,
        default=60,
        help=f"(prod_simulator, sign_in_remember_me) Percentage of remembered device logins",
        env_var=f"REMEMBERED_PERCENT",
    )

    # Ratios are used for the production simulators
    for k, v in RATIOS.items():
        lname = k.lower()
        cname = lname.replace("_", "-")
        parser.add_argument(
            cname,
            type=int,
            default=v,
            help=f"(prod_simulator) Ratio of {lname} test",
            env_var=f"RATIO_{k}",
        )
