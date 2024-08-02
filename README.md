<div align="center">
    <img src="assets/window.png">
</div>

### Setup
```sh
# Clone source code
git clone https://github.com/Cxmrykk/Seek-GUI.git
cd Seek-GUI

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install selenium

# Execute the program
python -m scraper
```

### Usage
1. Visit [Seek.com.au](https://seek.com.au/) in your broser and create a job search query
2. Copy the browser URL after the page has loaded
3. Open the GUI, paste into the "URL" field and click "Search"
