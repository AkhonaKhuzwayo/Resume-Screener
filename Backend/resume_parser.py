import re
import PyPDF2
import docx
import spacy
import csv
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer, util


class ResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def extract_text_from_pdf(self, file_path):
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text.strip()

    def extract_text_from_docx(self, file_path):
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def clean_text(self, text):
        return " ".join(text.split())

    def extract_contact_info(self, text):
        phone = re.findall(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", text)
        email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return {"phone": phone, "email": email}

    def extract_entities(self, text):
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]

    def extract_skills(self, text):
        skills_list = [
            "Python", "Java", "C#", "JavaScript", "HTML", "CSS", "SQL",
            "Business Analysis", "Communication", "Teamwork", "Customer Service",
            "MS Office", "Database", "Project Management"
        ]
        return [skill for skill in skills_list if skill.lower() in text.lower()]

    def match_score(self, resume_skills, job_description):
        skills_list = [
            "Python", "Java", "C#", "JavaScript", "HTML", "CSS", "SQL",
            "Business Analysis", "Communication", "Teamwork", "Customer Service",
            "MS Office", "Database", "Project Management"
        ]
        job_skills = [skill for skill in skills_list if skill.lower() in job_description.lower()]
        matches = [skill for skill in resume_skills if skill in job_skills]

        score = (len(matches) / len(job_skills)) * 100 if job_skills else 0
        return {"job_skills": job_skills, "matches": matches, "score": round(score, 2)}

    def calculate_total_experience(self, text):
        range_pattern = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}\s*[-–]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present)\s*\d{0,4}"
        ranges = re.findall(range_pattern, text)

        total_months = 0
        for start, end in ranges:
            try:
                start_date = datetime.strptime(start, "%b %Y")
                end_date = datetime.now() if "Present" in end else datetime.strptime(end, "%b %Y")
                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(months, 0)
            except:
                continue

        return round(total_months / 12, 2)

    def experience_score(self, candidate_years, required_years):
        if candidate_years >= required_years:
            return 100
        elif candidate_years >= 0.8 * required_years:
            return 80
        elif candidate_years >= 0.6 * required_years:
            return 60
        else:
            return 40

    def extract_education(self, text):
        degrees = ["Bachelor", "Master", "PhD", "Diploma", "Certificate"]
        fields = ["Computer Science", "Information Technology", "Business Analysis",
                  "Engineering", "Mathematics", "Data Science"]

        found_degrees = [deg for deg in degrees if deg.lower() in text.lower()]
        found_fields = [field for field in fields if field.lower() in text.lower()]
        return {"degrees": found_degrees, "fields": found_fields}

    def education_score(self, candidate_edu, required_degree, required_field):
        degree_match = 100 if required_degree in candidate_edu["degrees"] else (70 if candidate_edu["degrees"] else 0)
        field_match = 100 if required_field in candidate_edu["fields"] else (80 if candidate_edu["fields"] else 0)
        return round((degree_match * 0.5) + (field_match * 0.5), 2)

    def semantic_similarity_score(self, resume_text, job_description):
        embeddings = self.model.encode([resume_text, job_description], convert_to_tensor=True)
        similarity = util.cos_sim(embeddings[0], embeddings[1])
        return round(float(similarity) * 100, 2)

    def final_score(self, skills_score, experience_score, education_score, semantic_score):
        return round((skills_score * 0.40) + (experience_score * 0.30) +
                     (education_score * 0.15) + (semantic_score * 0.15), 2)

    def export_results_to_csv(self, candidate_name, contact_info, skills, education, scores, file_path="results.csv"):
        headers = ["Candidate", "Phone", "Email", "Skills", "Degrees", "Fields",
                   "Skills Score", "Experience Score", "Education Score", "Semantic Score", "Final Score"]

        row = [
            candidate_name,
            ", ".join(contact_info.get("phone", [])),
            ", ".join(contact_info.get("email", [])),
            ", ".join(skills),
            ", ".join(education.get("degrees", [])),
            ", ".join(education.get("fields", [])),
            scores["skills"],
            scores["experience"],
            scores["education"],
            scores["semantic"],
            scores["final"]
        ]

        file_exists = os.path.exists(file_path)
        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(headers)
            writer.writerow(row)

    def process_resume(self, file_path, job_description, required_degree="Bachelor", required_field="Business Analysis", required_years=3):
        if file_path.lower().endswith(".pdf"):
            text = self.extract_text_from_pdf(file_path)
        elif file_path.lower().endswith(".docx"):
            text = self.extract_text_from_docx(file_path)
        else:
            print(f"Unsupported file format: {file_path}")
            return None

        clean = self.clean_text(text)
        contact = self.extract_contact_info(clean)
        skills = self.extract_skills(clean)
        education = self.extract_education(clean)

        match = self.match_score(skills, job_description)
        semantic_score = self.semantic_similarity_score(clean, job_description)
        edu_score = self.education_score(education, required_degree, required_field)
        total_years = self.calculate_total_experience(clean)
        exp_score = self.experience_score(total_years, required_years)
        final = self.final_score(match["score"], exp_score, edu_score, semantic_score)

        scores = {
            "skills": match["score"],
            "experience": exp_score,
            "education": edu_score,
            "semantic": semantic_score,
            "final": final
        }

        candidate_name = os.path.basename(file_path).replace(".pdf", "").replace(".docx", "")
        self.export_results_to_csv(candidate_name, contact, skills, education, scores)
        return scores


if __name__ == "__main__":
    parser = ResumeParser()
    job_description = """
    We are looking for a Business Analyst with strong skills in SQL, Python,
    communication, teamwork, and project management.
    """

    resume_folder = "data/resumes"  # folder containing multiple resumes
    if not os.path.exists(resume_folder):
        print(f"Resume folder not found: {resume_folder}")
    else:
        processed = 0
        skipped = 0
        errors = 0
        for file in os.listdir(resume_folder):
            file_path = os.path.join(resume_folder, file)
            if not os.path.isfile(file_path):
                continue
            if not file.lower().endswith((".pdf", ".docx")):
                print(f"Skipping unsupported file: {file}")
                skipped += 1
                continue
            try:
                scores = parser.process_resume(file_path, job_description)
                if scores:
                    processed += 1
                    print(f"Processed {file}: Final Score {scores['final']}%")
                else:
                    print(f"Failed to process {file}")
            except Exception as e:
                errors += 1
                print(f"Error processing {file}: {e}")

        print(f"Batch processing complete. Processed: {processed}, Skipped: {skipped}, Errors: {errors}. Results saved to results.csv")