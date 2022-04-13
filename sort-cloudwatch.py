import boto3
from rs_auth import get_token
from collections import defaultdict


def list_all_alarms(client):
    response = client.describe_alarms(MaxRecords=50)["MetricAlarms"]
    alarm = defaultdict(list)
    for entry in response:
        alarm[entry["Dimensions"][0]["Value"]].append(
            {
                "Name": entry["AlarmName"],
                "MetricName": entry["MetricName"],
                "AlarmActions": entry["AlarmActions"],
                "type": entry["Dimensions"][0]["Name"],
            }
        )
    for k, v in alarm.items():
        print(k)
        for al in v:
            print(
                f"\t Name: {al['Name']} \n\t\tMetric: {al['MetricName']}\n\t\tAction: {al['AlarmActions']}"
            )
            # print("\t" + al["MetricName"] + " " + al["AlarmActions"])


if __name__ == "__main__":
    ddi = "1337824"
    account = "167718459780"
    session = boto3.Session(**get_token(ddi, account))

    # client = session.client("sts")
    # print(client.get_caller_identity())
    client = session.client("cloudwatch", region_name="us-east-1")
    list_all_alarms(client)
