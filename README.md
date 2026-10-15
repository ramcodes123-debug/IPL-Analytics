# IPL Analytics Dashboard

\---

## 1\. Project Overview

This project implements an IPL Analytics system for exploring Indian Premier League cricket data.

The project uses ball-by-ball delivery records and match-level information to analyze player performance, team results, venue statistics, match outcomes, and batter-versus-bowler matchups.

The project includes:

* Data loading and inspection
* Data cleaning and preprocessing
* Exploratory Data Analysis (EDA)
* Batting analytics
* Bowling analytics
* Team and match analytics
* Player-versus-player matchup analysis
* Venue analytics
* Advanced analytics
* Interactive Streamlit dashboard
* FastAPI service

\---

## 2\. Problem Statement

Cricket datasets contain detailed information about matches, innings, deliveries, players, teams, and venues. Extracting useful insights from these records manually can be time-consuming.

The objective of this project is to build an analytics system that organizes IPL data and presents useful statistics through interactive visualizations and dashboard pages.

The dashboard helps users explore player performance, compare teams and players, review venue statistics, and analyze individual matches.

\---

## 3\. Dataset

The project uses IPL match metadata and ball-by-ball delivery data stored as CSV files.

### Delivery data

Delivery records can include:

* Match ID and season
* Innings and ball information
* Batting team and bowling team
* Striker, non-striker, and bowler
* Runs off the bat and extras
* Wicket type and dismissed player
* Venue and match date

### Match data

Match-level information can include:

* Match ID and season
* Teams
* Date and venue
* Toss winner and toss decision
* Player of the match
* Winner and victory margin
* Match type and overs

The main processed datasets are expected at:

```text
DATA/PROCESSED/deliveries.csv
DATA/PROCESSED/matches.csv
```

**Data coverage note:** The processed datasets inspected during development did not contain seasons 2010 and 2020. Confirm source-data coverage and preprocessing before treating the dataset as complete across all IPL seasons.

\---

## 4\. Technologies Used

### Programming Language

* Python

### Data Analysis

* Pandas
* NumPy

### Visualization

* Plotly
* Matplotlib
* Seaborn

### Dashboard

* Streamlit

### API

* FastAPI
* Uvicorn

### Development Environment

* JupyterLab
* Git
* GitHub

### Deployment

* Docker

\---

## 5\. Analytics Workflow

The overall workflow is:

```text
Raw IPL Match Data
        ↓
Data Loading
        ↓
Data Inspection
        ↓
Data Cleaning and Preprocessing
        ↓
Feature Preparation
        ↓
Player / Team / Match / Venue Analytics
        ↓
Statistical Summaries
        ↓
Visualizations
        ↓
Streamlit Dashboard / FastAPI
```

\---

## 6\. Project Structure

