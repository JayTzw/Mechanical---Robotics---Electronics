import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os
import re

# ================================
# CONFIGURATION
# ================================
# Change this to "jobright.xlsx" or whatever your file is named
FILE_NAME = "jobright.xlsx" 
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, FILE_NAME)

options = Options()
options.add_argument(r"--user-data-dir=C:\Users\mudiw\Downloads\ChromeSelenium")
driver = webdriver.Chrome(options=options)

# ================================
# EXPANDED SKILLS & DISCIPLINES
# ================================
skills = [
    # Programming & AI
    "python", "c++", "c#", "java", "matlab", "simulink", "gdscript", "godot",
    "pytorch", "tensorflow", "opencv", "cuda", "ros", "ros2", "slam", "linux",
    
    # Electronics & Embedded
    "arduino", "raspberry pi", "stm32", "esp32", "firmware", "embedded", "rtos",
    "pcb", "altium", "kicad", "eagle", "circuit design", "fpga", "verilog", "vhdl",
    "i2c", "spi", "uart", "can bus", "modbus", "soldering", "emi", "sensor fusion",
    "imu", "lidar", "radar", "xbee", "oscilloscope", "multimeter",

    # Mechanical & CAD
    "cad", "solidworks", "autocad", "fusion 360", "inventor", "ansys", "fea", 
    "cfd", "gd&t", "3d printing", "cnc", "blender", "inkscape", "gimp", "krita",

    # Robotics & Control
    "robotics", "kinematics", "dynamics", "control", "pid", "state machine", 
    "path planning", "mechatronics", "haptics", "human-robot interaction", "hmi"
]

discipline_keywords = {
    "electrical": ["electrical engineer", "power systems", "circuit", "analog", "digital electronics"],
    "mechanical": ["mechanical engineer", "thermal", "mechanisms", "manufacturing", "structural"],
    "robotics": ["robotics", "automation", "autonomous", "perception", "motion planning"],
    "embedded": ["embedded systems", "firmware", "microcontroller", "soc"]
}

def get_matches(text, word_list):
    found = []
    for word in word_list:
        if re.search(r'\b' + re.escape(word) + r'\b', text.lower()):
            found.append(word)
    return list(set(found))

# ================================
# LOAD LINKS (Updated for Jobright: Col A, Row 3)
# ================================
# usecols=[0] targets Column A
# skiprows=2 skips the first 2 rows (so Row 3 is the first data row)
try:
    df_links = pd.read_excel(file_path, header=None, usecols=[0], skiprows=2)
    
    # Convert the column to a list and drop any empty cells
    links = df_links.iloc[:, 0].dropna().tolist()

    if not links:
        print(f"❌ No links found in {FILE_NAME} at Column A, Row 3.")
        driver.quit()
        exit()
    else:
        print(f"✅ Successfully loaded {len(links)} links from {FILE_NAME}. Starting extraction...")
except Exception as e:
    print(f"❌ Error loading {FILE_NAME}: {e}")
    driver.quit()
    exit()

# ================================
# SCRAPE LOOP
# ================================
data = []
driver.get("https://app.joinhandshake.com/login") # Login still required for Handshake links
input("Please log in/prepare your browser, then press ENTER...")

for i, link in enumerate(links):
    try:
        print(f"[{i+1}/{len(links)}] Scraping: {link}")
        driver.get(link)
        time.sleep(6) 

        soup = BeautifulSoup(driver.page_source, "html.parser")
        full_text = soup.get_text().lower()

        # Generic Extraction (Works across different sites)
        try:
            title = driver.find_element("tag name", "h1").text
        except:
            title = "N/A"

        # Classification
        matched_fields = [field for field, kws in discipline_keywords.items() if get_matches(full_text, kws)]
        discipline = ", ".join(matched_fields) if matched_fields else "other"
        
        detected_skills = get_matches(full_text, skills)

        data.append({
            "link": link,
            "title": title,
            "discipline": discipline,
            "skills": ", ".join(detected_skills)
        })
        print(f"   ✅ Processed: {title} | Skills Found: {len(detected_skills)}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

# ================================
# SAVE VERSION 2
# ================================
if data:
    df_v2 = pd.DataFrame(data)
    df_v2.to_excel("skillstracker_v2.xlsx", index=False)
    print("\n🚀 Version 2 saved as 'skillstracker_v2.xlsx'")
else:
    print("\n⚠️ No data collected.")

driver.quit()