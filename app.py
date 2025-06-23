import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import MarkerCluster, HeatMap
import branca
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout="wide") # Используем широкую раскладку для лучшего отображения

# --- Функции для загрузки данных с кешированием ---

@st.cache_data
def load_vacancy_data():
    """Загружает и подготавливает данные по вакансиям."""
    df = pd.read_csv("main_cleaned_vacancies.csv")
    return df

@st.cache_data
def load_resume_data():
    """Загружает и подготавливает данные по резюме."""
    df = pd.read_csv("resumes_enbekkz.csv")
    df = df.rename(columns={"City/Region": "Region"})
    return df

# --- Основная часть приложения ---

st.title("Kazakhstan Job Market Analysis: Vacancies & Resumes")

# --- Главный переключатель в боковом меню ---
analysis_type = st.sidebar.radio(
    "Choose Analysis Type",
    ("Vacancy Analysis", "Resume Analysis")
)

# --- БЛОК 1: АНАЛИЗ ВАКАНСИЙ ---
if analysis_type == "Vacancy Analysis":
    st.header("Vacancy Data Analysis")
    df_vacancies = load_vacancy_data()

    # --- Предобработка данных для вакансий (из первого скрипта) ---
    salary_by_education_experience = df_vacancies.groupby(['Образование', 'Опыт работы', 'Категория']).apply(
        lambda x: pd.Series({
            'Средняя зарплата': (x['Средняя зарплата'] * x['Рабочих мест']).sum() / x['Рабочих мест'].sum() if x['Рабочих мест'].sum() > 0 else 0,
            'Общее количество рабочих мест': x['Рабочих мест'].sum()
        })
    ).reset_index()
    salary_by_education_experience['Общее количество рабочих мест'] = salary_by_education_experience['Общее количество рабочих мест'].astype(int)
    salary_by_education_experience['Средняя зарплата'] = salary_by_education_experience['Средняя зарплата'].astype(int)

    trends_by_profession = df_vacancies.groupby(['Название работы', 'Фильтрованные регионы'])['Рабочих мест'].sum().reset_index(name='Количество вакансий')
    top_professions = trends_by_profession.sort_values(['Фильтрованные регионы', 'Количество вакансий'], ascending=[True, False]).groupby('Фильтрованные регионы').head(5)

    # --- Меню для выбора графика вакансий ---
    menu = st.sidebar.radio(
        "Choose a Vacancy Chart",
        [
            "The most popular professions by filtered regions",
            "The impact of work experience on average salary depending on education",
            "3D Scatter Plot",
            "Top 20 Regions by Number of Vacancies",
            "Average Salary in Each Region in 2024",
            'Kazakhstan Map',
            "Education Level Requirements in Job Vacancies in 2024",
            "Weighted Average Salary by Education Level in 2024",
            "Average Salary Distribution by Work Schedule in 2024",
            "Top 10 Companies with the Most Vacancies in 2024",
            'Relationship Between Job Category and Work Experience in 2024'
        ]
    )

    # --- Отображение графиков вакансий ---
    if menu == "The most popular professions by filtered regions":
        st.subheader("The most popular professions by filtered regions")
        selected_regions = st.multiselect(
            'Select Region(s)',
            options=top_professions['Фильтрованные регионы'].unique(),
            default=top_professions['Фильтрованные регионы'].unique()
        )
        filtered_data = top_professions[top_professions['Фильтрованные регионы'].isin(selected_regions)]
        fig_bar = px.bar(
            filtered_data, x='Название работы', y='Количество вакансий', color='Фильтрованные регионы',
            title='The most popular professions by filtered regions',
            labels={'Количество вакансий': 'Number of vacancies', 'Название работы': 'Professions'},
            height=800
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    elif menu == "The impact of work experience on average salary depending on education":
        st.subheader("The impact of work experience on average salary depending on education")
        fig_line = go.Figure()
        for education_level in salary_by_education_experience['Образование'].unique():
            subset = salary_by_education_experience[salary_by_education_experience['Образование'] == education_level]
            fig_line.add_trace(go.Scatter(
                x=subset['Опыт работы'], y=subset['Средняя зарплата'], mode='lines+markers',
                name=education_level, text=education_level, marker=dict(size=8)
            ))
        fig_line.update_layout(
            title='The impact of work experience on average salary depending on education',
            xaxis_title='Work experience (years)', yaxis_title='Average salary',
            legend_title='Education', height=800
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    # ... (здесь и далее вставляем все остальные `elif` из первого скрипта, заменяя `df` на `df_vacancies`) ...
    elif menu == "3D Scatter Plot":
        st.subheader("3D Scatter Plot of Experience, Education, and Salary")
        unique_categories = df_vacancies['Категория'].unique()
        selected_categories = st.multiselect(
            'Select categories', options=unique_categories, default=unique_categories
        )
        filtered_df = df_vacancies[df_vacancies['Категория'].isin(selected_categories)]
        colors = px.colors.qualitative.Plotly
        color_map = {category: colors[i % len(colors)] for i, category in enumerate(selected_categories)}

        fig_3d = px.scatter_3d(
            filtered_df, x='Опыт работы', y='Образование', z='Средняя зарплата', color='Категория',
            title='3D Scatter Plot', hover_name='Категория', size_max=5, color_discrete_sequence=colors
        )
        fig_3d.update_layout(
            scene=dict(xaxis_title='Experience', yaxis_title='Education Level', zaxis_title='Average Salary'),
            height=800
        )
        st.plotly_chart(fig_3d, use_container_width=True)

        fig_scatter = go.Figure()
        for category in selected_categories:
            filtered_salary_data = df_vacancies[df_vacancies['Категория'] == category]
            salary_by_education = filtered_salary_data.groupby('Образование')['Средняя зарплата'].mean().reset_index()
            fig_scatter.add_trace(go.Scatter(
                x=salary_by_education['Образование'], y=salary_by_education['Средняя зарплата'], mode='markers',
                name=category, marker=dict(size=10, color=color_map[category])
            ))
        fig_scatter.update_layout(
            title='Average salary by education for selected categories',
            xaxis_title='Education Level', yaxis_title='Average salary', height=600
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        fig_scatter1 = go.Figure()
        for category in selected_categories:
            filtered_salary_data = df_vacancies[df_vacancies['Категория'] == category]
            salary_by_experience = filtered_salary_data.groupby('Опыт работы')['Средняя зарплата'].mean().reset_index()
            fig_scatter1.add_trace(go.Scatter(
                x=salary_by_experience['Опыт работы'], y=salary_by_experience['Средняя зарплата'], mode='markers',
                name=category, marker=dict(size=10, color=color_map[category])
            ))
        fig_scatter1.update_layout(
            title='Average salary based on work experience for selected categories',
            xaxis_title='Work experience', yaxis_title='Average salary', height=600
        )
        st.plotly_chart(fig_scatter1, use_container_width=True)

    elif menu == "Top 20 Regions by Number of Vacancies":
        st.subheader("Top 20 Regions by Number of Vacancies")
        jobs_by_city = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum()
        top_cities = jobs_by_city.sort_values(ascending=False).head(20).reset_index()
        calm_colors_no_black = ['#A8DADC', '#457B9D', '#F1FAEE', '#F1C40F', '#F47C7C',
                                '#2A9D8F', '#264653', '#E9C46A', '#F4A261', '#F9C74F',
                                '#90BE6D', '#43AA8B', '#4D908E', '#577590', '#277DA1']
        
        fig = px.bar(
            top_cities, x='Фильтрованные регионы', y='Рабочих мест',
            title='Top 20 Regions by Number of Vacancies in 2024',
            labels={'Фильтрованные регионы': 'Region', 'Рабочих мест': 'Number of Vacancies'},
            text='Рабочих мест', color_discrete_sequence=calm_colors_no_black
        )
        fig.update_layout(height=700, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    elif menu == 'Kazakhstan Map':
        st.subheader("Interactive Map of Vacancies in Kazakhstan")
        df_vacancies["Средняя зарплата с учетом рабочих мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
        weighted_avg_salary = df_vacancies.groupby("Фильтрованные регионы").apply(
            lambda x: x["Средняя зарплата с учетом рабочих мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0
        )
        city_coords = { 
            'Область Абай': {'lat': 48.9434, 'lon': 80.1390}, 'Алматинская область': {'lat': 43.9368, 'lon': 76.8260}, 
            'Алматы': {'lat': 43.2380, 'lon': 76.8829}, 'Астана': {'lat': 51.169, 'lon': 71.449}, 
            'Атырауская область': {'lat': 47.9053, 'lon': 51.3781}, 'Акмолинская область': {'lat': 51.9165, 'lon': 69.4110}, 
            'Актюбинская область': {'lat': 48.7797, 'lon': 57.9974}, 'Западно-Казахстанская область': {'lat': 49.5568, 'lon': 50.2227}, 
            'Жамбылская область': {'lat': 44.4168, 'lon': 72.1341}, 'Область Жетісу': {'lat': 45.00, 'lon': 78.00}, 
            'Мангистауская область': {'lat': 44.5908, 'lon': 53.8500}, 'Павлодарская область': {'lat': 52.6509, 'lon': 76.7773}, 
            'Северо-Казахстанская область': {'lat': 53.9797, 'lon': 69.045}, 'Туркестанская область': {'lat': 42.2663, 'lon': 68.1431}, 
            'Шымкент': {'lat': 42.3205, 'lon': 69.5876}, 'Восточно-Казахстанская область': {'lat': 48.6130, 'lon': 84.71032}, 
            'Карагандинская область': {'lat': 48.1671, 'lon': 73.4729}, 'Костанайская область': {'lat': 52.0615, 'lon': 62.9372}, 
            'Кызылординская область': {'lat': 45.2058, 'lon': 63.9155}, 'Область Ұлытау': {'lat': 48.00, 'lon': 66.59}
        }
        jobs_by_city = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum()
        top_cities = jobs_by_city.sort_values(ascending=False).head(20).reset_index()
        max_jobs = top_cities["Рабочих мест"].max()
        min_jobs = top_cities["Рабочих мест"].min()
        colormap = branca.colormap.linear.YlOrRd_09.scale(min_jobs, max_jobs)
        colormap.caption = 'Number of vacancies'
        m = folium.Map(location=[48.0196, 66.9237], zoom_start=5, tiles="cartodb positron")
        marker_cluster = MarkerCluster().add_to(m)
        heat_data = []
        for _, row in top_cities.iterrows():
            region, jobs = row['Фильтрованные регионы'], row['Рабочих мест']
            if region in city_coords:
                coords, color = city_coords[region], colormap(jobs)
                avg_salary = weighted_avg_salary.get(region, 0)
                heat_data.append([coords['lat'], coords['lon'], jobs])
                radius = 8 + (jobs / max_jobs) * 12
                folium.CircleMarker(
                    location=[coords['lat'], coords['lon']], radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7,
                    tooltip=f"<strong>{region}</strong><br>Vacancies: {int(jobs)}<br>Avg Salary: {int(avg_salary)} KZT"
                ).add_to(marker_cluster)
        HeatMap(heat_data, radius=20, max_zoom=13).add_to(m)
        colormap.add_to(m)
        st_folium(m, width=725, height=500)

    # ... и так далее для всех остальных графиков из первого скрипта
    # Я добавлю еще несколько для полноты примера

    elif menu == "Education Level Requirements in Job Vacancies in 2024":
        st.subheader("Education Level Requirements in Job Vacancies in 2024")
        education_counts = df_vacancies["Образование"].value_counts()
        education_percentage = (education_counts / education_counts.sum()) * 100
        fig = go.Figure(data=[go.Pie(
            labels=education_percentage.index, values=education_percentage, textinfo='percent+label',
            marker=dict(colors=px.colors.qualitative.Pastel)
        )])
        fig.update_layout(title="Education Level Requirements in Job Vacancies in 2024")
        st.plotly_chart(fig, use_container_width=True)

    elif menu == 'Top 10 Companies with the Most Vacancies in 2024':
        st.subheader("Top 10 Companies with the Most Vacancies in 2024")
        top_companies = df_vacancies.groupby("Название компаний")["Рабочих мест"].sum().sort_values(ascending=False).head(10)
        fig = px.bar(
            top_companies, x=top_companies.values, y=top_companies.index, orientation='h',
            labels={'y': 'Company Name', 'x': 'Total number of vacancies'},
            title='Top 10 Companies with the Most Vacancies in 2024',
            text=top_companies.values, color=top_companies.index,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


# --- БЛОК 2: АНАЛИЗ РЕЗЮМЕ ---
elif analysis_type == "Resume Analysis":
    st.header("Resume Data Analysis")
    df_resumes = load_resume_data()

    # --- Меню для выбора графика резюме ---
    chart_type = st.sidebar.radio(
        "Choose a Resume Chart",
        [
            "Top 20 Regions by Number of Resumes",
            "Most Popular Professions by Region",
            "Salary vs. Work Experience",
            "Education Level Distribution",
            "Mean, Median, Mode Salaries by Region",
            "Salary Distribution by Work Conditions",
            "Salary Distribution by Sex"
        ]
    )
    
    # --- Общий фильтр по регионам для всех графиков резюме ---
    st.sidebar.subheader("Filters")
    region_selection = st.sidebar.multiselect(
        "Select Regions (optional)",
        df_resumes['Region'].unique(),
        default=list(df_resumes['Region'].unique())
    )
    filtered_df = df_resumes[df_resumes['Region'].isin(region_selection)]

    # --- Отображение графиков резюме ---
    if chart_type == "Top 20 Regions by Number of Resumes":
        st.subheader("Top 20 Regions by Resume Count")
        region_counts = filtered_df['Region'].value_counts().head(20)
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.barplot(x=region_counts.values, y=region_counts.index, ax=ax, palette="viridis")
        ax.set_xlabel("Number of Resumes")
        ax.set_ylabel("Region")
        ax.bar_label(ax.containers[0])
        st.pyplot(fig)

    elif chart_type == "Most Popular Professions by Region":
        st.subheader("Most Common Professions in Selected Regions")
        top_jobs = filtered_df['Category'].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.barplot(x=top_jobs.values, y=top_jobs.index, ax=ax, palette="plasma")
        ax.set_xlabel("Count")
        ax.set_ylabel("Job Category")
        ax.bar_label(ax.containers[0])
        st.pyplot(fig)

    elif chart_type == "Salary vs. Work Experience":
        st.subheader("Salary vs. Work Experience")
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.scatterplot(data=filtered_df, x="Work experience (year)", y="Salary", hue="Region", ax=ax, alpha=0.6)
        ax.set_xlabel("Work Experience (years)")
        ax.set_ylabel("Salary")
        st.pyplot(fig)

    elif chart_type == "Education Level Distribution":
        st.subheader("Education Level Distribution")
        edu_counts = filtered_df['Education'].value_counts()
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=edu_counts.values, y=edu_counts.index, ax=ax, palette="mako")
        ax.set_xlabel("Count")
        ax.set_ylabel("Education Level")
        ax.bar_label(ax.containers[0])
        st.pyplot(fig)

    elif chart_type == "Mean, Median, Mode Salaries by Region":
        st.subheader("Salary Statistics by Region (Top 20)")
        grouped = filtered_df.groupby("Region")["Salary"].agg(["mean", "median", lambda x: x.mode().iloc[0] if not x.mode().empty else None])
        grouped.columns = ["Mean", "Median", "Mode"]
        grouped = grouped.dropna().sort_values("Mean", ascending=False).head(20)
        st.dataframe(grouped.style.format("{:,.0f} KZT"))

    elif chart_type == "Salary Distribution by Work Conditions":
        st.subheader("Salary Distribution by Work Conditions")
        fig, ax = plt.subplots(figsize=(12, 7))
        sns.boxplot(data=filtered_df, x="working conditions", y="Salary", ax=ax)
        ax.set_xlabel("Working Conditions")
        ax.set_ylabel("Salary")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)

    elif chart_type == "Salary Distribution by Sex":
        st.subheader("Salary Distribution by Sex")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.boxplot(data=filtered_df, x="Sex", y="Salary", ax=ax)
        ax.set_xlabel("Sex")
        ax.set_ylabel("Salary")
        st.pyplot(fig)