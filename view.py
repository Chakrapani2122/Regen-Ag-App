import streamlit as st
import pandas as pd
from io import BytesIO, StringIO
import docx
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import numpy as np
from concurrent.futures import ThreadPoolExecutor

try:
    from scipy import stats
except Exception:
    stats = None

try:
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
except Exception:
    pairwise_tukeyhsd = None

from github_client import get_github_client

warnings.filterwarnings("ignore")

ROOT_EXCLUDED_FOLDERS = {"Visualizations"}
ROOT_EXCLUDED_FILES = {".gitattributes", ".gitignore"}


def validate_github_token(token):
    client = get_github_client(token)
    return client.validate_token()


@st.cache_data(show_spinner=False, ttl=120)
def get_repo_contents_cached(token, path=""):
    client = get_github_client(token)
    items, error, auth_error = client.list_contents(path)
    if auth_error:
        return [], [], "Authentication failed or token expired.", True
    if items is None:
        return [], [], error or "Unable to load repository contents.", False

    folders = []
    files = []
    for item in items:
        if item.get("type") == "dir":
            if not path and item.get("name") in ROOT_EXCLUDED_FOLDERS:
                continue
            folders.append(item.get("name"))
        elif item.get("type") == "file":
            if not path and item.get("name") in ROOT_EXCLUDED_FILES:
                continue
            files.append(item.get("name"))

    return sorted(folders), sorted(files), None, False


@st.cache_data(show_spinner=False, ttl=180)
def get_github_file_content_cached(token, file_path):
    client = get_github_client(token)
    content, error, auth_error, metadata = client.get_file_content(file_path)
    sha = metadata.get("sha") if metadata else None
    return content, error, auth_error, sha


def prefetch_next_level_contents(token, current_path, selected_folder):
    if not selected_folder:
        return

    next_path = f"{current_path}/{selected_folder}" if current_path else selected_folder

    # Warm cache for immediate next path and first-level subfolders.
    folders, _, _, _ = get_repo_contents_cached(token, next_path)
    if not folders:
        return

    with ThreadPoolExecutor(max_workers=4) as executor:
        for subfolder in folders[:4]:
            child_path = f"{next_path}/{subfolder}"
            executor.submit(get_repo_contents_cached, token, child_path)

def parse_csv_file(file_content):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    parse_attempts = [
        {"sep": ",", "engine": "python"},
        {"sep": None, "engine": "python"},
    ]

    last_error = None
    for encoding in encodings:
        for parse_kwargs in parse_attempts:
            try:
                text = file_content.decode(encoding)
                return pd.read_csv(StringIO(text), **parse_kwargs), None
            except Exception as exc:
                last_error = exc

    return None, str(last_error) if last_error else "Unknown CSV parsing error."

def parse_tsv_file(file_content):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for encoding in encodings:
        try:
            text = file_content.decode(encoding)
            return pd.read_csv(StringIO(text), sep="\t", engine="python"), None
        except Exception as exc:
            last_error = exc

    return None, str(last_error) if last_error else "Unknown TSV parsing error."

def decode_text_file(file_content):
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    last_error = None
    for encoding in encodings:
        try:
            return file_content.decode(encoding), None
        except Exception as exc:
            last_error = exc
    return None, str(last_error) if last_error else "Unknown text decoding error."


@st.cache_data(show_spinner=False, ttl=300)
def parse_dataframe_cached(file_name, file_content, sheet_name=None, file_sha=None):
    del file_sha
    file_name_lower = file_name.lower()

    if file_name_lower.endswith((".xls", ".xlsx")):
        excel_data = pd.ExcelFile(BytesIO(file_content))
        if not sheet_name:
            return None, "Please select a sheet."
        return excel_data.parse(sheet_name), None

    if file_name_lower.endswith(".csv"):
        return parse_csv_file(file_content)

    if file_name_lower.endswith(".tsv"):
        return parse_tsv_file(file_content)

    return None, "Unsupported dataframe format for parsing."

def read_docx(content):
    """Reads content from a .docx file."""
    try:
        doc = docx.Document(BytesIO(content))
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        return f"Error reading .docx file: {e}"

