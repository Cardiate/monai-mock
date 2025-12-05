import argparse
import requests
import re
import os
import json
import subprocess
import datetime



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
    """
    Executa uma tarefa Fargate no cluster 'fe-cluster',
    enviando os dados do dicionário api_data como variável EXAME_JSON.
    """
    # Converte o dicionário em JSON compacto
    json_str = json.dumps(api_data, separators=(",", ":"))

    # Nome único para identificar o run
    started_by = f"temporary-run-{int(datetime.datetime.now().timestamp())}"

    # Configurações fixas
    region = "us-east-2"
    cluster = "fe-cluster"
    task_definition = "fe-5-nov2025"
    subnet_id = "subnet-0a068dd9915049166"

    # Monta o JSON equivalente ao jq --overrides
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

    # Configuração de rede no formato correto JSON
    network_config = {
        "awsvpcConfiguration": {
            "subnets": [subnet_id],
            "assignPublicIp": "ENABLED"
        }
    }

    # Monta o comando AWS CLI final
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

    print(cmd)

    # Executa o comando e captura saída
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Exibe o resultado
    if result.returncode == 0:
        print("✅ Fargate task started successfully.")
        print("Output:", result.stdout)
    else:
        print("❌ Failed to start Fargate task.")
        print("Error:", result.stderr)
        
        


     

