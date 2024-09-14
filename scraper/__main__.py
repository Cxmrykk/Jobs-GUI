#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import re
import json
from datetime import datetime
import sys
import tkinter as tk
from tkinter import ttk
import threading
import webbrowser

# Set up Chrome options
#options = Options()
#options.add_argument("--headless=new")
#options.headless = True

# Initialize an empty dictionary to store the jobs
jobs = {}

# Create the main window
root = tk.Tk()
root.title("Job Search")

# Create a frame for Seek URL entry
seek_url_frame = tk.Frame(root)
seek_url_frame.pack(fill=tk.X, padx=5, pady=5)

# Create a label and entry field for Seek URL
seek_url_label = tk.Label(seek_url_frame, text="Seek URL:")
seek_url_label.pack(side=tk.LEFT)
seek_url_var = tk.StringVar()
seek_url_entry = tk.Entry(seek_url_frame, textvariable=seek_url_var)
seek_url_entry.pack(fill=tk.X, expand=True)

# Create a frame for Indeed URL entry
indeed_url_frame = tk.Frame(root)
indeed_url_frame.pack(fill=tk.X, padx=5, pady=5)

# Create a label and entry field for Indeed URL
indeed_url_label = tk.Label(indeed_url_frame, text="Indeed URL:")
indeed_url_label.pack(side=tk.LEFT)
indeed_url_var = tk.StringVar()
indeed_url_entry = tk.Entry(indeed_url_frame, textvariable=indeed_url_var)
indeed_url_entry.pack(fill=tk.X, expand=True)

# Create a frame for page number entry
page_frame = tk.Frame(root)
page_frame.pack(fill=tk.X, padx=5, pady=5)

# Create a label and entry field for page number
page_label = tk.Label(page_frame, text="Number of Pages:")
page_label.pack(side=tk.LEFT)
page_var = tk.StringVar(value="30")  # Default value is 30
page_entry = tk.Entry(page_frame, textvariable=page_var)
page_entry.pack(fill=tk.X, expand=True)

# Create a "Search" button
search_button = tk.Button(root, text="Search", command=lambda: threading.Thread(target=fetch_jobs).start())
search_button.pack(fill=tk.X, padx=5, pady=5)

