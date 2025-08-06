import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import humanize

st.set_page_config(
    page_title="Economics Data Viewer",
    layout="wide",
    page_icon="📈",
)

st.markdown("<h1 style='text-align: center; color: #2c3e50;'> Economics Data Viewer</h1>", unsafe_allow_html=True)
@st.cache_data
def load_ind():
    url="https://api.worldbank.org/v2/indicator?format=json&per_page=30000"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[1]
    except requests.RequestException as e:
        st.error(f"Failed to load indicators: {e}")
        return pd.DataFrame()
    df=pd.json_normalize(data)
    df = df[df["source.id"] == "2"]
    df = df[["id", "name"]]
    df.columns = ["code", "name"]
    return df


indicators_df=load_ind()

search=st.text_input("Search for indicators:", value="GDP")
filtered_df=indicators_df[indicators_df["name"].str.contains(search, case=False, na=False, regex=False)]
if not filtered_df.empty:
    name = st.selectbox("Select a specific indicator:", filtered_df["name"],index=filtered_df["name"].tolist().index("GDP (current US$)") if "GDP (current US$)" in filtered_df["name"].tolist() else 0)
    code = filtered_df[filtered_df["name"] == name]["code"].values[0]
 
else:
    st.warning("No indicators found. Try a different keyword.")
    st.stop()


@st.cache_data
def load_countries():
    excluded_ids = ["HIC", "INX", "LIC", "LMC", "LMY", "MIC", "UMC"]
    url = "https://api.worldbank.org/v2/country?format=json&per_page=300"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()[1]
    except requests.RequestException as e:
        st.error(f"Failed to load indicators: {e}")
        return pd.DataFrame()
    df = pd.json_normalize(data)
    real_df=[]
    for _, row in df.iterrows():
            the_code = row["id"]
            if not the_code in excluded_ids:
                real_df.append(row)
    df= pd.DataFrame(real_df)

    df=df[["id", "name"]]
    df.columns = ["code", "name"]
    return df

country_df = load_countries()
country_df = country_df[country_df["code"] != "NA"] 

countries = st.multiselect(
    "🌐 Select countries or regions:",
    options=country_df["name"].tolist()
)

bar=False



year_range = st.slider(
    "Select year range:",
    min_value=1960,
    max_value=2023,
    value=[1960, 2023])

if countries:
    col1, col2, col3 = st.columns(3)
    with col1:
        line = st.checkbox("Show line chart", value=True)

    with col2:
        bar=st.checkbox("Show bar chart")

    with col3:
        map=st.checkbox("Show map", value=True)


@st.cache_data
def get_data(indicator, country, year_range):
    all_data = []
    
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date={year_range[0]}:{year_range[1]}&format=json&per_page=25000"
    response = requests.get(url)

    if response.ok and response.json()[1] is not None:
        data = response.json()[1]
        for entry in data:
            all_data.append({
                "country": entry["country"]["value"],
                "year": int(entry["date"]),
                "value": entry["value"]
            })
    return pd.DataFrame(all_data)

selected_codes = country_df[country_df["name"].isin(countries)]["code"].tolist()


the_list=[]
code_list=[]
# Function to get countries by region code with API
@st.cache_data
def get_countries_by_region_api(region_code):
    
    url = f"https://api.worldbank.org/v2/country?region={region_code}&format=json&per_page=20000"
    response = requests.get(url)
    data = response.json()
    name=[]
    code=[]
    if len(data) < 2:
        names = country_df[country_df["code"] == region_code]["name"].dropna().unique()
        name.append(names[0])
        code.append(region_code)
        return 0, name, code
        
    else:
    
        country_list = data[1]  
        extracted = [{"name": c["name"], "code": c["id"]} for c in country_list]
        df = pd.DataFrame(extracted)
        name_list= df['name'].tolist()
        tempc_list= df['code'].tolist()
        code.extend(tempc_list)
        name.extend(name_list)
    return 1, name, code



region_codes = country_df[country_df["name"].isin(countries)]["code"].dropna().unique().tolist()



hi=0
countries_in_data=""

for temporary_code in region_codes:
    h_val, c_names, c_codes =  get_countries_by_region_api(temporary_code)
    hi=max(hi, h_val)
    the_list.extend(c_names)
    code_list.extend(c_codes)
    
countries_in_data= list(set(the_list))
chart_codes=selected_codes[:]
if hi>0:
    agree=st.checkbox("Show individual country charts")
    if agree:
        chart_codes.extend(code_list)
        chart_codes=list(set(chart_codes))
chart_codes=";".join(chart_codes)
   
code_list=list(set(code_list))

countries_in_data = ", ".join(countries_in_data) + "."
code_lists=";".join(code_list)


