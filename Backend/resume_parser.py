import re
import PyPDF2
import docx
import spacy

class ResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

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
        found_skills = []
        for skill in skills_list:
            if skill.lower() in text.lower():
                found_skills.append(skill)
        return found_skills


if __name__ == "__main__":
    parser = ResumeParser()
    text = parser.extract_text_from_pdf("data/AkhonaCV.pdf")
    clean = parser.clean_text(text)

    print("Resume Parser is ready, Akhona!")
    print("Contact Info:", parser.extract_contact_info(clean))
    print("Entities:", parser.extract_entities(clean))
    print("Skills:", parser.extract_skills(clean))
