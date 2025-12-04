from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import tempfile
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# URL do seu backend real
AI_BACKEND_URL = "http://localhost:8001/predict"

# ==================== ENDPOINTS MONAI LABEL COMPATÍVEIS ====================

@app.route("/info/", methods=["GET"])
@app.route("/info", methods=["GET"])
def info():
    """
    Endpoint obrigatório - XNAT chama isso primeiro
    Deve retornar exatamente este formato
    """
    return jsonify({
        "name": "MONAILabel",
        "version": "0.5.2",
        "description": "MONAI Label Mock Server with Interactive Tools",
        "labels": ["liver", "spleen", "kidney", "left_ventricle", "right_ventricle", "calcification"],
        "models": {
            # Modelos de Segmentação Automática
            #"segmentation_ct": {
            #    "type": "segmentation",
            #    "labels": {
            #        "liver": 1,
            #        "spleen": 2,
            #        "kidney": 3
            #    },
            #    "dimension": 3,
            #    "description": "Segmentação automática de órgãos abdominais"
            #},
            "ef_analysis": {
                "type": "segmentation", 
                "labels": {
                    "left_ventricle": 1,
                    "right_ventricle": 2
                },
                "dimension": 3,
                "description": "Análise de fração de ejeção cardíaca "
            },
            "calcium_score": {
                "type": "segmentation",
                "labels": {
                    "calcification": 1
                },
                "dimension": 3,
                "description": "Cálculo de escore de cálcio coronariano"
            },
            
            # Modelos Interativos - DeepEdit
            #"deepedit": {
            #    "type": "deepedit",
            #    "labels": {
            #        "organ": 1,
            #        "tumor": 2,
            #        "background": 0
            #    },
            #    "dimension": 3,
            #    "description": "Segmentação interativa com DeepEdit - cliques positivos/negativos"
            #},
            
            # DeepGrow
            #"deepgrow": {
            #    "type": "deepgrow",
            #    "labels": {
            #        "foreground": 1,
            #        "background": 0
            #    },
            #    "dimension": 3,
            #    "description": "Segmentação interativa com DeepGrow - cliques para crescimento de região"
            #},
            
            # Scribbles
            #"scribbles": {
            #    "type": "scribbles",
            #    "labels": {
            #        "organ": 1,
            #        "tumor": 2,
            #        "background": 0
            #    },
            #    "dimension": 3,
            #    "description": "Segmentação interativa com Scribbles - desenhe sobre a região"
            #}
        }
    })

@app.route("/info/models", methods=["GET"])
def info_models():
    """
    Lista de modelos - chamado após /info
    """
    return jsonify([
        #"segmentation_ct",
        "ef_analysis", 
        "calcium_score",
        #"deepedit",
        #"deepgrow",
        #"scribbles"
    ])

@app.route("/info/model/<model_name>", methods=["GET"])
def info_model(model_name):
    """
    Informações detalhadas de um modelo específico
    """
    models_info = {
        #"segmentation_ct": {
        #    "type": "segmentation",
        #    "labels": {
        #        "liver": 1,
        #        "spleen": 2,
        #        "kidney": 3
        #    },
        #    "dimension": 3,
        #    "description": "Segmentação automática de órgãos abdominais",
        #    "model_state": "COMPLETED"
        #},
        "ef_analysis": {
            "type": "segmentation",
            "labels": {
                "left_ventricle": 1,
                "right_ventricle": 2
            },
            "dimension": 3,
            "description": "Análise de fração de ejeção",
            "model_state": "COMPLETED"
        },
        "calcium_score": {
            "type": "segmentation",
            "labels": {
                "calcification": 1
            },
            "dimension": 3,
            "description": "Cálculo de escore de cálcio",
            "model_state": "COMPLETED"
        },
        #"deepedit": {
        #    "type": "deepedit",
        #    "labels": {
        #        "organ": 1,
        #        "tumor": 2,
        #        "background": 0
        #    },
        #    "dimension": 3,
        #    "description": "Segmentação interativa DeepEdit",
        #    "model_state": "COMPLETED"
        #},
        #"deepgrow": {
        #    "type": "deepgrow",
        #    "labels": {
        #        "foreground": 1,
        #        "background": 0
        #    },
        #    "dimension": 3,
        #    "description": "Segmentação interativa DeepGrow",
        #    "model_state": "COMPLETED"
        #},
        #"scribbles": {
        #    "type": "scribbles",
        #    "labels": {
        #        "organ": 1,
        #        "tumor": 2,
        #        "background": 0
        #    },
        #    "dimension": 3,
        #    "description": "Segmentação interativa Scribbles",
        #    "model_state": "COMPLETED"
        #}
    }
    
    if model_name in models_info:
        return jsonify(models_info[model_name])
    else:
        return jsonify({"error": f"Model {model_name} not found"}), 404

