
import streamlit as st
from diagnostics import check_website
from aws_diagnostics import (
    check_ec2_instances,
    check_ec2_health,
    check_ec2_cpu,
    check_ec2_memory_disk,
    check_s3_buckets,
    check_cloudwatch_alarms,
    analyze_cpu_usage,
    analyze_s3_buckets,
    analyze_cloudwatch_alarms,
    generate_overall_analysis
)
from troubleshooter import diagnose_ec2, diagnose_service
if "history" not in st.session_state:
    st.session_state.history = []
st.set_page_config(
    page_title="Cloud Failure Lab",
    page_icon="☁️",
    layout="wide"
)

st.markdown(
    """
    <style>
    /* Main application background and spacing */
    .stApp {
        background: linear-gradient(
            135deg, #080D1B 0%, #0B1020 55%, #11152B 100%
        );
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg, #10172A 0%, #0B1020 100%
        );
        border-right: 1px solid #263451;
    }

    [data-testid="stSidebar"] h1 {
        color: #C4B5FD;
        font-weight: 800;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(
            145deg, #151F35, #111827
        );
        border: 1px solid #293957;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.16);
    }

    [data-testid="stMetricLabel"] {
        color: #A5B4FC;
    }

    [data-testid="stMetricValue"] {
        color: #F8FAFC;
        font-weight: 750;
    }

    /* Buttons */
    .stButton > button {
        border: 1px solid #6551C7;
        border-radius: 10px;
        min-height: 44px;
        font-weight: 650;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(
            100deg, #7047F5, #4F46E5
        );
        color: white;
        border: none;
    }

    .stButton > button:hover {
        border-color: #A78BFA;
        color: white;
        box-shadow: 0 0 18px rgba(139, 92, 246, 0.22);
    }

    /* Cards and bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #293957;
        border-radius: 16px;
        background: rgba(17, 27, 48, 0.65);
    }

    /* Inputs and select boxes */
    [data-testid="stTextInput"] input {
        border-radius: 10px;
    }

    [data-testid="stSelectbox"] > div > div {
        border-radius: 10px;
    }

    /* Headings and separators */
    h1, h2, h3 {
        letter-spacing: -0.4px;
    }

    hr {
        border-color: #293957;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# AWS Connection
st.markdown("### ☁️ AWS Account Connection")
st.caption("Connect or disconnect the AWS identity used by Cloud Failure Lab.")

import boto3
from botocore.exceptions import BotoCoreError, ClientError

if "aws_connected" not in st.session_state:
    st.session_state.aws_connected = False

if "aws_identity" not in st.session_state:
    st.session_state.aws_identity = None

if st.button("🔗 Connect to AWS", key="connect_aws"):
    try:
        session = boto3.Session(region_name="us-east-1")
        identity = session.client("sts").get_caller_identity()

        st.session_state.aws_identity = identity
        st.session_state.aws_connected = True

    except (BotoCoreError, ClientError) as error:
        st.session_state.aws_identity = None
        st.session_state.aws_connected = False
        st.error("AWS connection failed. Check your AWS login.")
        st.caption(str(error))

if st.session_state.aws_connected and st.session_state.aws_identity:
    identity = st.session_state.aws_identity

    st.success("Connected to AWS successfully!")
    st.write("**Account ID:**", identity["Account"])
    st.write("**Authenticated identity:**", identity["Arn"])
    st.write("**Region:** us-east-1")

    if st.button("🔌 Disconnect AWS", key="disconnect_aws"):
        st.session_state.aws_connected = False
        st.session_state.aws_identity = None
        st.rerun()
else:
    st.info("AWS is disconnected from the app. Click Connect to AWS to check your current login.")



st.markdown(
    """
    <div style="padding: 8px 0 18px 0;">
        <div style="font-size: 13px; color: #A78BFA;
                    letter-spacing: 3px; font-weight: 700;">
            CLOUD OPERATIONS PLATFORM
        </div>
        <div style="font-size: 34px; font-weight: 800;
                    color: #F1F5F9; margin-top: 5px;">
            ☁️ Cloud Failure Lab
        </div>
        <div style="font-size: 15px; color: #94A3B8;
                    margin-top: 5px;">
            Diagnose failures. Understand the cause. Restore confidence.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.title("Cloud Failure Lab")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Failure Labs", "Troubleshooting History"]
)