def nav_option_value(item_type, name):
    return f"{item_type}|{name}"

def parse_nav_option(option):
    if not option or "|" not in option:
        return None, None
    item_type, item_name = option.split("|", 1)
    return item_type, item_name

def get_file_icon(file_name):
    ext = file_name.lower().rsplit(".", 1)[-1] if "." in file_name else ""
    icon_by_extension = {
        "xls": "📊",
        "xlsx": "📊",
        "csv": "📈",
        "tsv": "📈",
        "txt": "📄",
        "docx": "📝",
        "pdf": "📕",
        "png": "🖼️",
        "jpg": "🖼️",
        "jpeg": "🖼️",
        "gif": "🖼️",
        "xml": "🧾",
        "json": "🧾",
        "zip": "🗜️",
    }
    return icon_by_extension.get(ext, "📄")

def format_nav_option(option):
    if not option:
        return "Choose an item"

    item_type, item_name = parse_nav_option(option)
    if item_type == "folder":
        return f"📁 {item_name}"
    if item_type == "file":
        return f"{get_file_icon(item_name)} {item_name}"
    return option

def get_numeric_and_categorical_columns(df):
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    # Treat low-cardinality numeric columns as categorical candidates for grouping tests.
    for col in numeric_cols:
        if df[col].nunique(dropna=True) <= 10 and col not in categorical_cols:
            categorical_cols.append(col)

    return numeric_cols, categorical_cols

def render_selector_grid(selector_configs):
    selections = {}
    for row_start in range(0, len(selector_configs), 3):
        row_items = selector_configs[row_start:row_start + 3]
        cols = st.columns(3)
        for idx, cfg in enumerate(row_items):
            with cols[idx]:
                if cfg["kind"] == "single":
                    selections[cfg["key"]] = st.selectbox(
                        cfg["label"],
                        options=cfg["options"],
                        key=cfg["key"],
                    )
                elif cfg["kind"] == "multi":
                    selections[cfg["key"]] = st.multiselect(
                        cfg["label"],
                        options=cfg["options"],
                        default=cfg.get("default", []),
                        key=cfg["key"],
                    )
                elif cfg["kind"] == "number":
                    selections[cfg["key"]] = st.number_input(
                        cfg["label"],
                        min_value=cfg.get("min_value", 0.001),
                        max_value=cfg.get("max_value", 0.200),
                        value=cfg.get("value", 0.050),
                        step=cfg.get("step", 0.001),
                        key=cfg["key"],
                    )
    return selections


def cohen_d(sample_a, sample_b):
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    if len(a) < 2 or len(b) < 2:
        return np.nan
    pooled_std = np.sqrt(((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1)) / (len(a) + len(b) - 2))
    if pooled_std == 0:
        return np.nan
    return (np.mean(a) - np.mean(b)) / pooled_std


def welch_mean_diff_ci(sample_a, sample_b, alpha=0.05):
    a = np.asarray(sample_a, dtype=float)
    b = np.asarray(sample_b, dtype=float)
    mean_diff = float(np.mean(a) - np.mean(b))
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    n_a = len(a)
    n_b = len(b)
    se = np.sqrt((var_a / n_a) + (var_b / n_b))
    if se == 0:
        return mean_diff, mean_diff
    dof_num = ((var_a / n_a) + (var_b / n_b)) ** 2
    dof_den = ((var_a / n_a) ** 2) / (n_a - 1) + ((var_b / n_b) ** 2) / (n_b - 1)
    dof = dof_num / dof_den if dof_den else np.inf
    t_crit = stats.t.ppf(1 - alpha / 2, dof)
    margin = t_crit * se
    return mean_diff - margin, mean_diff + margin


def pearson_ci(r_value, n, alpha=0.05):
    if n <= 3:
        return np.nan, np.nan
    r_value = max(min(r_value, 0.999999), -0.999999)
    z = np.arctanh(r_value)
    se = 1 / np.sqrt(n - 3)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    lo = np.tanh(z - z_crit * se)
    hi = np.tanh(z + z_crit * se)
    return lo, hi


