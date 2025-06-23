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
from collections import Counter # Для подсчета навыков

# --- Конфигурация страницы ---
st.set_page_config(layout="wide", page_title="Анализ рынка труда Казахстана", page_icon="🇰🇿")

# --- Надежная загрузка данных ---
@st.cache_data
def load_data(file_name):
    """Универсальная функция для загрузки CSV-файлов."""
    try:
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Произошла ошибка при чтении файла {file_name}: {e}")
        return None

# --- Стилизация ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stApp {
        /* background-color: #f8f9fa; */ /* Пример фона */
    }
    h1, h2, h3 {
        /* color: #2c3e50; */ /* Пример цвета заголовков */
    }
</style>
""", unsafe_allow_html=True)


# --- Основная часть приложения ---
st.title("🇰🇿 Анализ рынка труда Казахстана")
st.caption("Интерактивный дашборд для исследования вакансий и резюме с портала enbek.kz")
st.divider()

# --- Боковая панель (Sidebar) ТОЛЬКО для навигации по разделам ---
# st.sidebar.image("https://enbek.kz/img/logo.29202521.svg", width=150) # Раскомментируйте, если есть лого
st.sidebar.title("🧭 Меню навигации")
analysis_type = st.sidebar.radio(
    "Выберите раздел для анализа:",
    ("📊 Анализ вакансий", "📄 Анализ резюме"),
    key="main_analysis_type_selector"
)
st.sidebar.divider()
st.sidebar.info("Дашборд предназначен для демонстрации возможностей анализа данных о рынке труда.")


# --- БЛОК 1: АНАЛИЗ ВАКАНСИЙ ---
if analysis_type == "📊 Анализ вакансий":
    st.header("📊 Анализ данных по вакансиям")
    df_vacancies = load_data("main_cleaned_vacancies.csv")

    if df_vacancies is None:
        st.error("Не удалось загрузить данные по вакансиям. Убедитесь, что файл 'main_cleaned_vacancies.csv' находится в корневой папке вашего проекта.")
    else:
        st.sidebar.subheader("Доступные графики:")
        menu_vacancies = st.sidebar.selectbox(
            "Выберите визуализацию для вакансий:",
            [
                "Самые популярные профессии по регионам",
                "Влияние опыта на зарплату",
                "3D-визуализация: Опыт, Образование, Зарплата",
                "Топ-20 регионов по количеству вакансий",
                "Средняя зарплата по регионам",
                'Карта вакансий по Казахстану',
                "Требования к уровню образования",
                "Средняя зарплата по уровню образования",
                "Распределение зарплат по графику работы",
                "Топ-10 компаний по количеству вакансий",
                'Связь категории и опыта работы'
            ],
            key="vacancy_chart_selector"
        )
        st.sidebar.divider()

        with st.container():
            st.subheader(f"🔍 {menu_vacancies}")
            st.markdown("---") # Используем markdown для более тонкого разделителя

            # Предобработка для некоторых графиков вакансий
            salary_by_education_experience = df_vacancies.groupby(['Образование', 'Опыт работы', 'Категория']).apply(
                lambda x: pd.Series({
                    'Средняя зарплата': (x['Средняя зарплата'] * x['Рабочих мест']).sum() / x['Рабочих мест'].sum() if x['Рабочих мест'].sum() > 0 else 0,
                    'Общее количество рабочих мест': x['Рабочих мест'].sum()
                })
            ).reset_index()
            salary_by_education_experience['Средняя зарплата'] = salary_by_education_experience['Средняя зарплата'].astype(int)

            if menu_vacancies == "Самые популярные профессии по регионам":
                trends_by_profession = df_vacancies.groupby(['Название работы', 'Фильтрованные регионы'])['Рабочих мест'].sum().reset_index(name='Количество вакансий')
                top_professions = trends_by_profession.sort_values(['Фильтрованные регионы', 'Количество вакансий'], ascending=[True, False]).groupby('Фильтрованные регионы').head(5)
                
                with st.expander("⚙️ Фильтры для графика", expanded=True):
                    selected_regions_vac = st.multiselect(
                        'Выберите регионы:', options=top_professions['Фильтрованные регионы'].unique(), default=top_professions['Фильтрованные регионы'].unique(), key="vac_pop_prof_region_filter"
                    )
                if selected_regions_vac:
                    filtered_data_vac = top_professions[top_professions['Фильтрованные регионы'].isin(selected_regions_vac)]
                    fig = px.bar(filtered_data_vac, x='Название работы', y='Количество вакансий', color='Фильтрованные регионы', title='Топ-5 популярных профессий по выбранным регионам', labels={'Количество вакансий': 'Кол-во вакансий', 'Название работы': 'Профессия'}, height=700, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Пожалуйста, выберите хотя бы один регион.")

            elif menu_vacancies == "Влияние опыта на зарплату":
                fig = px.line(salary_by_education_experience, x='Опыт работы', y='Средняя зарплата', color='Образование', title='Зависимость средней зарплаты от опыта и образования', labels={'Опыт работы': 'Опыт работы (лет)', 'Средняя зарплата': 'Средняя зарплата (KZT)', 'Образование': 'Уровень образования'}, markers=True, height=700)
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == "3D-визуализация: Опыт, Образование, Зарплата":
                with st.expander("⚙️ Фильтры для 3D-графика", expanded=True):
                    unique_categories_vac = df_vacancies['Категория'].unique()
                    selected_categories_vac = st.multiselect('Выберите категории:', options=unique_categories_vac, default=unique_categories_vac, key="vac_3d_cat_filter")
                if selected_categories_vac:
                    filtered_df_vac_3d = df_vacancies[df_vacancies['Категория'].isin(selected_categories_vac)]
                    fig_3d = px.scatter_3d(filtered_df_vac_3d, x='Опыт работы', y='Образование', z='Средняя зарплата', color='Категория', title='3D Scatter Plot', hover_name='Категория', height=800, labels={'Опыт работы': 'Опыт', 'Образование': 'Образование', 'Средняя зарплата': 'Ср. Зарплата'})
                    st.plotly_chart(fig_3d, use_container_width=True)
                else:
                    st.warning("Пожалуйста, выберите хотя бы одну категорию.")

            elif menu_vacancies == "Топ-20 регионов по количеству вакансий":
                jobs_by_city_vac = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum().sort_values(ascending=False).head(20).reset_index()
                fig = px.bar(jobs_by_city_vac, x='Фильтрованные регионы', y='Рабочих мест', title='Топ-20 регионов по количеству вакансий', labels={'Фильтрованные регионы': 'Регион', 'Рабочих мест': 'Количество вакансий'}, text_auto=True, color='Фильтрованные регионы', color_discrete_sequence=px.colors.qualitative.Vivid, height=700)
                fig.update_layout(xaxis_tickangle=-45, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == "Средняя зарплата по регионам":
                df_vacancies["ЗП_с_учетом_мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
                weighted_avg_salary_vac = df_vacancies.groupby("Фильтрованные регионы").apply(lambda x: x["ЗП_с_учетом_мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0).sort_values(ascending=False).astype(int).reset_index(name="Средняя зарплата")
                fig = px.bar(weighted_avg_salary_vac, x='Фильтрованные регионы', y='Средняя зарплата', title='Средняя зарплата по регионам (вакансии)', labels={'Фильтрованные регионы': 'Регион', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, text_auto=True, color='Фильтрованные регионы', color_discrete_sequence=px.colors.qualitative.Bold, height=700)
                fig.update_layout(xaxis_tickangle=-45, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == 'Карта вакансий по Казахстану':
                df_vacancies_map = df_vacancies.copy()
                df_vacancies_map["Средняя зарплата с учетом рабочих мест"] = df_vacancies_map["Средняя зарплата"] * df_vacancies_map["Рабочих мест"]
                weighted_avg_salary_map = df_vacancies_map.groupby("Фильтрованные регионы").apply(
                    lambda x: x["Средняя зарплата с учетом рабочих мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0
                )
                city_coords = { 'Область Абай': {'lat': 48.9434, 'lon': 80.1390}, 'Алматинская область': {'lat': 43.9368, 'lon': 76.8260}, 'Алматы': {'lat': 43.2380, 'lon': 76.8829}, 'Астана': {'lat': 51.169, 'lon': 71.449}, 'Атырауская область': {'lat': 47.9053, 'lon': 51.3781}, 'Акмолинская область': {'lat': 51.9165, 'lon': 69.4110}, 'Актюбинская область': {'lat': 48.7797, 'lon': 57.9974}, 'Западно-Казахстанская область': {'lat': 49.5568, 'lon': 50.2227}, 'Жамбылская область': {'lat': 44.4168, 'lon': 72.1341}, 'Область Жетісу': {'lat': 45.00, 'lon': 78.00}, 'Мангистауская область': {'lat': 44.5908, 'lon': 53.8500}, 'Павлодарская область': {'lat': 52.6509, 'lon': 76.7773}, 'Северо-Казахстанская область': {'lat': 53.9797, 'lon': 69.045}, 'Туркестанская область': {'lat': 42.2663, 'lon': 68.1431}, 'Шымкент': {'lat': 42.3205, 'lon': 69.5876}, 'Восточно-Казахстанская область': {'lat': 48.6130, 'lon': 84.71032}, 'Карагандинская область': {'lat': 48.1671, 'lon': 73.4729}, 'Костанайская область': {'lat': 52.0615, 'lon': 62.9372}, 'Кызылординская область': {'lat': 45.2058, 'lon': 63.9155}, 'Область Ұлытау': {'lat': 48.00, 'lon': 66.59}}
                jobs_by_city_map = df_vacancies_map.groupby("Фильтрованные регионы")["Рабочих мест"].sum()
                top_cities_map = jobs_by_city_map.sort_values(ascending=False).head(20).reset_index()
                max_jobs_map = top_cities_map["Рабочих мест"].max() if not top_cities_map.empty else 0
                min_jobs_map = top_cities_map["Рабочих мест"].min() if not top_cities_map.empty else 0
                
                colormap = branca.colormap.linear.YlOrRd_09.scale(min_jobs_map, max_jobs_map) if min_jobs_map < max_jobs_map else branca.colormap.linear.YlOrRd_09.scale(0,1) # Защита от одинаковых min/max
                colormap.caption = 'Количество вакансий'
                m = folium.Map(location=[48.0196, 66.9237], zoom_start=5, tiles="cartodb positron")
                marker_cluster = MarkerCluster().add_to(m)
                heat_data = []
                for _, row in top_cities_map.iterrows():
                    region, jobs = row['Фильтрованные регионы'], row['Рабочих мест']
                    if region in city_coords:
                        coords = city_coords[region]
                        color = colormap(jobs) if min_jobs_map < max_jobs_map else colormap(0)
                        avg_salary = weighted_avg_salary_map.get(region, 0)
                        heat_data.append([coords['lat'], coords['lon'], jobs])
                        radius = 8 + (jobs / max_jobs_map) * 12 if max_jobs_map > 0 else 8
                        folium.CircleMarker(location=[coords['lat'], coords['lon']], radius=radius, color=color, fill=True, fill_color=color, fill_opacity=0.7, tooltip=f"<strong>{region}</strong><br>Вакансий: {int(jobs)}<br>Ср. зарплата: {int(avg_salary)} KZT").add_to(marker_cluster)
                if heat_data:
                    HeatMap(heat_data, radius=20, max_zoom=13).add_to(m)
                colormap.add_to(m)
                st_folium(m, use_container_width=True, height=600)

            elif menu_vacancies == "Требования к уровню образования":
                education_counts_vac = df_vacancies["Образование"].value_counts()
                fig = px.pie(education_counts_vac, values=education_counts_vac.values, names=education_counts_vac.index, title="Доля вакансий по требуемому уровню образования", hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == "Средняя зарплата по уровню образования":
                df_vacancies["ЗП_с_учетом_мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
                avg_salary_by_edu_vac = df_vacancies.groupby("Образование").apply(lambda x: x["ЗП_с_учетом_мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0).sort_values(ascending=False).astype(int).reset_index(name="Средняя зарплата")
                fig = px.bar(avg_salary_by_edu_vac, x='Образование', y='Средняя зарплата', title='Средняя зарплата по уровню образования (вакансии)', labels={'Образование': 'Уровень образования', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, text_auto=True, height=600, color='Образование')
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == "Распределение зарплат по графику работы":
                fig = px.box(df_vacancies, x='График работы', y='Средняя зарплата', color='График работы', title="Распределение зарплат по графику работы (вакансии)", labels={'График работы': 'График работы', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, height=600, points="outliers")
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == 'Топ-10 компаний по количеству вакансий':
                top_companies_vac = df_vacancies.groupby("Название компаний")["Рабочих мест"].sum().nlargest(10).sort_values(ascending=True)
                fig = px.bar(top_companies_vac, x=top_companies_vac.values, y=top_companies_vac.index, orientation='h', labels={'y': 'Компания', 'x': 'Общее количество вакансий'}, title='Топ-10 компаний по количеству вакансий', text_auto=True, height=600, color=top_companies_vac.index, color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(yaxis_title="Название компании", showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            elif menu_vacancies == 'Связь категории и опыта работы':
                pivot_table_vac = pd.crosstab(index=df_vacancies['Категория'], columns=df_vacancies['Опыт работы'])
                fig = px.imshow(pivot_table_vac, text_auto=True, aspect="auto", labels=dict(x="Опыт работы (лет)", y="Категория", color="Количество вакансий"), title="Количество вакансий по категориям и опыту", height=800, color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)


# --- БЛОК 2: АНАЛИЗ РЕЗЮМЕ ---
elif analysis_type == "📄 Анализ резюме":
    st.header("📄 Анализ данных по резюме")
    df_resumes_raw = load_data("resumes_enbekkz.csv")
    
    if df_resumes_raw is None:
        st.error("Не удалось загрузить данные по резюме. Убедитесь, что файл 'resumes_enbekkz.csv' находится в корневой папке вашего проекта.")
    else:
        df_resumes = df_resumes_raw.rename(columns={
            "City/Region": "Region", 
            "Work experience (year)": "ExperienceYears",
            "education_level_target": "Education",
            "employment_type": "EmploymentType",
            "work_format": "WorkFormat",
            "Gender": "Sex" 
        })
        # Проверка и исправление имени колонки для пола, если необходимо
        if 'Sex' not in df_resumes.columns and 'Gender' in df_resumes_raw.columns: pass
        elif 'Gender' not in df_resumes.columns and 'Sex' in df_resumes_raw.columns:
            df_resumes = df_resumes_raw.rename(columns={"City/Region": "Region", "Work experience (year)": "ExperienceYears", "education_level_target": "Education", "employment_type": "EmploymentType", "work_format": "WorkFormat"})

        st.sidebar.subheader("Доступные графики:")
        chart_type_resume = st.sidebar.selectbox(
            "Выберите визуализацию для резюме:",
            [
                "Обзор регионов по количеству резюме",
                "Топ-10 профессий (категорий)",
                "Распределение категорий по полу",
                "Облако популярных навыков",
                "Топ-5 навыков по регионам",
                "Зарплата vs. Опыт работы (детально)",
                "Зарплата vs. Возраст",
                "Зарплата vs. Образование",
                "Зарплата vs. Количество языков",
                "Распределение по типу занятости и формату работы",
            ],
            key="resume_chart_selector"
        )
        st.sidebar.divider()

        with st.expander("⚙️ Настроить фильтры для анализа резюме", expanded=True):
            col_filter1, col_filter2 = st.columns(2)
            with col_filter1:
                all_regions_resume = sorted(df_resumes['Region'].dropna().unique())
                region_selection_resume = st.multiselect(
                    "Выберите регионы:", options=all_regions_resume, default=list(all_regions_resume), key="resume_page_region_filter"
                )
            with col_filter2:
                gender_options_resume = ['Все'] + sorted(df_resumes['Sex'].dropna().unique().tolist())
                selected_gender_resume = st.selectbox(
                    "Выберите пол:", options=gender_options_resume, index=0, key="resume_page_gender_filter"
                )

        filtered_df_global = df_resumes.copy()
        if region_selection_resume:
            filtered_df_global = filtered_df_global[filtered_df_global['Region'].isin(region_selection_resume)]
        
        if selected_gender_resume != 'Все':
            filtered_df_global = filtered_df_global[filtered_df_global['Sex'] == selected_gender_resume]
        
        with st.container():
            st.subheader(f"🔍 {chart_type_resume}")
            filter_info_resume = f"**Фильтры:** Регионы - {', '.join(region_selection_resume) if region_selection_resume else 'Все'}; Пол - {selected_gender_resume}."
            st.caption(filter_info_resume)
            st.markdown("---")

            if filtered_df_global.empty:
                st.warning("Нет данных для отображения с учетом выбранных фильтров. Попробуйте изменить фильтры.")
            else:
                if chart_type_resume == "Обзор регионов по количеству резюме":
                    region_counts_res = filtered_df_global['Region'].value_counts().reset_index()
                    region_counts_res.columns = ['Region', 'Count']
                    fig = px.bar(region_counts_res.head(20), x='Region', y='Count', title="Топ-20 регионов по количеству резюме", labels={'Region': 'Регион', 'Count': 'Количество резюме'}, text_auto=True, height=600, color='Region', color_discrete_sequence=px.colors.qualitative.T10)
                    fig.update_layout(xaxis_tickangle=-45, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type_resume == "Топ-10 профессий (категорий)":
                    top_jobs_res = filtered_df_global['Category'].value_counts().nlargest(10).reset_index()
                    top_jobs_res.columns = ['Category', 'Count']
                    fig = px.bar(top_jobs_res, y='Category', x='Count', orientation='h', title="Топ-10 категорий профессий", labels={'Category': 'Категория', 'Count': 'Количество резюме'}, text_auto=True, height=600, color='Category', color_discrete_sequence=px.colors.qualitative.Antique)
                    fig.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)

                elif chart_type_resume == "Распределение категорий по полу":
                    top_categories_res = filtered_df_global['Category'].value_counts().nlargest(5).index.tolist()
                    df_top_cat_gender_res = filtered_df_global[filtered_df_global['Category'].isin(top_categories_res)]
                    
                    if selected_gender_resume != 'Все':
                        category_counts_res = df_top_cat_gender_res['Category'].value_counts().reset_index()
                        category_counts_res.columns = ['Category', 'Count']
                        fig_title_res = f"Топ-5 категорий для пола: {selected_gender_resume}"
                        fig = px.bar(category_counts_res, x='Category', y='Count', color='Category', title=fig_title_res, labels={'Category': 'Категория', 'Count': 'Количество резюме'}, height=600)
                    else:
                        category_gender_counts_res = df_top_cat_gender_res.groupby(['Category', 'Sex']).size().reset_index(name='Count')
                        fig = px.bar(category_gender_counts_res, x='Category', y='Count', color='Sex', barmode='group', title="Распределение топ-5 категорий по полу", labels={'Category': 'Категория', 'Count': 'Количество резюме', 'Sex': 'Пол'}, height=600, color_discrete_map={'Мужской': px.colors.qualitative.Plotly[0], 'Женский': px.colors.qualitative.Plotly[1]})
                    st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type_resume == "Облако популярных навыков":
                    all_skills_text_res = []
                    for skills_entry in filtered_df_global['Skills'].dropna():
                        if isinstance(skills_entry, str):
                             all_skills_text_res.append(skills_entry)
                    text_res = " ".join(all_skills_text_res).replace(',', ' ').replace(';', ' ')

                    if text_res.strip():
                        try:
                            from wordcloud import WordCloud
                            wordcloud_res = WordCloud(width=1200, height=600, background_color='#ffffff', collocations=False, colormap="viridis").generate(text_res)
                            fig_wc_res, ax_wc_res = plt.subplots(figsize=(15, 7))
                            ax_wc_res.imshow(wordcloud_res, interpolation='bilinear')
                            ax_wc_res.axis("off")
                            plt.tight_layout()
                            st.pyplot(fig_wc_res)
                        except ImportError:
                            st.error("Библиотека 'wordcloud' не установлена. Пожалуйста, добавьте ее в requirements.txt.")
                        except Exception as e_wc:
                            st.error(f"Ошибка при генерации облака слов: {e_wc}")
                    else:
                        st.info("Нет данных по навыкам для генерации облака слов с учетом фильтров.")
            
                elif chart_type_resume == "Топ-5 навыков по регионам":
                    if region_selection_resume:
                        skills_data_res = []
                        for region_res in region_selection_resume:
                            region_df_res = filtered_df_global[filtered_df_global['Region'] == region_res]
                            skills_list_res = []
                            for s_res in region_df_res['Skills'].dropna().astype(str):
                                skills_list_res.extend([skill.strip().lower() for skill in s_res.replace(';',',').split(',') if skill.strip() and len(skill.strip()) > 1]) # Игнорируем слишком короткие "навыки"
                            
                            if skills_list_res:
                                top_5_skills_res = Counter(skills_list_res).most_common(5)
                                for skill_res, count_res in top_5_skills_res:
                                    skills_data_res.append({'Region': region_res, 'Skill': skill_res, 'Count': count_res})
                        
                        if skills_data_res:
                            df_skills_plot_res = pd.DataFrame(skills_data_res)
                            num_cols_facet = min(3, len(region_selection_resume))
                            num_rows_facet = (len(region_selection_resume) - 1) // num_cols_facet + 1
                            fig_height = 300 * num_rows_facet
                            
                            fig = px.bar(df_skills_plot_res, x='Skill', y='Count', color='Skill',
                                         facet_col='Region', facet_col_wrap=num_cols_facet,
                                         title="Топ-5 навыков по выбранным регионам",
                                         labels={'Skill': 'Навык', 'Count': 'Частота упоминания'},
                                         height=max(400, fig_height) # Минимальная высота
                                        )
                            fig.update_xaxes(matches=None, tickangle=-45)
                            fig.update_yaxes(matches=None, title_text="") # Убираем подпись Y для каждого фасета
                            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1])) # Очищаем заголовки фасетов
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("Не удалось извлечь навыки для выбранных регионов с учетом фильтров.")
                    else:
                        st.warning("Выберите хотя бы один регион в фильтрах для отображения топ навыков.")

                elif chart_type_resume == "Зарплата vs. Опыт работы (детально)":
                    df_plot_res = filtered_df_global.dropna(subset=['Salary', 'ExperienceYears'])
                    df_plot_res = df_plot_res[(df_plot_res['Salary'] > 10000) & (df_plot_res['Salary'] < 3000000)]

                    if not df_plot_res.empty:
                        col1_res, col2_res = st.columns(2)
                        with col1_res:
                            fig_scatter_res = px.scatter(df_plot_res, x="ExperienceYears", y="Salary", 
                                                     color="experience_level", 
                                                     trendline="ols", trendline_scope="overall",
                                                     title="Зарплата vs. Опыт (точечный)", 
                                                     labels={"ExperienceYears": "Опыт (лет)", "Salary": "Зарплата (KZT)", "experience_level": "Уровень опыта"},
                                                     hover_data=['Category', 'Region'], height=600)
                            st.plotly_chart(fig_scatter_res, use_container_width=True)
                        with col2_res:
                            fig_box_res = px.box(df_plot_res, x="experience_level", y="Salary", color="experience_level",
                                             title="Распределение зарплат по уровню опыта",
                                             labels={"experience_level": "Уровень опыта", "Salary": "Зарплата (KZT)"},
                                             height=600, points="all") # 'all' или 'outliers'
                            st.plotly_chart(fig_box_res, use_container_width=True)
                    else:
                        st.info("Нет данных для графика 'Зарплата vs. Опыт' с учетом фильтров.")
            
                elif chart_type_resume == "Зарплата vs. Возраст":
                    df_plot_res_age = filtered_df_global.dropna(subset=['Salary', 'Age'])
                    df_plot_res_age = df_plot_res_age[(df_plot_res_age['Salary'] > 10000) & (df_plot_res_age['Salary'] < 3000000) & (df_plot_res_age['Age'] > 16) & (df_plot_res_age['Age'] < 70)]
                    
                    if not df_plot_res_age.empty:
                        bins_age = [16, 25, 35, 45, 55, 70]
                        labels_age = ['16-24 года', '25-34 года', '35-44 года', '45-54 года', '55-69 лет']
                        df_plot_res_age['AgeGroup'] = pd.cut(df_plot_res_age['Age'], bins=bins_age, labels=labels_age, right=False)
                        fig = px.box(df_plot_res_age.sort_values('AgeGroup'), x="AgeGroup", y="Salary", color="AgeGroup", title="Распределение зарплат по возрастным группам", labels={"AgeGroup": "Возрастная группа", "Salary": "Зарплата (KZT)"}, height=600)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Нет данных для графика 'Зарплата vs. Возраст' с учетом фильтров.")

                elif chart_type_resume == "Зарплата vs. Образование":
                    df_plot_res_edu = filtered_df_global.dropna(subset=['Salary', 'Education'])
                    df_plot_res_edu = df_plot_res_edu[(df_plot_res_edu['Salary'] > 10000) & (df_plot_res_edu['Salary'] < 3000000)]
                    
                    if not df_plot_res_edu.empty:
                        # Попробуем упорядочить уровни образования для лучшей визуализации
                        # education_order = ['Среднее', 'Среднее специальное', 'Неоконченное высшее', 'Высшее', 'Бакалавр', 'Магистр', 'Ученая степень'] 
                        # df_plot_res_edu['Education'] = pd.Categorical(df_plot_res_edu['Education'], categories=education_order, ordered=True)
                        # df_plot_res_edu = df_plot_res_edu.sort_values('Education') # Если задан порядок

                        fig = px.box(df_plot_res_edu, x="Education", y="Salary", color="Education", title="Распределение зарплат по уровню образования", labels={"Education": "Уровень образования", "Salary": "Зарплата (KZT)"}, height=700)
                        fig.update_layout(xaxis_tickangle=-30) # Небольшой наклон для длинных названий
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Нет данных для графика 'Зарплата vs. Образование' с учетом фильтров.")

                elif chart_type_resume == "Зарплата vs. Количество языков":
                    df_plot_res_lang = filtered_df_global.dropna(subset=['Salary', 'n_languages', 'polyglot_level'])
                    df_plot_res_lang = df_plot_res_lang[(df_plot_res_lang['Salary'] > 10000) & (df_plot_res_lang['Salary'] < 3000000)]
                    
                    if not df_plot_res_lang.empty:
                        df_plot_res_lang['n_languages_str'] = df_plot_res_lang['n_languages'].astype(str) + " язык(а/ов)"
                        fig = px.box(df_plot_res_lang.sort_values('n_languages'), x="n_languages_str", y="Salary", color="polyglot_level", title="Зарплата в зависимости от количества языков и уровня владения", labels={"n_languages_str": "Количество языков", "Salary": "Зарплата (KZT)", "polyglot_level": "Уровень полиглота"}, height=600)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Нет данных для графика 'Зарплата vs. Количество языков' с учетом фильтров.")

                elif chart_type_resume == "Распределение по типу занятости и формату работы":
                    if not filtered_df_global.empty:
                        col1_res_emp, col2_res_emp = st.columns(2)
                        with col1_res_emp:
                            emp_type_counts_res = filtered_df_global['EmploymentType'].value_counts().reset_index()
                            emp_type_counts_res.columns = ['EmploymentType', 'Count']
                            fig1_res = px.pie(emp_type_counts_res, values='Count', names='EmploymentType', title='Распределение по типу занятости', hole=0.4, color_discrete_sequence=px.colors.
                            sequential.Agsunset)
                            fig1_res.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig1_res, use_container_width=True)
                        with col2_res_emp:
                            work_format_counts_res = filtered_df_global['WorkFormat'].value_counts().reset_index()
                            work_format_counts_res.columns = ['WorkFormat', 'Count']
                            fig2_res = px.pie(work_format_counts_res, values='Count', names='WorkFormat', title='Распределение по формату работы', hole=0.4, color_discrete_sequence=px.colors.sequential.Bluyl)
                            fig2_res.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig2_res, use_container_width=True)
                    else:
                        st.info("Нет данных для графиков 'Распределение по типу занятости и формату работы' с учетом фильтров.")