# main.py

from flask import Flask, jsonify
from flask_cors import CORS
from routes.mcp_tools import mcp
from security.cors import get_cors_config

app = Flask(__name__)

# CORS sécurisé
CORS(app, resources={r"/mcp/*": get_cors_config()})

app.register_blueprint(mcp, url_prefix="/mcp")


@app.route("/mcp", methods=["GET"])
def mcp_info():
    return jsonify({
        "name":        "Veynor",
        "version":     "1.0.0",
        "description": "Agent de prospection Instagram France",
        "tools": [
            {
                "name":        "run_session",
                "description": "Lance une session de prospection Instagram",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "niche": {
                            "type":        "string",
                            "description": "La niche à prospecter",
                            "enum": [
                                "coiffure", "beaute", "ecommerce",
                                "coaching", "sport", "restauration",
                                "patisserie", "immobilier", "photo", "creatifs"
                            ]
                        }
                    },
                    "required": ["niche"]
                }
            },
            {
                "name":        "get_prospects",
                "description": "Récupère les prospects déjà collectés",
                "inputSchema": {
                    "type":       "object",
                    "properties": {
                        "status": {
                            "type":        "string",
                            "description": "Filtre par status",
                            "enum":        ["pending", "prospected", "rejected"]
                        }
                    }
                }
            },
            {
                "name":        "get_niches",
                "description": "Liste toutes les niches disponibles",
                "inputSchema": {
                    "type":       "object",
                    "properties": {}
                }
            }
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