```text
INDIAN PREMIER LEAGUE/
├── API/
│   └── main.py
├── APP/
│   └── streamlit\_app.py
├── DATA/
│   ├── RAW/
│   └── PROCESSED/
│       ├── deliveries.csv
│       ├── matches.csv
│       ├── BATTING/
│       ├── BOWLING/
│       ├── TEAM\_MATCH/
│       └── ADVANCED\_ANALYTICS/
├── NOTEBOOKS/
├── SRC/
│   ├── config.py
│   ├── data\_loader.py
│   ├── preprocessing.py
│   ├── player\_analytics.py
│   ├── team\_analytics.py
│   ├── matchup\_analytics.py
│   ├── match\_analytics.py
│   ├── venue\_analytics.py
│   └── visualizations.py
├── TESTS/
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

\---

## 7\. Data Loading

The data-loading workflow reads the IPL delivery and match datasets for use by the analytics modules and dashboard.

The reusable data-loading implementation is located in:

```text
SRC/data\_loader.py
```

The project configuration and data paths are maintained in:

```text
SRC/config.py
```

The processed files must be available at the paths expected by the project's configuration.

\---

## 8\. Data Preprocessing

Preprocessing prepares the delivery data for reliable analysis.

Depending on the source columns and the processing workflow, preparation can include:

* Standardizing team names
* Converting numeric fields to appropriate types
* Handling missing values
* Preparing total-run calculations
* Identifying legal deliveries
* Preparing bowler-conceded runs
* Preparing wicket-related fields
* Excluding fields that would cause target leakage from relevant predictive analyses

The preprocessing implementation is located in:

```text
SRC/preprocessing.py
```

\---

## 9\. Exploratory Data Analysis

Exploratory Data Analysis (EDA) helps understand the structure, quality, and coverage of the IPL datasets.

The analysis can include:

* Dataset shape and column inspection
* Season coverage
* Match and delivery counts
* Team and venue coverage
* Missing-value inspection
* Run-scoring patterns
* Player performance distributions
* Match-result summaries
* Visualizations of important statistics

The EDA notebooks are available in:

```text
NOTEBOOKS/
```

Refer to the numbered notebook filenames in that folder for the relevant workflow.

\---

## 10\. Batting Analytics

Batting analytics summarizes player scoring performance using delivery-level data.

Possible statistics include:

* Runs scored
* Innings played
* Balls faced, where supported by the data
* Boundaries
* Highest individual innings score
* Season-level batting performance
* Top batters and batting leaderboards

The implementation is located in:

```text
SRC/player\_analytics.py
```

\---

## 11\. Bowling Analytics

Bowling analytics summarizes bowling performance using delivery-level data.

Possible statistics include:

* Wickets credited to the bowler
* Runs conceded
* Overs and legal deliveries
* Bowling figures by match or innings
* Season-level bowling performance
* Top bowlers and bowling leaderboards

Dismissals that are not credited to the bowler should be handled appropriately when calculating bowler wickets.

The implementation is located in:

```text
SRC/player\_analytics.py
```

\---

## 12\. Team Analytics

Team analytics supports the comparison of IPL teams and their results.

The analysis can include:

* Matches played
* Wins and losses, where match results are available
* Season-level team performance
* Head-to-head results
* Leading batters for a selected team
* Leading bowlers for a selected team

The implementation is located in:

```text
SRC/team\_analytics.py
```

\---

## 13\. Player Matchup Analytics

Player matchup analysis compares a batter against one or more bowlers using delivery-level records.

The dashboard supports matchup exploration such as:

* One batter versus one bowler
* Two batters versus one bowler
* One batter versus two bowlers

The available statistics depend on the selected players and the underlying delivery data.

The implementation is located in:

```text
SRC/matchup\_analytics.py
```

\---

## 14\. Match Analytics

Match analytics provides match-level and innings-level details.

It can be used to explore match information, scorecards, and innings summaries based on the available dataset.

The implementation is located in:

```text
SRC/match\_analytics.py
```

\---

## 15\. Venue Analytics

Venue analytics explores IPL statistics grouped by venue.

The analysis can include:

* Matches played at a venue
* Match results by venue
* Season-level venue summaries
* Venue comparisons where supported by the data

The implementation is located in:

```text
SRC/venue\_analytics.py
```

\---

## 16\. Advanced Analytics

The project includes processed analytics outputs organized into subfolders under:

```text
DATA/PROCESSED/
```

These may include batting, bowling, team-match, and advanced analytics summaries. The exact outputs depend on which notebooks and processing scripts have been run.

\---

## 17\. Streamlit Dashboard

The interactive dashboard is implemented in:

```text
APP/streamlit\_app.py
```

The dashboard includes these main pages:

1. Overview
2. Player Analytics
3. Team Analytics
4. Head-to-Head
5. Player vs Player
6. Venue Analytics
7. Match Explorer

The dashboard uses a dark theme with teal and cyan accents and page-specific filters.

\---

## 18\. API

The FastAPI application entry point is:

```text
API/main.py
```

The API provides programmatic access to the functionality implemented in the API module. Available endpoints depend on the current implementation.

FastAPI's interactive documentation can be accessed at:

```text
http://127.0.0.1:8000/docs
```

when the API is running.

\---

## 19\. Installation

### Clone the repository

```bash
git clone https://github.com/ramcodes123-debug/IPL-Analytics.git
cd IPL-Analytics
```

### Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
```

