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

# --- Надежная загрузка данных ---
@st.cache_data
def load_data(file_name):
    """Универсальная функция для загрузки CSV-файлов."""
    try:
        # Проверяем, существует ли файл, перед чтением
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            return df
        else:
            return None
    except Exception as e:
        st.error(f"Произошла ошибка при чтении файла {file_name}: {e}")
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

    # Проверяем, загрузились ли данные
    if df_vacancies is None:
        st.error("Не удалось загрузить данные по вакансиям. Убедитесь, что файл 'main_cleaned_vacancies.csv' находится в корневой папке вашего проекта.")
    else:
        # --- Меню для выбора графика вакансий ---
        st.sidebar.subheader("Аналитика по вакансиям")
        menu = st.sidebar.radio(
            "Выберите график:",
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
            ]
        )
        st.sidebar.divider()

        # --- Основная область для отображения ---
        st.header("Анализ данных по вакансиям")

        # --- Предобработка данных (выполняется только при необходимости) ---
        salary_by_education_experience = df_vacancies.groupby(['Образование', 'Опыт работы', 'Категория']).apply(
            lambda x: pd.Series({
                'Средняя зарплата': (x['Средняя зарплата'] * x['Рабочих мест']).sum() / x['Рабочих мест'].sum() if x['Рабочих мест'].sum() > 0 else 0,
                'Общее количество рабочих мест': x['Рабочих мест'].sum()
            })
        ).reset_index()
        salary_by_education_experience['Средняя зарплата'] = salary_by_education_experience['Средняя зарплата'].astype(int)

        if menu == "Самые популярные профессии по регионам":
            st.subheader("Топ-5 самых востребованных профессий в разрезе регионов")
            trends_by_profession = df_vacancies.groupby(['Название работы', 'Фильтрованные регионы'])['Рабочих мест'].sum().reset_index(name='Количество вакансий')
            top_professions = trends_by_profession.sort_values(['Фильтрованные регионы', 'Количество вакансий'], ascending=[True, False]).groupby('Фильтрованные регионы').head(5)
            
            selected_regions = st.multiselect(
                'Выберите регионы для отображения:', options=top_professions['Фильтрованные регионы'].unique(), default=top_professions['Фильтрованные регионы'].unique()
            )
            if selected_regions:
                filtered_data = top_professions[top_professions['Фильтрованные регионы'].isin(selected_regions)]
                fig = px.bar(filtered_data, x='Название работы', y='Количество вакансий', color='Фильтрованные регионы', title='Топ-5 популярных профессий по выбранным регионам', labels={'Количество вакансий': 'Кол-во вакансий', 'Название работы': 'Профессия'}, height=700)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")

        elif menu == "Влияние опыта на зарплату":
            st.subheader("Влияние опыта работы на среднюю зарплату в разрезе образования")
            fig = px.line(salary_by_education_experience, x='Опыт работы', y='Средняя зарплата', color='Образование', title='Зависимость средней зарплаты от опыта и образования', labels={'Опыт работы': 'Опыт работы (лет)', 'Средняя зарплата': 'Средняя зарплата (KZT)', 'Образование': 'Уровень образования'}, markers=True, height=700)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "3D-визуализация: Опыт, Образование, Зарплата":
            st.subheader("3D-визуализация зависимости зарплаты от опыта и образования")
            unique_categories = df_vacancies['Категория'].unique()
            selected_categories = st.multiselect('Выберите категории:', options=unique_categories, default=unique_categories)
            if selected_categories:
                filtered_df = df_vacancies[df_vacancies['Категория'].isin(selected_categories)]
                fig_3d = px.scatter_3d(filtered_df, x='Опыт работы', y='Образование', z='Средняя зарплата', color='Категория', title='3D Scatter Plot', hover_name='Категория', height=800, labels={'Опыт работы': 'Опыт', 'Образование': 'Образование', 'Средняя зарплата': 'Ср. Зарплата'})
                st.plotly_chart(fig_3d, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы одну категорию.")

        elif menu == "Топ-20 регионов по количеству вакансий":
            st.subheader("Топ-20 регионов по общему количеству открытых вакансий")
            jobs_by_city = df_vacancies.groupby("Фильтрованные регионы")["Рабочих мест"].sum().sort_values(ascending=False).head(20).reset_index()
            fig = px.bar(jobs_by_city, x='Фильтрованные регионы', y='Рабочих мест', title='Топ-20 регионов по количеству вакансий', labels={'Фильтрованные регионы': 'Регион', 'Рабочих мест': 'Количество вакансий'}, text_auto=True, color='Фильтрованные регионы', color_discrete_sequence=px.colors.qualitative.Prism, height=700)
            fig.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "Средняя зарплата по регионам":
            st.subheader("Средняя зарплата по регионам Казахстана")
            df_vacancies["ЗП_с_учетом_мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
            weighted_avg_salary = df_vacancies.groupby("Фильтрованные регионы").apply(lambda x: x["ЗП_с_учетом_мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0).sort_values(ascending=False).astype(int).reset_index(name="Средняя зарплата")
            fig = px.bar(weighted_avg_salary, x='Фильтрованные регионы', y='Средняя зарплата', title='Средняя зарплата по регионам', labels={'Фильтрованные регионы': 'Регион', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, text_auto=True, color='Фильтрованные регионы', color_discrete_sequence=px.colors.qualitative.G10, height=700)
            fig.update_layout(xaxis_tickangle=-45, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == 'Карта вакансий по Казахстану':
            st.subheader("Интерактивная карта вакансий и средней зарплаты по Казахстану")
            # ... ваш код для карты folium, он уже хорош ...
            # Я только добавлю use_container_width=True для лучшего отображения
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

        elif menu == "Требования к уровню образования":
            st.subheader("Требования к уровню образования в вакансиях")
            education_counts = df_vacancies["Образование"].value_counts()
            fig = px.pie(education_counts, values=education_counts.values, names=education_counts.index, title="Доля вакансий по требуемому уровню образования", hole=0.3)
            fig.update_traces(textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "Средняя зарплата по уровню образования":
            st.subheader("Средняя зарплата в зависимости от уровня образования")
            df_vacancies["ЗП_с_учетом_мест"] = df_vacancies["Средняя зарплата"] * df_vacancies["Рабочих мест"]
            avg_salary_by_edu = df_vacancies.groupby("Образование").apply(lambda x: x["ЗП_с_учетом_мест"].sum() / x["Рабочих мест"].sum() if x["Рабочих мест"].sum() > 0 else 0).sort_values(ascending=False).astype(int).reset_index(name="Средняя зарплата")
            fig = px.bar(avg_salary_by_edu, x='Образование', y='Средняя зарплата', title='Средняя зарплата по уровню образования', labels={'Образование': 'Уровень образования', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, text_auto=True, height=600)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == "Распределение зарплат по графику работы":
            st.subheader("Распределение средних зарплат по графику работы")
            fig = px.box(df_vacancies, x='График работы', y='Средняя зарплата', color='График работы', title="Распределение зарплат по графику работы", labels={'График работы': 'График работы', 'Средняя зарплата': 'Средняя зарплата (KZT)'}, height=600)
            st.plotly_chart(fig, use_container_width=True)

        elif menu == 'Топ-10 компаний по количеству вакансий':
            st.subheader("Топ-10 компаний с наибольшим количеством вакансий")
            top_companies = df_vacancies.groupby("Название компаний")["Рабочих мест"].sum().nlargest(10).sort_values(ascending=True)
            fig = px.bar(top_companies, x=top_companies.values, y=top_companies.index, orientation='h', labels={'y': 'Компания', 'x': 'Общее количество вакансий'}, title='Топ-10 компаний по количеству вакансий', text_auto=True, height=600)
            fig.update_layout(yaxis_title="Название компании")
            st.plotly_chart(fig, use_container_width=True)

        elif menu == 'Связь категории и опыта работы':
            st.subheader("Тепловая карта: Связь между категорией вакансии и требуемым опытом")
            pivot_table = pd.crosstab(index=df_vacancies['Категория'], columns=df_vacancies['Опыт работы'])
            fig = px.imshow(pivot_table, text_auto=True, aspect="auto", labels=dict(x="Опыт работы (лет)", y="Категория", color="Количество вакансий"), title="Количество вакансий по категориям и опыту", height=800)
            st.plotly_chart(fig, use_container_width=True)


# --- БЛОК 2: АНАЛИЗ РЕЗЮМЕ ---
elif analysis_type == "Анализ резюме":
    df_resumes_raw = load_data("resumes_enbekkz.csv")
    
    if df_resumes_raw is None:
        st.error("Не удалось загрузить данные по резюме. Убедитесь, что файл 'resumes_enbekkz.csv' находится в корневой папке вашего проекта.")
    else:
        df_resumes = df_resumes_raw.rename(columns={"City/Region": "Region"}) # Используем переименованный df_resumes

        # --- Меню для выбора графика резюме (остается в боковой панели) ---
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

        # ГЛОБАЛЬНЫЙ ФИЛЬТР УДАЛЕН ИЗ БОКОВОЙ ПАНЕЛИ

        # --- Основная область для отображения ---
        st.header("Анализ данных по резюме")
        # Информационная строка о выбранных регионах удалена, так как фильтр будет локальным
        # st.markdown(f"**Выбранные регионы:** {', '.join(region_selection) if region_selection else 'Все'}")
        st.divider() # Оставляем разделитель для визуальной структуры
        
        # --- Отображение графиков резюме с ЛОКАЛЬНЫМИ ФИЛЬТРАМИ ---
        
        if chart_type == "Топ-20 регионов по количеству резюме":
            st.subheader("Топ-20 регионов по количеству размещенных резюме")
            
            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_top_regions_filter" # Уникальный ключ для каждого multiselect
            )
            
            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                region_counts = filtered_df_local['Region'].value_counts().head(20)
                fig = px.bar(region_counts, x=region_counts.index, y=region_counts.values, title="Количество резюме по регионам", labels={'x': 'Регион', 'y': 'Количество резюме'}, text_auto=True, height=600)
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")
        
        elif chart_type == "Самые популярные профессии":
            st.subheader("Топ-10 самых популярных профессий среди соискателей")

            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_top_professions_filter"
            )

            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                top_jobs = filtered_df_local['Category'].value_counts().head(10)
                fig = px.bar(top_jobs, y=top_jobs.index, x=top_jobs.values, orientation='h', title="Топ-10 профессий в выбранных регионах", labels={'y': 'Категория профессии', 'x': 'Количество резюме'}, text_auto=True, height=600)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")
            
        elif chart_type == "Зависимость зарплаты от опыта":
            st.subheader("Зависимость ожидаемой зарплаты от опыта работы")

            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_salary_experience_filter"
            )
            
            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                df_plot = filtered_df_local.dropna(subset=['Salary', 'Work experience (year)'])
                df_plot = df_plot[df_plot['Salary'] < 5000000] 
                fig = px.scatter(df_plot, x="Work experience (year)", y="Salary", color="Region", title="Ожидаемая зарплата vs. Опыт работы", labels={"Work experience (year)": "Опыт работы (лет)", "Salary": "Ожидаемая зарплата (KZT)"}, hover_name="Category", height=600)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")

        elif chart_type == "Распределение по уровню образования":
            st.subheader("Распределение соискателей по уровню образования")

            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_education_filter"
            )

            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                edu_counts = filtered_df_local['education_level_target'].value_counts()
                fig = px.pie(edu_counts, values=edu_counts.values, names=edu_counts.index, title="Распределение по уровню образования", hole=0.3)
                fig.update_traces(textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")
        
        elif chart_type == "Статистика зарплат по регионам":
            st.subheader("Статистика зарплат (среднее, медиана, мода) по регионам")

            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_salary_stats_filter"
            )
            
            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                grouped = filtered_df_local.groupby("Region")["Salary"].agg(["mean", "median", lambda x: x.mode().iloc[0] if not x.mode().empty else None]).rename(columns={'<lambda_0>': 'mode'})
                grouped = grouped.dropna().sort_values("mean", ascending=False).head(20)
                st.dataframe(grouped.style.format("{:,.0f} KZT"), use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")
            
        elif chart_type == "Распределение зарплат по условиям работы":
            st.subheader("Распределение ожидаемых зарплат по условиям работы")

            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_salary_conditions_filter"
            )
            
            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                df_plot = filtered_df_local.dropna(subset=['Salary', 'working conditions'])
                df_plot = df_plot[df_plot['Salary'] < 5000000]
                fig = px.box(df_plot, x="working conditions", y="Salary", color="working conditions", title="Распределение зарплат по условиям работы", labels={"working conditions": "Условия работы", "Salary": "Ожидаемая зарплата (KZT)"}, height=600)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")

        elif chart_type == "Распределение зарплат по полу":
            st.subheader("Распределение ожидаемых зарплат по полу")
            
            # Локальный фильтр по регионам
            all_regions_local = sorted(df_resumes['Region'].dropna().unique())
            region_selection_local = st.multiselect(
                "Выберите регионы для этого графика:", 
                options=all_regions_local, 
                default=list(all_regions_local),
                key="resume_salary_sex_filter" # Уникальный ключ
            )

            if region_selection_local:
                filtered_df_local = df_resumes[df_resumes['Region'].isin(region_selection_local)]
                df_plot = filtered_df_local.dropna(subset=['Salary', 'Sex'])
                df_plot = df_plot[df_plot['Salary'] < 5000000]
                fig = px.box(df_plot, x="Sex", y="Salary", color="Sex", title="Распределение зарплат по полу", labels={"Sex": "Пол", "Salary": "Ожидаемая зарплата (KZT)"}, height=600)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Пожалуйста, выберите хотя бы один регион.")