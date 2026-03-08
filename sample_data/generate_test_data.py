import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

BASE = "sample_data"

EMPLOYEE_FILE = f"{BASE}/employees/employees.csv"

PROTOTYPE_DIR = f"{BASE}/prototypes"
LETTER_DIR = f"{BASE}/generated_letters"
LOGO_DIR = f"{BASE}/logos"

os.makedirs(PROTOTYPE_DIR, exist_ok=True)
os.makedirs(LETTER_DIR, exist_ok=True)
os.makedirs(LOGO_DIR, exist_ok=True)

# -----------------------------
# Create logos
# -----------------------------

logos = {
    "wealth.png": ("Wealth Management", "blue"),
    "investment.png": ("Investment Banking", "green"),
    "asset.png": ("Asset Management", "orange"),
}

for filename, (text, color) in logos.items():
    img = Image.new("RGB", (400, 150), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 60), text, fill=color)
    img.save(f"{LOGO_DIR}/{filename}")

print("Logos created")

# -----------------------------
# Create prototype letters
# -----------------------------

prototypes = {
    "promotion_prototype.pdf": "Promotion Letter Template\n\nCongratulations on your promotion.",
    "salary_increase_prototype.pdf": "Salary Increase Letter Template\n\nYour base pay has been increased.",
    "bonus_prototype.pdf": "Annual Incentive Letter Template\n\nYou are awarded a bonus.",
}

for filename, content in prototypes.items():
    c = canvas.Canvas(f"{PROTOTYPE_DIR}/{filename}", pagesize=letter)
    c.drawString(100, 700, content)
    c.save()

print("Prototype PDFs created")

# -----------------------------
# Generate employee letters
# -----------------------------

df = pd.read_csv(EMPLOYEE_FILE)

for _, row in df.iterrows():

    filename = f"{LETTER_DIR}/{row['employee_id']}_letter.pdf"

    c = canvas.Canvas(filename, pagesize=letter)

    c.drawString(100, 750, f"Employee Letter")

    c.drawString(100, 720, f"Name: {row['name']}")
    c.drawString(100, 700, f"Department: {row['department']}")
    c.drawString(100, 680, f"Title: {row['title']}")

    c.drawString(100, 640, f"Base Pay: ${row['base_pay']}")
    c.drawString(100, 620, f"Annual Incentive: ${row['annual_incentive']}")

    c.drawString(100, 580, "Thank you for your contributions.")

    c.save()

print("Generated employee letters")