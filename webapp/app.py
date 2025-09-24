from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
	raise ValueError("DATABASE_URL environment variable not set")

engine = create_engine(DATABASE_URL, echo=True, future=True)

@app.get("/")
def index():
	return jsonify({"message": "OK"})

@app.get("/health")
def health():
	try:
		with engine.connect() as conn:
			conn.execute(text("SELECT 1"))
		return {"ok": True}
	except Exception as e:
		print("Healthcheck DB connection failed:", str(e))
		return {"ok": False, "error": str(e)}, 500

@app.post("/api/submit")
def submit():
	data = request.get_json() or request.form.to_dict()
	required_fields = ["name", "email", "message"]
	if not data or not all(field in data for field in required_fields):
		return jsonify({"error": "Missing input"}), 400
	try:
		with engine.begin() as conn:
			conn.execute(
				text(
					"INSERT INTO entries (name, email, message) VALUES (:name, :email, :message)"
				),
				data,
			)
		return jsonify({"status": "ok"}), 200
	except Exception as e:
		print("Insert failed:", str(e))
		return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000)
