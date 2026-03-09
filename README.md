# KSURA — Kansas State University Regenerative Agriculture Web Application

A Streamlit-based web application for managing, visualizing, and analyzing regenerative agriculture research data at Kansas State University.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Prerequisites](#prerequisites)
7. [Installation](#installation)
8. [Configuration](#configuration)
9. [Running the Application](#running-the-application)
10. [Module Documentation](#module-documentation)
    - [app.py — Main Application Entry Point](#apppy--main-application-entry-point)
    - [view.py — View Data Module](#viewpy--view-data-module)
    - [upload.py — Upload Data Module](#uploadpy--upload-data-module)
    - [visualization.py — Visualizations Hub](#visualizationpy--visualizations-hub)
    - [visualize.py — Create Visualizations](#visualizepy--create-visualizations)
    - [display_visualizations.py — View Visualizations](#display_visualizationspy--view-visualizations)
    - [data_schedule.py — Data Schedule Module](#data_schedulepy--data-schedule-module)
    - [about.py — About Us Page](#aboutpy--about-us-page)
    - [contact.py — Contact Us Page](#contactpy--contact-us-page)
11. [Data Flow](#data-flow)
12. [Authentication & Security](#authentication--security)
13. [API Reference](#api-reference)
14. [Supported File Formats](#supported-file-formats)
15. [User Guide](#user-guide)
16. [Troubleshooting](#troubleshooting)
17. [Contributing](#contributing)
18. [License](#license)
19. [Contact](#contact)

---

## Project Overview

**KSURA (Kansas State University Regenerative Agriculture)** is a collaborative research initiative dedicated to advancing regenerative agriculture practices in Kansas and beyond. This web application serves as the central data management and visualization platform for the KSURA research team.

The application enables team members to:
- Browse and inspect research datasets stored in a private GitHub repository
- Upload new data files to organized folder structures
- Generate publication-quality visualizations from research data
- Manage and view saved visualizations with metadata
- Access project schedules and team information

The platform is built with [Streamlit](https://streamlit.io/) and integrates directly with the GitHub API for secure, version-controlled data storage in the **Regen-Ag-Data** repository.

---

## Features

### Home Page
- Welcome landing page with project overview and team photo
- Summary of KSURA's mission, principles, and collaboration opportunities
- Information about the Kansas Soil Health Network (KSHN)

### View Data
- Browse the GitHub data repository folder structure (folders and subfolders)
- Preview Excel (`.xls`, `.xlsx`), CSV (`.csv`), and Word (`.docx`) files directly in the browser
- Select individual sheets from multi-sheet Excel workbooks
- Column filtering for large datasets (10+ columns)
- Expandable sections for:
  - **File Display** — Full data table with interactive scrolling
  - **Data Types** — Column names and their pandas dtypes
  - **Summary** — Shape, row/column counts, and missing value analysis per column
  - **Descriptive Statistics** — Mean, std, min, max, quartiles for all columns

### Upload Data
- Upload multiple files simultaneously (`.xls`, `.xlsx`, `.csv`, `.dat`, `.txt`)
- Data validation summary with file count, validity check, and total size metrics
- Preview uploaded file contents and inspect sheet selection for Excel files
- Expandable **Data Types** inspector showing column types
- Navigate the GitHub repository folder/subfolder structure to choose an upload destination
- Duplicate file detection — warns if a file with the same name already exists
- Upload history tracking within the session (last 5 uploads displayed)

### Visualizations — Create
- Two data source options: upload a local file or select a file from the GitHub repository
- Support for Excel, CSV, DAT, and TXT file formats
- Interactive visualization configuration:
  - Multi-select X-axis and Y-axis columns
  - Nine chart types: Line Plot, Bar Plot, Scatter Plot, Histogram, Box Plot, Heatmap, Violin Plot, Pair Plot, Trend Analysis
  - Five chart styles: Default, Seaborn, ggplot (R-style), FiveThirtyEight, Dark Mode
- Quick Data Insights panel showing numeric column count, highest correlation, and missing values
- Download generated visualization as PNG
- Export underlying visualization data as CSV
- Statistical summary panel with mean, standard deviation, min, and max for selected columns
- Upload visualizations to the GitHub repository with custom name and description
- Automatic XML metadata catalog update upon upload

### Visualizations — View
- Fetches visualization catalog from `visualizations.xml` in the GitHub repository
- Three view modes: **Gallery**, **Grid**, and **List**
- Sorting options: Date (Newest/Oldest), Name (A-Z/Z-A)
- Search/filter visualizations by name or description
- Auto-tagging with badges (Soil Health, Crops, Trends) based on description keywords
- Download individual visualization images

### Data Schedule
- Displays the project data collection schedule from an Excel file (`Data_Schedule.xlsx`)
- Full-width interactive data table

### About Us
- Overview of KSURA's mission and regenerative agriculture principles
- Kansas farming statistics and adoption metrics
- Barriers to adoption and team mission statement

### Contact Us
- Email, physical address, and social media links
- Links to website, Facebook, X (Twitter), and LinkedIn

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                   │
│  ┌──────┐ ┌──────┐ ┌──────────┐ ┌───────┐ ┌──────────┐  │
│  │ Home │ │ View │ │  Upload  │ │ Viz   │ │ Schedule │  │
│  └──────┘ └──┬───┘ └────┬─────┘ └───┬───┘ └────┬─────   │
│              │          │           │          │        │
│              ▼          ▼           ▼          ▼        │
│         ┌─────────────────────────────────┐   Local     │
│         │     GitHub REST API (v3)        │   Excel     │
│         │     Authentication via Token    │   File      │
│         └──────────────┬──────────────────┘             │
│                        │                                │
└────────────────────────┼────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  GitHub Repository  │
              │  Regen-Ag-Data      │
              │  ├── Folder1/       │
              │  │   ├── Sub1/      │
              │  │   └── files...   │
              │  ├── Folder2/       │
              │  ├── Visualizations/│
              │  │   ├── *.png      │
              │  │   └── viz.xml    │
              │  └── ...            │
              └─────────────────────┘
```

### Component Interaction

| Component | Responsibility |
|---|---|
| `app.py` | Entry point, page routing, sidebar navigation |
| `view.py` | Read-only data browsing from GitHub |
| `upload.py` | File upload to GitHub with validation |
| `visualization.py` | Visualization hub with tabbed Create/View interface |
| `visualize.py` | Chart generation, statistical analysis, visualization upload |
| `display_visualizations.py` | Visualization gallery with search, sort, and filtering |
| `data_schedule.py` | Data schedule display from local Excel file |
| `about.py` | Static informational content |
| `contact.py` | Static contact information |

---

## Technology Stack

| Category | Technology | Version |
|---|---|---|
| **Framework** | Streamlit | ≥ 1.25.0 |
| **Language** | Python | 3.8+ |
| **Data Processing** | pandas | ≥ 1.5.0 |
| **Numerical Computing** | NumPy | ≥ 1.24.0 |
| **Visualization** | Matplotlib | ≥ 3.6.0 |
| **Visualization** | Seaborn | ≥ 0.12.0 |
| **Excel Support** | openpyxl | ≥ 3.1.0 |
| **Word Document Support** | python-docx | 1.2.0 |
| **HTTP Client** | Requests | ≥ 2.28.0 |
| **Data Storage** | GitHub API (REST v3) | — |
| **Metadata Format** | XML (ElementTree) | stdlib |

---

## Project Structure

```
Regen-Ag-App/
├── app.py                      # Main application entry point & page router
├── view.py                     # View Data page — browse & inspect GitHub data
├── upload.py                   # Upload Data page — upload files to GitHub
├── visualization.py            # Visualizations hub — tabbed Create/View interface
├── visualize.py                # Create Visualizations — chart generation & upload
├── display_visualizations.py   # View Visualizations — gallery, grid, list views
├── data_schedule.py            # Data Schedule page — display schedule from Excel
├── about.py                    # About Us page — project information
├── contact.py                  # Contact Us page — contact details & links
├── requirements.txt            # Python package dependencies
├── README.md                   # This documentation file
├── assets/                     # Static assets
│   ├── logo.png                # KSURA logo (sidebar & home page)
│   ├── team.png                # Team photo (home page)
│   └── Data_Schedule.xlsx      # Data collection schedule spreadsheet
└── __pycache__/                # Python bytecode cache (auto-generated)
```

---

## Prerequisites

- **Python 3.8** or higher
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- A valid **GitHub Personal Access Token** with read/write access to the `Chakrapani2122/Regen-Ag-Data` repository

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Chakrapani2122/Regen-Ag-App.git
cd Regen-Ag-App
```

### 2. Create a Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:

| Package | Purpose |
|---|---|
| `streamlit>=1.25.0` | Web application framework |
| `pandas>=1.5.0` | Data manipulation and analysis |
| `requests>=2.28.0` | HTTP requests to GitHub API |
| `matplotlib>=3.6.0` | Static chart generation |
| `seaborn>=0.12.0` | Statistical data visualization |
| `openpyxl>=3.1.0` | Reading/writing Excel `.xlsx` files |
| `python-docx==1.2.0` | Reading Word `.docx` files |
| `numpy>=1.24.0` | Numerical operations and trend analysis |

---

## Configuration

### GitHub Token Setup

The application requires a GitHub Personal Access Token (PAT) to interact with the private `Regen-Ag-Data` repository.

**To create a token:**

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Select the following scopes:
   - `repo` (Full control of private repositories)
4. Copy the generated token

**Token usage in the app:**
- The token is entered via a password-masked input field on pages that require GitHub access (View Data, Upload Data, Visualizations)
- Once validated, the token is stored in `st.session_state['gh_token']` for the duration of the browser session
- The token is never persisted to disk or logged

---

## Running the Application

### Start the Streamlit Server

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Command-Line Options

```bash
# Run on a specific port
streamlit run app.py --server.port 8080

# Run with wide layout (already configured in code)
streamlit run app.py --server.headless true

# Run accessible on the network
streamlit run app.py --server.address 0.0.0.0
```

---

## Module Documentation

### `app.py` — Main Application Entry Point

**Purpose:** Serves as the entry point and router for the entire application. Configures the Streamlit page settings, renders the sidebar navigation, and routes to the appropriate module based on user selection.

**Key Components:**
- **Page Config:** Sets page title to "KSU - Regenerative Agriculture", wide layout, and favicon from `assets/logo.png`
- **Sidebar Navigation:** Displays the KSURA logo and a radio button menu with all page options
- **Page Routing:** Maps page names to their respective `main()` functions and dispatches accordingly
- **Home Page Content:** Renders the welcome message, team photo, project overview, principles of regenerative agriculture, and call-to-action for the Kansas Soil Health Network

**Navigation Pages:**
| Page | Module | Function |
|---|---|---|
| Home | `app.py` (inline) | Rendered directly |
| View Data | `view.py` | `view_main()` |
| Upload Data | `upload.py` | `upload_main()` |
| Visualizations | `visualization.py` | `visualization_main()` |
| About Us | `about.py` | `about_main()` |
| Contact Us | `contact.py` | `contact_main()` |
| Data Schedule | `data_schedule.py` | `data_schedule_main()` |

---

### `view.py` — View Data Module

**Purpose:** Provides a read-only interface for browsing and inspecting data files stored in the `Regen-Ag-Data` GitHub repository.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `validate_github_token(token)` | `token: str` | `bool` | Validates a GitHub PAT by making a test API call to the repository |
| `get_github_folders(token)` | `token: str` | `list[str]` | Fetches top-level directory names from the repository (excludes `Visualizations`) |
| `get_folder_contents(token, path)` | `token: str, path: str` | `tuple[list, list]` | Returns `(subfolders, files)` for a given repository path |
| `get_github_files(token, folder)` | `token: str, folder: str` | `list[str]` | Fetches file names within a specific folder |
| `get_github_file_content(token, path, file)` | `token: str, path: str, file: str` | `bytes \| None` | Downloads and base64-decodes a file's content from GitHub |
| `read_docx(content)` | `content: bytes` | `str` | Extracts text content from a `.docx` file's byte content |
| `main()` | — | — | Renders the View Data page UI |

**Workflow:**
1. User authenticates with a GitHub token
2. User navigates folder → subfolder → file via cascading dropdown selectors
3. For Excel files, an additional sheet selector is shown
4. File content is displayed in an expandable data table
5. Additional expandable sections show data types, summary statistics, and descriptive statistics
6. Metadata sheets (named "Metadata") skip the statistical analysis sections

---

### `upload.py` — Upload Data Module

**Purpose:** Enables authenticated team members to upload data files to the GitHub repository with validation, preview, and folder navigation.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `get_github_folders(token)` | `token: str` | `list[str]` | Fetches top-level repository directories (excludes `Visualizations`) |
| `get_folder_contents(token, path)` | `token: str, path: str` | `tuple[list, list]` | Returns subfolders and files at a given path |
| `validate_github_token(token)` | `token: str` | `bool` | Validates the provided GitHub PAT |
| `main()` | — | — | Renders the Upload Data page UI |

**Workflow:**
1. User authenticates with a GitHub token
2. User selects one or more files to upload (drag-and-drop or file picker)
3. Application displays validation summary: total files, valid files, total size
4. User can preview file contents and inspect data types
5. User selects a target folder (and optional subfolder) in the repository
6. On upload, the application checks for duplicate filenames and uploads new files via the GitHub Contents API
7. Successful uploads are recorded in session-based upload history

**Upload API Flow:**
```
File Selected → Validation → Preview → Select Destination → Check Duplicates → PUT to GitHub API → Success/Error
```

---

### `visualization.py` — Visualizations Hub

**Purpose:** Acts as the parent container for the visualization feature, providing a unified token input and a tabbed interface for creating and viewing visualizations.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `validate_github_token_local(token)` | `token: str` | `bool` | Validates token by delegating to child module validators with fallback chain |
| `main()` | — | — | Renders the tabbed Visualizations page (Create / View tabs) |

**Tab Structure:**
- **Create Tab** → Delegates to `visualize.main()`
- **View Tab** → Delegates to `display_visualizations.main()`

---

### `visualize.py` — Create Visualizations

**Purpose:** Provides a full-featured visualization creation pipeline — from data loading through chart configuration, rendering, statistical analysis, and uploading to GitHub.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `validate_github_token(token)` | `token: str` | `bool` | Validates GitHub PAT |
| `get_github_folders(token)` | `token: str` | `list[str]` | Lists top-level repository folders |
| `get_folder_contents(token, path)` | `token: str, path: str` | `tuple[list, list]` | Returns subfolders and files at a path |
| `get_github_file_content(token, path, file)` | `token: str, path: str, file: str` | `bytes \| None` | Downloads file content from GitHub |
| `main()` | — | — | Renders the Create Visualization page UI |

**Supported Chart Types:**

| Chart Type | Library | Use Case |
|---|---|---|
| Line Plot | Matplotlib | Time series, trends |
| Bar Plot | Matplotlib | Categorical comparisons |
| Scatter Plot | Matplotlib | Correlation, distribution |
| Histogram | Matplotlib | Frequency distribution |
| Box Plot | Seaborn | Statistical spread, outliers |
| Heatmap | Seaborn | Correlation matrices |
| Violin Plot | Seaborn | Distribution shape comparison |
| Pair Plot | Seaborn | Multi-variable relationships |
| Trend Analysis | Matplotlib + NumPy | Linear trend lines overlaid on data |

**Chart Styles:**
- Default, Seaborn, ggplot (R-style), FiveThirtyEight, Dark Mode

**Visualization Upload Flow:**
1. Chart is generated and stored in `st.session_state['visualization_buffer']` as a PNG byte buffer
2. User provides a name and description
3. The PNG is uploaded to `Visualizations/{name}.png` via the GitHub Contents API
4. The `Visualizations/visualizations.xml` catalog is fetched, updated with new `<Image>` metadata (Name, Path, Description, Date), and pushed back

**XML Catalog Schema:**
```xml
<Images>
  <Image>
    <Name>chart_name.png</Name>
    <Path>Visualizations/chart_name.png</Path>
    <Description>Description of the chart</Description>
    <Date>2026-03-09</Date>
  </Image>
  <!-- ... more images -->
</Images>
```

---

### `display_visualizations.py` — View Visualizations

**Purpose:** Fetches and displays all saved visualizations from the GitHub repository with multiple viewing modes, sorting, searching, and download capabilities.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `render_badge(text)` | `text: str` | — | Renders a badge using `st.badge()` with fallback to markdown |
| `validate_github_token(token)` | `token: str` | `bool` | Validates GitHub PAT |
| `display_image_compatible(img_bytesio, caption)` | `img_bytesio: BytesIO, caption: str` | — | Displays an image with Streamlit version compatibility (tries `use_container_width`, then `use_column_width`, then fixed width) |
| `main()` | — | — | Renders the View Visualizations page UI |

**View Modes:**

| Mode | Layout | Details Shown |
|---|---|---|
| **Gallery** | 2-column (image + details) | Full image, name, date, description, category badges, download button |
| **Grid** | 3-column grid | Thumbnail, name, date |
| **List** | Tabular rows | Name, truncated description, date |

**Filtering & Sorting:**
- **Search:** Filters by name or description (case-insensitive substring match)
- **Sort:** Date Newest, Date Oldest, Name A-Z, Name Z-A

---

### `data_schedule.py` — Data Schedule Module

**Purpose:** Displays the project's data collection schedule from a local Excel file.

**Functions:**

| Function | Parameters | Returns | Description |
|---|---|---|---|
| `main()` | — | — | Loads and displays `assets/Data_Schedule.xlsx` (sheet: "Schedule") as an interactive data table |

**Error Handling:** Displays an error message if the Excel file is missing or cannot be read, with guidance to check the file location.

---

### `about.py` — About Us Page

**Purpose:** Presents static informational content about the KSURA initiative, regenerative agriculture principles, Kansas farming statistics, and the team's mission.

---

### `contact.py` — Contact Us Page

**Purpose:** Displays contact information including email, physical address, and social media links for the KSURA team.

**Contact Channels:**
| Channel | Details |
|---|---|
| Email | kstateregenag@ksu.edu |
| Address | Throckmorton Hall, 1712 Claflin Rd, Manhattan, KS 66502 |
| Website | [kstateregenag.org](https://www.kstateregenag.org/) |
| Facebook | [@KSURA](https://www.facebook.com/profile.php?id=61554293039301) |
| X (Twitter) | [@KStateRegenAg](https://x.com/KStateRegenAg) |
| LinkedIn | [KSURA](https://www.linkedin.com/company/ksura/) |

---

## Data Flow

### Reading Data (View Data)

```
User selects folder/file
        │
        ▼
GitHub API: GET /repos/.../contents/{path}
        │
        ▼
Base64 decode file content
        │
        ▼
Parse with pandas (Excel/CSV) or python-docx (DOCX)
        │
        ▼
Display in Streamlit data table
```

### Uploading Data

```
User selects local files
        │
        ▼
Validate file type & display preview
        │
        ▼
User selects target folder in GitHub repo
        │
        ▼
GitHub API: GET (check if file exists)
        │
        ├── Exists → Warning: duplicate
        │
        └── Not found (404) → PUT /repos/.../contents/{path}
                                    │
                                    ▼
                              File uploaded to GitHub
```

### Creating & Uploading Visualizations

```
User loads data (upload or GitHub)
        │
        ▼
Configure chart (axes, type, style)
        │
        ▼
Matplotlib/Seaborn generates chart
        │
        ▼
PNG buffer stored in session state
        │
        ├── Download PNG locally
        │
        └── Upload to GitHub
                │
                ├── PUT image to Visualizations/{name}.png
                │
                └── GET + UPDATE visualizations.xml with metadata
```

---

## Authentication & Security

### Token-Based Authentication

| Aspect | Details |
|---|---|
| **Method** | GitHub Personal Access Token (PAT) |
| **Input** | Password-masked text input (`type="password"`) |
| **Validation** | API call to `GET /repos/Chakrapani2122/Regen-Ag-Data` — returns `200` for valid tokens |
| **Storage** | `st.session_state['gh_token']` (in-memory, per browser session) |
| **Persistence** | None — token is discarded when the browser tab is closed |
| **Scope Required** | `repo` (read/write access to private repositories) |

### Security Considerations

- Tokens are **never written to disk** or logged
- Token input fields use Streamlit's `type="password"` to mask input
- All GitHub API calls use HTTPS
- The application only accesses the specific repository (`Chakrapani2122/Regen-Ag-Data`)
- No user accounts or roles are managed by the application itself — access is controlled entirely through GitHub token permissions

---

## API Reference

The application interacts with the **GitHub REST API v3** at `https://api.github.com`.

### Endpoints Used

| HTTP Method | Endpoint | Purpose | Used In |
|---|---|---|---|
| `GET` | `/repos/{owner}/{repo}` | Validate token / repo access | `view.py`, `upload.py`, `visualize.py`, `display_visualizations.py` |
| `GET` | `/repos/{owner}/{repo}/contents/{path}` | List folder contents or fetch file content | `view.py`, `upload.py`, `visualize.py`, `display_visualizations.py` |
| `PUT` | `/repos/{owner}/{repo}/contents/{path}` | Create or update a file | `upload.py`, `visualize.py` |

### Request Headers

```
Authorization: token {GITHUB_PAT}
```

### Response Handling

- **200 OK** — Success; parse JSON body
- **404 Not Found** — File/folder does not exist (used to confirm safe upload)
- **Other errors** — Displayed to the user via `st.error()`

---

## Supported File Formats

### For Upload & Viewing

| Format | Extensions | Read Library | Notes |
|---|---|---|---|
| Excel | `.xls`, `.xlsx` | pandas + openpyxl | Multi-sheet support with sheet selector |
| CSV | `.csv` | pandas | Standard comma-delimited |
| Tab-delimited | `.dat`, `.txt` | pandas | Parsed with `delimiter="\t"` |
| Word Document | `.docx` | python-docx | Text extraction only (View Data page) |

### For Visualization Export

| Format | Description |
|---|---|
| PNG | Generated chart image |
| CSV | Underlying data used in the visualization |

---

## User Guide

### First-Time Setup

1. Obtain a GitHub Personal Access Token with `repo` scope (see [Configuration](#configuration))
2. Clone and install the application (see [Installation](#installation))
3. Run `streamlit run app.py`
4. Enter your token on any page that requires authentication — it will be reused across pages for the session

### Viewing Data

1. Navigate to **View Data** from the sidebar
2. Enter your GitHub token (if not already entered)
3. Select a folder from the dropdown
4. Select a subfolder (if applicable) and then a file
5. For Excel files, choose a sheet from the dropdown
6. Expand sections to see data types, summary, and descriptive statistics

### Uploading Data

1. Navigate to **Upload Data** from the sidebar
2. Drag and drop or browse to select files
3. Review the validation summary (file count, size)
4. Preview file contents in the expandable section
5. Select a destination folder (and subfolder) in the repository
6. Click **Upload Files**
7. Check for success/warning messages

### Creating Visualizations

1. Navigate to **Visualizations** from the sidebar
2. In the **Create** tab, choose to upload a file or select one from GitHub
3. Select X-axis and Y-axis columns
4. Choose a chart type and style
5. Click **Generate Visualization**
6. Download the chart or export the data
7. To save to the repository, enter a name and description, then click **Upload Visualization**

### Viewing Saved Visualizations

1. In the **Visualizations** page, switch to the **View** tab
2. Use search, sort, and view mode controls to browse
3. Click **Download** on any visualization to save it locally

---

## Troubleshooting

| Issue | Possible Cause | Solution |
|---|---|---|
| "Invalid token or access issue" | Token expired, revoked, or lacks `repo` scope | Generate a new token with `repo` scope |
| "Could not load Data_Schedule.xlsx" | File missing from `assets/` folder | Ensure `assets/Data_Schedule.xlsx` exists with a "Schedule" sheet |
| Blank page after selecting a file | File content is empty or corrupted | Check the file in the GitHub repository directly |
| "File already exists" warning on upload | A file with the same name exists in the target folder | Rename the file or choose a different folder |
| Visualization not displaying | No X/Y axis columns selected, or data is non-numeric | Ensure numeric columns are selected for the chosen chart type |
| Pair Plot not rendering | Too many columns selected | Limit to 4-5 columns for pair plots |
| Images not loading in View tab | GitHub API rate limit exceeded | Wait a few minutes and retry, or use a token with higher rate limits |
| Application crashes on startup | Missing dependencies | Run `pip install -r requirements.txt` |

---

## Contributing

This application is maintained by the KSURA research team at Kansas State University.

### Development Workflow

1. **Fork** the repository
2. **Create a feature branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes** and test locally with `streamlit run app.py`
4. **Commit** with descriptive messages: `git commit -m "Add feature description"`
5. **Push** to your fork: `git push origin feature/your-feature-name`
6. **Open a Pull Request** against the main branch

### Code Style Guidelines

- Follow PEP 8 for Python code style
- Use descriptive function and variable names
- Keep Streamlit UI logic in `main()` functions
- Reuse helper functions (e.g., `validate_github_token`, `get_github_folders`) across modules
- Suppress warnings with `warnings.filterwarnings("ignore")` at module level

---

## License

This project is developed and maintained by Kansas State University. Please contact the KSURA team for licensing and usage information.

---

## Contact

**Kansas State University Regenerative Agriculture (KSURA)**

- **Email:** kstateregenag@ksu.edu
- **Address:** Throckmorton Hall, 1712 Claflin Rd, Manhattan, KS 66502
- **Website:** [kstateregenag.org](https://www.kstateregenag.org/)
- **Facebook:** [@KSURA](https://www.facebook.com/profile.php?id=61554293039301)
- **X (Twitter):** [@KStateRegenAg](https://x.com/KStateRegenAg)
- **LinkedIn:** [KSURA](https://www.linkedin.com/company/ksura/)

