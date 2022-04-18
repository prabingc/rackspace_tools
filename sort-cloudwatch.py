import boto3
from rs_auth import get_token
from collections import defaultdict

operatormap = {
    "GreaterThanThreshold": ">",
    "GreaterThanOrEqualToThreshold": ">=",
    "LessThanOrEqualToThreshold": "<=",
    "LowerThanThreshold": "<",
}


def seconds_to_minute(seconds):
    seconds = int(seconds)
    minute = seconds // 60
    seconds = seconds % 60
    result = f"{str(minute)} minutes"
    if seconds:
        result += f" {str(seconds)} secs"
    return result


def list_all_alarms(client):
    response = client.describe_alarms()["MetricAlarms"]
    alarm = defaultdict(list)
    with open("220417-ord-0000355.txt", "a") as output_file:
        print(
            f"*********************************************\n{region}\n*********************************************",
            file=output_file,
        )
        for entry in response:
            try:
                alarm[entry["Dimensions"][0]["Value"]].append(
                    {
                        "Name": entry["AlarmName"],
                        "Threshold": f"""{entry["MetricName"]} {operatormap[entry["ComparisonOperator"]]} {entry["Threshold"]} for {entry["EvaluationPeriods"]} datapoints within {seconds_to_minute(entry["Period"]*entry["EvaluationPeriods"])}""",
                        "AlarmActions": entry["AlarmActions"],
                        "State": entry["StateValue"],
                    }
                )
            except IndexError:
                print(f'skipping {entry["AlarmName"]}')
        for k, v in alarm.items():
            print("\n" + k, file=output_file)
            for al in v:
                print(
                    f"\t Name: {al['Name']} \n\t\tThreshold: {al['Threshold']}\n\t\tAction: {al['AlarmActions']}\n\t\tState: {al['State']}",
                    file=output_file,
                )
                # print("\t" + al["MetricName"] + " " + al["AlarmActions"])
    output_file.close()


if __name__ == "__main__":
    ddi = "check"
    account = "new"
    session = boto3.Session(**get_token(ddi, account))

    # client = session.client("sts")
    # print(client.get_caller_identity())
    regions = ["ca-central-1", "us-east-1", "us-west-1", "us-west-2"]
    for region in regions:
        client = session.client("cloudwatch", region_name=region)
        list_all_alarms(client)
