
def diagnose_ec2(
    cpu_percent=None,
    memory_percent=None,
    disk_percent=None,
    instance_state=None,
    system_status=None,
    instance_status=None
):
    """Analyze EC2 metrics and return troubleshooting recommendations."""

    issues = []
    missing_metrics = []

    # Identify missing diagnostic information
    if cpu_percent is None:
        missing_metrics.append("CPU")
    if memory_percent is None:
        missing_metrics.append("Memory")
    if disk_percent is None:
        missing_metrics.append("Disk")
    if instance_state is None:
        missing_metrics.append("EC2 instance state")
    if system_status is None:
        missing_metrics.append("System health")
    if instance_status is None:
        missing_metrics.append("Instance health")

    # Check EC2 instance state
    if instance_state and instance_state != "running":
        issues.append({
            "severity": "Critical",
            "issue": f"EC2 instance is {instance_state}.",
            "possible_cause": (
                "The instance may be stopped or transitioning states."
            ),
            "recommendation": (
                "Check the instance state and review recent AWS actions."
            )
        })

    # Check AWS system health
    if system_status and system_status != "ok":
        issues.append({
            "severity": "Critical",
            "issue": f"AWS system status is {system_status}.",
            "possible_cause": (
                "There may be an issue with the underlying host "
                "or AWS infrastructure."
            ),
            "recommendation": (
                "Review EC2 status checks and AWS Health events."
            )
        })

    # Check EC2 instance health
    if instance_status and instance_status != "ok":
        issues.append({
            "severity": "High",
            "issue": f"Instance status check is {instance_status}.",
            "possible_cause": (
                "The operating system or instance networking may be unhealthy."
            ),
            "recommendation": (
                "Review system logs, networking, and instance status checks."
            )
        })

    # Check CPU usage
    if cpu_percent is not None:
        if cpu_percent >= 90:
            issues.append({
                "severity": "High",
                "issue": f"Very high CPU utilization: {cpu_percent}%.",
                "possible_cause": (
                    "A heavy workload, inefficient process, "
                    "or unexpected traffic."
                ),
                "recommendation": (
                    "Inspect running processes and application logs "
                    "before considering scaling."
                )
            })
        elif cpu_percent >= 80:
            issues.append({
                "severity": "Medium",
                "issue": f"High CPU utilization: {cpu_percent}%.",
                "possible_cause": (
                    "The workload may be approaching the instance's capacity."
                ),
                "recommendation": (
                    "Check CPU trends and running processes."
                )
            })

    # Check memory usage
    if memory_percent is not None:
        if memory_percent >= 90:
            issues.append({
                "severity": "High",
                "issue": f"Very high memory usage: {memory_percent}%.",
                "possible_cause": (
                    "Memory-intensive processes or insufficient available RAM."
                ),
                "recommendation": (
                    "Inspect processes and system logs; check for "
                    "out-of-memory events."
                )
            })
        elif memory_percent >= 80:
            issues.append({
                "severity": "Medium",
                "issue": f"High memory usage: {memory_percent}%.",
                "possible_cause": (
                    "Applications may be using most available memory."
                ),
                "recommendation": (
                    "Monitor available memory and identify processes "
                    "consuming RAM."
                )
            })

    # Check disk usage
    if disk_percent is not None:
        if disk_percent >= 90:
            issues.append({
                "severity": "High",
                "issue": f"Disk usage is critically high: {disk_percent}%.",
                "possible_cause": (
                    "Logs, temporary files, or application data "
                    "may be filling the disk."
                ),
                "recommendation": (
                    "Identify large files and review log rotation "
                    "before deleting anything."
                )
            })
        elif disk_percent >= 80:
            issues.append({
                "severity": "Medium",
                "issue": f"Disk usage is high: {disk_percent}%.",
                "possible_cause": "Disk space is running low.",
                "recommendation": (
                    "Check disk usage and consider monitoring or log rotation."
                )
            })

    # Report missing diagnostic information
    if missing_metrics:
        issues.append({
            "severity": "Incomplete",
            "issue": (
                "Some diagnostic checks are missing: "
                + ", ".join(missing_metrics)
            ),
            "possible_cause": (
                "Some metrics or EC2 health statuses could not "
                "be retrieved or were not supplied."
            ),
            "recommendation": (
                "Retry failed checks and review AWS permissions, "
                "CloudWatch metric availability, and SSM connectivity."
            )
        })

    # Report healthy results when all checks are available
    if not issues:
        issues.append({
            "severity": "Healthy",
            "issue": "No threshold-based problems detected.",
            "possible_cause": (
                "The available metrics and statuses are within "
                "the configured thresholds."
            ),
            "recommendation": (
                "Continue monitoring. This does not guarantee that "
                "every application or cloud service is working."
            )
        })

    return issues


