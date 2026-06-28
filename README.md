**Predicting Medication Management Difficulty Using Machine Learning**

**Author: Diana Opiyo**

Dataset: 2021 National Consumer Survey on Medication Experiences & Pharmacists' Roles (NCSME)

Task: Binary Classification — predicting which patients are at high risk of medication management difficulty

**Overview**

This project builds and evaluates machine learning models to identify patients who are likely to find managing their medications difficult. Early identification allows pharmacists to proactively target vulnerable patients for support and intervention.
The target variable (Med_Difficult) is derived from a 7-point Likert scale and binarized: scores ≥ 5 (Agree and above) are classified as High Risk (1), and scores 1–4 as Low Risk (0).

**Dataset**

Source: 2021 NCSME survey (NCSME_PR.xlsx)
Sample size: N = 1,521
Predictors: 15 variables across four domains:

Medication complexity (NumRx, NumOTC, NumHerbal)
Health burden (NumHealthProb, RateHealth, HospLastYear)
Barriers (Fin_Hardship, Transport, Side_Effects)
Demographics (Age, Education, HouseIncome, RuralUrban)
Engineered features: Total_Meds, Barrier_Score, Support_Score, Health_Score

<img width="450" height="321" alt="image" src="https://github.com/user-attachments/assets/ba8caf04-d8ae-4db0-87bf-7b1913dde69f" />


<img width="500" height="450" alt="image" src="https://github.com/user-attachments/assets/53b44b2e-3fec-465a-b5c4-56dc8c600401" />


