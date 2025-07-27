# TCAS Program Analysis Dashboard

This project consists of two main components: a web scraper to gather university program data from the [MyTCAS](https://course.mytcas.com) website, and a data dashboard to analyze and visualize this information.

## 1. Web Scraper (`webscraping.py`)

The scraper uses Playwright to automate browsing the MyTCAS website. It searches for specified keywords (e.g., "วิศวกรรมคอมพิวเตอร์", "วิศวกรรมปัญญาประดิษฐ์") and extracts detailed information for each program found.

### Features
- Searches for multiple program queries.
- Navigates to each program's detail page to scrape information.
- Extracts data such as program name, university, tuition fees, and admission round capacity.
- Intelligently parses tuition fee text to calculate a per-semester cost, even when only per-program costs are listed.
- Handles duplicate programs found through different search queries by merging them and adding the new keyword.
- Saves all the collected data into a clean, structured `tcas_data.json` file.

## 2. Analysis Dashboard (`dashboard.py`)

The dashboard is built with Plotly Dash and provides an interactive interface to explore the scraped program data.

### Features
- **Interactive Filters**: Filter the data by program keywords, program type (e.g., Thai, International), and admission rounds.
- **Key Performance Indicators (KPIs)**: At a glance, see the total number of programs, average semester tuition, and the number of universities based on your filters.
- **Visualizations**:
    - **Top 15 Average Tuition**: A bar chart showing the universities with the highest average tuition fees.
    - **Program Type Distribution**: A donut chart illustrating the proportion of different program types.
    - **Tuition Fee Distribution**: A histogram showing the frequency of different tuition fee ranges.
- **Data Table**: A paginated table to view the detailed program data, including clickable links to the original TCAS program page.
- **Download Data**: A link to download the currently filtered data as a CSV file.

---

## How to Set Up and Run the Project

### Prerequisites
- Python 3.7+
- A web browser (the script uses Chromium by default)

### 1. Installation

First, clone or download the project files to your local machine.
```
git clone https://github.com/nimpy-wth/tuitionfee-dashboard.git
```

Create and activate a virtual environment. This keeps the project's dependencies isolated.
```bash
# Create a virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

Install the required Python packages using the `requirements.txt` file:
```bash
pip install -r requirements.txt
```

The scraper uses Playwright, which needs to install browser binaries. Run the following command to install them:
```bash
playwright install
```

### 2. Run the Web Scraper

To collect the data, run the `webscraping.py` script. This may take several minutes as it needs to visit many web pages.
```bash
python webscraping.py
```
This will create the `tcas_data.json` file in the same directory. You can customize the `search_queries` list at the bottom of the file to scrape different programs.

### 3. Run the Dashboard

Once `tcas_data.json` has been created, you can start the dashboard application:
```bash
python dashboard.py
```
The dashboard will be available in your web browser at the following address:
[http://127.0.0.1:8050](http://127.0.0.1:8050)
