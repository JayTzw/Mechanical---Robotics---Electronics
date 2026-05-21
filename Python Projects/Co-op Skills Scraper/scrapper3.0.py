import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime

# ================================
# CONFIGURATION
# ================================
BATCH_SIZE = 50
TOTAL_TARGET = 500

# Targeted keywords to ensure we only scrape relevant jobs
TARGET_KEYWORDS = ["robotics", "mechanical", "mechatronics", "hardware", "automation","electronic","electrical", "control", "embedded", "manufacturing"]

options = Options()
options.add_argument(r"--user-data-dir=C:\Users\mudiw\Downloads\ChromeSelenium")
driver = webdriver.Chrome(options=options)

skills = [
    "python", "c++", "matlab", "arduino", "ros", "ros2", "opencv", "pytorch",
    "cad", "solidworks", "altium", "pcb", "mechatronics", "embedded", "firmware",
    "kinematics", "dynamics", "control", "pid", "state machine", "path planning",
    "sensor fusion", "imu", "lidar", "radar", "haptics", "human-robot interaction",
    "i2c", "spi", "uart", "rtos", "fpga", "ansys", "gd&t"
]

def get_matches(text, word_list):
    found = []
    text = text.lower()
    for word in word_list:
        # Use a more flexible regex that handles symbols like ++ or &
        pattern = r'(?i)\b' + word + r'\b'
        if re.search(pattern, text):
            found.append(word.replace("\\", ""))
    return list(set(found))

def is_relevant(title, text):
    combined = (title + " " + text).lower()
    return any(keyword in combined for keyword in TARGET_KEYWORDS)

# ================================
# SCRAPE ENGINE
# ================================
driver.get("https://app.joinhandshake.com/stu/jobs")

print("👉 ACTION REQUIRED:")
print("1. Apply filters (Mechanical Engineering, Robotics, etc.) in the browser.")
print("2. Ensure the job list is visible on the left.")
input("\nPress ENTER here to start scraping...")

all_data = []
processed_links = set()

while len(all_data) < TOTAL_TARGET:
    try:
        # Find all job links in the sidebar
        job_elements = driver.find_elements("css selector", "a[href*='/jobs/']")
        
        current_links = []
        for el in job_elements:
            href = el.get_attribute("href")
            if href and "/jobs/" in href:
                clean_link = href.split('?')[0]
                # Pre-filter by title if possible to save time
                try:
                    title_text = el.text.lower()
                    if any(k in title_text for k in TARGET_KEYWORDS):
                        current_links.append(clean_link)
                except:
                    current_links.append(clean_link)

        current_links = list(dict.fromkeys(current_links))
        new_links = [l for l in current_links if l not in processed_links]

    except Exception as e:
        print(f"⚠️ Sidebar error: {e}")
        new_links = []

    if not new_links:
        print("⏸️ No new relevant links. Scrolling...")
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(3)
        continue

    for link in new_links:
        if len(all_data) >= TOTAL_TARGET: break
        
        try:
            driver.get(link)
            time.sleep(4) # Wait for description to load
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            page_text = soup.get_text().lower()
            
            try:
                # Handshake titles are usually in an h1 or a specific data attribute
                title = driver.find_element("tag name", "h1").text
            except:
                title = "Unknown Title"

            # FINAL VALIDATION: Is this job actually what we want?
            if is_relevant(title, page_text):
                detected_skills = get_matches(page_text, skills)
                
                all_data.append({
                    "link": link,
                    "title": title,
                    "skills": ", ".join(detected_skills),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                print(f"✅ [{len(all_data)}/{TOTAL_TARGET}] Saved: {title}")
                
                # Batch save
                if len(all_data) % BATCH_SIZE == 0:
                    pd.DataFrame(all_data).to_excel(f"jobs_checkpoint_{len(all_data)}.xlsx", index=False)
            else:
                print(f"⏩ Skipped (Irrelevant): {title}")

            processed_links.add(link)
            driver.back()
            time.sleep(2)

        except Exception as e:
            print(f"❌ Error processing {link}: {e}")
            driver.get("https://app.joinhandshake.com/stu/jobs")
            time.sleep(4)

# ================================
# FINAL SAVE
# ================================
if all_data:
    final_df = pd.DataFrame(all_data)
    final_df.to_excel("final_robotics_meche_jobs.xlsx", index=False)
    print(f"🏁 Done! Total relevant jobs saved: {len(all_data)}")
else:
    print("❌ No jobs were saved. Check your keyword filters.")

driver.quit()