**macOS/Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run these commands from the project root.

\---

## 20\. Running the Streamlit Dashboard

From the project root, run:

```bash
streamlit run APP/streamlit\_app.py
```

Streamlit will print a local address, usually:

```text
http://localhost:8501
```

Open that address in a browser.

The dashboard requires the processed datasets at the paths expected by the project's configuration. The large delivery and match CSV files may not be included in GitHub because they are excluded by `.gitignore`.

\---

## 21\. Running the API

If `API/main.py` exposes a FastAPI application instance named `app`, start the API from the project root with:

```bash
python -m uvicorn API.main:app --reload
```

The API is normally available at:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

If the application instance uses a different name, adjust the command to match `API/main.py`.

\---

## 22\. Docker Deployment

The project includes a Dockerfile for running the Streamlit dashboard.

Build the image from the project root:

```bash
docker build -t ipl-analytics .
```

Run the container:

```bash
docker run --rm -p 8501:8501 ipl-analytics
```

Open:

```text
http://localhost:8501
```

The application also needs access to the processed datasets. If the data files are excluded from the Docker image, mount the local processed-data directory when starting the container. For Windows PowerShell:

```powershell
docker run --rm -p 8501:8501 `
  -v "${PWD}\\DATA\\PROCESSED:/app/DATA/PROCESSED" `
  ipl-analytics
```

This Dockerfile is configured for the Streamlit dashboard; the API would need its own container command or a separate service configuration.

\---

## 23\. Data Files and GitHub

The GitHub repository is:

https://github.com/ramcodes123-debug/IPL-Analytics

The `.gitignore` excludes raw source data and the large processed `deliveries.csv` and `matches.csv` files, along with notebook checkpoints and environment files.

Consequently, a fresh clone may not contain the data needed to run the dashboard. Place the required processed datasets in `DATA/PROCESSED/` or update the data-loading configuration to point to their actual location.

Before redistributing data, check its license and attribution requirements.

\---

## 24\. Data Coverage

During development, the processed datasets were found to contain seasons 2009, 2011–2019, and 2021–2026. Seasons 2010 and 2020 were absent from the processed files at that time.

This does not by itself establish why those seasons are absent. Check the source data and preprocessing workflow before claiming complete coverage across all IPL seasons.

\---

## 25\. Troubleshooting

### Processed CSV file not found

Confirm that the expected files exist:

```text
DATA/PROCESSED/deliveries.csv
DATA/PROCESSED/matches.csv
```

Check `SRC/config.py` and `SRC/data\_loader.py` for the paths used by the project.

### Module import errors

Run Streamlit and Uvicorn from the project root rather than from inside `APP/`, `API/`, or `SRC/`.

### Missing Python package

Activate the intended virtual environment and run:

```bash
pip install -r requirements.txt
```

### Port already in use

For Streamlit in Docker, use a different host port:

```bash
docker run --rm -p 8502:8501 ipl-analytics
```

Then open `http://localhost:8502`.

\---

## 26\. Future Improvements

Possible future improvements include:

* Completing and validating missing season coverage
* Adding further player and team comparisons
* Improving venue-level visualizations and maps
* Adding more match and innings breakdowns
* Improving API endpoint documentation
* Automating data updates and preprocessing
* Deploying the dashboard to a hosting platform
* Adding screenshots and usage examples to the repository

\---

## 27\. Author and Repository

**Name:** SITARAM

**GitHub profile:** https://github.com/ramcodes123-debug

**Project repository:** https://github.com/ramcodes123-debug/IPL-Analytics

\---

## 28\. License

This project is developed for educational and project submission purposes.