def cramers_v(chi2, n, rows, cols):
    denom = n * min(rows - 1, cols - 1)
    if denom <= 0:
        return np.nan
    return np.sqrt(chi2 / denom)


def render_data_quality_profiler(df):
    with st.expander("Data Quality Profiler", expanded=False):
        row_count, col_count = df.shape
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        object_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

        missing_count = int(df.isna().sum().sum())
        duplicate_count = int(df.duplicated().sum())

        constant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
        near_constant_cols = []
        for col in df.columns:
            vc = df[col].value_counts(dropna=False)
            if vc.empty:
                continue
            top_ratio = float(vc.iloc[0] / len(df)) if len(df) else 0
            if top_ratio >= 0.95 and col not in constant_cols:
                near_constant_cols.append(col)

        inconsistent_type_cols = []
        for col in object_cols:
            sample = df[col].dropna().head(500)
            if sample.empty:
                continue
            if sample.map(type).nunique() > 1:
                inconsistent_type_cols.append(col)

        outlier_summary = {}
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = int(((series < lower) | (series > upper)).sum())
            if outliers > 0:
                outlier_summary[col] = outliers

        stats_cols = st.columns(3)
        stats_cols[0].metric("Rows", row_count)
        stats_cols[1].metric("Columns", col_count)
        stats_cols[2].metric("Missing Cells", missing_count)

        missing_by_column = (
            df.isna()
            .sum()
            .rename("Missing Values")
            .reset_index()
            .rename(columns={"index": "Column"})
            .sort_values("Missing Values", ascending=False)
        )
        missing_by_column["Missing %"] = (
            (missing_by_column["Missing Values"] / max(len(df), 1)) * 100
        ).round(2)
        missing_by_column = missing_by_column[missing_by_column["Missing Values"] > 0]
        if not missing_by_column.empty:
            st.write("Missing values by column")
            st.dataframe(missing_by_column, use_container_width=True)
        else:
            st.write("No missing values detected in any column.")

        stats_cols = st.columns(3)
        stats_cols[0].metric("Duplicate Rows", duplicate_count)
        stats_cols[1].metric("Constant Columns", len(constant_cols))
        stats_cols[2].metric("Near-Constant Columns", len(near_constant_cols))

        if constant_cols:
            st.write("Constant columns:", ", ".join(constant_cols))
        if near_constant_cols:
            st.write("Near-constant columns:", ", ".join(near_constant_cols))
        if inconsistent_type_cols:
            st.write("Type-inconsistency candidates:", ", ".join(inconsistent_type_cols))

        if outlier_summary:
            outlier_df = pd.DataFrame(
                [{"Column": k, "Outlier Count": v} for k, v in outlier_summary.items()]
            ).sort_values("Outlier Count", ascending=False)
            st.write("Outlier flags (IQR method):")
            st.dataframe(outlier_df, use_container_width=True)


def render_smart_recommendations(df):
    with st.expander("Smart Recommendations", expanded=False):
        numeric_cols, categorical_cols = get_numeric_and_categorical_columns(df)
        missing_ratio = float(df.isna().sum().sum() / (df.shape[0] * max(df.shape[1], 1))) if len(df) else 0.0
        duplicate_count = int(df.duplicated().sum())

        test_recommendations = []
        chart_recommendations = []
        cleaning_recommendations = []

        if len(numeric_cols) >= 2:
            test_recommendations.append("Pearson Correlation and Correlation Matrix")
            chart_recommendations.append("Scatter Plot and Heatmap")
        if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
            test_recommendations.append("ANOVA or Independent T-Test if grouping has 2 levels")
            chart_recommendations.append("Box Plot or Violin Plot")
        if len(categorical_cols) >= 2:
            test_recommendations.append("Chi-Square Test for association")
            chart_recommendations.append("Stacked Bar Chart")

        if missing_ratio > 0.05:
            cleaning_recommendations.append("Address missing values (imputation or filtered analysis)")
        if duplicate_count > 0:
            cleaning_recommendations.append("Review and remove duplicate rows")
        constant_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
        if constant_cols:
            cleaning_recommendations.append("Drop constant columns with no analytical variance")

        if not cleaning_recommendations:
            cleaning_recommendations.append("Data quality looks good for statistical analysis")

        st.write("Suggested statistical tests")
        for item in test_recommendations or ["No strong test recommendations from current column types."]:
            st.write(f"- {item}")

        st.write("Suggested visualizations")
        for item in chart_recommendations or ["Use table summaries until more numeric/categorical columns are available."]:
            st.write(f"- {item}")

        st.write("Suggested data cleaning steps")
        for item in cleaning_recommendations:
            st.write(f"- {item}")


