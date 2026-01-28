from flask import Flask, request, jsonify
from flask_cors import CORS
import ef

app = Flask(__name__)
CORS(
    app,
    supports_credentials=True,
    origins=[
        "http://localhost",
        "http://131.255.22.222",
        "http://localhost:8000",
        "https://go.imside.ai"
    ]
)



@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return "", 200


#------------------------------------
# CONFIGURAÇÃO DOS MODELOS
# ---------------------------------------------------------
MODEL_TARGETS = {
    "ef_analysis": "http://ef_analysis:5000"
}

# =========================================================
# 1) /info
# =========================================================
@app.route("/info", methods=["GET"])
@app.route("/info/", methods=["GET"])
def info():
    return jsonify({
        "name": "MONAILabel MOCK",
        "version": "1.0",
        "description": "MONAI Label mock server (print api_data only)",
        "labels": ["heart"],
        "models": {
            "ef_analysis": {
                "type": "segmentation",
                "labels": {"heart": 1},
                "dimension": 3
            }
        }
    })


# =========================================================
# 2) /info/models
# =========================================================
@app.route("/info/models", methods=["GET"])
def info_models():
    return jsonify([
        "ef_analysis"
    ])


# =========================================================
# 3) /info/model/<name>
# =========================================================
@app.route("/info/model/<name>", methods=["GET"])
def info_model(name):

    if name not in MODEL_TARGETS:
        return jsonify({"error": "Model not found"}), 404

    return jsonify({
        "type": "segmentation",
        "labels": {"heart": 1},
        "dimension": 3,
        "model_state": "READY"
    })


# =========================================================
# 4) /datastore/image/info/
# =========================================================
@app.route("/datastore/image/info/", methods=["GET"])
def datastore_info():
    image_path = request.args.get("image", "")
    parts = image_path.split("/")
    scan_id = parts[-1] if len(parts) >= 1 else "unknown"

    return jsonify({
        "id": scan_id,
        "name": image_path,
        "size": 1,
        "status": "READY"
    })


# =========================================================
# 5) /session
# =========================================================
@app.route("/session/", methods=["POST", "OPTIONS"])
def session_create():
    print("\n✅ MONAILabel Requested Session")

    return jsonify({
        "session_id": "mock-session",
        "expiry": 7200,
        "status": "READY"
    })


# =========================================================
# 6) /infer/ef_analysis
# =========================================================
@app.route("/infer/<model_name>", methods=["POST"])
def infer(model_name):

    if model_name not in MODEL_TARGETS:
        return jsonify({"error": f"Model '{model_name}' not supported"}), 404

    print(f"\n🚀 Infer request received for model: {model_name}")

    # Caminho enviado pelo MONAI / OHIF
    image_path = request.args.get("image", "")
    parts = image_path.split("/") if image_path else []

    project    = parts[0] if len(parts) > 0 else ""
    subject    = parts[1] if len(parts) > 1 else ""
    experiment = parts[2] if len(parts) > 2 else ""
    scan       = parts[3] if len(parts) > 3 else ""

    api_data = {
        "xnathost": "https://go.imside.ai",
        "user": "admin",
        "project": project,
        "subject": subject,
        "experiment": experiment,
        "experiment_type": "MR",
        "scan": scan,
        "scan_description": "rEIXO_CURTO",
        "resource_name": "DICOM",
        "files": "data"
    }

    print("\n📦 API DATA SENT TO EF MODULE:")
    print(api_data)

    try:
        ef.run_fargate_task(api_data)
        print("✅ Fargate task triggered successfully")
    except Exception as e:
        print("❌ Error while calling ef.run_fargate_task:", str(e))
        return jsonify({"error": "Failed to run ef_analysis"}), 500
        

    return jsonify({"message": "OK - ef_analysis"}), 200


# =========================================================
# 7) /health
# =========================================================
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    print("\n🚀 MONAI Label mock server running at:")
    print("👉 http://0.0.0.0:8000\n")

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True,
        threaded=True
    )
