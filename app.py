import sys
import os
# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, send_file
import csv
from datetime import datetime
from backend.resume_parser import ResumeParser

app = Flask(__name__,
            template_folder='frontend/templates',  # Templates are in frontend/templates
            static_folder='frontend/static')  # Static files are in frontend/static
parser = ResumeParser()

UPLOAD_FOLDER = "data/resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    job_description = request.args.get("job_description", "")
    return render_template("index.html", job_description=job_description)

@app.route("/upload", methods=["POST"])
def upload():
    if "resumes" not in request.files:
        return "No files uploaded", 400

    files = request.files.getlist("resumes")
    job_description = request.form.get("job_description", "").strip()

    if not job_description:
        return "Job description is required", 400

    results = []
    for file in files:
        if file.filename == "":
            continue
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        scores = parser.process_resume(file_path, job_description)
        if scores:
            results.append({"filename": file.filename, "scores": scores})

    results.sort(key=lambda x: x["scores"]["final"], reverse=True)

    # Save full results
    csv_path = "results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Candidate", "Skills", "Experience", "Education", "Semantic", "Final"])
        for r in results:
            s = r["scores"]
            writer.writerow([r["filename"], s["skills"], s["experience"], s["education"], s["semantic"], s["final"]])

    # Save Top 3 results
    top3_path = "top3_results.csv"
    with open(top3_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Candidate", "Skills", "Experience", "Education", "Semantic", "Final"])
        for r in results[:3]:
            s = r["scores"]
            writer.writerow([r["filename"], s["skills"], s["experience"], s["education"], s["semantic"], s["final"]])

    timestamp = datetime.now().strftime("%d %b %Y, %H:%M")
    return render_template("results.html", results=results, count=len(results), timestamp=timestamp, job_description=job_description)

@app.route("/download")
def download():
    return send_file("results.csv", as_attachment=True)

@app.route("/download_top3")
def download_top3():
    return send_file("top3_results.csv", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)