from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, "handshake.xlsx")

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} not found.")
    exit()

options = Options()
# Ensure this path is correct for your machine
options.add_argument(r"--user-data-dir=C:\Users\mudiw\Downloads\ChromeSelenium")
driver = webdriver.Chrome(options=options)

# ================================
# LOGIN
# ================================
driver.get("https://app.joinhandshake.com/login")
print("👉 Please log in to Handshake in the browser window.")
input("After you are logged in and see your dashboard, press ENTER here to start scraping...")

# ================================
# LOAD LINKS (Targeting Col B, Row 11)
# ================================
# usecols=[1] is Column B | skiprows=10 starts at Row 11
df_links = pd.read_excel(file_path, header=None, usecols=[1], skiprows=10)
links = df_links.iloc[:, 0].dropna().tolist()

if not links:
    print("❌ No links found in Column B starting at Row 11.")
    driver.quit()
    exit()
else:
    print(f"✅ Successfully loaded {len(links)} links. Starting extraction...")

# ================================
# SKILLS & DISCIPLINES
# ================================
skills = [
    # --- Programming & Software ---
    "python", "c++", "c#", "java", "javascript", "sql", "linux", "unix", "bash",
    "git", "github", "docker", "unit testing", "atlassian", "jira","medical device", 

    # --- Robotics & AI ---
    "ros", "ros2", "opencv", "pytorch", "tensorflow", "keras", "scikit-learn",
    "kinematics", "dynamics", "motion planning", "slam", "lidar", "radar", 
    "computer vision", "perception", "path planning", "point cloud", "cuda",

    # --- Embedded Systems & Electronics ---
    "arduino", "raspberry pi", "stm32", "esp32", "rtos", "firmware", "embedded c",
    "pcb", "altium", "kicad", "eagle", "circuit design", "fpga", "verilog", "vhdl",
    "i2c", "spi", "uart", "can bus", "modbus", "ethercat", "oscilloscope", "multimeter",

    # --- Mechanical & CAD ---
    "cad", "solidworks", "autocad", "fusion 360", "inventor", "ansys", "fea", 
     "gd&t", "3d printing", "rapid prototyping", "cnc", "cam",

    # --- Controls & Automation ---
    "matlab", "simulink", "pid", "plc", "allen bradley", "siemens", "hmi", 
    "scada", "industrial automation", "mechatronics", "control systems", "labview",

    # --- General Engineering & Methods ---
    "six sigma", "lean manufacturing", "root cause analysis", "fmea", 
    "systems engineering", "project management", "agile", "scrum"
]
discipline_keywords = {
    "electrical": ["electrical engineer", "circuit", "electronics"],
    "mechanical": ["mechanical engineer", "solidworks", "cad"],
    "robotics": ["robotics", "ros", "mechatronics"]
}

def get_matches(text, word_list):
    found = []
    for word in word_list:
        if re.search(r'\b' + re.escape(word) + r'\b', text.lower()):
            found.append(word)
    return list(set(found))

# ================================
# UPDATED SCRAPE LOOP WITH SECTION EXTRACTION
# ================================
data = []

# List of headers we want to "hunt" for
requirement_headers = [
    "required skills", "required qualifications", "qualifications", 
    "basic qualifications", "minimum requirements", "what you'll need",
    "desired skills", "preferred qualifications"
]

for i, link in enumerate(links):
    try:
        print(f"[{i+1}/{len(links)}] Opening: {link}")
        driver.get(link)
        time.sleep(7) 

        soup = BeautifulSoup(driver.page_source, "html.parser")
        full_text = soup.get_text().lower()

        # 1. BASE EXTRACTION (Title & Company)
        try: title = driver.find_element("tag name", "h1").text
        except: title = "N/A"
        try: company = driver.find_element("xpath", "//a[contains(@href, '/employers/')]").text
        except: company = "N/A"

        # 2. TARGETED SECTION EXTRACTION
        # We look for specific headers and grab the text blocks following them
        requirements_summary = "Not Found"
        
        # We search for tags that might be headers (h2, h3, p, strong, div)
        potential_headers = soup.find_all(['h2', 'h3', 'h4', 'strong', 'p', 'div'])
        
        for header in potential_headers:
            header_text = header.get_text().strip().lower()
            
            # If we find a match for our requirement keywords
            if any(req in header_text for req in requirement_headers):
                # Grab the next sibling or parent's next sibling which usually contains the list
                content_block = header.find_next(['ul', 'ol', 'p', 'div'])
                if content_block:
                    requirements_summary = content_block.get_text(separator=" | ").strip()
                    break # Stop searching once we find the primary qualification section

        # 3. EXISTING SKILL MATCHING (Your list-based matching)
        detected_skills = get_matches(full_text, skills)
        skills_string = ", ".join(detected_skills)

        # 4. DISCIPLINE CLASSIFICATION
        matched_disciplines = []
        for field, keywords in discipline_keywords.items():
            if get_matches(full_text, keywords):
                matched_disciplines.append(field)
        discipline = ", ".join(matched_disciplines) if matched_disciplines else "other"

        data.append({
            "link": link,
            "title": title,
            "company": company,
            "discipline": discipline,
            "skills": skills_string,
            "extracted_requirements": requirements_summary # NEW COLUMN
        })

        print(f"   ✅ Done: {title} | Requirements Extracted: {'Yes' if requirements_summary != 'Not Found' else 'No'}")

    except Exception as e:
        print(f"   ❌ Error with link: {link}\n   {e}")

# ================================
# SAVE OUTPUT
# ================================
if data:
    df_output = pd.DataFrame(data)
    # Keep 'other' for now so you can see if you're missing keywords, 
    # or filter it out as you did before:
    df_filtered = df_output[df_output["discipline"] != "other"]
    
    df_filtered.to_excel("skillstracker.xlsx", index=False)
    print(f"\n✅ Completed! Results saved to skillstracker.xlsx")
else:
    print("\n⚠️ No data was collected. Check your internet or login status.")

driver.quit()