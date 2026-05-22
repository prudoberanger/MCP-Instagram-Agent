# main.py

from flask import Flask, jsonify
from routes.mcp_tools import mcp

app = Flask(__name__)
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
            "status":    "PATCH /mcp/prospect/status",
            "prospects": "GET  /mcp/prospects"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
