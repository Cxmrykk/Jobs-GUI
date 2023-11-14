from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import json
from datetime import datetime

# Set up Chrome options
options = Options()
options.add_argument("--headless=new")
options.headless = True

# Create a new instance of the Chrome driver
driver = webdriver.Chrome(options=options)

# Initialize an empty dictionary to store the jobs
jobs = {}

# Iterate over the pages
for page in range(1, 11):
    # Go to the Seek page
    driver.get(f'https://www.seek.com.au/jobs/in-Linley-Point-NSW-2066?distance=5&sortmode=ListedDate&worktype=243%2C245&page={page}')

    # Get the source of the page
    html = driver.page_source

    # Find the first text that matches the pattern
    pattern = re.compile('window\\.SEEK_REDUX_DATA = (\\{[^\\n]+\\});\\n')
    match = pattern.search(html)

    if match:
        # Replace 'undefined' with 'null'
        json_text = re.sub('"(.*?)"\\s*:\\s*undefined', '"\\1": null', match.group(1))

        # Convert the JSON text to a Python dictionary
        data = json.loads(json_text.strip())

        # Iterate over the jobs
        for job in data["results"]["results"]["jobs"]:
            # Add the job to the dictionary
            jobs[job['id']] = job

# Close the browser
driver.quit()

# Function to truncate
def truncate(content, length):
    return (content[:length] + ' ' * length)[:length]

# Print the jobs
for id, job in jobs.items():
    content = ""

    # print job title
    content += f"{truncate(job['title'], 30):<30} | "

    # print company
    content += f"{truncate(job['advertiser']['description'], 26):<26} | "

    # print work type
    content += f"{truncate(job['workType'], 20):<20} | "

    # print location
    try:
        content += f"{truncate(job['suburb'], 20):<20} | "
    except:
        content += f"{truncate(job['area'], 20):<20} | "
    
    # Calculate the difference in time from the listing date to now
    listing_date = datetime.strptime(job['listingDate'], "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.now()
    time_difference = now - listing_date
    content += f"{time_difference.days:<3} Days Ago"

    print(content)
