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
import os

# --- Конфигурация страницы и опции ---
st.set_page_config(layout="wide", page_title="Kazakhstan Job Market Analysis")
st.set_option('deprecation.showPyplotGlobalUse', False) # Убираем предупреждение для st.pyplot()

# --- Надежная загрузка данных ---
@st.cache_data
def load_data(file_name):
    """Универсальная функция для загрузки CSV-файлов."""
    try:
        df = pd.read_csv(file_name)
        return df
    except FileNotFoundError:
        st.error(f"Ошибка: Файл '{file_name}' не найден. Убедитесь, что он находится в корневой папке проекта.")
        return None

# --- Основная часть приложения ---

st.title("🇰🇿 Анализ рынка труда Казахстана: Вакансии и Резюме")
st.markdown("---")

# --- Боковая панель (Sidebar) для навигации ---
st.sidebar.title("Панель управления")
analysis_type = st.sidebar.radio(
    "Выберите тип анализа:",
    ("Анализ вакансий", "Анализ резюме"),
    captions=["Данные с портала enbek.kz о предложениях работы", "Данные с портала enbek.kz о соискателях"]
)
st.sidebar.divider()

# --- БЛОК 1: АНАЛИЗ ВАКАНСИЙ ---
if analysis_type == "Анализ вакансий":
    df_vacancies = load_data("main_cleaned_vacancies.csv")

    if df_vacancies is not None:
        # --- Меню для выбора графика вакансий ---
        st.sidebar.subheader("Аналитика по вакансиям")
        menu = st.sidebar.radio(
            "Выберите график:",
            [
                "Самые популярные профессии по регионам",
                "Влияние опыта на зарплату в разрезе образования",
                "3D-визуализация: Опыт, Образование, Зарплата",
                "Топ-20 регионов по количеству вакансий",
                "Средняя зарплата по регионам",
                'Карта вакансий по Казахстану',
                "Требования к уровню образования",
                "Средняя зарплата по уровню образования",
                "Распределение зарплат по графику работы",
                "Топ-10 компаний по количеству вакансий",
                'Связь категории и опыта работы'
            ]
        )
        st.sidebar.divider()

        # --- Основная область для отображения ---
        st.header("Анализ данных по вакансиям")

        if menu == "Самые популярные профессии по регионам":
            st.subheader("Топ-5 самых востребованных профессий в разрезе регионов")
            
            trends_by_profession = df_vacancies.groupby(['Название работы', 'Фильтрованные регионы'])['Рабочих мест'].sum().reset_index(name='Количество вакансий')
            top_professions = trends_by_profession.sort_values(['Фильтрованные регионы', 'Количество вакансий'], ascending=[True, False]).groupby('Фильтрованные регионы').head(5)

            # Локальный фильтр над графиком
            selected_regions = st.multiselect(
                'Выберите регионы для отображения:',
                options=top_professions['Фильтрованные регионы'].unique(),
                default=top_professions['Фильтрованные регионы'].unique()
            )
            
            if selected_regions:
                filtered_data = top_professions[top_professions['Фильтрованные регионы'].isin(selected_regions)]
                fig_bar = px.bar(
                    filtered_data, x='Название работы', y='Количество вакансий', color='Фильтрованные регионы',
                    title='Топ-5 популярных профессий по выбранным регионам',
                    labels={'Количество вакансий': 'Количество вакансий', 'Название работы': 'Профессия'},
                    height=700
                )
                fig_bar.update_layout(xaxis_title="Профессия", yaxis_title="Количество вакансий")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")

        # ... (остальные `elif` для вакансий)
        # Я не буду переписывать каждый график, но покажу, как можно улучшить некоторые из них
        elif menu == "Топ-20 регионов по количеству вакансий":
            st.subheader("Топ-20 регионов по общему количеству открытых вакансий")
            jobs_by_city = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum().sort_values(ascending=False).head(20).reset_index()
            fig = px.bar(
                jobs_by_city, x='Фильтрованные регионы', y='Рабочих мест',
                title='Топ-20 регионов по количеству вакансий в 2024 году',
                labels={'Фильтрованные регионы': 'Регион', 'Рабочих мест': 'Количество вакансий'},
                text_auto=True, color='Фильтрованные регионы', color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig.update_layout(height=700, xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == 'Карта вакансий по Казахстану':
            # Этот код оставляем как есть, он уже хорошо структурирован
            st.subheader("Интерактивная карта вакансий и средней зарплаты по Казахстану")
            # ... (ваш код для карты folium)
            df_vacancies["Средняя зарплата с учетом рабочих мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
            weighted_avg_salary = df_vacancies.groupby("Фильтрованные регионы").apply(
                lambda x: x["Средняя зарплата с учетом рабочих мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0
            )
            city_coords = { 'Область Абай': {'lat': 48.9434, 'lon': 80.1390}, 'Алматинская область': {'lat': 43.9368, 'lon': 76.8260}, 'Алматы': {'lat': 43.2380, 'lon': 76.8829}, 'Астана': {'lat': 51.169, 'lon': 71.449}, 'Атырауская область': {'lat': 47.9053, 'lon': 51.3781}, 'Акмолинская область': {'lat': 51.9165, 'lon': 69.4110}, 'Актюбинская область': {'lat': 48.7797, 'lon': 57.9974}, 'Западно-Казахстанская область': {'lat': 49.5568, 'lon': 50.2227}, 'Жамбылская область': {'lat': 44.4168, 'lon': 72.1341}, 'Область Жетісу': {'lat': 45.00, 'lon': 78.00}, 'Мангистауская область': {'lat': 44.5908, 'lon': 53.8500}, 'Павлодарская область': {'lat': 52.6509, 'lon': 76.7773}, 'Северо-Казахстанская область': {'lat': 53.9797, 'lon': 69.045}, 'Туркестанская область': {'lat': 42.2663, 'lon': 68.1431}, 'Шымкент': {'lat': 42.3205, 'lon': 69.5876}, 'Восточно-Казахстанская область': {'lat': 48.6130, 'lon': 84.71032}, 'Карагандинская область': {'lat': 48.1671, 'lon': 73.4729}, 'Костанайская область': {'lat': 52.0615, 'lon': 62.9372}, 'Кызылординская область': {'lat': 45.2058, 'lon': 63.9155}, 'Область Ұлытау': {'lat': 48.00, 'lon': 66.59}}
            jobs_by_city = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum()
            top_cities = jobs_by_city.sort_values(ascending=False).head(20).reset_index()
            max_jobs = top_cities["Рабочих мест"].max()
            min_jobs = top_cities["Рабочих мест"].min()
            colormap = branca.colormap.linear.YlOrRd_09.scale(min_jobs, max_jobs)
            colormap.caption = 'Количество вакансий'
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
                    folium.CircleMarker(location=[coords['lat'], coords['lon']], radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7, tooltip=f"<strong>{region}</strong><br>Вакансий: {int(jobs)}<br>Ср. зарплата: {int(avg_salary)} KZT").add_to(marker_cluster)
            HeatMap(heat_data, radius=20, max_zoom=13).add_to(m)
            colormap.add_to(m)
            st_folium(m, use_container_width=True)
            
# --- БЛОК 2: АНАЛИЗ РЕЗЮМЕ ---
elif analysis_type == "Анализ резюме":
    df_resumes_raw = load_data("resumes_enbekkz.csv")
    
    if df_resumes_raw is not None:
        # Переименовываем колонку для консистентности
        df_resumes = df_resumes_raw.rename(columns={"City/Region": "Region"})

        # --- Меню для выбора графика резюме ---
        st.sidebar.subheader("Аналитика по резюме")
        chart_type = st.sidebar.radio(
            "Выберите график:",
            [
                "Топ-20 регионов по количеству резюме",
                "Самые популярные профессии",
                "Зависимость зарплаты от опыта",
                "Распределение по уровню образования",
                "Статистика зарплат по регионам",
                "Распределение зарплат по условиям работы",
                "Распределение зарплат по полу"
            ]
        )
        st.sidebar.divider()

        # --- ГЛОБАЛЬНЫЙ ФИЛЬТР ПО РЕГИОНАМ (теперь он всегда на виду) ---
        st.sidebar.subheader("Фильтры")
        all_regions = df_resumes['Region'].dropna().unique()
        region_selection = st.sidebar.multiselect(
            "Выберите регионы:",
            options=all_regions,
            default=list(all_regions)
        )
        
        # Применяем фильтр
        if region_selection:
            filtered_df = df_resumes[df_resumes['Region'].isin(region_selection)]
        else:
            filtered_df = df_resumes
            st.sidebar.warning("Не выбрано ни одного региона. Отображаются данные по всей стране.")

        # --- Основная область для отображения ---
        st.header("Анализ данных по резюме")
        
        if chart_type == "Топ-20 регионов по количеству резюме":
            st.subheader("Топ-20 регионов по количеству размещенных резюме")
            st.markdown(f"**Выбранные регионы:** {', '.join(region_selection) if region_selection else 'Все'}")
            
            region_counts = filtered_df['Region'].value_counts().head(20)
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.barplot(x=region_counts.values, y=region_counts.index, ax=ax, palette="crest")
            ax.set_title("Количество резюме по регионам", fontsize=16)
            ax.set_xlabel("Количество резюме", fontsize=12)
            ax.set_ylabel("Регион", fontsize=12)
            ax.bar_label(ax.containers[0])
            plt.tight_layout()
            st.pyplot(fig)
        
        elif chart_type == "Самые популярные профессии":
            st.subheader("Топ-10 самых популярных профессий среди соискателей")
            st.markdown(f"**Выбранные регионы:** {', '.join(region_selection) if region_selection else 'Все'}")
            
            top_jobs = filtered_df['Category'].value_counts().head(10)
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.barplot(x=top_jobs.values, y=top_jobs.index, ax=ax, palette="magma")
            ax.set_title("Топ-10 профессий в выбранных регионах", fontsize=16)
            ax.set_xlabel("Количество резюме", fontsize=12)
            ax.set_ylabel("Категория профессии", fontsize=12)
            ax.bar_label(ax.containers[0])
            plt.tight_layout()
            st.pyplot(fig)
            
        elif chart_type == "Зависимость зарплаты от опыта":
            st.subheader("Зависимость ожидаемой зарплаты от опыта работы")
            st.markdown(f"**Выбранные регионы:** {', '.join(region_selection) if region_selection else 'Все'}")

            fig = px.scatter(
                filtered_df.dropna(subset=['Salary', 'Work experience (year)']),
                x="Work experience (year)",
                y="Salary",
                color="Region",
                title="Ожидаемая зарплата vs. Опыт работы",
                labels={"Work experience (year)": "Опыт работы (лет)", "Salary": "Ожидаемая зарплата (KZT)"},
                hover_name="Category"
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Распределение зарплат по полу":
            st.subheader("Распределение ожидаемых зарплат по полу")
            st.markdown(f"**Выбранные регионы:** {', '.join(region_selection) if region_selection else 'Все'}")

            fig = px.box(
                filtered_df.dropna(subset=['Salary', 'Sex']),
                x="Sex",
                y="Salary",
                color="Sex",
                title="Распределение зарплат по полу",
                labels={"Sex": "Пол", "Salary": "Ожидаемая зарплата (KZT)"}
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

# Обработка случая, когда данные не загрузились
else:
    if analysis_type == "Анализ вакансий" and df_vacancies is None:
        st.error("Не удалось загрузить данные по вакансиям. Проверьте наличие файла 'main_cleaned_vacancies.csv'.")
    elif analysis_type == "Анализ резюме" and df_resumes_raw is None:
        st.error("Не удалось загрузить данные по резюме. Проверьте наличие файла 'resumes_enbekkz.csv'.")