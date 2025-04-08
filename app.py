import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
@st.cache_data

def load_data():
    df = pd.read_csv("resumes_cleaned_en.csv")
    df = df.rename(columns={"Область": "Region"})
    return df

df = load_data()

# Sidebar
st.sidebar.title("Select a Chart")
chart_type = st.sidebar.radio("Chart:", [
    "Top 20 Regions by Number of Resumes",
    "Most Popular Professions by Region",
    "Salary vs. Work Experience",
    "Education Level Distribution",
    "Mean, Median, Mode Salaries by Region",
    "Salary Distribution by Work Conditions",
    "Salary Distribution by Sex"
])

all_regions = df['Region'].dropna().unique()
selected_regions = st.sidebar.multiselect("Select Regions", all_regions, default=list(all_regions))
filtered_df = df[df['Region'].isin(selected_regions)]

# Title
st.title("Resume Data Dashboard")

# Chart 1: Top 20 Regions by Resume Count
if chart_type == "Top 20 Regions by Number of Resumes":
    st.subheader("Top 20 Regions by Resume Count")
    region_counts = df['Region'].value_counts().head(20)
    fig, ax = plt.subplots()
    sns.barplot(x=region_counts.values, y=region_counts.index, ax=ax)
    ax.set_xlabel("Number of Resumes")
    ax.set_ylabel("Region")
    st.pyplot(fig)

# Chart 2: Most Popular Professions
elif chart_type == "Most Popular Professions by Region":
    st.subheader("Most Common Professions in Selected Regions")
    top_jobs = filtered_df['Category'].value_counts().head(10)
    fig, ax = plt.subplots()
    sns.barplot(x=top_jobs.values, y=top_jobs.index, ax=ax)
    ax.set_xlabel("Count")
    ax.set_ylabel("Job Category")
    st.pyplot(fig)

# Chart 3: Salary vs Work Experience
elif chart_type == "Salary vs. Work Experience":
    st.subheader("Salary vs. Work Experience")
    fig, ax = plt.subplots()
    sns.scatterplot(data=filtered_df, x="Work experience (year)", y="Salary", ax=ax)
    ax.set_xlabel("Work Experience (years)")
    ax.set_ylabel("Salary")
    st.pyplot(fig)

# Chart 5: Mean, Median, Mode Salaries by Region (Top 20)
elif chart_type == "Mean, Median, Mode Salaries by Region":
    st.subheader("Salary Statistics by Region (Top 20)")
    grouped = df.groupby("Region")["Salary"].agg(["mean", "median", lambda x: x.mode().iloc[0] if not x.mode().empty else None])
    grouped.columns = ["Mean", "Median", "Mode"]
    grouped = grouped.dropna().sort_values("Mean", ascending=False).head(20)
    st.dataframe(grouped.style.format("{:.0f}"))

# Chart 6: Salary Distribution by Work Conditions
elif chart_type == "Salary Distribution by Work Conditions":
    st.subheader("Salary Distribution by Work Conditions")
    fig, ax = plt.subplots()
    sns.boxplot(data=filtered_df, x="working conditions", y="Salary", ax=ax)
    ax.set_xlabel("Working Conditions")
    ax.set_ylabel("Salary")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Chart 7: Salary Distribution by Sex
elif chart_type == "Salary Distribution by Sex":
    st.subheader("Salary Distribution by Sex")
    fig, ax = plt.subplots()
    sns.boxplot(data=filtered_df, x="Sex", y="Salary", ax=ax)
    ax.set_xlabel("Sex")
    ax.set_ylabel("Salary")
    st.pyplot(fig)
