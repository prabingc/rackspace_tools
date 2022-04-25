import boto3
import botocore
from pprint import pprint

# boto3.setup_default_session(profile_name="lab")


def configure_monitor(boto_client, alarm: dict):
    #
    # this will add alert or print error if unsuccessful
    #
    print(f"\t {alarm['AlarmName']}")
    try:
        boto_client.put_metric_alarm(**alarm)
    except botocore.exceptions.ClientError:
        print(f"\t\tFailed to create alert for {alarm['AlarmName']} ")


def default_RS_Monitors(instance: dict):
    #
    # instance = {"name": "ec2-name", "id": "i-06cffbxx4997e96xx", "region": "us-east-1"  }
    # This will configure RS default 5 monitors
    #
    default_attribute = {
        "ActionsEnabled": True,
        "OKActions": [
            f'arn:aws:sns:{instance["region"]}:{instance["account"]}:rackspace-support-emergency'
        ],
        "AlarmActions": [
            f'arn:aws:sns:{instance["region"]}:{instance["account"]}:rackspace-support-emergency'
        ],
        "Namespace": "AWS/EC2",
        "Statistic": "Minimum",
        "Dimensions": [{"Name": "InstanceId", "Value": f'{instance["id"]}'}],
        "Period": 60,
        "Unit": "Count",
        "EvaluationPeriods": 2,
        "Threshold": 0.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "missing",
    }
    StatusCheckFailedSystemAlarmTicket = default_attribute.copy()
    StatusCheckFailedSystemAlarmTicket.update(
        {
            "AlarmName": f'StatusCheckFailedSystemAlarmTicket-{instance["name"]}',
            "AlarmDescription": "Status checks have failed for system, generating ticket.",
            "MetricName": "StatusCheckFailed_System",
        }
    )
    StatusCheckFailedInstanceAlarmTicket = default_attribute.copy()
    StatusCheckFailedInstanceAlarmTicket.update(
        {
            "AlarmName": f'StatusCheckFailedInstanceAlarmTicket-{instance["name"]}',
            "AlarmDescription": "Status checks have failed, generating ticket",
            "MetricName": "StatusCheckFailed_Instance",
            "EvaluationPeriods": 10,
        }
    )
    StatusCheckFailedSystemAlarmRecover = default_attribute.copy()
    StatusCheckFailedSystemAlarmRecover.update(
        {
            "AlarmName": f'StatusCheckFailedSystemAlarmRecover-{instance["name"]}',
            "AlarmDescription": "Status checks have failed for system, recovering instance.",
            "AlarmActions": [f'arn:aws:automate:{instance["region"]}:ec2:recover'],
            "MetricName": "StatusCheckFailed_System",
        }
    )
    StatusCheckFailedInstanceAlarmReboot = default_attribute.copy()
    StatusCheckFailedInstanceAlarmReboot.update(
        {
            "AlarmName": f'StatusCheckFailedInstanceAlarmReboot-{instance["name"]}',
            "AlarmDescription": "Status checks have failed, rebooting system",
            "AlarmActions": [
                f'arn:aws:swf:{instance["region"]}:{instance["account"]}:action/actions/AWS_EC2.InstanceId.Reboot/1.0'
            ],
            "MetricName": "StatusCheckFailed_Instance",
            "EvaluationPeriods": 5,
        }
    )
    CPUHighAlarm = {
        "AlarmName": f'CPU-HighAlarmTicket-{instance["name"]}',
        "AlarmDescription": "CPU Alarm GreaterThanThreshold 90% for 25 minutes.",
        "ActionsEnabled": True,
        "AlarmActions": [
            f'arn:aws:sns:{instance["region"]}:{instance["account"]}:rackspace-support-standard'
        ],
        "MetricName": "CPUUtilization",
        "Namespace": "AWS/EC2",
        "Statistic": "Average",
        "Dimensions": [{"Name": "InstanceId", "Value": f'{instance["id"]}'}],
        "Period": 60,
        "EvaluationPeriods": 25,
        "Threshold": 90.0,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "missing",
    }
    default_ec2_monitors = [
        StatusCheckFailedSystemAlarmTicket,
        StatusCheckFailedInstanceAlarmTicket,
        StatusCheckFailedSystemAlarmRecover,
        StatusCheckFailedInstanceAlarmReboot,
        CPUHighAlarm,
    ]
    # print(f'Working on {instance["id"]}')
    return default_ec2_monitors  # [CPUHighAlarm]


