# HACKATHON_DATA_AUDIT.md

# 1. Official Hackathon Requirements

## Problem Context
Based on the Problem Context Brief PDF:
- The problem is around data science related jobs, skills and personality traits of data scientists
- Analysis should include data management, visualizations, patterns, statistical or data mining analysis
- Objective: bring out best information from available data

## Data Points (Big Picture)
1. Data Science Job Postings including descriptions, salary, experience and so on
2. Skill traits in data scientists for success including technical skills like coding, math, AI, ML and dashboards and story telling
3. Personality traits including neuroticism, extraversion, openness to experience, agreeableness and conscientiousness

## Data Description Summary
From Data Description Doc.pdf:
- Four data files provided:
  1. **Data Science Jobs**: Around 1600 rows of sample data describing number of jobs posted by leading companies including details like salary, experience (years 2024-25)
  2. **Analytics Jobs**: Around 15800 rows of sample data describing job postings in analytics area including details like job description, designation, location, salary (years 2024-25)
  3. **JDS Skill Traits** (Junior Data Scientists): Around 140 rows of sample data of a company's skillset data of its junior/entry level data scientists. Presents measured technical skillsets and outcome like promotion or salary hike (high/low)
  4. **SDS Personality Traits** (Senior Data Scientists): Around 160 rows of sample data of a company trait analysis data of its senior and customer facing level data scientists. Presents measured personality traits and outcome like overall success (high/low)

## Evaluation Criteria (from Problem Context)
Based on the marking scheme in the Problem Context document:
- **Round 1 (Qualifier)**: 30 marks for data understanding & preparation, 20 marks for exploratory analysis
- **Round 2 (Top 20 teams)**: 
  - 15 marks for Objective identification & problem definition
  - 15 marks for Approach description
  - 25 marks for Data Exploration (data manipulation, derivation, consolidation, preparation)
  - 30 marks for Data Analysis (statistical/non-statistical skills, descriptive/prescriptive analytical skills)
  - 10 marks for Results and Conclusions (linkage to problem statement)
  - 5 marks for Implications (implications to stakeholders)
- **Round 3 (Top 8 teams)**: Presentation (100 marks)
  - 25 marks for Presentation and communication skills
  - 10 marks for Usage of graphics
  - 5 marks for Slide Management
  - 20 marks for Overall Presentation Storyline
  - 15 marks for Concluding slides
  - 25 marks for Q&A by Jury
- Final Score: Round 2 Marks (70%) + Round 3 Marks (30%) = Total (Top 3)

## Key Considerations from Data
1. Dataset contains public, self-reported or masked information
2. May contain meaningless/misspelled/mistyped entries
3. May contain outliers and other problems
4. Need to do data cleaning and preparation

# 2. Dataset Inventory

| Dataset | Rows | Columns | File Type | Description |
|---------|------|---------|-----------|-------------|
| Analytics Jobs.csv | 15841 | 8 | CSV | Job postings in analytics area |
| DataScience Jobs.csv | 1602 | 8 | CSV | Data science job postings by companies |
| JDS Skill Traits.xlsx | 139 | 7 | Excel | Junior data scientist skill traits and salary hike outcome |
| SDS Personality Traits.xlsx | 161 | 7 | Excel | Senior data scientist personality traits and success outcome |
