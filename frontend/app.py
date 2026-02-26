from flask import Flask, render_template, request, redirect, url_for
import os
from backend.resume_parser import ResumeParser

app = Flask(__name__)
parser = ResumeParser()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        return "No file uploaded", 400

    file = request.files["resume"]
    if file.filename == "":
        return "No selected file", 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    job_description = """
    We are looking for a Business Analyst with strong skills in SQL, Python,
    communication, teamwork, and project management.
    """

    scores = parser.process_resume(file_path, job_description)

    return render_template("results.html", filename=file.filename, scores=scores)

if __name__ == "__main__":
    app.run(debug=True)