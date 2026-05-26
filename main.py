# main.py

import os
from flask import Flask, jsonify
from flask_cors import CORS
from routes.mcp_tools import mcp
from security.cors import get_cors_config

app = Flask(__name__)
CORS(app, resources={r"/mcp/*": get_cors_config()})
app.register_blueprint(mcp, url_prefix="/mcp")


@app.route("/")
def root():
    return jsonify({
        "status":  "online",
        "service": "MCP Instagram Agent",
        "version": "1.0.0",
        "endpoints": {
            "quota":     "GET  /mcp/quota",
            "niches":    "GET  /mcp/niches",
            "session":   "POST /mcp/run-session",
            "prospects": "GET  /mcp/prospects"
        }
    })


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
                            "type": "string",
                            "enum": ["pending", "prospected", "rejected"]
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
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
