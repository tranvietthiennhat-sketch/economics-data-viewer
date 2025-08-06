# Economics Data Viewer 📈

A lightweight Streamlit app for exploring World Bank economic indicators—GDP, inflation, employment, and thousands of others—in just a few clicks.

---

## Key features

- **Search-ready catalogue** – filter the full World Bank indicator list in real time  
- **Multi-country views** – compare countries, income groups, or custom regions  
- **Flexible charts** – switch between line, bar, and choropleth map visualisations  
- **Custom date ranges** – focus on a single year or decades of history  
- **Smart caching** – API calls are cached to keep the app quick and responsive  

---

## Run the app

### 1. Streamlit Cloud (free)

1. Fork or clone this repository.  
2. Sign in to [Streamlit Cloud](https://streamlit.io/cloud).  
3. Click **New app** → select this repo and `streamlit_app.py` as the entry point.  
4. Press **Deploy**. That’s it.

### 2. Local machine

```bash
git clone https://github.com/your-username/economics-data-viewer.git
cd economics-data-viewer
pip install -r requirements.txt
streamlit run streamlit_app.py
