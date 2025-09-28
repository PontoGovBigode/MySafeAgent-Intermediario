from flask import Flask, request, jsonify
import datetime, secrets

app = Flask(__name__)

# ===============================
# ARMAZENAMENTO EM MEMÓRIA (MVP)
# agents: {
#   agent_id: {
#     "paired": bool,
#     "pair_code": "ABCDEFG8",
#     "device_token": "tok_xxx",
#     "last_seen": "2025-09-28T12:00:00Z",
#     "pending_command": None | "destroy"
#   }
# }
# ===============================
agents = {}

def now_iso():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def make_device_token():
    # token aleatório (poderia ser JWT no futuro)
    return "tok_" + secrets.token_urlsafe(24)

# ============ PAREAMENTO ============
@app.route("/pair/init", methods=["POST"])
def pair_init():
    """
    Body: { "agent_id": "uuid", "pair_code": "ABCDEFG8" }
    Efeito: cria/atualiza registro do agente, paired=False
    """
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent_id")
    pair_code = data.get("pair_code")

    if not agent_id or not pair_code:
        return jsonify({"error": "missing agent_id or pair_code"}), 400

    rec = agents.get(agent_id) or {}
    rec.update({
        "paired": False,
        "pair_code": pair_code,
        "device_token": None,
        "last_seen": now_iso(),
        "pending_command": None
    })
    agents[agent_id] = rec
    return jsonify({"status": "ok"}), 200

@app.route("/pair/confirm", methods=["POST"])
def pair_confirm():
    """
    Body (via app, autenticado na prática): { "agent_id": "...", "pair_code": "..." }
    Se confere, marca paired=True e gera device_token.
    """
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent_id")
    pair_code = data.get("pair_code")

    if not agent_id or not pair_code:
        return jsonify({"error": "missing agent_id or pair_code"}), 400

    rec = agents.get(agent_id)
    if not rec or rec.get("pair_code") != pair_code:
        return jsonify({"error": "invalid agent or pair_code"}), 404

    rec["paired"] = True
    if not rec.get("device_token"):
        rec["device_token"] = make_device_token()
    rec["last_seen"] = now_iso()

    return jsonify({"status": "paired", "device_token": rec["device_token"]}), 200

@app.route("/pair/status", methods=["GET"])
def pair_status():
    """
    Query: ?agent_id=...
    Retorna { paired: bool, device_token?: str }
    """
    agent_id = request.args.get("agent_id")
    rec = agents.get(agent_id or "")
    if not rec:
        return jsonify({"paired": False}), 200
    resp = {"paired": bool(rec.get("paired"))}
    if rec.get("paired") and rec.get("device_token"):
        resp["device_token"] = rec["device_token"]
    rec["last_seen"] = now_iso()
    return jsonify(resp), 200

# ============ COMANDOS ============
@app.route("/command", methods=["POST"])
def send_command():
    """
    Body (via app, autenticado na prática):
      { "agent_id": "...", "action": "destroy" }
    Seta comando pendente para o agente consumir uma única vez.
    """
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agent_id")
    action = data.get("action")

    if not agent_id or not action:
        return jsonify({"error": "missing agent_id or action"}), 400
    if action not in ("destroy", ):
        return jsonify({"error": "unsupported action"}), 400

    rec = agents.get(agent_id)
    if not rec or not rec.get("paired"):
        return jsonify({"error": "agent not paired"}), 404

    rec["pending_command"] = action
    rec["last_seen"] = now_iso()
    return jsonify({"status": "queued"}), 200

@app.route("/agents/<agent_id>/poll", methods=["GET"])
def poll(agent_id):
    """
    Query: ?token=DEVICE_TOKEN
    Valida token e entrega comando pendente (se houver), depois limpa.
    Resp: { "command": "destroy" | "" }
    """
    token = request.args.get("token", "")
    rec = agents.get(agent_id or "")
    if not rec or token != rec.get("device_token"):
        return jsonify({"error": "unauthorized"}), 401

    cmd = rec.get("pending_command")
    # entrega e limpa (one-shot)
    rec["pending_command"] = None
    rec["last_seen"] = now_iso()

    return jsonify({"command": cmd or ""}), 200

# ============ MONITORAMENTO (opcional) ============
@app.route("/status", methods=["GET"])
def status():
    """
    Lista agentes e última comunicação (somente debug/MVP).
    """
    out = []
    for aid, rec in agents.items():
        out.append({
            "agent_id": aid,
            "paired": rec.get("paired"),
            "last_seen": rec.get("last_seen"),
            "has_token": bool(rec.get("device_token")),
            "pending_command": rec.get("pending_command"),
        })
    return jsonify(out), 200

@app.route("/")
def home():
    return "MySafeAgent Intermediary Server (pair + command + poll) OK."

if __name__ == "__main__":
    # Railway usa Gunicorn via Procfile em produção
    app.run(host="0.0.0.0", port=8080)
