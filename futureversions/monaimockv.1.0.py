from flask import Flask, request, jsonify
from flask_cors import CORS
import io
from flask import redirect
import os
import ef  
#import scorecalcium 


# primeiro conectamos via rede o xnat ao 





app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------------------------
# CONFIGURAÇÃO DOS MODELOS
# ---------------------------------------------------------
MODEL_TARGETS = {
    "ef_analysis": "http://ef_analysis:5000",
    "calcium_score": "http://calcium_score:5000"
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
        "labels": ["heart", "calcification"],
        "models": {
            "ef_analysis": {
                "type": "segmentation",
                "labels": {"heart": 1},
                "dimension": 3
            },
            "calcium_score": {
                "type": "segmentation",
                "labels": {"calcification": 1},
                "dimension": 3
            }
        }
    })


# =========================================================
# 2) /info/models
# =========================================================
@app.route("/info/models", methods=["GET"])
def info_models():
    return jsonify(["ef_analysis", "calcium_score"])


# =========================================================
# 3) /info/model/<name>
# =========================================================
@app.route("/info/model/<name>", methods=["GET"])
def info_model(name):

    if name not in MODEL_TARGETS:
        return jsonify({"error": "Model not found"}), 404

    return jsonify({
        "type": "segmentation",
        "labels": {"auto": 1},
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
    print("\n✅ MONAILabel Requested Session\n")

    return jsonify({
        "session_id": "mock-session",
        "expiry": 7200,
        "status": "READY"
    })


# =========================================================
# 6) /infer/<model>
# =========================================================
@app.route("/infer/<model_name>", methods=["POST"])
def infer(model_name):

    if model_name not in MODEL_TARGETS:
        return jsonify({"error": f"Model '{model_name}' not supported"}), 404

    # Recebe o caminho enviado pelo MONAI/OHIF
    image_path = request.args.get("image", "")
    parts = image_path.split("/") if image_path else []

    project    = parts[0] if len(parts) > 0 else ""
    subject    = parts[1] if len(parts) > 1 else ""
    experiment = parts[2] if len(parts) > 2 else ""
    scan       = parts[3] if len(parts) > 3 else ""

    # Dados solicitados
    if model_name == 'ef_analysis':

        api_data = {
            "xnathost": os.getenv("XNAT_HOST"),
            "user": 'admin',
            "project": project,
            "subject": subject,
            "experiment": experiment,
            "experiment_type": 'MR',
            "scan": scan,
            "scan_description": 'rEIXO_CURTO',
            "resource_name": 'DICOM',
            "files": 'data'
            }
        
        print(api_data)
        ef.run_fargate_task(api_data)


    elif model_name == 'calcium_score':

        api_data = {
            "xnathost": os.getenv("XNAT_HOST"),
            "user": 'admin',
            "project": project,
            "subject": subject,
            "experiment": experiment,
            "experiment_type": 'CT',
            "scan": scan,
            "scan_description": 'breast',
            "resource_name": 'DICOM',
            "files": 'data'
            }        
        
        print(api_data)               
        scorecalcium .run_fargate_task(api_data)

    
    return jsonify({"message": "OK"}), 200
    







@app.route("/health", methods=["GET"])
def health():
    return "OK", 200


if __name__ == "__main__":
    print("\n🚀 MONAI Label mock server running at:")
    print("👉 http://0.0.0.0:8000\n")

    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