@app.route("/infer/<model_name>", methods=["POST"])
@app.route("/infer/<model_name>/", methods=["POST"])
def infer(model_name):
    """
    Endpoint de inferência - quando o usuário clica em 'Run'
    Suporta modelos automáticos e interativos
    """
    # Verifica se recebeu arquivo
    file_data = None
    
    if request.files and 'file' in request.files:
        file_data = request.files['file']
    elif request.files and 'image' in request.files:
        file_data = request.files['image']
    elif request.data:
        # Dados raw no body
        temp_path = tempfile.mktemp(suffix=".nii.gz")
        with open(temp_path, "wb") as f:
            f.write(request.data)
        file_data = temp_path
    else:
        return jsonify({
            "error": "No file received",
            "message": "Expected 'file' or 'image' in multipart/form-data"
        }), 400
    
    # Salva arquivo temporário
    if isinstance(file_data, str):
        temp_path = file_data
    else:
        temp_path = tempfile.mktemp(suffix=".nii.gz")
        file_data.save(temp_path)
    
    # Captura parâmetros interativos (para DeepEdit, DeepGrow, Scribbles)
    params = request.form.to_dict() if request.form else {}
    
    # Para ferramentas interativas, os cliques/scribbles vêm no form
    # Exemplo: {"foreground": [[x,y,z], [x,y,z]], "background": [[x,y,z]]}
    
    try:
        # Tenta enviar para seu backend real
        with open(temp_path, "rb") as f:
            response = requests.post(
                AI_BACKEND_URL,
                files={"file": f},
                data={
                    "model": model_name,
                    "params": str(params)  # Envia parâmetros interativos
                },
                timeout=300
            )
        
        if response.status_code == 200:
            result = response.json()
        else:
            # Backend retornou erro
            result = {
                "error": f"Backend returned {response.status_code}",
                "details": response.text
            }
    
    except requests.exceptions.ConnectionError:
        # Backend não disponível - retorna resultado fake
        print(f"⚠️  Backend não disponível em {AI_BACKEND_URL}")
        print(f"   Retornando resultado fake para modelo '{model_name}'")
        
        result = generate_fake_result(model_name, params)
    
    except Exception as e:
        result = {
            "error": str(e),
            "type": type(e).__name__
        }
    
    finally:
        # Limpa arquivo temporário
        if os.path.exists(temp_path) and "file" not in result:
            os.remove(temp_path)
    
    return jsonify(result)

@app.route("/activelearning/<model_name>", methods=["POST"])
def activelearning(model_name):
    """
    Endpoint de active learning (opcional mas às vezes chamado)
    """
    return jsonify({
        "status": "not_implemented",
        "message": "Active learning não implementado neste mock"
    })

def generate_fake_result(model_name, params=None):
    """
    Gera resultado fake para testes quando o backend real não está disponível
    """
    result = {
        "status": "success",
        "model": model_name,
        "label_names": get_labels_for_model(model_name),
        "warning": "⚠️ Backend AI não disponível - resultado de teste"
    }
    
    # Se for ferramenta interativa, menciona os parâmetros recebidos
    if model_name in ["deepedit", "deepgrow", "scribbles"] and params:
        result["interactive_params"] = params
        result["message"] = f"Ferramenta interativa '{model_name}' processada com parâmetros recebidos"
    
    return result

def get_labels_for_model(model_name):
    """
    Retorna labels para cada modelo
    """
    labels = {
        #"segmentation_ct": {
        #    "liver": 1,
        #    "spleen": 2,
        #    "kidney": 3
        #},
        "ef_analysis": {
            "left_ventricle": 1,
            "right_ventricle": 2
        },
        "calcium_score": {
            "calcification": 1
        },
        #"deepedit": {
        #    "organ": 1,
        #    "tumor": 2,
        #    "background": 0
        #},
        #"deepgrow": {
        #    "foreground": 1,
        #    "background": 0
        #},
        #"scribbles": {
        #    "organ": 1,
        #    "tumor": 2,
        #    "background": 0
        #}
    }
    return labels.get(model_name, {})

# ==================== ENDPOINTS AUXILIARES ====================

@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({
        "status": "READY",
        "healthy": True,
        "version": "0.5.2"
    })

@app.route("/logs/", methods=["GET"])
@app.route("/logs", methods=["GET"])
def logs():
    """Logs (opcional)"""
    return jsonify([])

# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🏥 MONAI Label Mock Server with Interactive Tools")
    print("=" * 70)
    print(f"📡 Server running on: http://0.0.0.0:8000")
    print(f"🤖 AI Backend URL: {AI_BACKEND_URL}")
    print("=" * 70)
    print("\n✓ Endpoints MONAI Label compatíveis:")
    print("   GET  /info                    - Server info (XNAT chama primeiro)")
    print("   GET  /info/models             - Lista de modelos")
    print("   GET  /info/model/<n>       - Info de modelo específico")
    print("   POST /infer/<model>           - Executar inferência")
    print("=" * 70)
    print("\n💡 Modelos Automáticos:")
    #print("   • segmentation_ct   - Segmentação de órgãos abdominais")
    print("   • ef_analysis       - Análise de fração de ejeção")
    print("   • calcium_score     - Cálculo de escore de cálcio")
    #print("\n🖱️  Modelos Interativos:")
    #print("   • deepedit          - Cliques positivos/negativos")
    #print("   • deepgrow          - Crescimento de região por cliques")
    #print("   • scribbles         - Desenho sobre a região")
    print("=" * 70)
    print("\n🚀 Aguardando requisições do XNAT/OHIF...\n")
    
    app.run(host="0.0.0.0", port=8000, debug=True, threaded=True)