#make the line chart
if selected_codes:
    df = get_data(code, chart_codes, year_range)
        

    if not df.empty:
        pivot_df = df.sort_values(by=["country", "year"]).pivot(index="year", columns="country", values="value").reset_index()
        df_melted = pd.melt(pivot_df, id_vars="year", var_name="country", value_name="value")
        df_melted["humanized"] = df_melted["value"].apply(lambda x: humanize.intword(x, format="%.2f") if pd.notnull(x) else "N/A")
        if line:
            # Title and chart
            title = f"{name} for {', '.join(countries)} from {year_range[0]} to {year_range[1]}"
            fig = px.line(
                df_melted,
                x="year",
                y="value",
                color="country",
                title=title,
                labels={"value": f"{name}", "year": "Year", "country": "Countries"},
                custom_data=["country", "humanized"]
        
            )

            fig.update_traces(
                hovertemplate="<b>Country: %{customdata[0]}</b><br>" +
                            "Year: %{x}<br>" +
                            f"{name}: %{{customdata[1]}}<extra></extra>"
            )

            fig.update_layout(
                hoverlabel=dict(
                    font_color="black"
                )
            )
            st.plotly_chart(fig, use_container_width=True)
    


    else:
        st.warning("⚠️ No data found for these regions for chart analysis.")
else:
    st.info("Please select at least one country or region.")

if selected_codes:
    if bar or map:
        year = st.slider("Select year for map", year_range[0], year_range[1], value=year_range[0])

#Bar data
if bar and not df.empty:
    df_bar = df_melted[df_melted["year"] == year]

    # Chart
    title = f"{name} in {year} for {', '.join(countries)}"

    fig = px.bar(
        df_bar.sort_values("value", ascending=False),
        x="country",
        y="value",
        title=title,
        labels={"value": f"{name}", "country": "Country"},
        custom_data=["country", "humanized"]
    )

    fig.update_traces(
        hovertemplate="<b>Country: %{customdata[0]}</b><br>" +
                    f"{name}: %{{customdata[1]}}<extra></extra>"
    )


    fig.update_layout(
        hoverlabel=dict(
            font_color="black"
        )
    )

    st.plotly_chart(fig, use_container_width=True)


# Get all countries map data
@st.cache_data
def get_data(indicator, country, year_range):
    all_data = []
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}?date={year_range[0]}:{year_range[1]}&format=json&per_page=25000"
    response = requests.get(url)

    if response.ok and response.json()[1] is not None:
        data = response.json()[1]
        for entry in data:
            all_data.append({
                "country": entry["country"]["value"],
                "year": int(entry["date"]),
                "value": entry["value"],
                "iso_alpha": entry["countryiso3code"]
            })
    return pd.DataFrame(all_data)


df = get_data(code, code_lists, year_range)


# Map code
if not df.empty and selected_codes and map:



    df_year = df[df["year"] == year]
    df_year["str"] = df_year["value"].apply(lambda x: humanize.intword(x, format="%.2f") if pd.notnull(x) else "N/A")

    df_year["value"] = df_year["value"].fillna(-1)

    real_vals = df_year.loc[df_year["value"] > 0, "value"]
    vmin, vmax = (real_vals.min(), real_vals.max()) if not real_vals.empty else (0, 1)


    custom_scale = [
        [0.0,     "#404040"],
        [0.00001, "#440154"],  
        [0.25,    "#3b528b"],
        [0.5,     "#21918c"],
        [0.75,    "#5ec962"],
        [1.0,     "#fde725"],
    ]


    map_fig = px.choropleth(
        df_year,
        locations="iso_alpha",
        color="value",
        hover_name="value",
        color_continuous_scale=custom_scale,
        range_color=[vmin, vmax], 
        labels={"value": f"{name}", "iso_alpha": "Country Code"},
            hover_data={
            "iso_alpha": True,
            "str": True,
            "value": False
        },
        custom_data=["iso_alpha", "str","country"],
        title=f"Map of the countries {name} in {year}"
    )
    
    map_fig.update_geos(
        showland=True,
        landcolor="lightblue",
        showocean=True,
        oceancolor="lightgrey",
        showframe=False,
        showcountries=True,
        countrycolor="black", 
        projection_type="natural earth"
    )

    map_fig.update_traces(
        hovertemplate="<b>%{customdata[2]}</b><br>" +
                    "Country Code: %{customdata[0]}<br>" +
                    "GDP (current US$): %{customdata[1]}<extra></extra>"
    )

    st.plotly_chart(map_fig, use_container_width=True)


        



if selected_codes:
    if map or line:
        with st.expander("🌍 View all countries in selected regions"):
                st.write(f"{countries_in_data}")

st.feedback("thumbs")




