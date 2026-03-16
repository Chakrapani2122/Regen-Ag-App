# KSURA Web Application — Complete Technical Documentation

**Kansas State University Regenerative Agriculture (KSURA) Web App**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Module Documentation](#module-documentation)
6. [Data Flow](#data-flow)
7. [Authentication & Security](#authentication--security)
8. [Session State Management](#session-state-management)
9. [API Reference](#api-reference)
10. [Supported File Formats](#supported-file-formats)
11. [Key Features](#key-features)
12. [Development & Modification Guide](#development--modification-guide)
13. [Troubleshooting](#troubleshooting)
14. [Deployment](#deployment)

---

## Project Overview

### Purpose
KSURA is a **Streamlit-based web application** designed to support regenerative agriculture research at Kansas State University. The app provides a centralized platform for managing, visualizing, and analyzing research datasets while maintaining secure GitHub-based storage.

### Core Functionality
- **Data Browsing** — Browse and inspect research datasets stored in a private GitHub repository
- **Data Upload** — Upload new data files with organized folder structure support
- **Data Analysis** — Statistical analysis with 7+ test types, data profiling, and insights
- **Visualization Creation** — Generate publication-quality charts with customization options
  - Single chart generation
  - Comparative visualization (side-by-side)
  - Customizable titles and axis labels
- **Visualization Management** — View, search, and filter saved visualizations
- **Project Management** — Access team contact info, about page, and data schedules

### Target Users
- Research team members
- Faculty and graduate students
- Data analysts
- Farmers or external stakeholders (read-only access)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────┐
│         Streamlit Web Interface                 │
│  (Browser-based, runs in localhost)             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│   GitHub Client Layer                           │
│  (github_client.py)                             │
│  - Token validation                             │
│  - API request management                       │
│  - Retry/backoff logic                          │
│  - Connection pooling                           │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│   GitHub REST API                               │
│  (api.github.com)                               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│   GitHub Repository                             │
│  - Data files (CSV, TSV, XLSX, TXT, MD, DOCX)   │
│  - Visualizations folder                        │
│  - visualizations.xml (metadata)                │
└─────────────────────────────────────────────────┘
```

### Data Storage
- **Backend**: GitHub repository (`Chakrapani2122/Regen-Ag-Data`)
- **Structure**: Organized folders by dataset/research area
- **Authorization**: OAuth token-based authentication
- **Metadata**: XML-based catalog for visualizations

---

## Technology Stack

### Frontend
- **Streamlit** ≥1.25.0 — Web framework for rapid data app development
- **Pandas** ≥1.5.0 — Data manipulation and analysis
- **NumPy** ≥1.24.0 — Numerical computing

### Visualization & Analysis
- **Matplotlib** ≥3.6.0 — Low-level plotting library
- **Seaborn** ≥0.12.0 — Statistical data visualization
- **SciPy** ≥1.10.0 — Scientific computing (statistical tests)
- **Statsmodels** ≥0.14.0 — Statistical modeling (Tukey HSD post-hoc)

### Backend & API
- **Requests** ≥2.28.0 — HTTP client library
- **GitHub REST API** — Data storage and retrieval
- **urllib3** — Advanced HTTP client (via requests)

### File Processing
- **OpenpyXL** ≥3.1.0 — Excel file reading/writing
- **python-docx** 1.2.0 — DOCX file reading

### Other
- **Python** 3.8+ — Programming language
- **Git** — Version control

---

## Project Structure

```
Regen-Ag-App/
├── app.py                      # Main application entry point (Streamlit)
├── github_client.py            # Centralized GitHub API client
├── view.py                     # Data viewing & analysis page
├── upload.py                   # File upload page
├── visualize.py                # Visualization creation page
├── visualization.py            # Visualizations hub (Create + View tabs)
├── display_visualizations.py   # Visualization viewing page
├── about.py                    # About page
├── contact.py                  # Contact page
├── data_schedule.py            # Data schedule page
├── requirements.txt            # Python dependencies
├── README.md                   # Project README
├── Documentation.md            # This file
├── assets/
│   ├── logo.png               # App logo
│   ├── team.png               # Team image
│   └── Data_Schedule.xlsx      # Data schedule spreadsheet
├── .devcontainer/              # Dev container config (Docker)
├── .gitignore                  # Git ignore rules
├── .gitattributes              # Git attributes
└── __pycache__/               # Python cache
```

---

## Module Documentation

### 1. **app.py** — Main Application Entry Point

**Purpose**: Routes user navigation and initializes the Streamlit app.

**Key Components**:
- **Page Configuration**: Sets app title, layout, and favicon
- **Sidebar Navigation**: Logo and radio button menu
- **Home Page**: Welcome screen with project overview
- **Page Router**: Dynamically loads page modules based on user selection

**Functions**:
```python
# No public functions; app.py is purely structural
```

**Key Variables**:
```python
PAGES = {
    "Home": None,                          # Home page (inline)
    "View Data": view_main,               # view.py
    "Upload Data": upload_main,            # upload.py
    "Visualizations": visualization_main,  # visualization.py
    "About Us": about_main,                # about.py
    "Contact Us": contact_main,            # contact.py
    "Data Schedule": data_schedule_main     # data_schedule.py
}
```

**Session State**:
- `gh_token` — Cached GitHub token (shared across pages)
- `gh_token_validated` — Boolean flag for one-time validation

**UI Components**:
- Logo in sidebar (80px width)
- App icon from `assets/logo.png`
- Wide layout (full screen)

---

### 2. **github_client.py** — Centralized GitHub API Client

**Purpose**: Encapsulates all GitHub API interactions with retry logic, connection pooling, and error handling.

**Key Classes**:

#### `GitHubClient`
Manages authenticated requests to GitHub REST API.

**Constructor**:
```python
GitHubClient(token: str, repo: str = "Chakrapani2122/Regen-Ag-Data")
```
- `token` — GitHub personal access token
- `repo` — Target repository in `owner/repo` format
- Initializes `requests.Session` with HTTPAdapter and retry policy

**Methods**:

| Method | Signature | Returns | Purpose |
|--------|-----------|---------|---------|
| `validate_token()` | `() -> bool` | True if valid | Validates token by testing repo access |
| `list_contents()` | `(path: str) -> (items, error, auth_error)` | Tuple | List folders/files at path |
| `get_file_metadata()` | `(file_path: str) -> (metadata, error, auth_error)` | Tuple | Get file metadata (size, sha, etc) |
| `get_file_content()` | `(file_path: str) -> (bytes, error, auth_error, metadata)` | Tuple | Download file content |
| `put_file()` | `(file_path, message, content_b64, sha, extra_fields)` | Tuple | Upload/update file |

**Error Handling**:
- Automatic retry on 429 (rate limit), 500, 502, 503, 504
- Exponential backoff with 0.5s factor
- Up to 3 retry attempts
- Distinguishes auth errors (401/403) from other failures

**Resource Factory**:
```python
get_github_client(token, repo) -> GitHubClient
```
Streamlit-cached factory (resource-scoped) for connection reuse.

**Key Features**:
- Connection pooling (10 connections, 20 max)
- 30-second default timeout
- Base64 encoding for binary files
- Raw content fallback for large files

---

### 3. **view.py** — Data Viewing & Analysis Page

**Purpose**: Browse repository data files and perform statistical analysis.

**Key Functions**:

#### Data Loading & Caching
```python
get_repo_contents_cached(token, path="") -> (folders, files, error, auth_error)
```
- Cached 120 seconds
- Lists folders and files at a path
- Excludes `Visualizations` folder and `.gitattributes`/`.gitignore`

```python
get_github_file_content_cached(token, file_path) -> (content, error, auth_error, sha)
```
- Cached 180 seconds
- Fetches file content and SHA hash
- Returns bytes content

```python
parse_dataframe_cached(file_name, file_content, sheet_name, file_sha) -> (df, error)
```
- Cached 300 seconds
- Auto-detects file format (CSV, TSV, XLSX)
- Handles multiple encodings (UTF-8, latin-1, cp1252)
- Returns pandas DataFrame

#### File Format Parsing
```python
parse_csv_file(file_content) -> (df, error)
parse_tsv_file(file_content) -> (df, error)
decode_text_file(file_content) -> (text, error)
read_docx(file_content) -> text
```

#### Navigation
```python
render_repository_navigation(token) -> (selected_path, file_name, file_path)
```
- 3-column dropdown grid for folder/file navigation
- Lazy-loads folder contents
- Background prefetch of next level (ThreadPoolExecutor)

#### Navigation Helpers
```python
nav_option_value(item_type, name) -> str
parse_nav_option(option) -> (item_type, name)
get_file_icon(file_name) -> emoji
format_nav_option(option) -> formatted_string
```

#### Statistical Tests & Analysis
```python
get_numeric_and_categorical_columns(df) -> (numeric_cols, categorical_cols)
```
- Identifies numeric (int64, float64) and categorical columns
- Marks low-cardinality columns as categorical

```python
render_selector_grid(selector_configs) -> selections_dict
```
- Dynamic 3-column dropdown/multiselect/number input grid
- Used for parameterizing statistical tests

```python
render_statistical_tests(df)
```
- Expander with 7 test options:
  1. Pearson Correlation — linear relationship between 2 numeric columns
  2. Correlation Matrix — pairwise correlations with heatmap
  3. T-Test — compare means of 2 groups
  4. Mann-Whitney U Test — non-parametric alternative to T-Test
  5. ANOVA — compare means across 3+ groups
  6. Chi-Square — test independence of categorical variables
  7. Shapiro-Wilk — test normality assumption
- Each includes effect sizes (Cohen's d, eta-squared, Cramer's V)
- Confidence intervals (95% by default)
- Tukey HSD post-hoc for ANOVA

#### Data Quality & Smart Recommendations
```python
render_smart_recommendations(df)
```
- Suggests relevant tests based on data
- Suggests chart types for visualization
- Suggests data cleaning steps

**UI Workflow**:
1. User provides GitHub token
2. Navigate repository folders/files
3. Load dataset (auto-detects format)
4. File Display section with column filtering
5. Data Types, Summary Statistics, Correlation Matrix
6. Statistical Tests with customizable parameters
7. Smart Recommendations panel

**Session State Keys**:
- `gh_token` — GitHub token (shared)
- `gh_token_validated` — Validation flag
- `view_sheet_select` — Selected Excel sheet
- `view_selected_cols` — Columns to display
- Navigation: `view_nav_level_{i}` — Folder navigation state

---

### 4. **upload.py** — File Upload Page

**Purpose**: Upload data files to the GitHub repository with folder organization.

**Key Functions**:

```python
get_upload_folders_cached(token, path="") -> (folders, error, auth_error)
```
- Cached 120 seconds
- Lists folders for upload destination

```python
render_folder_navigation(token) -> selected_destination_path
```
- 3-column grid for folder selection
- Returns destination path as string
- Excludes `Visualizations` folder

#### Navigation Helpers
```python
nav_option_value(item_type, name) -> str
parse_nav_option(option) -> (item_type, name)
format_upload_nav_option(option) -> emoji + name
```

**UI Workflow**:
1. Token input/validation
2. File uploader (XLS, XLSX, CSV, DAT, TXT)
3. Data validation summary (# files, size)
4. File preview expander
5. Data types table
6. Folder navigation for destination
7. Upload button with GitHub API integration

**Session State Keys**:
- `gh_token` — GitHub token
- `upload_files_widget` — Selected files
- `file_select` — Current file for preview
- `sheet_select` — Excel sheet selection
- `upload_dest_level_{i}` — Folder navigation state
- `upload_history` — Recently uploaded files

**Features**:
- Multiple file upload
- Encoding auto-detection (UTF-8, latin-1, cp1252)
- File existence checking (avoids overwrites)
- Metadata tracking with upload history
- Error handling for network/auth issues

---

### 5. **visualize.py** — Visualization Creation Page

**Purpose**: Generate and customize single/comparative visualizations from data.

**Key Functions**:

#### Chart Helpers
```python
_apply_chart_style(style)
```
- Maps style name to matplotlib style

```python
_render_chart_on_ax(df, x_axis, y_axis, plot_type, ax, 
                    custom_title=None, custom_x_label=None, custom_y_label=None) -> bool
```
- Draws chart on given axis
- Supports 8 plot types: Line, Bar, Scatter, Histogram, Box, Heatmap, Violin, Trend
- Supports custom labels
- Returns False for Pair Plot (unsupported in axis mode)

```python
_fig_to_buffer(fig) -> BytesIO
```
- Converts matplotlib figure to PNG buffer

#### UI Constants
```python
_CHART_TYPES = ["Line Plot", "Bar Plot", "Scatter Plot", ...]
_CHART_STYLES = ["Default", "Seaborn", "ggplot (R-style)", ...]
_CHART_STYLE_MAP = {mapping of style names to matplotlib styles}
```

**UI Workflow**:

**Single Chart Mode** (default):
1. Data loading: upload file or select from repo
2. Data preview
3. Chart configuration (X/Y axes, type, style)
4. **Chart Customization** section:
   - Chart Title (optional)
   - X-Axis Label (optional)
   - Y-Axis Label (optional)
5. Generate Visualization button
6. Display chart + download PNG + download data CSV
7. Statistical summary table (mean, std, min, max per column)
8. Visualization name/description inputs
9. Upload to Visualizations folder + update visualizations.xml

**Comparative Mode** (checkbox):
1. Enable with "🔀 Comparative Visualization" checkbox
2. Alignment checkboxes (X-axis, Y-axis)
3. **Chart 1** configuration (X/Y, type, style)
4. **Chart 2** configuration (X/Y, type, style)
5. **Customization**:
   - Chart 1 Title (optional)
   - Chart 2 Title (optional)
   - X-Axis Label (shared, optional)
   - Y-Axis Label (shared, optional)
6. Generate Comparative Visualization button
7. Display side-by-side chart (1x2 subplot)
8. Single combined PNG download
9. Visualization name/description inputs
10. Upload + XML update

**Session State Keys**:
- `gh_token`, `gh_token_validated` — Token
- `viz_action_radio` — Upload or Select file action
- `viz_file_uploader` — File uploader
- `viz_df` — Loaded DataFrame (persisted)
- `viz_df_source` — Data source (Upload/Select)
- `viz_sheet_select` — Excel sheet selection
- `viz_x_axis`, `viz_y_axis` — Column multiselects
- `viz_plot_type`, `viz_chart_style` — Chart config
- `viz_custom_title`, `viz_custom_x_label`, `viz_custom_y_label` — Custom labels
- Comparative mode:
  - `compare_mode_cb` — Toggle
  - `cmp_align_x`, `cmp_align_y` — Axis alignment
  - `cmp_x1/y1`, `cmp_x2/y2` — Chart configs
  - `cmp_pt1/cs1`, `cmp_pt2/cs2` — Types/styles
  - `cmp_title1/2`, `cmp_x_label`, `cmp_y_label` — Custom labels
  - `cmp_buf_combined` — Generated figure buffer

**Features**:
- 8 chart types (9 with Pair Plot)
- 5 chart styles (Default, Seaborn, ggplot, FiveThirtyEight, Dark Mode)
- Custom title and axis labels for single and comparative
- Axis alignment in comparative mode
- PNG download
- CSV data export
- GitHub upload with metadata (name, description, date)
- visualizations.xml metadata tracking

---

### 6. **visualization.py** — Visualizations Hub (Create + View)

**Purpose**: Unified entry point for visualization creation and viewing with single token input.

**Key Functions**:

```python
validate_github_token_local(token) -> bool
```
- Fallback validator using visualize module
- Last resort: accepts non-empty token

```python
main()
```
- Creates two tabs: Create, View
- Single token input with `key="visualizations_token"`
- Stores token in `st.session_state['gh_token']`
- Delegates to `visualize.main()` and `display_visualizations.main()`

**UI Components**:
- Title: "Visualizations"
- Token input (password field)
- Two tabs:
  - **Create**: Visualization creation UI
  - **View**: Visualization browsing UI

**Session State Keys**:
- `gh_token` — Shared token
- `visualizations_token` — Tab-specific token input key

---

### 7. **display_visualizations.py** — Visualization Viewing Page

**Purpose**: Browse, filter, and display saved visualizations with metadata.

**Key Functions**:

```python
validate_github_token(token) -> bool
```
- Validates GitHub token

```python
display_image_compatible(img_bytesio, caption=None)
```
- Tries multiple `st.image()` parameters for Streamlit version compatibility
- Fallback chain: `use_container_width` → `use_column_width` → fixed width

```python
main()
```
- Controls section:
  - Sort by: Date (Newest/Oldest), Name (A-Z/Z-A)
  - Search by name/description
  - View mode: Gallery, List, Grid
- Fetches `Visualizations/visualizations.xml`
- Parses XML and displays images
- Grid/list layout with filtering/searching

**XML Structure**:
```xml
<Images>
  <Image>
    <Name>visualization_name.png</Name>
    <Path>Visualizations/visualization_name.png</Path>
    <Description>User-provided description</Description>
    <Date>YYYY-MM-DD</Date>
  </Image>
  ...
</Images>
```

**UI Features**:
- Filter by sort order and search term
- Real-time filtering
- Display modes (Gallery, List, Grid)
- Clickable images (opens in lightbox if supported)
- Metadata display (name, date, description)

---

### 8. **about.py** — About Page

**Purpose**: Display project mission, principles, and context.

**Key Components**:
- Regenerative agriculture definition
- Kansas context (statistics on farming practices)
- Why it matters (benefits, barriers)
- Team mission statement

**No UI interactivity** — static markdown content.

---

### 9. **contact.py** — Contact Page

**Purpose**: Display contact information and social media links.

**Key Components**:
- Email: `kstateregenag@ksu.edu`
- Physical address (Throckmorton Hall, Manhattan, KS)
- Social media (Facebook, Twitter/X, LinkedIn)
- Website link

**No UI interactivity** — static markdown content.

---

### 10. **data_schedule.py** — Data Schedule Page

**Purpose**: Display project data collection/analysis schedule.

**Key Components**:
- Loads `assets/Data_Schedule.xlsx` (sheet: "Schedule")
- Displays as interactive Streamlit dataframe
- Error handling for missing file

**Session State Keys**: None

---

## Data Flow

### File Upload Flow

```
User uploads file
    ↓
visualize.py / upload.py file_uploader
    ↓
File content read to bytes
    ↓
Encoding detection (UTF-8, latin-1, cp1252)
    ↓
Pandas parse (CSV/TSV/XLSX)
    ↓
DataFrame stored in session_state (visualize.py: 'viz_df')
    ↓
User creates visualization
    ↓
GitHub API upload via github_client.put_file()
    ↓
visualizations.xml updated with metadata
    ↓
Success message + refresh
```

### File Selection & Analysis Flow

```
User selects GitHub token
    ↓
Token validated (github_client.validate_token())
    ↓
Repository contents listed (github_client.list_contents())
    ↓
User navigates folders via dropdowns
    ↓
File selected
    ↓
File content fetched (github_client.get_file_content())
    ↓
Auto format detection (extension-based)
    ↓
Parse to DataFrame (parse_dataframe_cached)
    ↓
Display file + metadata + statistics
    ↓
User selects test type (statistical tests panel)
    ↓
Test executed with parameters
    ↓
Results displayed with effect sizes + CIs
```

### Visualization Creation Flow

```
Data loaded (upload or select)
    ↓
User selects columns (X/Y), chart type, style
    ↓
Optional: enter custom title/labels
    ↓
Click "Generate Visualization"
    ↓
_render_chart_on_ax() draws chart
    ↓
Optional axis alignment (comparative mode)
    ↓
Figure saved to PNG buffer
    ↓
Display in st.image()
    ↓
Download PNG or data CSV
    ↓
Optional: enter name/description + upload
    ↓
github_client.put_file() uploads PNG
    ↓
visualizations.xml updated with ElementTree
    ↓
Success message
```

---

## Authentication & Security

### Token Management

**Token Scope**:
- GitHub Personal Access Token (requires `repo` scope)
- Allows read/write to private repository
- **NOT stored persistently** — only in `st.session_state` for session duration

**Token Validation**:
```python
# One-time per session
if not st.session_state.get('gh_token_validated', False):
    token = st.text_input("Enter your security token:", type="password")
    if validate_github_token(token):
        st.session_state['gh_token'] = token
        st.session_state['gh_token_validated'] = True
```

**Token Reuse**:
- Stored in shared `st.session_state['gh_token']`
- Passed to all pages
- Reduces re-prompting across page navigation

### Authorization Errors

**401/403 Responses**:
```python
if auth_error:
    st.session_state['gh_token'] = None
    st.session_state['gh_token_validated'] = False
    st.error("Authentication failed. Please re-enter your security token.")
```
- Session state cleared
- User re-prompted on next request

### Network Security
- HTTPS-only GitHub API calls
- No credentials in logs/code
- Token masked in UI (password field: `type="password"`)

---

## Session State Management

Streamlit's session state is used to preserve user inputs across page navigations.

**Global State Keys**:
```python
st.session_state['gh_token']              # GitHub token (shared)
st.session_state['gh_token_validated']    # Bool validation flag
```

**View Page**:
```python
st.session_state['view_sheet_select']     # Excel sheet selection
st.session_state['view_selected_cols']    # Column multiselect
st.session_state['view_nav_level_{i}']    # Folder navigation (per level)
```

**Upload Page**:
```python
st.session_state['upload_files_widget']   # File uploader
st.session_state['file_select']           # Preview file selection
st.session_state['sheet_select']          # Excel sheet selection
st.session_state['upload_dest_level_{i}'] # Folder navigation (per level)
st.session_state['upload_history']        # List of recent uploads
```

**Visualize Page**:
```python
st.session_state['viz_action_radio']      # "Upload file" vs "Select file"
st.session_state['viz_file_uploader']     # File uploader
st.session_state['viz_df']                # Loaded DataFrame (persisted)
st.session_state['viz_df_source']         # Data source identifier
st.session_state['viz_sheet_select']      # Excel sheet
st.session_state['viz_x_axis']            # X-axis columns (multiselect)
st.session_state['viz_y_axis']            # Y-axis columns (multiselect)
st.session_state['viz_plot_type']         # Chart type (selectbox)
st.session_state['viz_chart_style']       # Chart style (selectbox)
st.session_state['viz_custom_title']      # Custom chart title
st.session_state['viz_custom_x_label']    # Custom X-axis label
st.session_state['viz_custom_y_label']    # Custom Y-axis label
st.session_state['visualization_buffer']  # Generated chart PNG buffer

# Comparative mode:
st.session_state['compare_mode_cb']       # Comparative checkbox
st.session_state['cmp_align_x']           # Align X-axis checkbox
st.session_state['cmp_align_y']           # Align Y-axis checkbox
st.session_state['cmp_x1/y1']             # Chart 1 columns
st.session_state['cmp_x2/y2']             # Chart 2 columns
st.session_state['cmp_pt1/cs1']           # Chart 1 type/style
st.session_state['cmp_pt2/cs2']           # Chart 2 type/style
st.session_state['cmp_title1/2']          # Custom titles
st.session_state['cmp_x_label']           # Shared X label
st.session_state['cmp_y_label']           # Shared Y label
st.session_state['cmp_buf_combined']      # Generated combined chart
```

### Session State Persistence
**TTL-based Caching**:
- `get_repo_contents_cached()` — 120 seconds
- `get_github_file_content_cached()` — 180 seconds
- `parse_dataframe_cached()` — 300 seconds

**Manual Session Persistence**:
- `visualization_buffer` — Manually cleared when new chart generated
- `viz_df` — Persists across page navigations

---

## API Reference

### GitHub API Endpoints Used

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Validate token access |
| GET | `/contents/{path}` | List folder/file contents |
| GET | `/contents/{file_path}` | Get file metadata |
| GET | (raw content) | Download large files |
| PUT | `/contents/{file_path}` | Upload/update file |

### Rate Limiting
- GitHub: 5,000 requests/hour (authenticated)
- App retry strategy: 3 attempts with 0.5s backoff
- Client-side caching: 120-300s TTLs reduce API load

### Error Codes Handled
- **401**: Invalid token
- **403**: Access denied (closed repo, insufficient permissions)
- **404**: File not found
- **429**: Rate limit exceeded (retried)
- **5xx**: Server errors (retried)

---

## Supported File Formats

### Data Files

| Format | Extension | Parsing Method | Notes |
|--------|-----------|-----------------|-------|
| CSV | `.csv` | `pd.read_csv()` with encoding detection | Auto detects delimiter (`,`, tab) |
| TSV | `.tsv` | `pd.read_csv(sep="\t")` | Tab-separated values |
| Excel | `.xls`, `.xlsx` | `pd.ExcelFile()` per sheet | User selects sheet |
| Text | `.txt` | `decode_text_file()` | Displayed as text, not parsed as data |
| Markdown | `.md`, `.markdown` | `st.markdown()` | Renders as formatted HTML |
| DOCX | `.docx` | `python-docx` | Text extracted and displayed |

### Visualization Files

| Format | Extension | Purpose |
|--------|-----------|---------|
| PNG | `.png` | Chart output format |
| XML | `visualizations.xml` | Metadata catalog |

### Configuration Files

| Format | Location | Purpose |
|--------|----------|---------|
| Excel | `assets/Data_Schedule.xlsx` | Data schedule display |
| PNG | `assets/logo.png` | App logo |
| PNG | `assets/team.png` | Team image |

---

## Key Features

### 1. **Data Discovery**
- Browse repository folder structure
- 3-column grid interface for efficient navigation
- Auto-refresh on page return (via session state)
- Background prefetch of next folder level

### 2. **Data Analysis**
- **7 statistical tests**:
  1. Pearson correlation (effect: r, 95% CI)
  2. Correlation matrix with heatmap
  3. T-Test (effect: Cohen's d, 95% CI)
  4. Mann-Whitney U (non-parametric)
  5. ANOVA (effect: eta-squared, Tukey HSD post-hoc)
  6. Chi-Square (effect: Cramer's V)
  7. Shapiro-Wilk (normality test)
- **Data profiling**: missing values, outliers, duplicates
- **Smart recommendations**: suggest tests and charts

### 3. **Visualization**
- **8 chart types**:
  - Line Plot, Bar Plot, Scatter Plot, Histogram
  - Box Plot, Heatmap, Violin Plot, Trend Analysis
  - Pair Plot (standalone)
- **5 styles**: Default, Seaborn, ggplot, FiveThirtyEight, Dark Mode
- **Customization**:
  - Custom title
  - Custom X/Y axis labels
  - Comparative mode (side-by-side)
  - Axis alignment for comparison
- **Export**: PNG download, CSV data export

### 4. **Visualization Management**
- Save visualizations with name and description
- XML-based metadata catalog
- Search and filter by name/description
- Sort by date or name
- Gallery/List/Grid view modes

### 5. **Session Persistence**
- All widget selections persist across page navigation
- DataFrame cached in session
- File selections remembered
- Column configurations retained

### 6. **User Convenience**
- One-time token validation per session
- Auto-encoding detection for text files
- Safe file existence checking before upload
- Upload history tracking
- Quick data insights (column counts, correlations)

---

## Development & Modification Guide

### Adding a New Statistical Test

**In `view.py`, `render_statistical_tests()` function**:

1. Add test configuration to selector configs:
```python
selector_configs = [
    {
        "label": "Your Test",
        "key": "your_test",
        "type": "selectbox",
        "options": ["Column1", "Column2", ...],
    },
    ...
]
```

2. Add test execution logic in `if run_test` block:
```python
elif selected_test == "Your Test":
    col1_name = selections.get("your_test_col1")
    col2_name = selections.get("your_test_col2")
    
    # Perform test
    from scipy import stats as scipy_stats
    statistic, pvalue = scipy_stats.your_test(df[col1_name], df[col2_name])
    
    # Display results
    st.write(f"Statistic: {statistic:.4f}")
    st.write(f"P-value: {pvalue:.4e}")
    st.write(f"Effect size: ...")
```

### Adding a New Chart Type

**In `visualize.py`, `_render_chart_on_ax()` function**:

1. Add to `_CHART_TYPES`:
```python
_CHART_TYPES = [
    ...,
    "Your Chart Type",
]
```

2. Add rendering logic:
```python
elif plot_type == "Your Chart Type":
    # Your plotting code
    ax.plot(...)
    default_title = "Your Chart Type"
```

3. Specify axis requirements:
```python
def _needs_x(pt):
    return pt not in ("Histogram", "Box Plot", ..., "Your Chart Type" if no_x else)
def _needs_y(pt):
    return pt not in ("Histogram", ..., "Your Chart Type" if no_y else)
```

### Adding a New Page

**In `app.py`**:

1. Create new module (e.g., `my_page.py`):
```python
import streamlit as st

def main():
    st.title("My Page")
    st.write("Content here")
```

2. Import and register in `app.py`:
```python
from my_page import main as my_page_main

PAGES = {
    ...
    "My Page": my_page_main,
}
```

### Modifying GitHub Repository

The app uses `Chakrapani2122/Regen-Ag-Data` by default. To change:

**In `github_client.py`**:
```python
DEFAULT_REPO = "your_username/your_repo"
```

**Or pass at runtime**:
```python
client = get_github_client(token, repo="your_username/your_repo")
```

### Extending File Format Support

**In `view.py`, `parse_dataframe_cached()`**:

1. Add file extension check:
```python
elif file_name_lower.endswith(".your_format"):
    # Parse with your library
    df = your_parser.parse(file_content)
    return df, None
```

2. Add to supported formats list (view.py, upload.py, visualize.py file_uploader type parameter)

---

## Troubleshooting

### Token Issues

**Problem**: "Invalid token or access issue"
- **Solution**: Verify token has `repo` scope in GitHub settings
- Regenerate token if > 1 year old
- Check token for special characters

**Problem**: "Authentication failed. Please re-enter your security token"
- **Solution**: Token may have expired or been revoked
- Generate new token on GitHub.com → Settings → Developer settings
- Verify token still has repo access

### File Upload Issues

**Problem**: "File already exists at '{path}'"
- **Solution**: Use different filename or delete via GitHub web UI
- Or navigate to different folder

**Problem**: "Unable to parse the file"
- **Solution**: Check file format is supported (CSV, TSV, XLSX, TXT)
- For CSV/TSV: ensure proper delimiters and encoding
- Try CSV export from source application

### Visualization Issues

**Problem**: "Error generating visualization"
- **Solution**: Ensure columns selected are correct type for chart
- Line/Bar/Scatter require numeric Y-axis
- Box Plot requires Y-axis columns
- Check for NaN/null values in data

**Problem**: Chart title/labels not appearing
- **Solution**: Empty custom labels fall back to defaults
- Enter text in customization inputs
- Session state may have cleared — re-enter values

### Data Issues

**Problem**: Missing values shown as different counts
- **Solution**: Different parsing libraries count nulls differently
- Check raw file for encoding issues
- Verify file wasn't corrupted during upload

**Problem**: Statistical tests return error
- **Solution**: Ensure selected columns contain numeric data
- Check for NaN values in columns
- Some tests have minimum sample size (e.g., Shapiro-Wilk: n > 3)

### Performance Issues

**Problem**: Page loads slowly
- **Solution**: TTL cache may be cold — reload page
- Large files (>50MB) may take time to download
- Check GitHub API rate limit: `https://api.github.com/rate_limit`

**Problem**:  "Network error" repeatedly
- **Solution**: Check internet connection
- Verify GitHub is not down (`status.github.com`)
- Router/firewall may block GitHub API — check network settings

---

## Deployment

### Local Development

```bash
# Clone repository
git clone <repo_url>
cd Regen-Ag-App

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run app
streamlit run app.py
```

App runs at `http://localhost:8501`

### Production Deployment (Streamlit Cloud)

1. Push code to GitHub repository
2. Go to `streamlit.io`
3. Create new app → Select repository, branch, main file (`app.py`)
4. Configure secrets (GitHub token in `.streamlit/secrets.toml`):
```toml
[github]
token = "your_github_token"
```
5. Deploy

### Docker Deployment

Use `.devcontainer/devcontainer.json` for containerized development:
```bash
docker build -t ksura-app:latest .
docker run -p 8501:8501 ksura-app:latest streamlit run app.py
```

### Environment Variables

**Optional** (if deployed with environment variables):
```bash
export GITHUB_TOKEN="your_token"
export GITHUB_REPO="owner/repo"
```

Then modify `github_client.py` to read from env:
```python
import os
DEFAULT_REPO = os.getenv("GITHUB_REPO", "Chakrapani2122/Regen-Ag-Data")
```

---

## Summary for New Team Members

### What This App Does
- **Browse and analyze** research data stored safely on GitHub
- **Create publication-quality charts** with customization and comparison tools
- **Run statistical tests** to validate hypotheses
- **Upload new data** to organized folders
- **Manage and view** saved visualizations with descriptions

### How to Use (Quick Start)
1. Go to app home page
2. Select "View Data" to explore datasets
3. Select "Upload Data" to contribute new files
4. Select "Visualizations" → "Create" to generate charts
5. Select "Visualizations" → "View" to browse saved charts

### Tech Stack (High Level)
- **Frontend**: Streamlit (Python, web-based)
- **Data**: GitHub repository (backend storage)
- **Analysis**: Pandas, NumPy, SciPy, Statsmodels
- **Visualization**: Matplotlib, Seaborn

### Files Most Frequently Modified
1. `view.py` — Data analysis features
2. `visualize.py` — Chart generation
3. `github_client.py` — API interactions
4. `upload.py` — Upload interface

### Key Concepts
- **Session State**: Preserves user inputs while navigating pages
- **Caching**: Speeds up repeated operations (TTL-based)
- **GitHub API**: Handles all file I/O (read/write)
- **Token Authentication**: One per session, reused across pages

### For Questions
Refer to specific module sections in this documentation for detailed function signatures and behavior.

---

**Documentation Version**: 1.0  
**Last Updated**: March 13, 2026  
**Maintained By**: KSURA Development Team
