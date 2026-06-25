# E-Commerce Customer Behavior Analysis — Dashboard

A Streamlit dashboard built on the UCI **Online Retail** dataset, implementing
the four-module spec (Alpha → Delta) for customer behavior analysis, RFM
segmentation, product analytics, and regional revenue mapping. Gated behind
an admin-only login.

---

## 1. Project Structure

```
jitgo_retail_project/
├── app.py                      # Main entry point — login gate + sidebar nav
├── auth.py                     # Admin login logic (reads st.secrets)
├── data_access.py              # Cached data-loading layer for the dashboard
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── config.toml             # Theme settings (safe to commit)
│   └── secrets.toml            # Admin credentials (DO NOT COMMIT — gitignored)
├── data/
│   ├── Online_Retail.xlsx      # Raw dataset (commit this — needed for first-run build)
│   └── ecommerce.db            # Generated SQLite DB (built automatically, can gitignore)
├── modules/
│   ├── module_alpha.py         # Consumer Log Handler — cleaning + DB load
│   ├── module_beta.py          # RFM Segmentation Core
│   ├── module_gamma.py         # Product Purchase Analytics
│   └── module_delta.py         # Regional Revenue Mapping
└── pages/
    ├── overview.py             # Home/KPI summary page
    ├── page_alpha.py           # Module Alpha dashboard view
    ├── page_beta.py            # Module Beta dashboard view (RFM scatter, etc.)
    ├── page_gamma.py           # Module Gamma dashboard view (product analytics)
    └── page_delta.py           # Module Delta dashboard view (regional map)
```

**Note on `pages/` naming:** these files are NOT Streamlit's automatic
multi-page-app folder (that requires numeric prefixes and creates its own
URL-based nav). They're plain Python modules dispatched manually from
`app.py`'s sidebar `st.radio`, which is what gives you full control over the
sidebar labels/grouping/icons exactly as you wanted.

---

## 2. Local Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the database (first time only — app.py also auto-builds this on first run)
python modules/module_alpha.py
python modules/module_beta.py

# 4. Set your admin credentials locally
# Edit .streamlit/secrets.toml and change the default password:
#   [admin]
#   username = "admin"
#   password = "your-real-password"

# 5. Run the app
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`). Log in with
the credentials from `secrets.toml`.

---

## 3. How the Pipeline Works (Module Alpha & Beta)

- `modules/module_alpha.py` reads `data/Online_Retail.xlsx`, cleans it
  (drops missing CustomerID/Description, removes cancelled orders and
  bad quantity/price rows, dedupes), and writes the result into
  `data/ecommerce.db` as a `transactions` table.
- `modules/module_beta.py` reads `transactions`, computes Recency/Frequency/
  Monetary per customer, scores each into quintiles (1–5), and writes a
  `rfm_segments` table back into the same database.
- `modules/module_gamma.py` and `modules/module_delta.py` don't write new
  tables — they're query libraries that read `transactions` on demand
  (top products, country rollups, timelines, drill-downs).

`app.py` calls `ensure_database_exists()` on startup, so if `ecommerce.db`
is missing (e.g. a fresh clone or fresh Streamlit Cloud deploy), it
auto-builds it from the Excel file before rendering anything. There's also
a **"Rebuild data"** button in the sidebar if you ever replace the Excel
file and want to refresh the database without redeploying.

---

## 4. Deploying to Streamlit Community Cloud

### Step 1 — Push to GitHub
```bash
cd jitgo_retail_project
git init
git add .
git commit -m "Initial commit: e-commerce analytics dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

**Important:** `.streamlit/secrets.toml` is in `.gitignore` and will NOT be
pushed — that's intentional, your real password should never be in the repo.

Also confirm `data/Online_Retail.xlsx` is small enough for GitHub (it's
~23MB, fine for a normal repo; GitHub's hard limit is 100MB per file).
If you'd rather not commit the raw Excel file, you can instead commit
`data/ecommerce.db` directly and skip the auto-build step — either works.

### Step 2 — Create the app on Streamlit Cloud
1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **"New app"**.
3. Select your repository, branch (`main`), and set **Main file path** to
   `app.py`.
4. Click **"Advanced settings"** before deploying.

### Step 3 — Add your secrets
Still in **Advanced settings** (or later via **App settings → Secrets**
after deploying), paste:

```toml
[admin]
username = "admin"
password = "your-real-password-here"
```

This is the cloud equivalent of your local `.streamlit/secrets.toml` —
`auth.py` reads from `st.secrets` either way, so no code changes are needed
between local and deployed environments.

### Step 4 — Deploy
Click **Deploy**. First boot will take a little longer since it needs to
build `ecommerce.db` from the Excel file — after that, it's cached.

### Step 5 — Share access
Streamlit Community Cloud apps are public URLs by default, but only people
who know the URL **and** have the admin username/password can get past your
login screen. If you want the app itself unlisted, you can also enable
"Make this app private" in Streamlit Cloud's settings to restrict it to
specific Google/GitHub accounts on top of the password gate.

---

## 5. Changing the Admin Password Later

- **Locally:** edit `.streamlit/secrets.toml` directly.
- **On Streamlit Cloud:** go to your app → **Settings (⋮ menu) → Secrets**,
  edit the value, save — the app restarts automatically with the new
  credentials. No redeploy or code change needed.

---

## 6. Module-to-Dashboard Mapping (per your project spec)

| Spec Module | Code | Dashboard Page | What it shows |
|---|---|---|---|
| Module Alpha — Consumer Log Handler | `modules/module_alpha.py` | "Module Alpha" | Cleaning audit trail, filterable raw transaction explorer |
| Module Beta — RFM Segmentation Core | `modules/module_beta.py` | "Module Beta" | Segment KPIs, **Customer Segment Scatter Diagram**, per-segment drill-down |
| Module Gamma — Product Purchase Analytics | `modules/module_gamma.py` | "Module Gamma" | **Purchase Ingestion Timeline**, top products, **Catalog Revenue Matrix**, product drill-down |
| Module Delta — Regional Revenue Mapping | `modules/module_delta.py` | "Module Delta" | World choropleth map, country revenue/customer bars, country trend drill-down |

The **Overview** page ties all four together into a single executive summary
(total revenue/orders/customers, monthly trend, segment pie, top 5 markets).
