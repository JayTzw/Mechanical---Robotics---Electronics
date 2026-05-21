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
# ================================
# UPDATED CONFIGURATION
# ================================
options = Options()

# 1. Path to the 'User Data' folder
options.add_argument(r"--user-data-dir=C:\Users\mudiw\AppData\Local\Google\Chrome\User Data")

# 2. The specific profile folder name you just found
options.add_argument(r"--profile-directory=Profile 1")

# Optional: These help prevent "automated software" detection
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options)

# Your expanded skills list
skills = [
    "python", "c++", "matlab", "arduino", "ros", "ros2", "opencv", "pytorch", 
    "cad", "solidworks", "altium", "pcb", "mechatronics", "embedded", "firmware", 
    "kinematics", "dynamics", "control", "pid", "state machine", "path planning", 
    "sensor fusion", "imu", "lidar", "radar", "haptics", "human-robot interaction",
    "i2c", "spi", "uart", "rtos", "fpga", "ansys", "gd&t"
]

def get_matches(text, word_list):
    found = []
    for word in word_list:
        if re.search(r'\b' + re.escape(word) + r'\b', text.lower()):
            found.append(word)
    return list(set(found))

# ================================
# LOGIN HANDLER
# ================================
driver.get("https://jobright.ai/jobs/recommend")

print("\n🔒 LOGIN REQUIRED")
print("--------------------------------------------------")
print("1. Log in manually (use Google/LinkedIn if PWD is blocked).")
print("2. Navigate to your recommended jobs or search results.")
print("--------------------------------------------------")

while True:
    user_ready = input("Are you logged in and looking at the job list? (type 'yes'): ")
    if user_ready.lower() == 'yes':
        # Broad selector for job cards
        cards = driver.find_elements("css selector", "div[class*='JobCard'], div[class*='item']")
        if cards:
            print("✅ Job cards detected. Starting sweep...")
            break
        else:
            print("⚠️ No job cards found yet. Check if the page fully loaded.")

# ================================
# SCRAPE LOOP
# ================================
all_data = []
processed_links = set()

while len(all_data) < TOTAL_TARGET:
    # Refresh card list after each scroll/batch
    cards = driver.find_elements("css selector", "div[class*='JobCard'], div[class*='item']")
    
    new_cards_in_view = 0
    for card in cards:
        if len(all_data) >= TOTAL_TARGET:
            break
            
        try:
            # Scroll to card and click to load details in the right pane
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
            time.sleep(1)
            card.click()
            time.sleep(3) # Wait for detail pane to load

            current_link = driver.current_url
            if current_link in processed_links:
                continue
            
            # Scrape details
            soup = BeautifulSoup(driver.page_source, "html.parser")
            text = soup.get_text().lower()

            try:
                title = driver.find_element("css selector", "h1, h2[class*='title']").text
            except:
                title = "Unknown Job"

            detected_skills = get_matches(text, skills)
            
            all_data.append({
                "link": current_link,
                "title": title,
                "skills": ", ".join(detected_skills),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            processed_links.add(current_link)
            new_cards_in_view += 1

            print(f"[{len(all_data)}/{TOTAL_TARGET}] Scraped: {title}")

            # Batch Save
            if len(all_data) % BATCH_SIZE == 0:
                pd.DataFrame(all_data).to_excel(f"jobright_batch_{len(all_data)//BATCH_SIZE}.xlsx", index=False)
                print(f"💾 Milestone saved: {len(all_data)} jobs.")

        except Exception as e:
            continue

    # If we didn't find anything new, scroll down to load more jobs
    if new_cards_in_view == 0:
        print("⏬ Scrolling to load more jobs...")
        driver.execute_script("window.scrollBy(0, 2000);")
        time.sleep(5)
    
    # Safety break if we get stuck
    if len(cards) > 1000: # Handshake/Jobright can get laggy with too many DOM elements
        print("⚠️ Page limit reached. Finalizing current data.")
        break

# ================================
# FINAL SAVE
# ================================
if all_data:
    pd.DataFrame(all_data).to_excel("jobright_final_500.xlsx", index=False)
    print(f"🏁 Mission Complete! Total jobs: {len(all_data)}")
else:
    print("⚠️ No data was collected.")

driver.quit()