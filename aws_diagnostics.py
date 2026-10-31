
import boto3
from botocore.exceptions import BotoCoreError, ClientError

def check_ec2_instances():
    try:
        session = boto3.Session(region_name="us-east-1")
        ec2 = session.client("ec2")

        response = ec2.describe_instances()

        instances = []

        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append({
                    "instance_id": instance["InstanceId"],
                    "state": instance["State"]["Name"],
                    "instance_type": instance["InstanceType"]
                })

        return {
            "success": True,
            "instances": instances
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def check_ec2_health(instance_id):
    try:
        session = boto3.Session(region_name="us-east-1")
        ec2 = session.client("ec2")

        response = ec2.describe_instance_status(
            InstanceIds=[instance_id],
            IncludeAllInstances=True
        )

        if not response["InstanceStatuses"]:
            return {
                "success": False,
                "message": "No health status found."
            }

        status = response["InstanceStatuses"][0]

        return {
            "success": True,
            "instance_id": instance_id,
            "instance_state": status["InstanceState"]["Name"],
            "system_status": status["SystemStatus"]["Status"],
            "instance_status": status["InstanceStatus"]["Status"]
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def check_ec2_cpu(instance_id):
    from datetime import datetime, timedelta, timezone

    try:
        session = boto3.Session(region_name="us-east-1")
        cloudwatch = session.client("cloudwatch")

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=3)

        response = cloudwatch.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[
                {
                    "Name": "InstanceId",
                    "Value": instance_id
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=["Average"]
        )

        datapoints = sorted(
            response["Datapoints"],
            key=lambda point: point["Timestamp"]
        )

        if not datapoints:
            return {
                "success": False,
                "message": "No CPU metrics available yet."
            }

        latest = datapoints[-1]["Average"]

        return {
            "success": True,
            "instance_id": instance_id,
            "cpu_percent": round(latest, 2),
            "timestamp": datapoints[-1]["Timestamp"].isoformat()
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def check_cloudwatch_alarms():
    try:
        session = boto3.Session(region_name="us-east-1")
        cloudwatch = session.client("cloudwatch")

        response = cloudwatch.describe_alarms(
            MaxRecords=100
        )

        alarms = []

        for alarm in response.get("MetricAlarms", []):
            alarms.append({
                "alarm_name": alarm["AlarmName"],
                "state": alarm["StateValue"],
                "metric": alarm.get("MetricName", "Unknown"),
                "namespace": alarm.get("Namespace", "Unknown"),
                "reason": alarm.get(
                    "StateReason",
                    "No reason provided"
                )
            })

        for alarm in response.get("CompositeAlarms", []):
            alarms.append({
                "alarm_name": alarm["AlarmName"],
                "state": alarm["StateValue"],
                "metric": "Composite alarm",
                "namespace": "CloudWatch",
                "reason": alarm.get(
                    "StateReason",
                    "No reason provided"
                )
            })

        return {
            "success": True,
            "alarms": alarms
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def check_ec2_memory_disk(instance_id):
    import time
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    try:
        session = boto3.Session(region_name="us-east-1")
        ssm = session.client("ssm")

        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": ["free -b && df -B1 /"]
            }
        )

        command_id = response["Command"]["CommandId"]

        for attempt in range(15):
            time.sleep(2)

            result = ssm.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )

            if result["Status"] == "Success":
                return {
                    "success": True,
                    "output": result["StandardOutputContent"]
                }

            if result["Status"] in [
                "Failed", "Cancelled", "TimedOut"
            ]:
                return {
                    "success": False,
                    "message": result.get(
                        "StandardErrorContent",
                        "SSM command failed."
                    ) or result["Status"]
                }

        return {
            "success": False,
            "message": "Command is taking too long. Please try again."
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def check_s3_buckets():
    try:
        session = boto3.Session(region_name="us-east-1")
        s3 = session.client("s3")
        response = s3.list_buckets()

        buckets = []

        for bucket in response.get("Buckets", []):
            buckets.append({
                "bucket_name": bucket["Name"],
                "creation_date": (
                    bucket["CreationDate"].strftime("%Y-%m-%d")
                    if bucket.get("CreationDate")
                    else "Unknown"
                )
            })

        return {
            "success": True,
            "buckets": buckets
        }

    except (BotoCoreError, ClientError) as error:
        return {
            "success": False,
            "message": str(error)
        }

def analyze_s3_buckets(s3_result):
    """Analyze S3 inventory and provide recommendations."""

    if not s3_result.get("success"):
        return {
            "status": "Unknown",
            "severity": "Warning",
            "message": "Unable to retrieve S3 bucket information.",
            "recommendation": s3_result.get(
                "message", "Check AWS connection and S3 permissions."
            )
        }

    buckets = s3_result.get("buckets", [])
    count = len(buckets)

    if count == 0:
        return {
            "status": "No Buckets Found",
            "severity": "Info",
            "message": "No S3 buckets were found.",
            "recommendation": (
                "Check the AWS account and permissions if you "
                "expected to see buckets."
            )
        }

    return {
        "status": "Inventory Available",
        "severity": "Info",
        "message": f"Successfully retrieved {count} S3 bucket(s).",
        "recommendation": (
            "Review bucket permissions, encryption, versioning, "
            "and lifecycle settings."
        )
    }


def analyze_cloudwatch_alarms(alarm_result):
    """Interpret CloudWatch alarm states and suggest next steps."""

    if not alarm_result.get("success"):
        return {
            "status": "Unknown",
            "severity": "Warning",
            "message": "Unable to retrieve CloudWatch alarms.",
            "recommendation": alarm_result.get(
                "message",
                "Check AWS connection and CloudWatch permissions."
            )
        }

    alarms = alarm_result.get("alarms", [])

    if not alarms:
        return {
            "status": "No Alarms",
            "severity": "Info",
            "message": "No CloudWatch alarms were found.",
            "recommendation": (
                "Consider creating alarms for important metrics "
                "when you have suitable AWS resources."
            )
        }

    alarm_count = sum(
        1 for alarm in alarms
        if alarm.get("state") == "ALARM"
    )

    insufficient_count = sum(
        1 for alarm in alarms
        if alarm.get("state") == "INSUFFICIENT_DATA"
    )

    if alarm_count > 0:
        return {
            "status": "ALARM",
            "severity": "Critical",
            "message": (
                f"{alarm_count} of {len(alarms)} alarm(s) "
                "are in ALARM state."
            ),
            "recommendation": (
                "Review the affected alarm's reason, metric, "
                "and recent resource activity before taking action."
            )
        }

    if insufficient_count > 0:
        return {
            "status": "Insufficient Data",
            "severity": "Warning",
            "message": (
                f"{insufficient_count} alarm(s) have insufficient data."
            ),
            "recommendation": (
                "Check whether the metric is reporting and whether "
                "the alarm has enough recent data."
            )
        }

    return {
        "status": "OK",
        "severity": "Info",
        "message": (
            f"All {len(alarms)} retrieved alarm(s) are outside "
            "the ALARM and INSUFFICIENT_DATA states."
        ),
        "recommendation": (
            "Continue monitoring and review alarm thresholds "
            "periodically."
        )
    }


def generate_overall_analysis(
    cpu_analysis=None,
    s3_analysis=None,
    cloudwatch_analysis=None
):
    """Combine findings from CPU, S3, and CloudWatch."""

    findings = []
    recommendations = []
    analyses = [
        ("CPU", cpu_analysis),
        ("S3", s3_analysis),
        ("CloudWatch", cloudwatch_analysis)
    ]

    for name, analysis in analyses:
        if analysis:
            findings.append(
                f"{name}: {analysis.get('message', 'No details available.')}"
            )
            recommendation = analysis.get("recommendation")
            if recommendation:
                recommendations.append(recommendation)

    if not findings:
        return {
            "status": "No Data",
            "findings": [],
            "recommendations": []
        }

    severities = [
        analysis.get("severity", "Info")
        for _, analysis in analyses
        if analysis
    ]

    if "Critical" in severities:
        status = "Critical"
    elif any(s in severities for s in ["High", "Warning", "Medium"]):
        status = "Warning"
    elif len(analyses) != sum(bool(a) for _, a in analyses):
        status = "Incomplete"
    else:
        status = "Review"

    return {
        "status": status,
        "findings": findings,
        "recommendations": recommendations
    }


def analyze_cpu_usage(cpu_result):
    """Classify EC2 CPU usage for Cloud Failure Lab."""

    if not cpu_result.get("success"):
        return {
            "status": "Unknown",
            "severity": "Warning",
            "message": cpu_result.get(
                "message", "CPU metrics could not be retrieved."
            ),
            "recommendation": "Check the EC2 instance ID and CloudWatch metrics."
        }

    cpu = cpu_result["cpu_percent"]

    if cpu >= 85:
        return {
            "status": "Critical",
            "severity": "Critical",
            "message": f"EC2 CPU usage is very high at {cpu}%.",
            "recommendation": (
                "Investigate running processes and recent workload changes. "
                "Consider scaling only after verifying the cause."
            )
        }

    elif cpu >= 70:
        return {
            "status": "Warning",
            "severity": "Medium",
            "message": f"EC2 CPU usage is elevated at {cpu}%.",
            "recommendation": (
                "Monitor CPU trends and check whether the workload is expected."
            )
        }

    else:
        return {
            "status": "Normal",
            "severity": "Info",
            "message": f"EC2 CPU usage is {cpu}%.",
            "recommendation": "No CPU threshold alert. Continue monitoring."
        }




if __name__ == "__main__":
    print("\n--- Smart S3 Monitoring Test ---")

    sample_s3_result = {
        "success": True,
        "buckets": [
            {"bucket_name": "demo-bucket", "creation_date": "2026-01-01"},
            {"bucket_name": "test-bucket", "creation_date": "2026-02-01"}
        ]
    }

    s3_analysis = analyze_s3_buckets(sample_s3_result)

    print("Status:", s3_analysis["status"])
    print("Severity:", s3_analysis["severity"])
    print("Message:", s3_analysis["message"])
    print("Recommendation:", s3_analysis["recommendation"])

    print("\n--- Smart CPU Monitoring Test ---")

    for cpu in [45, 75, 92]:
        result = analyze_cpu_usage({
            "success": True,
            "cpu_percent": cpu
        })
        print(f"CPU: {cpu}% | Status: {result['status']}")
    
    print("\n--- Smart CloudWatch Monitoring Test ---")

    sample_alarms = {
        "success": True,
        "alarms": [
            {"alarm_name": "High-CPU", "state": "ALARM"},
            {"alarm_name": "Low-Disk", "state": "OK"}
        ]
    }

    analysis = analyze_cloudwatch_alarms(sample_alarms)

    print("Status:", analysis["status"])
    print("Severity:", analysis["severity"])
    print("Message:", analysis["message"])
    print("Recommendation:", analysis["recommendation"])
    
    print("\n--- Overall Smart Analysis Test ---")


    cpu_test = {
        "status": "Critical",
        "severity": "Critical",
        "message": "EC2 CPU usage is very high at 92%.",
        "recommendation": "Investigate high CPU usage."
    }

    s3_test = {
        "status": "Inventory Available",
        "severity": "Info",
        "message": "Successfully retrieved 2 S3 bucket(s).",
        "recommendation": "Review S3 security settings."
    }

    cloudwatch_test = {
        "status": "ALARM",
        "severity": "Critical",
        "message": "1 of 2 alarm(s) are in ALARM state.",
        "recommendation": "Investigate the affected alarm."
    }

    overall = generate_overall_analysis(
        cpu_analysis=cpu_test,
        s3_analysis=s3_test,
        cloudwatch_analysis=cloudwatch_test
    )

    print("Overall Status:", overall["status"])
    print("\nFindings:")
    for finding in overall["findings"]:
        print("-", finding)

    print("\nRecommendations:")
    for recommendation in overall["recommendations"]:
        print("-", recommendation)
