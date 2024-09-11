from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import json
from datetime import datetime
import sys
import tkinter as tk
from tkinter import ttk
import threading
import webbrowser

# Set up Chrome options
options = Options()
options.add_argument("--headless=new")
options.headless = True

# Initialize an empty dictionary to store the jobs
jobs = {}

# Create the main window
root = tk.Tk()
root.title("Job Search")

# Create a frame for URL entry
url_frame = tk.Frame(root)
url_frame.pack(fill=tk.X, padx=5, pady=5)

# Create a label and entry field for URL
url_label = tk.Label(url_frame, text="URL:")
url_label.pack(side=tk.LEFT)
url_var = tk.StringVar()
url_entry = tk.Entry(url_frame, textvariable=url_var)
url_entry.pack(fill=tk.X, expand=True)

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

    # Get the URL from the URL entry field
    url = url_var.get()

    # Get the number of pages from the page entry field
    try:
        num_pages = int(page_var.get())
    except ValueError:
        status_var.set("Invalid number of pages.")
        return

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(options=options)

    try:
        # Iterate over the pages
        for page in range(1, num_pages + 1):
            # Update the status bar
            status_var.set(f"Fetching jobs from page {page}...")

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

                    tree.insert('', 'end', values=(job['title'], job['advertiser']['description'], job['workType'], location, f"{time_difference.days} Days Ago"))

                    # Sort the tree view by date posted
                    sort_tree_date('Listed')

            # Update the GUI
            root.update_idletasks()

            # Update the status bar
            status_var.set("Finished fetching jobs.")

    # Gracefully catch any errors and display message
    except:
        status_var.set("Couldn't fetch any more jobs (Error)")

    # Close the browser
    finally:
        driver.quit()

# Create a tree view
tree = ttk.Treeview(root, columns=('Title', 'Company', 'Work Type', 'Location', 'Listed'))
tree.heading('Title', text='Title', command=lambda: sort_tree_abc('Title'))
tree.heading('Company', text='Company', command=lambda: sort_tree_abc('Company'))
tree.heading('Work Type', text='Work Type', command=lambda: sort_tree_abc('Work Type'))
tree.heading('Location', text='Location', command=lambda: sort_tree_abc('Location'))
tree.heading('Listed', text='Listed', command=lambda: sort_tree_date('Listed'))
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
                location = job['area']
            listing_date = datetime.strptime(job['listingDate'], "%Y-%m-%dT%H:%M:%SZ")
            now = datetime.now()
            time_difference = now - listing_date
            tree.insert('', 'end', values=(job['title'], job['advertiser']['description'], job['workType'], location, f"{time_difference.days} Days Ago"))

# Function to sort the tree view by alphabetical order
def sort_tree_abc(column):
    items = [(tree.set(child, column), child) for child in tree.get_children('')]
    items.sort()
    for index, (value, child) in enumerate(items):
        tree.move(child, '', index)

# Function to sort the tree view by date posted
def sort_tree_date(column):
    items = [(int(tree.set(child, column).split(' ')[0]), child) for child in tree.get_children('')]
    items.sort(reverse=False)  # reverse=True will sort from newest to oldest
    for index, (value, child) in enumerate(items):
        tree.move(child, '', index)

def open_job_url(event):
    # Get the selected item
    item = tree.selection()[0]
    # Get the job ID from the 'jobs' dictionary using the job title
    job_id = [job['id'] for job in jobs.values() if job['title'] == tree.item(item)['values'][0]][0]
    # Open the URL in the default web browser
    webbrowser.open(f'https://seek.com.au/job/{job_id}')

# Update the tree view when the search term changes
search_var.trace('w', update_search)

# Start the main loop
root.mainloop()