if page == "Dashboard":
    st.header("Cloud Dashboard")
    st.write("Monitor servers and investigate infrastructure failures.")
    
    st.markdown(
        """
        <div style="color:#94A3B8; font-size:15px; margin-bottom:18px;">
            Monitor infrastructure health, investigate incidents, and
            diagnose cloud failures from one workspace.
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("☁️ Servers Monitored", "1", "EC2")

    with col2:
        st.metric("⚠️ Active Incidents", "0", "No incidents recorded")

    with col3:
        st.metric("✓ Issues Resolved", "0", "Session total")

    
    st.divider()

    st.markdown(
        """
        <div style="margin-bottom: 22px;">
            <div style="font-size: 12px; color: #A78BFA;
                        font-weight: 700; letter-spacing: 2px;">
                AWS MONITORING
            </div>
            <div style="font-size: 27px; font-weight: 800;
                        color: #F1F5F9; margin-top: 5px;">
                ☁️ Live EC2 Diagnostics
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 6px;">
                Inspect compute performance, instance health,
                infrastructure inventory, and system resources.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    # Discover EC2 instances automatically
    aws_result = check_ec2_instances()

    if aws_result["success"]:
        instances = aws_result["instances"]

        if instances:
            instance_options = {
               f'{i["instance_id"]} ({i["state"]})': i["instance_id"]
               for i in instances
            }

            selected_instance = st.selectbox(
                "Select EC2 Instance",
                options=list(instance_options.keys())
            )

            selected_instance_id = instance_options[selected_instance]

        else:
            selected_instance_id = None
            st.info("No EC2 instances found in us-east-1.")
            

    else:
        selected_instance_id = None
        st.warning("AWS instance discovery is unavailable.")
        st.error(aws_result.get("message", "Unknown AWS error"))
    
    diagnostic_cards = [
        {
            "title": "CPU Usage",
            "icon": "⚡",
            "description": "Inspect recent CPU utilization and identify high workloads.",
            "button": "Check CPU Usage"
        },
        {
            "title": "EC2 Health",
            "icon": "💚",
            "description": "Verify instance state and AWS system status checks.",
            "button": "Check EC2 Health"
        },
        {
            "title": "AWS Instances",
            "icon": "🖥️",
            "description": "View your EC2 inventory and count running instances.",
            "button": "Check AWS Instances"
        },
        {
            "title": "Memory & Disk",
            "icon": "💾",
            "description": "Inspect RAM usage and available disk capacity through SSM.",
            "button": "Check Memory & Disk"
        }

    ]

    diagnostic_col1, diagnostic_col2 = st.columns(2, gap="medium")

    for index, card in enumerate(diagnostic_cards):
        current_col = diagnostic_col1 if index % 2 == 0 else diagnostic_col2

        with current_col:
            with st.container(border=True):
                st.markdown(
                    f"""
<div style="padding: 0 0 4px 0;">
    <div style="font-size: 22px; margin-bottom: 6px;">
        {card["icon"]}
    </div>
    <div style="font-size: 17px; font-weight: 700;
                color: #F1F5F9; margin-bottom: 5px;">
        {card["title"]}
    </div>
    <div style="font-size: 13px; line-height: 1.5;
                color: #94A3B8; min-height: 38px;">
        {card["description"]}
    </div>
</div>
""",
unsafe_allow_html=True
                )

                
                if st.button(
                    card["button"],
                    key=f"diagnostic_{index}",
                    use_container_width=True,
                    type="secondary"
                ):
                    if index in (0, 1, 3) and not selected_instance_id:
                        st.warning(
                            "No EC2 instance is available. "
                            "These diagnostics require a selected EC2 instance."
                        )
                    elif index == 0:
                        with st.spinner("Fetching CPU metrics..."):
                            cpu_result = check_ec2_cpu(
                                selected_instance_id
                            )

                    

                        if cpu_result["success"]:
                            st.metric(
                                "EC2 CPU Utilization",
                                f'{cpu_result["cpu_percent"]}%'
                            )

                            st.caption(
                                f'Latest available reading: {cpu_result["timestamp"]}'
                            )

                            if cpu_result["cpu_percent"] >= 80:
                                st.warning(
                                    "High CPU usage detected. Investigate the workload."
                                )
                            else:
                                st.success(
                                    "CPU utilization is below the high-usage threshold."
                                )
                        else:
                            st.info(cpu_result["message"])

                    elif index == 1:
                        with st.spinner("Checking EC2 health..."):
                            health = check_ec2_health(
                                selected_instance_id
                            )

                        if health["success"]:
                            st.markdown("### EC2 Health Results")

                            st.write("Instance ID:", health["instance_id"])
                            st.write("Instance State:", health["instance_state"])
                            st.write("System Status:", health["system_status"])
                            st.write("Instance Status:", health["instance_status"])

                            if (
                                health["instance_state"] == "running"
                                and health["system_status"] == "ok"
                                and health["instance_status"] == "ok"
                            ):
                                st.success("Your EC2 instance is healthy!")
                            else:
                                st.warning(
                                    "EC2 needs attention. Review the status results."
                                )
                        else:
                            st.error("Could not check EC2 health.")
                            st.write(health["message"])

                    elif index == 2:
                        with st.spinner("Connecting to AWS..."):
                            aws_result = check_ec2_instances()

                        if aws_result["success"]:
                            instances = aws_result["instances"]

                            st.success(
                                f"Connected to AWS! Found {len(instances)} instance(s)."
                            )

                            if instances:
                                st.dataframe(
                                    instances,
                                    use_container_width=True
                                )

                                running_count = sum(
                                    1 for instance in instances
                                    if instance["state"] == "running"
                                )

                                st.metric(
                                    "Running EC2 Instances",
                                    running_count
                                )
                            else:
                                st.info(
                                    "No EC2 instances found in us-east-1."
                                )
                        else:
                            st.error(
                                "Could not retrieve AWS instance information."
                            )
                            st.write(aws_result["message"])

                    elif index == 3:
                        with st.spinner(
                            "Fetching live memory and disk information through SSM..."
                        ):
                            resource_result = check_ec2_memory_disk(
                               selected_instance_id
                            )

                        if resource_result["success"]:
                            import re

                            output = resource_result["output"]

                            memory = re.search(
                                r"Mem:\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+(\d+)",
                                output
                            )

                            disk = re.search(
                                r"/dev/root\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%",
                                output
                            )

                            st.subheader("EC2 Resource Monitoring")

                            if memory and disk:
                                total_mem, used_mem, free_mem, available_mem = map(
                                    int, memory.groups()
                                )

                                total_disk, used_disk, available_disk, disk_percent = map(
                                    int, disk.groups()
                                )

                                mem_percent = round(
                                    used_mem / total_mem * 100, 1
                                )

                                memory_col, disk_col = st.columns(2)

                                with memory_col:
                                    st.markdown("### 🧠 Memory")
                                    st.metric("Memory Used", f"{mem_percent}%")
                                    st.progress(min(int(mem_percent), 100))

                                    st.caption(
                                        f"{used_mem / 1024**3:.2f} GB used "
                                        f"of {total_mem / 1024**3:.2f} GB"
                                    )

                                    st.caption(
                                        f"{available_mem / 1024**3:.2f} GB available"
                                    )

                                with disk_col:
                                    st.markdown("### 💾 Disk")
                                    st.metric("Disk Used", f"{disk_percent}%")
                                    st.progress(min(disk_percent, 100))

                                    st.caption(
                                        f"{used_disk / 1024**3:.2f} GB used "
                                        f"of {total_disk / 1024**3:.2f} GB"
                                    )

                                    st.caption(
                                        f"{available_disk / 1024**3:.2f} GB available"
                                    )

                                st.success(
                                    "Memory and disk diagnostics completed."
                                )
                            else:
                                st.warning(
                                    "Could not interpret the resource output. "
                                    "Please check the command output format."
                                )

                            if "Mem:" in output and "Use%" in output:
                                st.success(
                                    "Memory and disk information retrieved successfully."
                                )
                            else:
                                st.warning(
                                    "Results received, but some metrics may be missing."
                                )
                        else:
                            st.error(
                                "Could not retrieve memory and disk information."
                            )
                            st.write(resource_result["message"])
                    
    st.divider()                 
    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 16px;">
            <div style="font-size: 12px; color: #FBBF24;
                        font-weight: 700; letter-spacing: 2px;">
                OBJECT STORAGE
            </div>
            <div style="font-size: 27px; font-weight: 800;
                        color: #F1F5F9; margin-top: 5px;">
                🪣 S3 Diagnostics
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 5px;">
                Inspect your existing Amazon S3 buckets independently
                of EC2 instances.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown("### S3 Bucket Inventory")
        st.write(
            "View the names and creation dates of your existing S3 buckets."
        )
        
        
        if not st.session_state.get("aws_connected", False):
            st.info("Please connect to AWS before checking S3 buckets.")

        else:
            if st.button(
               "Check S3 Buckets",
                key="check_s3_buckets",
                use_container_width=True
            ):
                with st.spinner("Checking S3 buckets..."):
                    s3_result = check_s3_buckets()

                if s3_result["success"]:
                    buckets = s3_result["buckets"]

                    st.success(
                       f"Connected to S3! Found {len(buckets)} bucket(s)."
                    )

                    if buckets:
                       st.dataframe(
                       buckets,
                       use_container_width=True,
                       hide_index=True
                       )
                    else:
                       st.info("No S3 buckets found in your AWS account.")
                else:
                    st.error("Could not retrieve S3 bucket information.")
                    st.write(s3_result["message"])


    
    
    
    st.divider()
    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 16px;">
            <div style="font-size: 12px; color: #A78BFA;
                        font-weight: 700; letter-spacing: 2px;">
                INTELLIGENT ANALYSIS
            </div>
            <div style="font-size: 24px; font-weight: 750;
                        color: #F1F5F9; margin-top: 5px;">
                🧠 Smart Troubleshooting
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 5px;">
                Analyse live EC2 metrics and get actionable recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    selected_service = st.selectbox(
        "Select a service to troubleshoot",
         ["EC2", "S3", "CloudWatch"]
    )

    
    
    if not st.session_state.get("aws_connected", False):
       st.info("Please connect to AWS before running diagnostics.")
       st.session_state.pop("s3_result", None)
        # Store the latest smart analysis for each service
    if "smart_results" not in st.session_state:
        st.session_state["smart_results"] = {
            "CPU": None,
            "S3": None,
            "CloudWatch": None
        }   
    if st.button(
        f"🔍 Analyse {selected_service} & Generate Recommendations",
        use_container_width=True,
        type="primary",
        disabled=not st.session_state.get("aws_connected", False)
    ):
        
        recommendations = []

        if selected_service == "EC2":
            instance_id = selected_instance_id

            if not instance_id:
                st.warning(
                    "No EC2 instance is available. "
                    "Select an instance before running EC2 troubleshooting."
                )
            else:
                with st.spinner("Collecting live EC2 diagnostic information..."):
                    cpu_result = check_ec2_cpu(instance_id)
                    health_result = check_ec2_health(instance_id)
                    resource_result = check_ec2_memory_disk(instance_id)

                cpu_value = (
                    cpu_result.get("cpu_percent")
                    if cpu_result.get("success")
                    else None
                )
                memory_value = None
                disk_value = None

                if resource_result.get("success"):
                    import re

                    output = resource_result.get("output", "")

                    memory = re.search(
                        r"Mem:\s+(\d+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+(\d+)",
                        output
                    )
                    disk = re.search(
                        r"/dev/root\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)%",
                        output
                    )

                    if memory:
                        total_mem, used_mem, available_mem = map(
                            int, memory.groups()
                        )
                        if total_mem:
                            memory_value = round(
                                used_mem / total_mem * 100, 1
                            )

                    if disk:
                        total_disk, used_disk, available_disk, disk_percent = map(
                            int, disk.groups()
                        )
                        disk_value = disk_percent

                health_values = {}
                if health_result.get("success"):
                    health_values = {
                        "instance_state": health_result["instance_state"],
                        "system_status": health_result["system_status"],
                        "instance_status": health_result["instance_status"]
                    }

                recommendations = diagnose_ec2(
                    cpu_percent=cpu_value,
                    memory_percent=memory_value,
                    disk_percent=disk_value,
                    **health_values
                )
                
                cpu_analysis = analyze_cpu_usage(cpu_result)
                st.session_state["smart_results"]["CPU"] = cpu_analysis

                st.markdown("### 🧠 Smart CPU Monitoring")

                if cpu_analysis["severity"] == "Critical":
                    st.error(
                        f"🔴 {cpu_analysis['status']}: "
                        f"{cpu_analysis['message']}"
                    )
                elif cpu_analysis["severity"] == "Medium":
                    st.warning(
                        f"🟠 {cpu_analysis['status']}: "
                        f"{cpu_analysis['message']}"
                    )
                elif cpu_analysis["status"] == "Normal":
                    st.success(
                        f"🟢 {cpu_analysis['status']}: "
                        f"{cpu_analysis['message']}"
                    )
                else:
                    st.info(
                        f"ℹ️ {cpu_analysis['status']}: "
                        f"{cpu_analysis['message']}"
                    )

                st.write("**Smart recommendation:**")
                st.write(cpu_analysis["recommendation"])


                st.markdown("### 📊 Live EC2 Diagnostic Summary")

                metric1, metric2, metric3, metric4 = st.columns(4)

                with metric1:
                    st.metric(
                        "⚡ CPU Usage",
                        f"{cpu_value}%" if cpu_value is not None else "Unavailable"
                    )

                with metric2:
                    st.metric(
                        "🧠 Memory Used",
                        f"{memory_value}%" if memory_value is not None else "Unavailable"
                    )

                with metric3:
                    st.metric(
                        "💾 Disk Used",
                        f"{disk_value}%" if disk_value is not None else "Unavailable"
                    )

                with metric4:
                    if health_values:
                        healthy = (
                            health_values["instance_state"] == "running"
                            and health_values["system_status"] == "ok"
                            and health_values["instance_status"] == "ok"
                        )
                        st.metric(
                            "☁️ EC2 Health",
                            "Healthy" if healthy else "Needs Attention"
                        )
                    else:
                        st.metric("☁️ EC2 Health", "Unavailable")

        
        elif selected_service == "S3":
            with st.spinner("Checking S3 bucket inventory..."):
                s3_result = check_s3_buckets()

            s3_analysis = analyze_s3_buckets(s3_result)
            st.session_state["smart_results"]["S3"] = s3_analysis

            st.markdown("### 🧠 Smart S3 Monitoring")

            if s3_analysis["severity"] == "Warning":
                st.warning(
                    f'{s3_analysis["status"]}: '
                    f'{s3_analysis["message"]}'
                )
            elif s3_analysis["status"] == "Inventory Available":
                st.success(
                    f'{s3_analysis["status"]}: '
                    f'{s3_analysis["message"]}'
                )
            else:
                st.info(
                    f'{s3_analysis["status"]}: '
                    f'{s3_analysis["message"]}'
                )

            st.write("**Smart recommendation:**")
            st.write(s3_analysis["recommendation"])

            recommendations = diagnose_service(
                "S3",
                diagnostic_data=s3_result
            )

            if s3_result.get("success"):
                buckets = s3_result.get("buckets", [])
                if buckets:
                    st.dataframe(
                        buckets,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info(
                        "No S3 buckets were found in this AWS account."
                    )
            else:
                st.error(
                    "S3 check failed: "
                    + s3_result.get("message", "Unknown error")
                )


        
        
        elif selected_service == "CloudWatch":
            with st.spinner("Checking CloudWatch alarms..."):
                cloudwatch_result = check_cloudwatch_alarms()

            cloudwatch_analysis = analyze_cloudwatch_alarms(
                cloudwatch_result
            )
            st.session_state["smart_results"]["CloudWatch"] = cloudwatch_analysis

            st.markdown("### 🧠 Smart CloudWatch Monitoring")

            if cloudwatch_analysis["severity"] == "Critical":
                st.error(
                    f'{cloudwatch_analysis["status"]}: '
                    f'{cloudwatch_analysis["message"]}'
                )
            elif cloudwatch_analysis["severity"] == "Warning":
                st.warning(
                    f'{cloudwatch_analysis["status"]}: '
                    f'{cloudwatch_analysis["message"]}'
                )
            else:
                st.info(
                    f'{cloudwatch_analysis["status"]}: '
                    f'{cloudwatch_analysis["message"]}'
                )

            st.write("**Smart recommendation:**")
            st.write(cloudwatch_analysis["recommendation"])

            recommendations = diagnose_service(
                "CloudWatch",
                diagnostic_data=cloudwatch_result
            )

            if cloudwatch_result.get("success"):
                alarms = cloudwatch_result.get("alarms", [])

                if alarms:
                    st.dataframe(
                        alarms,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No existing CloudWatch alarms were found.")
            else:
                st.error(
                    "CloudWatch check failed: "
                    + cloudwatch_result.get("message", "Unknown error")
                )


        # Display recommendations for the selected service.
        if recommendations:
            st.subheader("🔍 Troubleshooting Results")

            for item in recommendations:
                severity = item.get("severity", "Info")

                if severity in ("Critical", "High"):
                    st.error(
                        f"{severity}: {item.get('issue', 'No details available')}"
                    )
                elif severity in ("Medium", "Incomplete", "Warning"):
                    st.warning(
                        f"{severity}: {item.get('issue', 'No details available')}"
                    )
                else:
                    st.success(
                        f"{severity}: {item.get('issue', 'No details available')}"
                    )

                st.write(
                    "**Possible cause:**",
                    item.get("possible_cause", "Not available")
                )
                st.write(
                    "**Recommendation:**",
                    item.get("recommendation", "Not available")
                )
                st.divider()
        
        # Overall Smart Analysis
        st.subheader("🧠 Overall Smart Analysis")

        smart_results = st.session_state.get("smart_results", {})

        overall_analysis = generate_overall_analysis(
            cpu_analysis=smart_results.get("CPU"),
            s3_analysis=smart_results.get("S3"),
            cloudwatch_analysis=smart_results.get("CloudWatch")
        )

        status = overall_analysis["status"]

        if status == "Critical":
            st.error(f"🔴 Overall Status: {status}")
        elif status == "Warning":
            st.warning(f"🟠 Overall Status: {status}")
        elif status == "No Data":
            st.info("ℹ️ No smart analysis results available yet.")
        elif status == "Incomplete":
            st.warning(f"🟡 Overall Status: {status}")
        else:
            st.info(f"ℹ️ Overall Status: {status}")

        if overall_analysis["findings"]:
            st.markdown("#### Findings")
            for finding in overall_analysis["findings"]:
                st.write(f"- {finding}")

            st.markdown("#### Recommendations")
            for recommendation in overall_analysis["recommendations"]:
                st.write(f"- {recommendation}")





    

    st.divider()
    
    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 16px;">
            <div style="font-size: 12px; color: #60A5FA;
                        font-weight: 700; letter-spacing: 2px;">
                WEBSITE MONITORING
            </div>
            <div style="font-size: 24px; font-weight: 750;
                        color: #F1F5F9; margin-top: 5px;">
                🌐 Website Diagnostics
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 5px;">
                Check website availability and understand HTTP errors.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    with st.container(border=True, key="website_diagnostics_card"):
        url = st.text_input(
            "Enter website URL",
            placeholder="https://example.com",
            help="Enter a complete website address starting with https:// or http://"
        )


        if st.button("Check Website", use_container_width=True):
            if not url.startswith(("http://", "https://")):
                st.error("Enter a valid URL starting with http:// or https://")
            else:
                with st.spinner("Checking website..."):
                    result = check_website(url)

                st.markdown("### 📋 Website Check Results")

                
                if result["status"] == "HEALTHY":
                    st.success("🟢 WEBSITE ONLINE")
                    st.write(result["message"])
                elif result["status"] == "UNREACHABLE":
                    st.error("🔴 WEBSITE UNREACHABLE")
                    st.write(result["message"])
                else:
                    st.warning("🟡 WEBSITE ERROR")
                    st.write(result["message"])


                st.write("**Status:**", result["status"])
                st.write("**HTTP Code:**", result["http_code"])
                st.subheader("Troubleshooting Advice")
                if result["status"] == "HEALTHY":
                    st.success("The website is responding normally.")
                    st.write("Suggestion: Continue monitoring the website.")
                elif result["status"] == "UNREACHABLE":
                    st.warning("The website could not be reached.")
                    st.write("Possible causes:")
                    st.write("- Incorrect website URL")
                    st.write("- Internet or DNS problem")
                    st.write("- Connection timeout")
                    st.write("Suggestion: Check the URL and your internet connection.") 
                else:
                    st.warning("The website returned an error.")
                    st.write("Possible cause: The website may be returning an HTTP error.")
                    st.write("Suggestion: Check the HTTP code and the website's configuration.")



elif page == "Failure Labs":
    
    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 20px;">
            <div style="font-size: 12px; color: #A78BFA;
                        font-weight: 700; letter-spacing: 2px;">
                SIMULATED INCIDENTS
            </div>
            <div style="font-size: 26px; font-weight: 750;
                        color: #F1F5F9; margin-top: 5px;">
                🧪 Failure Labs
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 5px;">
                Practise diagnosing cloud and website failures in a safe,
                simulated environment.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    
    with st.container(border=True):
        st.markdown("### 🔧 Configure Failure Scenario")
        st.caption(
            "Choose a simulated incident to practise diagnosing."
        )

        scenario = st.selectbox(
            "Choose a test scenario",
            [
                "Healthy Website",
                "HTTP 500 - Server Error",
                "Website Unreachable"
            ]
        )


    
    if st.button(
        "🧪 Run Failure Simulation",
        use_container_width=True,
        type="primary"
    ):

        if scenario == "Healthy Website":
            status = "HEALTHY"
            advice = "Continue monitoring the website."

        elif scenario == "HTTP 500 - Server Error":
            status = "SERVER ERROR"
            advice = "Check application logs and server configuration."

        else:
            status = "UNREACHABLE"
            advice = "Check network connectivity, DNS, and server availability."

        st.session_state.history.append({
            "Scenario": scenario,
            "Status": status,
            "Advice": advice
        })

        
        st.markdown("### 📊 Simulation Results")

        with st.container(border=True):
            st.markdown("**Scenario**")
            st.write(scenario)

            st.markdown("**Status**")
            if status == "HEALTHY":
                st.success("🟢 HEALTHY")
            elif status == "SERVER ERROR":
                st.error("🔴 SERVER ERROR")
            else:
                st.warning("🟡 UNREACHABLE")

            st.markdown("**Recommended Action**")
            st.info(advice)


else:
    
    st.markdown(
        """
        <div style="margin-top: 10px; margin-bottom: 16px;">
            <div style="font-size: 12px; color: #A78BFA;
                        font-weight: 700; letter-spacing: 2px;">
                ACTIVITY CENTRE
            </div>
            <div style="font-size: 26px; font-weight: 750;
                        color: #F1F5F9; margin-top: 5px;">
                📋 Troubleshooting History
            </div>
            <div style="font-size: 14px; color: #94A3B8;
                        margin-top: 5px;">
                Review your previous tests and troubleshooting results.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    
    if st.session_state.history:
        st.metric(
            "📝 Total Troubleshooting Records",
            len(st.session_state.history)
        )

        st.dataframe(
            st.session_state.history,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No troubleshooting history yet. Run a test in Failure Labs.")

