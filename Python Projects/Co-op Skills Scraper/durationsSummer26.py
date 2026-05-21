import pandas as pd
import yt_dlp
import time

def get_total_duration_hours(url):
    """
    Connects to YouTube using yt-dlp to extract metadata and compute 
    the total duration of a single video or an entire playlist in hours.
    """
    if not isinstance(url, str) or not url.strip():
        return None
        
    ydl_opts = {
        'skip_download': True,
        'extract_flat': False,  # MUST be False to fetch individual video durations in a playlist
        'quiet': True,
        'no_warnings': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url.strip(), download=False)
            
            # Case A: The link is a playlist containing multiple entries
            if 'entries' in info:
                total_seconds = 0
                for entry in info['entries']:
                    if entry and 'duration' in entry and entry['duration'] is not None:
                        total_seconds += entry['duration']
                return round(total_seconds / 3600.0, 2) # Convert seconds to hours
                
            # Case B: The link is a single standalone video
            else:
                seconds = info.get('duration', 0)
                if seconds:
                    return round(seconds / 3600.0, 2)
                return 0.0
    except Exception as e:
        print(f"  [Error] Could not fetch duration for {url}: {e}")
        return None

# 1. Load the original Excel file (Swapped to read_excel)
file_path = r'C:\Users\mudiw\OneDrive\Desktop\Internships Summer 2026\Co-op Skills Scraper\Summer 2026 Plan.xlsx'
df = pd.read_excel(file_path, header=1)

print("🚀 Starting to explore YouTube links from Column D...")

# Ensure the HOURS column exists and is treated as a float type
if 'HOURS' not in df.columns:
    df['HOURS'] = None

# 2. Iterate over the dataframe rows and fetch the duration
for index, row in df.iterrows():
    url = row['LINKS']
    
    # Check if the row contains a valid YouTube link
    if pd.notna(url) and isinstance(url, str) and ('youtube.com' in url or 'youtu.be' in url):
        resource_name = row['RESOURCES'] if pd.notna(row['RESOURCES']) else f"Row {index+1}"
        print(f"⏳ Processing: '{resource_name}'")
        
        # Fetch the total hours
        hours = get_total_duration_hours(url)
        
        if hours is not None:
            # Retain and insert the total duration into the 'HOURS' column
            df.at[index, 'HOURS'] = hours
            print(f"  ✅ Retained: {hours} hours")
        
        # Respectful rate limiting pause (slightly increased since it's parsing playlists deeper now)
        time.sleep(1.0)

# 3. Save the modified DataFrame to a new file 
# Saving as an Excel file keeps it clean, or change to .csv if you strictly want a CSV output.
output_file = r'C:\Users\mudiw\OneDrive\Desktop\Internships Summer 2026\Co-op Skills Scraper\Summer_2026_Plan_With_Durations.xlsx'
df.to_excel(output_file, index=False)

print(f"\n🎉 Process Complete! The updated plan has been saved to: '{output_file}'")