def diagnose_service(service, diagnostic_data=None):
    """Return troubleshooting recommendations for a selected service."""

    diagnostic_data = diagnostic_data or {}
    issues = []

    # EC2 troubleshooting
    if service == "EC2":
        return diagnose_ec2(**diagnostic_data)

    # S3 troubleshooting
    elif service == "S3":
        if diagnostic_data.get("success") is False:
            issues.append({
                "severity": "High",
                "issue": "Could not retrieve S3 bucket information.",
                "possible_cause": (
                    "AWS credentials, permissions, or the S3 API request "
                    "may be causing the failure."
                ),
                "recommendation": (
                    "Check AWS credentials and the "
                    "s3:ListAllMyBuckets permission."
                )
            })

        elif diagnostic_data.get("success") is True:
            buckets = diagnostic_data.get("buckets", [])
            issues.append({
                "severity": "Healthy",
                "issue": (
                    "S3 bucket inventory retrieved successfully. "
                    f"Found {len(buckets)} bucket(s)."
                ),
                "possible_cause": (
                    "The bucket-listing request completed successfully. "
                    "Individual bucket configurations have not been checked."
                ),
                "recommendation": (
                    "For deeper checks, review bucket access, policies, "
                    "encryption, and public-access settings."
                )
            })

        else:
            issues.append({
                "severity": "Incomplete",
                "issue": "S3 diagnostic data is missing.",
                "possible_cause": "No S3 inventory result was supplied.",
                "recommendation": "Run the S3 bucket inventory check first."
            })

    # CloudWatch is not integrated yet
    
    # CloudWatch troubleshooting
    elif service == "CloudWatch":
        if diagnostic_data.get("success") is False:
            issues.append({
                "severity": "High",
                "issue": "Could not retrieve CloudWatch alarms.",
                "possible_cause": (
                    "AWS credentials, permissions, or the CloudWatch "
                    "API request may be causing the failure."
                ),
                "recommendation": (
                    "Check AWS credentials and the "
                    "cloudwatch:DescribeAlarms permission."
                )
            })

        elif diagnostic_data.get("success") is True:
            alarms = diagnostic_data.get("alarms", [])

            if not alarms:
                issues.append({
                    "severity": "Info",
                    "issue": "No existing CloudWatch alarms were found.",
                    "possible_cause": (
                        "There are no alarms in the retrieved results "
                        "for the selected AWS region."
                    ),
                    "recommendation": (
                        "Review available CloudWatch metrics if you need "
                        "to investigate a specific service problem. "
                        "No alarm needs to be created for this check."
                    )
                })

            else:
                for alarm in alarms:
                    state = alarm.get("state", "UNKNOWN")

                    if state == "ALARM":
                        severity = "High"
                        recommendation = (
                            "Review the alarm reason and related metrics "
                            "to investigate the reported condition."
                        )
                    elif state == "OK":
                        severity = "Healthy"
                        recommendation = (
                            "The alarm is currently OK. Review other "
                            "metrics and logs if the problem continues."
                        )
                    else:
                        severity = "Warning"
                        recommendation = (
                            "Check the alarm reason and metric data "
                            "to understand why the alarm state is "
                            "not confirmed as OK."
                        )

                    issues.append({
                        "severity": severity,
                        "issue": (
                            f"Alarm '{alarm.get('alarm_name', 'Unknown')}' "
                            f"is in state {state}."
                        ),
                        "possible_cause": alarm.get(
                            "reason",
                            "No alarm reason was provided."
                        ),
                        "recommendation": recommendation
                    })

        else:
            issues.append({
                "severity": "Incomplete",
                "issue": "CloudWatch diagnostic data is missing.",
                "possible_cause": (
                    "No CloudWatch alarm results were supplied."
                ),
                "recommendation": (
                    "Run the CloudWatch alarm check first."
                )
            })

    # Any other service
    else:
        issues.append({
            "severity": "Incomplete",
            "issue": f"{service} diagnostics are not integrated yet.",
            "possible_cause": "No diagnostic handler exists for this service.",
            "recommendation": (
                "Add service-specific diagnostic checks before "
                "generating troubleshooting recommendations."
            )
        })

    return issues