def custom_monitors(boto_client, instance: dict):
    #
    # These will be additional monitors ideally under CWAgent namespace
    #
    default_attribute = {
        "ActionsEnabled": True,
        "AlarmActions": [
            f'arn:aws:sns:{instance["region"]}:{instance["account"]}:rackspace-support-standard'
        ],
        "MetricName": "LogicalDisk % Free Space",
        "Namespace": "CWAgent",
        "Statistic": "Average",
        "Period": 300,
        "EvaluationPeriods": 5,
        "DatapointsToAlarm": 5,
        "Threshold": 10.0,
        "ComparisonOperator": "LessThanThreshold",
        "TreatMissingData": "missing",
    }
    MermoryHighAlarm = default_attribute.copy()
    MermoryHighAlarm.update(
        {
            "AlarmName": f'Memory-HighAlarmTicket-{instance["name"]}',
            "AlarmDescription": "Memory usages has been over 90% for 25 minutes",
            "Dimensions": [{"Name": "InstanceId", "Value": f'{instance["id"]}'}],
        }
    )
    DiskHighAlarm = default_attribute.copy()
    alerts_to_add = [MermoryHighAlarm]
    for volume in get_all_volumes(boto_client, instance):
        DiskHighAlarm = default_attribute.copy()
        DiskHighAlarm.update(
            {
                "AlarmName": f'DiskUsageHighAlarmTicket-{instance["name"]}-{volume}',
                "AlarmDescription": f"Disk usages for {volume} has been over 90% for 25 minutes",
                "Dimensions": [
                    {"Name": "InstanceId", "Value": f'{instance["id"]}'},
                    {"Name": "instance", "Value": f"{volume}"},
                    {"Name": "objectname", "Value": "LogicalDisk"},
                ],
            }
        )
        alerts_to_add.append(DiskHighAlarm)
    return alerts_to_add


def rds_monitors(rds_names: dict):
    #
    # rds_names = { 'id': "name", 'region': 'us-east-1', 'account': '12134', 'threashold': 200}
    # threashold should 10% of allocated
    #
    default_attribute = {
        "ActionsEnabled": True,
        "AlarmActions": [
            f'arn:aws:sns:{rds_names["region"]}:{rds_names["account"]}:rackspace-support-emergency'
        ],
        "Namespace": "AWS/RDS",
        "Statistic": "Average",
        "Dimensions": [{"Name": "DBInstanceIdentifier", "Value": f'{rds_names["id"]}'}],
        "Period": 300,
        "Unit": "Count",
        "EvaluationPeriods": 5,
        "DatapointsToAlarm": 5,
        "Threshold": 0.0,
        "ComparisonOperator": "LessThanThreshold",
        "TreatMissingData": "missing",
    }


def get_all_volumes(boto_client, instance: dict, name="CWAgent"):
    #
    # this will return all volumes as a list for which we are collecting metrics under namespace CWAgent (default) for an instance.
    #
    response = boto_client.list_metrics(
        Namespace=name, Dimensions=[{"Name": "InstanceId", "Value": instance["id"]}]
    )
    volume = []
    for metric in response["Metrics"]:
        if "LogicalDisk" in metric["MetricName"]:
            for dim in metric["Dimensions"]:
                if dim["Name"] == "instance":
                    volume.append(dim["Value"])
    return volume


def get_instance_detail(instanceid):
    ec2_client = boto3.client("ec2")
    regions = [
        "us-east-2"
    ]  # [x["RegionName"] for x in ec2_client.describe_regions()["Regions"]]
    result = {}
    for item in regions:
        try:
            regional_client = boto3.client("ec2", region_name=item)
            response = regional_client.describe_instances(InstanceIds=[instanceid])
            name_tag = [
                x
                for x in response["Reservations"][0]["Instances"][0]["Tags"]
                if x["Key"] == "Name"
            ]
            name = name_tag[0]["Value"] if name_tag else instanceid
            if not name:
                name = instanceid
            result = {
                "name": name.strip(),
                "id": instanceid,
                "region": item,
            }
            break
        except botocore.exceptions.ClientError:
            pass
        except:
            pass
    return result


def get_account_number():
    sts_client = boto3.client("sts")
    response = sts_client.get_caller_identity()
    return response["Account"]


if __name__ == "__main__":
    account_num = get_account_number()
    # print(account_num)
    # test_id = "i-078923e9b94a43271"
    # print(get_instance_detail(test_id))
    instance_ids = [
        "i-0578114c99894563a",
    ]
    for id in instance_ids:
        instance = get_instance_detail(id)
        print(f'Creating alerts for {instance["id"]} - {instance["name"]}')
        instance["account"] = account_num
        client = boto3.client("cloudwatch", region_name=instance["region"])
        configure_alerts = default_RS_Monitors(instance)
        # configure_alerts += custom_monitors(client, instance)
        for alerts in configure_alerts:
            configure_monitor(client, alerts)
    # instance = {
    #     "id": "i-0059c8ef4f6bccfcd",
    #     "region": "us-east-1",
    #     "account": 167718459780,
    #     "name": "prabin",
    # }
    # client = boto3.client("cloudwatch", region_name="us-east-1")
    # custom_monitors(client, instance)