def render_statistical_tests(df):
    with st.expander("Statistical Tests", expanded=False):
        numeric_cols, categorical_cols = get_numeric_and_categorical_columns(df)

        st.caption(
            f"Detected {len(numeric_cols)} numeric and {len(categorical_cols)} categorical/grouping columns."
        )

        if stats is None:
            st.warning("SciPy is not available. Install 'scipy' to run statistical tests.")
            return

        top_controls = render_selector_grid([
            {
                "kind": "single",
                "label": "Choose a test:",
                "options": [
                    "Pearson Correlation (2 numeric columns)",
                    "Correlation Matrix (multiple numeric columns)",
                    "Independent T-Test (numeric by 2 groups)",
                    "Mann-Whitney U (numeric by 2 groups)",
                    "One-way ANOVA (numeric by multi-group category)",
                    "Chi-Square Test (2 categorical columns)",
                    "Shapiro-Wilk Normality Test (single numeric column)",
                ],
                "key": "view_test_name",
            },
            {
                "kind": "number",
                "label": "Significance level (alpha)",
                "key": "view_test_alpha",
                "min_value": 0.001,
                "max_value": 0.200,
                "value": 0.050,
                "step": 0.001,
            },
        ])
        test_name = top_controls["view_test_name"]
        alpha = top_controls["view_test_alpha"]
        test_key = test_name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("-", "_")

        if test_name == "Pearson Correlation (2 numeric columns)":
            if len(numeric_cols) < 2:
                st.info("At least 2 numeric columns are required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column 1",
                    "options": numeric_cols,
                    "key": "pearson_col1",
                },
            ])
            col1 = controls["pearson_col1"]
            col2_candidates = [c for c in numeric_cols if c != col1] or numeric_cols
            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column 2",
                    "options": col2_candidates,
                    "key": "pearson_col2",
                },
            ])
            col2 = controls["pearson_col2"]

            pair_df = df[[col1, col2]].dropna()
            if len(pair_df) < 3:
                st.warning("Need at least 3 non-null paired rows for Pearson correlation.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            corr, p_val = stats.pearsonr(pair_df[col1], pair_df[col2])
            ci_low, ci_high = pearson_ci(corr, len(pair_df), alpha=alpha)
            st.write(f"Correlation (r): **{corr:.4f}**")
            st.write(f"{int((1 - alpha) * 100)}% CI for r: **[{ci_low:.4f}, {ci_high:.4f}]**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write("Result: **Statistically significant**" if p_val < alpha else "Result: **Not statistically significant**")

        elif test_name == "Correlation Matrix (multiple numeric columns)":
            if len(numeric_cols) < 2:
                st.info("At least 2 numeric columns are required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "multi",
                    "label": "Select numeric columns",
                    "options": numeric_cols,
                    "default": numeric_cols[: min(5, len(numeric_cols))],
                    "key": "corr_matrix_cols",
                },
            ])
            selected = controls["corr_matrix_cols"]
            if len(selected) < 2:
                st.info("Select at least 2 numeric columns.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            corr_df = df[selected].corr(method="pearson")
            st.dataframe(corr_df, use_container_width=True)

        elif test_name == "Independent T-Test (numeric by 2 groups)":
            if not numeric_cols:
                st.info("A numeric column is required.")
                return
            if not categorical_cols:
                st.info("A categorical/grouping column is required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column",
                    "options": numeric_cols,
                    "key": "ttest_value_col",
                },
                {
                    "kind": "single",
                    "label": "Grouping column (must have 2 groups)",
                    "options": categorical_cols,
                    "key": "ttest_group_col",
                },
            ])
            value_col = controls["ttest_value_col"]
            group_col = controls["ttest_group_col"]

            subset = df[[value_col, group_col]].dropna()
            groups = subset[group_col].unique().tolist()
            if len(groups) != 2:
                st.warning(f"Grouping column must contain exactly 2 groups. Found {len(groups)}.")
                return

            group_a = subset[subset[group_col] == groups[0]][value_col]
            group_b = subset[subset[group_col] == groups[1]][value_col]
            if len(group_a) < 2 or len(group_b) < 2:
                st.warning("Each group needs at least 2 observations.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            stat, p_val = stats.ttest_ind(group_a, group_b, equal_var=False, nan_policy="omit")
            d_value = cohen_d(group_a, group_b)
            ci_low, ci_high = welch_mean_diff_ci(group_a, group_b, alpha=alpha)
            st.write(f"Groups: **{groups[0]}** (n={len(group_a)}) vs **{groups[1]}** (n={len(group_b)})")
            st.write(f"T statistic: **{stat:.4f}**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write(f"Cohen's d: **{d_value:.4f}**")
            st.write(f"{int((1 - alpha) * 100)}% CI for mean difference: **[{ci_low:.4f}, {ci_high:.4f}]**")
            st.write("Result: **Statistically significant**" if p_val < alpha else "Result: **Not statistically significant**")

        elif test_name == "Mann-Whitney U (numeric by 2 groups)":
            if not numeric_cols:
                st.info("A numeric column is required.")
                return
            if not categorical_cols:
                st.info("A categorical/grouping column is required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column",
                    "options": numeric_cols,
                    "key": "mw_value_col",
                },
                {
                    "kind": "single",
                    "label": "Grouping column (must have 2 groups)",
                    "options": categorical_cols,
                    "key": "mw_group_col",
                },
            ])
            value_col = controls["mw_value_col"]
            group_col = controls["mw_group_col"]

            subset = df[[value_col, group_col]].dropna()
            groups = subset[group_col].unique().tolist()
            if len(groups) != 2:
                st.warning(f"Grouping column must contain exactly 2 groups. Found {len(groups)}.")
                return

            group_a = subset[subset[group_col] == groups[0]][value_col]
            group_b = subset[subset[group_col] == groups[1]][value_col]
            if len(group_a) < 2 or len(group_b) < 2:
                st.warning("Each group needs at least 2 observations.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            stat, p_val = stats.mannwhitneyu(group_a, group_b, alternative="two-sided")
            st.write(f"Groups: **{groups[0]}** (n={len(group_a)}) vs **{groups[1]}** (n={len(group_b)})")
            st.write(f"U statistic: **{stat:.4f}**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write("Result: **Statistically significant**" if p_val < alpha else "Result: **Not statistically significant**")

        elif test_name == "One-way ANOVA (numeric by multi-group category)":
            if not numeric_cols:
                st.info("A numeric column is required.")
                return
            if not categorical_cols:
                st.info("A categorical/grouping column is required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column",
                    "options": numeric_cols,
                    "key": "anova_value_col",
                },
                {
                    "kind": "single",
                    "label": "Grouping column",
                    "options": categorical_cols,
                    "key": "anova_group_col",
                },
            ])
            value_col = controls["anova_value_col"]
            group_col = controls["anova_group_col"]

            subset = df[[value_col, group_col]].dropna()
            grouped_values = [
                grp[value_col].values
                for _, grp in subset.groupby(group_col)
                if len(grp[value_col]) >= 2
            ]
            if len(grouped_values) < 2:
                st.warning("Need at least 2 groups with 2+ observations each.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            stat, p_val = stats.f_oneway(*grouped_values)
            overall_mean = subset[value_col].mean()
            ss_total = ((subset[value_col] - overall_mean) ** 2).sum()
            ss_between = 0.0
            for _, grp in subset.groupby(group_col):
                ss_between += len(grp) * ((grp[value_col].mean() - overall_mean) ** 2)
            eta_sq = (ss_between / ss_total) if ss_total else np.nan

            st.write(f"F statistic: **{stat:.4f}**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write(f"Eta-squared: **{eta_sq:.4f}**")
            st.write("Result: **Statistically significant**" if p_val < alpha else "Result: **Not statistically significant**")

            if pairwise_tukeyhsd is not None:
                tukey_result = pairwise_tukeyhsd(
                    endog=subset[value_col].astype(float),
                    groups=subset[group_col].astype(str),
                    alpha=alpha,
                )
                tukey_table = pd.DataFrame(
                    tukey_result.summary().data[1:],
                    columns=tukey_result.summary().data[0],
                )
                st.write("Tukey HSD post-hoc")
                st.dataframe(tukey_table, use_container_width=True)
            else:
                st.info("Install statsmodels to enable Tukey HSD post-hoc analysis.")

        elif test_name == "Chi-Square Test (2 categorical columns)":
            if len(categorical_cols) < 2:
                st.info("At least 2 categorical/grouping columns are required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Categorical column 1",
                    "options": categorical_cols,
                    "key": "chi_col_left",
                },
            ])
            col_left = controls["chi_col_left"]
            col_right_candidates = [c for c in categorical_cols if c != col_left] or categorical_cols
            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Categorical column 2",
                    "options": col_right_candidates,
                    "key": "chi_col_right",
                },
            ])
            col_right = controls["chi_col_right"]

            subset = df[[col_left, col_right]].dropna()
            contingency = pd.crosstab(subset[col_left], subset[col_right])
            if contingency.empty or contingency.shape[0] < 2 or contingency.shape[1] < 2:
                st.warning("Need at least a 2x2 contingency table for a meaningful chi-square test.")
                return

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            chi2, p_val, dof, _ = stats.chi2_contingency(contingency)
            c_v = cramers_v(chi2, contingency.to_numpy().sum(), contingency.shape[0], contingency.shape[1])
            st.write("Contingency Table")
            st.dataframe(contingency, use_container_width=True)
            st.write(f"Chi-square statistic: **{chi2:.4f}**")
            st.write(f"Degrees of freedom: **{dof}**")
            st.write(f"Cramer's V: **{c_v:.4f}**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write("Result: **Statistically significant**" if p_val < alpha else "Result: **Not statistically significant**")

        elif test_name == "Shapiro-Wilk Normality Test (single numeric column)":
            if not numeric_cols:
                st.info("A numeric column is required.")
                return

            controls = render_selector_grid([
                {
                    "kind": "single",
                    "label": "Numeric column",
                    "options": numeric_cols,
                    "key": "shapiro_value_col",
                },
            ])
            value_col = controls["shapiro_value_col"]
            values = df[value_col].dropna()
            if len(values) < 3:
                st.warning("Need at least 3 observations for Shapiro-Wilk.")
                return

            if len(values) > 5000:
                values = values.sample(5000, random_state=42)
                st.caption("Shapiro-Wilk is limited to 5000 rows, so a random sample was used.")

            if not st.button("Run Selected Test", key=f"run_{test_key}"):
                return

            stat, p_val = stats.shapiro(values)
            st.write(f"W statistic: **{stat:.4f}**")
            st.write(f"P-value: **{p_val:.6f}**")
            st.write("Result: **Looks non-normal**" if p_val < alpha else "Result: **No evidence against normality**")

def render_repository_navigation(token):
    # --- Pass 1: walk via session_state to collect every level's (label, options, key) ---
    levels = []
    current_path = ""
    breadcrumbs = []
    level = 0

    while True:
        folders, files, error, auth_error = get_repo_contents_cached(token, current_path)
        if auth_error:
            st.session_state['gh_token'] = None
            st.session_state['gh_token_validated'] = False
            st.error("Authentication failed. Please re-enter your security token.")
            return "", None, None
        if error:
            st.warning(error)
            break

        options = [""] + [nav_option_value("folder", folder) for folder in folders] + [nav_option_value("file", file) for file in files]

        if len(options) == 1:
            break

        key = f"repo_nav_level_{level}"
        label = "Select a folder or file:" if level == 0 else f"Level {level + 1}:"

        # Invalidate stale stored value
        if key in st.session_state and st.session_state[key] not in options:
            st.session_state[key] = ""

        levels.append((label, options, key))

        # Read already-stored selection to decide whether to go deeper
        stored = st.session_state.get(key, "")
        if not stored:
            break

        item_type, item_name = parse_nav_option(stored)
        if item_type == "folder":
            breadcrumbs.append(item_name)
            current_path = "/".join(breadcrumbs)
            prefetch_next_level_contents(token, "/".join(breadcrumbs[:-1]), item_name)
            level += 1
        else:
            # File selected — no deeper levels needed
            break

    # --- Pass 2: render levels in a 3-column grid (new row every 3 levels) ---
    for row_start in range(0, len(levels), 3):
        row_levels = levels[row_start:row_start + 3]
        cols = st.columns(3)
        for col_idx, (label, options, key) in enumerate(row_levels):
            with cols[col_idx]:
                st.selectbox(
                    label, options, key=key,
                    format_func=format_nav_option
                )

    # --- Pass 3: re-walk session_state to derive final path and file ---
    breadcrumbs = []
    selected_file = None
    for _, _, key in levels:
        stored = st.session_state.get(key, "")
        if not stored:
            break
        item_type, item_name = parse_nav_option(stored)
        if item_type == "folder":
            breadcrumbs.append(item_name)
        else:
            selected_file = item_name
            break

    selected_path = "/".join(breadcrumbs)
    selected_file_path = f"{selected_path}/{selected_file}" if selected_path and selected_file else selected_file
    return selected_path, selected_file, selected_file_path

def main():
    st.title("View Data")
    st.write("*Access only to team members.*")

    # Use or ask for token: allow the user to provide it here (will be saved to session)
    token = st.session_state.get('gh_token', None)
    if not token:
        entered = st.text_input("Enter your security token:", type="password", key="view_token")
        if entered:
            if validate_github_token(entered):
                st.session_state['gh_token'] = entered
                st.session_state['gh_token_validated'] = True
                st.success("Token validated and saved for this session.")
                token = entered
            else:
                st.error("Invalid token or access issue.")
                return
        else:
            st.warning("Please provide your security token to proceed.")
            return
    else:
        # Validate once per session; rely on 401/403 to force re-entry after that.
        if 'gh_token_validated' not in st.session_state:
            st.session_state['gh_token_validated'] = True

    st.write("### Repository Browser")
    selected_path, file_name, selected_file_path = render_repository_navigation(token)
    if selected_file_path:
        st.caption(f"Current path: {selected_file_path}")
    elif selected_path:
        st.caption(f"Current path: {selected_path}/")

    sheet_name = None
    file_sha = None
    df = None
    
    if file_name:
        path = selected_path
        file_path = f"{path}/{file_name}" if path else file_name
        file_content, file_error, auth_error, file_sha = get_github_file_content_cached(token, file_path)
        if auth_error:
            st.session_state['gh_token'] = None
            st.session_state['gh_token_validated'] = False
            st.error("Authentication failed. Please re-enter your security token.")
            return
        if file_content is None:
            st.error(f"Unable to load the selected file: {selected_file_path or file_name}")
            if file_error:
                st.caption(f"Details: {file_error}")
            return
        
        file_name_lower = file_name.lower()

        if file_name_lower.endswith((".xls", ".xlsx")):
            try:
                excel_data = pd.ExcelFile(BytesIO(file_content))
                sheet_name = st.selectbox("Select a sheet:", excel_data.sheet_names, key="view_sheet_select")
                if sheet_name:
                    df, parse_error = parse_dataframe_cached(file_name, file_content, sheet_name=sheet_name, file_sha=file_sha)
                    if parse_error:
                        st.error(f"Unable to parse the selected sheet: {parse_error}")
                        return
            except Exception as exc:
                st.error(f"Unable to read the Excel file: {exc}")
                return
        elif file_name_lower.endswith((".csv", ".tsv")):
            df, parse_error = parse_dataframe_cached(file_name, file_content, file_sha=file_sha)
            if df is None:
                st.error(f"Unable to parse the file: {parse_error}")
                return
        elif file_name_lower.endswith(".txt"):
            text_content, text_error = decode_text_file(file_content)
            if text_content is None:
                st.error(f"Unable to read the TXT file: {text_error}")
                return

            with st.expander("TXT Content", expanded=True):
                st.text_area("Content", text_content, height=700, disabled=True, label_visibility="hidden")
        elif file_name.lower().endswith((".md", ".markdown")):
            markdown_content, markdown_error = decode_text_file(file_content)
            if markdown_content is None:
                st.error(f"Unable to read the Markdown file: {markdown_error}")
                return

            with st.expander("Markdown Preview", expanded=True):
                st.markdown(markdown_content)
        elif file_name_lower.endswith(".docx"):
            st.info("Successfully fetched .docx file content.")
            st.write(f"File size: {len(file_content)} bytes")
            
            docx_text = read_docx(file_content)

            if "Error reading .docx file" in docx_text:
                st.error(docx_text)
            elif not docx_text.strip():
                st.warning("The .docx file appears to be empty or could not be read.")
            else:
                with st.expander("DOCX Content", expanded=True):
                    st.text_area("Content", docx_text, height=700, disabled=True, label_visibility="hidden")
        else:
            st.warning("Only Excel, CSV, TSV, TXT, Markdown, and DOCX files are supported for preview.")

    if df is not None:
        with st.expander("File Display", expanded=True):
            selected_cols = st.multiselect(
                "Select columns to display:",
                df.columns.tolist(),
                default=df.columns.tolist()[: min(10, len(df.columns))],
                key="view_selected_cols",
            ) if len(df.columns) > 10 else df.columns.tolist()

            df_display = df[selected_cols] if selected_cols else df
            preview_size = st.selectbox("Preview rows", [100, 250, 500, 1000], index=1, key="preview_rows")
            st.dataframe(df_display.head(preview_size), height=500, use_container_width=True)
            if st.checkbox("Load full dataframe preview (slower)", key="load_full_df"):
                st.dataframe(df_display, height=700, use_container_width=True)

        # Only show Data Types, Summary, and Descriptive Statistics if sheet_name is not 'Metadata'
        if not (sheet_name and sheet_name.strip().lower() == "metadata"):
            with st.expander("Data Types", expanded=False):
                col_data = [(col, str(df[col].dtype)) for col in df.columns]
                col1, col2, col3, col4 = st.columns(4)
                for i, (col_name, col_type) in enumerate(col_data):
                    if i % 4 == 0:
                        col1.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 1:
                        col2.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 2:
                        col3.write(f"{col_name} : \n{col_type}")
                    elif i % 4 == 3:
                        col4.write(f"{col_name} : \n{col_type}")
            with st.expander("Summary", expanded=False):
                st.write(f"**Shape:** Rows: {df.shape[0]}, Columns: {df.shape[1]}")
                st.write("**Missing values per column:**")
                missing_data = df.isnull().sum()
                col1, col2, col3, col4 = st.columns(4)
                for i, (col_name, missing) in enumerate(missing_data.items()):
                    if i % 4 == 0:
                        col1.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 1:
                        col2.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 2:
                        col3.write(f"**{col_name}**: {missing}")
                    elif i % 4 == 3:
                        col4.write(f"**{col_name}**: {missing}")

            with st.expander("Descriptive Statistics", expanded=False):
                st.write(df.describe(include='all'))

            with st.expander("Correlation Matrix", expanded=False):
                numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                if len(numeric_cols) < 2:
                    st.info("At least 2 numeric columns are required.")
                else:
                    corr_cols = st.multiselect(
                        "Select numeric columns",
                        numeric_cols,
                        default=numeric_cols[: min(6, len(numeric_cols))],
                        key="corr_matrix_main_cols",
                    )
                    if len(corr_cols) >= 2:
                        st.dataframe(df[corr_cols].corr(), use_container_width=True)
                    else:
                        st.info("Select at least 2 numeric columns.")

            render_data_quality_profiler(df)
            render_smart_recommendations(df)

            render_statistical_tests(df)

if __name__ == "__main__":
    main()