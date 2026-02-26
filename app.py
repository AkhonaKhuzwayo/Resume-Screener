import sys
import os
import tempfile  # Added for Vercel's writable directory
from pathlib import Path  # Added for better path handling

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, send_file
import csv
from datetime import datetime
from backend.resume_parser import ResumeParser

app = Flask(__name__,
            template_folder='frontend/templates',
            static_folder='frontend/static')
parser = ResumeParser()

# Check if running on Vercel
IS_VERCEL = os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV')

# Configure paths based on environment
if IS_VERCEL:
    # Use /tmp for writable files on Vercel (serverless environment)
    BASE_DIR = '/tmp'
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'resumes')
    CSV_PATH = os.path.join(BASE_DIR, 'results.csv')
    TOP3_PATH = os.path.join(BASE_DIR, 'top3_results.csv')
else:
    # Local development paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'resumes')
    CSV_PATH = os.path.join(BASE_DIR, 'results.csv')
    TOP3_PATH = os.path.join(BASE_DIR, 'top3_results.csv')

# Create upload directory if it doesn't exist
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
        
        # Secure filename to prevent path traversal
        filename = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            scores = parser.process_resume(file_path, job_description)
            if scores:
                results.append({"filename": filename, "scores": scores})
        except Exception as e:
            # Log error but continue processing other files
            print(f"Error processing {filename}: {str(e)}")
            continue

    if not results:
        return "No resumes could be processed successfully", 400

    results.sort(key=lambda x: x["scores"]["final"], reverse=True)

    # Save full results
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Candidate", "Skills", "Experience", "Education", "Semantic", "Final"])
        for r in results:
            s = r["scores"]
            writer.writerow([r["filename"], s["skills"], s["experience"], s["education"], s["semantic"], s["final"]])

    # Save Top 3 results
    with open(TOP3_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Candidate", "Skills", "Experience", "Education", "Semantic", "Final"])
        for r in results[:3]:
            s = r["scores"]
            writer.writerow([r["filename"], s["skills"], s["experience"], s["education"], s["semantic"], s["final"]])

    timestamp = datetime.now().strftime("%d %b %Y, %H:%M")
    return render_template("results.html", results=results, count=len(results), timestamp=timestamp, job_description=job_description)

@app.route("/download")
def download():
    """Download all results"""
    if not os.path.exists(CSV_PATH):
        return "No results file found", 404
    return send_file(CSV_PATH, as_attachment=True, download_name="results.csv")

@app.route("/download_top3")
def download_top3():
    """Download top 3 results"""
    if not os.path.exists(TOP3_PATH):
        return "No top 3 results file found", 404
    return send_file(TOP3_PATH, as_attachment=True, download_name="top3_results.csv")

# Health check endpoint for Vercel
@app.route("/api/health")
def health():
    return {"status": "healthy"}, 200

# This is ignored on Vercel but used for local development
if __name__ == "__main__":
    app.run(debug=True)