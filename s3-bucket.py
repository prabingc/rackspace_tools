import boto3


def get_all_bucket(client):
    response = client.list_buckets()
    result = [bucket["Name"] for bucket in response["Buckets"]]
    return result


def print_inventory_config(client):
    for bucket in get_all_bucket(client):
        response = client.list_bucket_inventory_configurations(Bucket=bucket)
        config = response.get("InventoryConfigurationList", 0)
        if config and len(response["InventoryConfigurationList"]) > 1:
            print(
                f'bucket: {bucket} IncludedObjectVersions: {response["InventoryConfigurationList"]}'
            )
        elif config and len(response["InventoryConfigurationList"]) == 1:
            print(
                f'bucket: {bucket} IncludedObjectVersions: {response["InventoryConfigurationList"][0]["IncludedObjectVersions"]}'
            )
        else:
            print(f"bucket: {bucket} Inventory is not enabled")


def modify_inventory_config(client):
    config_bucket = {
        "us-east-1": "arn:aws:s3:::651732464523-inventory",
        "us-east-2": "arn:aws:s3:::651732464523-inventory-us-east-2",
        "us-west-2": "arn:aws:s3:::651732464523-inventory-us-west-2",
    }
    default_settings = {
        "Destination": {
            "S3BucketDestination": {
                "AccountId": "651732464523",
                "Bucket": "arn:aws:s3:::651732464523-inventory",
                "Format": "CSV",
            }
        },
        "IsEnabled": True,
        "Id": "daily-inventory-files",
        "IncludedObjectVersions": "Current",
        "OptionalFields": [
            "Size",
            "LastModifiedDate",
            "StorageClass",
            "ETag",
            "IsMultipartUploaded",
            "ReplicationStatus",
            "EncryptionStatus",
            "BucketKeyStatus",
            "IntelligentTieringAccessTier",
            "ObjectLockMode",
            "ObjectLockRetainUntilDate",
            "ObjectLockLegalHoldStatus",
        ],
        "Schedule": {"Frequency": "Daily"},
    }
    bucket_list = [
        "179268807624-us-east-1-migrated-179268807624",
        "1a27ks9b8uxpd-migrated-179268807624-2",
        "651732464523-build-state-bucket",
    ]
    for bucket in get_all_bucket(client):
        # for bucket in bucket_list:
        response = client.list_bucket_inventory_configurations(Bucket=bucket)
        config = response.get("InventoryConfigurationList", 0)
        current_region = "us-east-1"
        print(f"bucket: {bucket}")
        if config:
            if len(config) > 1:
                print(f"\tContains too many inventory config; manual review needed")
            else:
                print(f"\tModifying existing inventory configuration.")

                location_response = client.get_bucket_location(Bucket=bucket)
                new_location = (
                    location_response["LocationConstraint"]
                    if location_response["LocationConstraint"]
                    else "us-east-1"
                )

                if new_location != current_region:
                    default_settings["Destination"]["S3BucketDestination"][
                        "Bucket"
                    ] = config_bucket[new_location]
                    current_region = new_location
                put_response = client.put_bucket_inventory_configuration(
                    Bucket=bucket,
                    Id=response["InventoryConfigurationList"][0]["Id"],
                    InventoryConfiguration=default_settings,
                )
                result = (
                    "success"
                    if put_response["ResponseMetadata"]["HTTPStatusCode"] == 204
                    else "failure"
                )
                print(f"\t\t{result}")

        else:
            print(f"\tDoes not contain any inventory config.")


if __name__ == "__main__":
    s3_client = boto3.client("s3")
    print_inventory_config(s3_client)
    # modify_inventory_config(s3_client)
