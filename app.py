import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
@st.cache_data

def load_data():
    df = pd.read_csv("resumes_cleaned.csv")
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

# Title
st.title("Resume Data Dashboard")

# Chart 1: Top 20 Regions by Resume Count
if chart_type == "Top 20 Regions by Number of Resumes":
    st.subheader("Top 20 Regions by Resume Count")
    region_selection = st.multiselect("Select Regions (optional)", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    region_counts = filtered_df['Region'].value_counts().head(20)
    fig, ax = plt.subplots()
    bars = sns.barplot(x=region_counts.values, y=region_counts.index, ax=ax)
    ax.set_xlabel("Number of Resumes")
    ax.set_ylabel("Region")
    ax.bar_label(ax.containers[0])
    st.pyplot(fig)

# Chart 2: Most Popular Professions
elif chart_type == "Most Popular Professions by Region":
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    st.subheader("Most Common Professions in Selected Regions")
    top_jobs = filtered_df['Category'].value_counts().head(10)
    fig, ax = plt.subplots()
    bars = sns.barplot(x=top_jobs.values, y=top_jobs.index, ax=ax)
    ax.set_xlabel("Count")
    ax.set_ylabel("Job Category")
    ax.bar_label(ax.containers[0])
    st.pyplot(fig)

# Chart 3: Salary vs Work Experience
elif chart_type == "Salary vs. Work Experience":
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    st.subheader("Salary vs. Work Experience")
    fig, ax = plt.subplots()
    sns.scatterplot(data=filtered_df, x="Work experience (year)", y="Salary", hue="Region", ax=ax)
    ax.set_xlabel("Work Experience (years)")
    ax.set_ylabel("Salary")
    st.pyplot(fig)

# Chart 4: Education Distribution
elif chart_type == "Education Level Distribution":
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    st.subheader("Education Level Distribution")
    edu_counts = filtered_df['Education'].value_counts()
    fig, ax = plt.subplots()
    bars = sns.barplot(x=edu_counts.values, y=edu_counts.index, ax=ax)
    ax.set_xlabel("Count")
    ax.set_ylabel("Education Level")
    ax.bar_label(ax.containers[0])
    st.pyplot(fig)

# Chart 5: Mean, Median, Mode Salaries by Region (Top 20)
elif chart_type == "Mean, Median, Mode Salaries by Region":
    st.subheader("Salary Statistics by Region (Top 20)")
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    grouped = filtered_df.groupby("Region")["Salary"].agg(["mean", "median", lambda x: x.mode().iloc[0] if not x.mode().empty else None])
    grouped.columns = ["Mean", "Median", "Mode"]
    grouped = grouped.dropna().sort_values("Mean", ascending=False).head(20)
    st.dataframe(grouped.style.format("{:.0f}"))

# Chart 6: Salary Distribution by Work Conditions
elif chart_type == "Salary Distribution by Work Conditions":
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    st.subheader("Salary Distribution by Work Conditions")
    fig, ax = plt.subplots()
    sns.boxplot(data=filtered_df, x="working conditions", y="Salary", ax=ax)
    ax.set_xlabel("Working Conditions")
    ax.set_ylabel("Salary")
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Chart 7: Salary Distribution by Sex
elif chart_type == "Salary Distribution by Sex":
    region_selection = st.multiselect("Select Regions", df['Region'].unique(), default=list(df['Region'].unique()))
    filtered_df = df[df['Region'].isin(region_selection)]

    st.subheader("Salary Distribution by Sex")
    fig, ax = plt.subplots()
    sns.boxplot(data=filtered_df, x="Sex", y="Salary", ax=ax)
    ax.set_xlabel("Sex")
    ax.set_ylabel("Salary")
    st.pyplot(fig)
