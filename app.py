import os
import re
from flask import Flask, render_template, request
import pdfplumber
from difflib import SequenceMatcher

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Clean text by removing special characters
def clean_text(text):
    return re.sub(r'[^A-Za-z0-9 ]+', '', text).strip()

# Extract full cleaned text
def extract_text(path):
    full_text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                cleaned = clean_text(text)
                full_text += cleaned + "\n"
    return full_text.strip()

# Extract line-by-line cleaned text
def extract_lines(path):
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    cleaned = clean_text(line)
                    if cleaned:
                        lines.append(cleaned)
    return lines


@app.route("/", methods=["GET", "POST"])
def index():
    output = None

    if request.method == "POST":
        pdf1 = request.files["pdf1"]
        pdf2 = request.files["pdf2"]

        path1 = os.path.join(app.config["UPLOAD_FOLDER"], pdf1.filename)
        path2 = os.path.join(app.config["UPLOAD_FOLDER"], pdf2.filename)

        pdf1.save(path1)
        pdf2.save(path2)

        # Extract text and lines
        pdf1_lines = extract_lines(path1)
        pdf2_lines = extract_lines(path2)

        # 1. Lines only in PDF 1 (order preserved)
        only_pdf1 = [line for line in pdf1_lines if line not in pdf2_lines]

        # 2. Lines only in PDF 2 (order preserved)
        only_pdf2 = [line for line in pdf2_lines if line not in pdf1_lines]

        # 3. Lines present in both PDFs but differ in content
        different = []
        already_added = set()

        for l1 in pdf1_lines:
            for l2 in pdf2_lines:
                if l1 == l2:
                    continue

                similarity = SequenceMatcher(None, l1, l2).ratio()

                # If similarity shows both lines are related but different
                if similarity > 0.50:
                    key = (l1, l2)
                    if key not in already_added:
                        different.append((l1, l2))
                        already_added.add(key)
                    break

        output = {
            "only_pdf1": only_pdf1,
            "only_pdf2": only_pdf2,
            "different": different
        }

    return render_template("index.html", output=output)


# Create uploads folder if not exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

if __name__ == "__main__":
    app.run(debug=True)
