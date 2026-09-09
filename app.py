import os
import base64

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI
import fitz


# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)


# OpenRouter AI client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


# LENS+ instructions
SYSTEM_PROMPT = """
You are LENS+, an AI-powered medical report analysis assistant.

Your main purpose is to analyze uploaded medical reports, prescriptions,
lab reports, and other medical documents and present the information
clearly in simple language.

IMPORTANT:
- Focus mainly on information that is actually visible in the uploaded document.
- Clearly identify the report/document type when possible.
- Extract and organize visible tests, values, units, reference ranges,
  medicines, dosage instructions, dates, and other important information.
- If medicine names are clearly readable, write them clearly.
- If handwriting or text is unclear, DO NOT guess it.
- Say that the text is unclear and should be confirmed with a doctor or pharmacist.
- Do not invent information that is not visible in the document.
- Do not diagnose diseases.
- Do not prescribe medicines.
- Do not tell the user to start, stop, or change medication.

LANGUAGE:
- Always respond in the language selected by the user.
- Support English, Hindi, Marathi, Bengali, Kannada, Tamil, Telugu,
  Gujarati, Punjabi, Malayalam, Urdu and other languages when requested.
- Keep commonly used medical terms in English when that makes the explanation clearer.

FORMAT:
- Keep the response short and easy to understand.
- Use clear headings.
- Use bullet points where useful.
- Highlight important information.
- Avoid unnecessary long paragraphs.
- Do not repeat the user's question.

For a medical report, explain what is actually written or visible in the report
rather than giving unrelated medical information.
"""


@app.route("/")
def home():
    return "LENS+ Backend is running!"


# ---------------- CHAT ----------------

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

        print("CHAT ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to connect to the AI service."
        }), 500


# ---------------- REPORT ANALYSIS ----------------

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

    mime_type = report.mimetype or ""

    prompt = f"""
Analyze the uploaded medical document.

Respond in {language}.

Give the result in this simple structure:

### Document
Briefly identify what type of document this appears to be.

### Information Found
List the important information that is clearly visible in the document.

Include, when available:
- Test names
- Values
- Units
- Reference ranges
- Dates
- Medicine names
- Dosage/instructions
- Other important written information

### Easy Explanation
Explain the visible information in simple language.
Do not add information that is not present in the document.

### Unclear Information
If any word, number, medicine name, or handwriting cannot be read clearly,
mention it here instead of guessing.

Do not diagnose.
Do not prescribe.
Do not recommend changing medication.
"""


    try:

        # -------- PDF --------

        if mime_type == "application/pdf" or report.filename.lower().endswith(".pdf"):

            pdf = fitz.open(stream=file_bytes, filetype="pdf")

            image_data_list = []

            # Convert PDF pages into images
            # Limit to first 5 pages for the prototype
            for page in pdf[:5]:

                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))

                png_bytes = pix.tobytes("png")

                encoded = base64.b64encode(
                    png_bytes
                ).decode("utf-8")

                image_data_list.append(
                    f"data:image/png;base64,{encoded}"
                )

            pdf.close()

            if not image_data_list:
                return jsonify({
                    "success": False,
                    "message": "Could not read the PDF."
                }), 400


        # -------- IMAGE --------

        elif mime_type.startswith("image/"):

            encoded_file = base64.b64encode(
                file_bytes
            ).decode("utf-8")

            image_data_list = [
                f"data:{mime_type};base64,{encoded_file}"
            ]


        # -------- UNSUPPORTED FILE --------

        else:

            return jsonify({
                "success": False,
                "message": "Please upload a JPG, PNG, JPEG image or PDF."
            }), 400


        # -------- SEND TO AI --------

        content = [
            {
                "type": "text",
                "text": prompt
            }
        ]

        for image_data in image_data_list:

            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image_data
                }
            })


        response = client.chat.completions.create(
            model="openrouter/free",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        )


        answer = response.choices[0].message.content


        return jsonify({
            "success": True,
            "message": answer
        })


    except Exception as e:

        print("ANALYZE ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Unable to analyze the uploaded document."
        }), 500


# ---------------- RUN SERVER ----------------

if __name__ == "__main__":
    app.run(debug=True)