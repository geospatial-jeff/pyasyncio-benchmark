import json

import boto3
import requests


def _get_instance_type() -> str:
    """Fetch running instance type from Instance Metadata Service.

    Must be called on a running EC2
    """
    token_url = "http://169.254.169.254/latest/api/token"
    meta_data_instance_id = "http://169.254.169.254/latest/meta-data/instance-type"

    headers = {"X-aws-ec2-metadata-token-ttl-seconds": "21600"}
    response = requests.put(token_url, headers=headers, timeout=1)

    headers = {"X-aws-ec2-metadata-token": response.text}
    response = requests.get(meta_data_instance_id, headers=headers)
    metadata = response.text

    return metadata


def _get_instance_price(instance_type: str):
    """Get hourly price (USD) of instance type in `us-east-1`."""
    client = boto3.client("pricing", region_name="us-east-1")
    data = client.get_products(
        ServiceCode="AmazonEC2",
        Filters=[
            {"Field": "instanceType", "Value": instance_type, "Type": "TERM_MATCH"},
            {"Field": "operatingSystem", "Value": "Linux", "Type": "TERM_MATCH"},
            {"Field": "capacitystatus", "Value": "Used", "Type": "TERM_MATCH"},
            {"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"},
            {"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"},
            {
                "Field": "location",
                "Value": "US East (N. Virginia)",
                "Type": "TERM_MATCH",
            },
        ],
    )
    od = json.loads(data["PriceList"][0])["terms"]["OnDemand"]
    id1 = list(od)[0]
    id2 = list(od[id1]["priceDimensions"])[0]
    price = od[id1]["priceDimensions"][id2]["pricePerUnit"]["USD"]
    return price


def get_ec2_billing_info() -> dict | None:
    """Get hourly price (USD) for running instance."""
    try:
        instance_type = _get_instance_type()
        return {
            "instance_type": instance_type,
            "hourly_cost": _get_instance_price(instance_type),
        }
    except (
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError,
    ):
        # Not running on EC2
        return None
