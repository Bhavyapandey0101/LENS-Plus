import os
import base64

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

SYSTEM_PROMPT = """
You are LENS+, a medical report explanation assistant.

Your job is to explain medical reports and prescriptions in simple language.

You can:
- Explain test names and their meanings.
- Explain visible values, units and reference ranges.
- Point out values that appear outside the provided reference range.
- Explain clearly visible medicines and instructions from prescriptions.
- Answer questions about the uploaded report.
- Explain information in English, Hindi or Marathi.

Important safety rules:
- Do not diagnose diseases.
- Do not prescribe medicines.
- Do not tell the user to start, stop or change medication.
- Never guess unclear handwriting or unclear medical information.
- If something is unreadable, clearly say that it is unclear.
- Encourage the user to discuss concerning findings with a qualified healthcare professional.

Keep explanations simple and easy to understand.
"""


@app.route("/")
def home():
    return "LENS+ Backend is running!"


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "No message received."
        }), 400

    user_message = data.get("message", "").strip()
    language = data.get("language", "English")

    if not user_message:
        return jsonify({
            "success": False,
            "message": "Message cannot be empty."
        }), 400

    prompt = f"""
Respond in {language}.

User question:
{user_message}
"""

    try:

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

        return jsonify({
            "success": True,
            "message": answer
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@app.route("/analyze", methods=["POST"])
def analyze_report():

    if "report" not in request.files:
        return jsonify({
            "success": False,
            "message": "No report uploaded."
        }), 400

    report = request.files["report"]

    if report.filename == "":
        return jsonify({
            "success": False,
            "message": "No file selected."
        }), 400

    language = request.form.get("language", "English")

    file_bytes = report.read()

    if not file_bytes:
        return jsonify({
            "success": False,
            "message": "The uploaded file is empty."
        }), 400

    mime_type = report.mimetype or "image/jpeg"

    encoded_file = base64.b64encode(file_bytes).decode("utf-8")

    prompt = f"""
Analyze this medical document.

Respond in {language}.

Explain:
1. What type of report/document this appears to be.
2. Important visible tests, values and reference ranges.
3. Which values appear outside the provided reference range.
4. A simple explanation of the visible results.
5. Any clearly visible medicine names or instructions if this is a prescription.
6. What the user should discuss with their doctor.

Do not diagnose or prescribe.
Do not guess unclear text.
"""

    try:

        if not mime_type.startswith("image/"):
            return jsonify({
                "success": False,
                "message": "For this prototype, please upload a JPG or PNG image of the report."
            }), 400

        image_data = f"data:{mime_type};base64,{encoded_file}"

        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content

        return jsonify({
            "success": True,
            "message": answer
        })

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)