from subprocess import run, PIPE
import re


def get_token(ddi, account):
    """
    This functions takes RS DDI and AWS account number and returns credentials to be used by boto3 client.
    """
    bash_command = run(
        ["faws", "env", "-r", ddi, "-a", account], stdout=PIPE, universal_newlines=True
    )
    cred = re.sub("export ", "", bash_command.stdout)
    token = {}
    for x in cred.split("\n")[:3]:
        x_split = x.split("=")
        token[x_split[0].lower()] = x_split[1]
    return token


if __name__ == "__main__":
    print(get_token("1337824", "167718459780"))
