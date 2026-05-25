# main.py

from flask import Flask, jsonify
from flask_cors import CORS
from routes.mcp_tools import mcp
from security.cors import get_cors_config

app = Flask(__name__)

# CORS sécurisé
CORS(app, resources={r"/mcp/*": get_cors_config()})

app.register_blueprint(mcp, url_prefix="/mcp")


@app.route("/")
def root():
    return jsonify({
        "status":  "online",
        "service": "MCP Instagram Agent",
        "version": "1.0.0"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
