import json
import subprocess
import datetime
from threading import Thread


desired_descriptions = [
    "CINE EC 2",
    "rEIXO_CURTO",
    "SHORT_AXIS",
    "SHORT AXIS",
    "SA CINE",
    "CINE SA",
    "CINE_SHORT_AXIS",
    "CINE SA 2",
    "EIXO_CURTO",
    "EIXO_CURTO_CINE",
    "EC EIXO_CURTO",
    "R_EIXO_CURTO",
    "R EIXO CURTO",
    "SX CINE SA",
    "CINE EC SHORT AXIS"
]


def run_fargate_task(api_data):

    def _run():

        json_str = json.dumps(api_data, separators=(",", ":"))
        started_by = f"temporary-run-{int(datetime.datetime.now().timestamp())}"

        region = "us-east-2"
        cluster = "fe-cluster"
        task_definition = "fe-5-nov2025"
        subnet_id = "subnet-0a068dd9915049166"

        overrides = {
            "containerOverrides": [
                {
                    "name": task_definition,
                    "environment": [
                        {"name": "EXAME_JSON", "value": json_str}
                    ]
                }
            ]
        }

        network_config = {
            "awsvpcConfiguration": {
                "subnets": [subnet_id],
                "assignPublicIp": "ENABLED"
            }
        }

        cmd = [
            "aws", "ecs", "run-task",
            "--region", region,
            "--cluster", cluster,
            "--launch-type", "FARGATE",
            "--task-definition", task_definition,
            "--network-configuration", json.dumps(network_config),
            "--started-by", started_by,
            "--overrides", json.dumps(overrides)
        ]

        try:
            print("\n🛰️ Running AWS Fargate:")
            print(" ".join(cmd))

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(timeout=25)

            if process.returncode == 0:
                print("✅ Fargate started successfully for:", started_by)
                print(stdout)
            else:
                print("❌ Fargate failed:", started_by)
                print(stderr)

        except Exception as e:
            print("❌ Error running Fargate:", str(e))

    # ✅ DISPARA EM SEGUNDO PLANO (não trava o Flask)
    Thread(target=_run, daemon=True).start()

    return 



     

