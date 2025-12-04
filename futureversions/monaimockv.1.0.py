# Comentarios

#     Monai label possui a cabpacidade de enviar arquivos, requisicoes e receber mascaras inclusive
# entretanto enviaremos apenas requisicoes para o Fargate. Esse metodo, a partir do visualizador, por nao 
# haver necessidade de evocar a api xnatpy, eh bem mais rapido que o metodo da plataforma Xnat - 'run container'.



from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess




app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------
# CONFIGURAÇÃO DOS MODELOS E CONTAINERS
# ---------------------------------------------------------
MODEL_TARGETS = {
    "ef_analysis": "http://ef_analysis:5000",
    "calcium_score": "http://calcium_score:5000"
}

XNAT_HOST = "http://xnat:8080"   # Ajuste se necessário
XNAT_USER = "admin"


# =========================================================
# 1) ENDPOINT FUNDAMENTAL: /info
# =========================================================
@app.route("/info", methods=["GET"])
@app.route("/info/", methods=["GET"])
def info():
    return jsonify({
        "name": "MONAILabel",
        "version": "1.0",
        "description": "Fully functional MONAI Label mock server",
        "labels": ["heart", "calcification"],
        "models": {
            "ef_analysis": {
                "type": "segmentation",
                "labels": {"heart": 1},
                "dimension": 3,
                "description": "Ejection Fraction Analysis"
            },
            "calcium_score": {
                "type": "segmentation",
                "labels": {"calcification": 1},
                "dimension": 3,
                "description": "Coronary Calcium Score"
            }
        }
    })


# =========================================================
# 2) /info/models
# =========================================================
@app.route("/info/models", methods=["GET"])
def info_models():
    return jsonify(["ef_analysis MR", "calcium_score CT"])


# =========================================================
# 3) /info/model/<name>
# =========================================================
@app.route("/info/model/<name>", methods=["GET"])
def info_model(name):
    if name not in MODEL_TARGETS:
        return jsonify({"error": "Model not found"}), 404

    if name == "ef_analysis":
        return jsonify({
            "type": "segmentation",
            "labels": {"heart": 1},
            "dimension": 3,
            "description": "Ejection Fraction Analysis",
            "model_state": "COMPLETED"
        })

    if name == "calcium_score":
        return jsonify({
            "type": "segmentation",
            "labels": {"calcification": 1},
            "dimension": 3,
            "description": "Coronary Calcium Score",
            "model_state": "COMPLETED"
        })


# =========================================================
# 4) ENDPOINT OBRIGATÓRIO: /datastore/image/info/
# =========================================================
@app.route("/datastore/image/info/", methods=["GET"])
def datastore_info():
    image_path = request.args.get("image", "")

    # Ex: prod/XNAT_S0001/XNAT_E0001/5334
    parts = image_path.split("/")
    scan_id = parts[-1] if len(parts) >= 1 else "unknown"

    return jsonify({
        "id": scan_id,
        "name": image_path,
        "size": 1,
        "status": "READY"
    })


# =========================================================
# 5) ENDPOINT OBRIGATÓRIO: /session
# =========================================================
@app.route("/session/", methods=["POST", "OPTIONS"])
def session_create():
    return jsonify({
        "session_id": "mock-session",
        "expiry": 7200,
        "uncompress": False,
        "status": "READY"
    })


# =========================================================
# 6) PRINCIPAL: /infer/<model>
# =========================================================
@app.route("/infer/<model_name>", methods=["POST"])
def infer(model_name):

    # -----------------------------------------------------
    # Verifica se modelo existe
    # -----------------------------------------------------
    if model_name not in MODEL_TARGETS:
        return jsonify({"error": f"Model '{model_name}' not supported"}), 404

    # -----------------------------------------------------
    # Extrai o caminho enviado pelo OHIF/MONAI
    # -----------------------------------------------------
    image_path = request.args.get("image") or request.form.get("image")
    if not image_path:
        return jsonify({"error": "No image path provided"}), 400

    parts = image_path.split("/")
    project     = parts[0] if len(parts) > 0 else ""
    subject     = parts[1] if len(parts) > 1 else ""
    experiment  = parts[2] if len(parts) > 2 else ""
    scan        = parts[3] if len(parts) > 3 else ""

    # -----------------------------------------------------
    # Monta JSON solicitado (api_data)
    # -----------------------------------------------------
    api_data = {
        "xnathost": XNAT_HOST,
        "user": XNAT_USER,
        "project": project,
        "subject": subject,
        "experiment": experiment,
        "scan": scan,
        "modelo": model_name
    }

    print("\n======== API DATA RECEBIDO ========")
    print(api_data)
    print("===================================\n")

    # -----------------------------------------------------
    # Caminho completo no XNAT
    # -----------------------------------------------------
    XNAT_ENDPOINT = (
        f"/data/archive/projects/{project}"
        f"/subjects/{subject}"
        f"/experiments/{experiment}"
        f"/scans/{scan}"
    )

    # -----------------------------------------------------
    # Decide container de destino
    # -----------------------------------------------------
    target_container_ip = MODEL_TARGETS[model_name]

    # -----------------------------------------------------
    # Monta comando
    # -----------------------------------------------------
    cmd = (
        f"bash -c 'python3 api_caller.py "
        f"-url \"{XNAT_HOST}\" "
        f"-s \"{XNAT_ENDPOINT}\" "
        f"-u \"{XNAT_USER}\" "
        f"-ip \"{target_container_ip}\"'"
    )

    print(">> Executando comando:\n", cmd)

    # -----------------------------------------------------
    # Executa
    # -----------------------------------------------------
    try:
        output = subprocess.check_output(
            cmd, shell=True, stderr=subprocess.STDOUT
        ).decode("utf-8")

        return jsonify({
            "status": "success",
            "api_data": api_data,
            "command": cmd,
            "model": model_name,
            "output": output
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "status": "error",
            "api_data": api_data,
            "command": cmd,
            "stderr": e.output.decode("utf-8")
        }), 500


# =========================================================
# HEALTH
# =========================================================
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "READY", "healthy": True})


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    print("MONAI Label mock server running at http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