# Create a status bar
status_var = tk.StringVar()
status_bar = tk.Label(root, textvariable=status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

def fetch_jobs():
    # Clear the existing results
    for item in tree.get_children():
        tree.delete(item)
    jobs.clear()

    # Get the URLs and number of pages
    seek_url = seek_url_var.get()
    indeed_url = indeed_url_var.get()
    try:
        num_pages = int(page_var.get())
    except ValueError:
        status_var.set("Invalid number of pages.")
        return

    # Create a new instance of the Chrome driver
    #driver = webdriver.Chrome(options=options)
    driver = uc.Chrome(headless=False, use_subprocess=False)

    try:
        # Fetch Seek jobs
        if seek_url:
            fetch_seek_jobs(driver, seek_url, num_pages)

        # Fetch Indeed jobs
        if indeed_url:
            fetch_indeed_jobs(driver, indeed_url, num_pages)

        # Update the status bar
        status_var.set("Finished fetching jobs.")

    # Gracefully catch any errors and display message
    except Exception as e:
        status_var.set(f"Couldn't fetch jobs (Error: {e})")

    # Close the browser
    finally:
        driver.quit()

def fetch_seek_jobs(driver, url, num_pages):
    for page in range(1, num_pages + 1):
        # Update the status bar
        status_var.set(f"Fetching Seek jobs from page {page}...")

        # Go to the Seek page
        driver.get(f'{url}&page={page}')

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

                # Calculate the difference in time from the listing date to now
                listing_date = datetime.strptime(job['listingDate'], "%Y-%m-%dT%H:%M:%SZ")
                now = datetime.now()
                time_difference = now - listing_date

                # Add the job to the tree view
                try:
                    location = job['suburb']
                except:
                    location = job['area']

                tree.insert('', 'end', values=(job['title'], job['advertiser']['description'], job['workType'], location, f"{time_difference.days} Days Ago", "Seek"))

                # Sort the tree view by date posted
                sort_tree_date('Listed')

        # Update the GUI
        root.update_idletasks()

def fetch_indeed_jobs(driver, url, num_pages):
    for page in range(0, num_pages * 10, 10):
        # Update the status bar
        status_var.set(f"Fetching Indeed jobs from page {page // 10 + 1}...")

        # Go to the Indeed page
        driver.get(f'{url}&start={page}')

        # Get the source of the page
        html = driver.page_source

        # Find the script tag containing job data
        script_tag = re.findall(r'window.mosaic.providerData\["mosaic-provider-jobcards"\]=(\{.+?\});', html)

        if script_tag:
            # Convert the JSON text to a Python dictionary
            json_blob = json.loads(script_tag[0])

            # Extract jobs from the search page
            jobs_list = json_blob['metaData']['mosaicProviderJobCardsModel']['results']
            for index, job in enumerate(jobs_list):
                if job.get('jobkey') is not None:
                    # Add the job to the dictionary
                    jobs[job['jobkey']] = job

                    # Add the job to the tree view
                    try:
                        # Try to parse the date as a timestamp (milliseconds since epoch)
                        timestamp_ms = int(job.get('pubDate'))
                        date_obj = datetime.fromtimestamp(timestamp_ms / 1000)  # Convert to seconds
                        time_difference = datetime.now() - date_obj
                        listed_date = f"{time_difference.days} Days Ago"
                    except:
                        # If parsing fails, assume it's a date string and calculate days ago
                        try:
                            date_obj = datetime.strptime(job.get('pubDate'), "%a, %d %b %Y %H:%M:%S GMT")
                            time_difference = datetime.now() - date_obj
                            listed_date = f"{time_difference.days} Days Ago"
                        except:
                            # If both parsing attempts fail, display the original date string
                            listed_date = job.get('pubDate')

                    tree.insert('', 'end', values=(
                        job.get('title'),
                        job.get('company'),
                        ", ".join(job.get('jobTypes')),  # Get workType from Indeed data
                        f"{job.get('jobLocationCity')}, {job.get('jobLocationState')}",
                        listed_date,
                        "Indeed"
                    ))

                    # Sort the tree view by date posted
                    sort_tree_date('Listed')

        # Update the GUI
        root.update_idletasks()

# Create a tree view
tree = ttk.Treeview(root, columns=('Title', 'Company', 'Work Type', 'Location', 'Listed', 'Source'))
tree.heading('Title', text='Title', command=lambda: sort_tree_abc('Title'))
tree.heading('Company', text='Company', command=lambda: sort_tree_abc('Company'))
tree.heading('Work Type', text='Work Type', command=lambda: sort_tree_abc('Work Type'))
tree.heading('Location', text='Location', command=lambda: sort_tree_abc('Location'))
tree.heading('Listed', text='Listed', command=lambda: sort_tree_date('Listed'))
tree.heading('Source', text='Source', command=lambda: sort_tree_abc('Source'))
tree['show'] = 'headings'
tree.pack(fill=tk.BOTH, expand=1, padx=5, pady=5)
tree.bind('<Double-1>', lambda e: open_job_url(e))

# Create a search bar
search_frame = tk.Frame(root)
search_frame.pack(fill=tk.X, padx=5, pady=5)
search_label = tk.Label(search_frame, text="Filter Text:")
search_label.pack(side=tk.LEFT)
search_var = tk.StringVar()
search_bar = tk.Entry(search_frame, textvariable=search_var)
search_bar.pack(fill=tk.X, expand=True)

# Function to update the tree view with the search results
def update_search(*args):
    search_term = search_var.get()
    for item in tree.get_children():
        tree.delete(item)
    for id, job in jobs.items():
        if search_term.lower() in job['title'].lower():
            try:
                location = job['suburb']
            except:
                try:
                    location = job['area']
                except:
                    location = f"{job.get('jobLocationCity')}, {job.get('jobLocationState')}"

            try:
                listing_date = datetime.strptime(job['listingDate'], "%Y-%m-%dT%H:%M:%SZ")
                now = datetime.now()
                time_difference = now - listing_date
                listed_date = f"{time_difference.days} Days Ago"
            except:
                listed_date = job.get('pubDate')

            try:
                source = "Seek"
                work_type = job['workType']
                company = job['advertiser']['description']
            except:
                source = "Indeed"
                work_type = "N/A"
                company = job.get('company')

            tree.insert('', 'end', values=(job['title'], company, work_type, location, listed_date, source))

# Function to sort the tree view by alphabetical order
def sort_tree_abc(column):
    items = [(tree.set(child, column), child) for child in tree.get_children('')]
    items.sort()
    for index, (value, child) in enumerate(items):
        tree.move(child, '', index)

# Function to sort the tree view by date posted
def sort_tree_date(column):
    items = []
    for child in tree.get_children(''):
        try:
            value = int(tree.set(child, column).split(' ')[0])
        except:
            value = 0  # Assign 0 for "Just posted" or other non-numeric values
        items.append((value, child))
    items.sort(reverse=False)  # reverse=True will sort from newest to oldest
    for index, (value, child) in enumerate(items):
        tree.move(child, '', index)

def open_job_url(event):
    # Get the selected item
    item = tree.selection()[0]
    # Get the job title and source
    job_title = tree.item(item)['values'][0]
    source = tree.item(item)['values'][5]

    if source == "Seek":
        # Get the job ID from the 'jobs' dictionary using the job title
        job_id = [job['id'] for job in jobs.values() if job['title'] == job_title][0]
        # Open the URL in the default web browser
        webbrowser.open(f'https://seek.com.au/job/{job_id}')
    elif source == "Indeed":
        # Get the jobkey from the 'jobs' dictionary using the job title
        jobkey = [job['jobkey'] for job in jobs.values() if job['title'] == job_title][0]
        # Open the URL in the default web browser
        webbrowser.open(f'https://www.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={jobkey}')

# Update the tree view when the search term changes
search_var.trace('w', update_search)

# Start the main loop
root.mainloop()