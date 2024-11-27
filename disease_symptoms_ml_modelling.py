# -*- coding: utf-8 -*-
"""disease_symptoms_ml_modelling.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/14TYYPjpgMBXnmo9LnDsBjmKnQ0Fsa9Wc

# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>IMPORTS</font></div>
"""

!pip install catboost

# Base Libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Data Analysis Libraries
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.preprocessing import MinMaxScaler,StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.metrics import accuracy_score,recall_score,precision_score,f1_score,roc_auc_score
from sklearn.model_selection import train_test_split, cross_val_score,GridSearchCV
from sklearn.metrics import classification_report,confusion_matrix

# Machine Learning Libraries
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier,GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier

# İgnore Warnings
import warnings
warnings.filterwarnings("ignore")

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_rows', 150)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>LOADING DATA</font></div>"""

df = pd.read_csv('Disease_symptom_and_patient_profile_dataset.csv')

df.head()

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>FEATURES</font></div>

**Disease:** The name of the disease or medical condition.

**Fever:** Indicates whether the patient has a fever (Yes/No).

**Cough:** Indicates whether the patient has a cough (Yes/No).

**Fatigue:** Indicates whether the patient experiences fatigue (Yes/No).

**Difficulty Breathing:** Indicates whether the patient has difficulty breathing (Yes/No).

**Age:** The age of the patient in years.

**Gender:** The gender of the patient (Male/Female).

**Blood Pressure:** The blood pressure level of the patient (Normal/High).

**Cholesterol Level:** The cholesterol level of the patient (Normal/High).

**Outcome Variable:** The outcome variable indicating the result of the diagnosis or assessment for the specific disease (Positive/Negative).

# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>DATA INFORMATION</font></div>
"""

df.shape

df.rename(columns={
    'Difficulty Breathing': 'DB',
    'Blood Pressure' : 'BP',
    'Cholesterol Level' : 'CL',
    'Outcome Variable' : 'Results'},inplace=True)

df.info()

#df.groupby(['Gender','Fever']).mean()

# Select only numeric columns for calculating the mean
numeric_cols = df.select_dtypes(include=['number']).columns
df.groupby(['Gender','Fever'])[numeric_cols].mean()

#Alternatively, if you want to analyze the 'Disease' column:
# you can get the most frequent disease for each group
df.groupby(['Gender', 'Fever'])['Disease'].agg(lambda x: x.mode()[0])
# or count the occurence of each disease within each group:
df.groupby(['Gender', 'Fever'])['Disease'].value_counts()

def grab_col_names(dataframe, cat_th=10, car_th=20):

    # cat_cols, cat_but_car
    cat_cols = [col for col in dataframe.columns if dataframe[col].dtypes == "O"]
    num_but_cat = [col for col in dataframe.columns if dataframe[col].nunique() < cat_th and dataframe[col].dtypes != "O"]
    cat_but_car = [col for col in dataframe.columns if dataframe[col].nunique() > car_th and dataframe[col].dtypes == "O"]
    cat_cols = cat_cols + num_but_cat
    cat_cols = [col for col in cat_cols if col not in cat_but_car]

    # num_cols
    num_cols = [col for col in dataframe.columns if dataframe[col].dtypes != "O"]
    num_cols = [col for col in num_cols if col not in num_but_cat]

    print(f"Observations: {dataframe.shape[0]}")
    print(f"Variables: {dataframe.shape[1]}")
    print(f'cat_cols: {len(cat_cols)}')
    print(f'num_cols: {len(num_cols)}')
    print(f'cat_but_car: {len(cat_but_car)}')
    print(f'num_but_cat: {len(num_but_cat)}')

    return cat_cols, num_cols, cat_but_car


cat_cols, num_cols, cat_but_car = grab_col_names(df)

cat_cols, num_cols, cat_but_car

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>EDA</font></div>"""

def cat_summary(dataframe, col_name, plot=False):
    print(pd.DataFrame({col_name: dataframe[col_name].value_counts(),
                        "Ratio": 100 * dataframe[col_name].value_counts() / len(dataframe)}))

    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(8, 6))
        plt.subplot(1, 2, 1)
        sns.countplot(x=dataframe[col_name], data=dataframe)
        plt.title("Frequency of " + col_name)
        plt.xticks(rotation=90)

        plt.subplot(1, 2, 2)
        values = dataframe[col_name].value_counts()
        plt.pie(x=values, labels=values.index, autopct=lambda p: '{:.2f}% ({:.0f})'.format(p, p/100 * sum(values)))
        plt.title("Frequency of " + col_name)
        plt.legend(labels=['{} - {:.2f}%'.format(index, value/sum(values)*100) for index, value in zip(values.index, values)],
                   loc='upper center', bbox_to_anchor=(0.5, -0.2), fancybox=True, shadow=True, ncol=1)
        plt.show(block=True)

for col in cat_cols:
    cat_summary(df, col, True)

import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats

def num_summary(dataframe, numerical_col, plot=False):
    quantiles = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
    print(dataframe[numerical_col].describe(quantiles).T)

    if plot:
        fig, axs = plt.subplots(1, 2, figsize=(10, 8))

        # Histogram
        plt.subplot(1, 2, 1)
        dataframe[numerical_col].hist(bins=50)
        plt.xlabel(numerical_col)
        plt.title(numerical_col + ' Distribution')

        # Boxplot
        plt.subplot(1, 2, 2)
        sns.boxplot(y=numerical_col, data=dataframe)
        plt.title("Boxplot of " + numerical_col)
        plt.xticks(rotation=90)

        plt.tight_layout()
        plt.show(block=True)

    print("#####################################")

for col in num_cols:
    num_summary(df, col, plot=True)

"""#It Counts the Difference with respect to number of female and male suffer from different Disease"""

plt.figure(figsize=(20,10))
sns.countplot(x = df['Disease'],hue = df['Gender'])
plt.xticks(rotation=90,fontsize=10)
plt.xlabel('Disease', fontsize=14)
plt.ylabel('Counts by Gender', fontsize=14)
plt.legend(fontsize=12)
plt.show()

"""#It Counts the Difference With Respect to  age and a Kind Of Diseases suffering From"""

plt.figure(figsize=(10, 12))
plt.barh(df['Disease'], df['Age'], height=0.3, align='center')
plt.xticks(fontsize=8)
plt.yticks(fontsize=7)
plt.xlabel('Age', fontsize=10)
plt.ylabel('Kind of Diseases', fontsize=10)
plt.title('Disease and Age Relation', fontsize=10)
plt.grid()
plt.show()

"""#It Will Find out In what age the human suffer from that disease."""

plt.figure(figsize=(16,6))
plt.scatter(df['Disease'],df['Age'])
plt.xticks(rotation=90)
plt.title('Year and Disease Relations')
plt.grid()
plt.show()

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>ML MODELS BEFORE FEATURE EXTRACTION</font></div>"""

df2 = df.copy()

df2.head()

le = LabelEncoder()
df2['Fever'] = le.fit_transform(df2['Fever'])
df2['Cough'] = le.fit_transform(df2['Cough'])
df2['Fatigue'] = le.fit_transform(df2['Fatigue'])
df2['DB'] = le.fit_transform(df2['DB'])
df2['Gender'] = le.fit_transform(df2['Gender'])
df2['BP'] = le.fit_transform(df2['BP'])
df2['CL'] = le.fit_transform(df2['CL'])
df2['Results'] = le.fit_transform(df2['Results'])

df2.head()

y = df2['Results']
X = df2.drop(['Results','Disease'],axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

models = [('LR', LogisticRegression()),
          ('KNN', KNeighborsClassifier()),
          ('CART', DecisionTreeClassifier()),
          ('RF', RandomForestClassifier()),
          ('GBM', GradientBoostingClassifier()),
          ("XGBoost", XGBClassifier()),
          ("LightGBM", LGBMClassifier(verbose=-1)),
          ("CatBoost", CatBoostClassifier(verbose=False))]

acclist=[]
for name, model in models:
    acc = np.mean(cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy"))
    acclist.append([name,acc])
    print(f"ACC: {round(acc, 4)} ({name}) ")

cat = CatBoostClassifier(verbose=False)
model = cat.fit(X_train,y_train)
model.score(X_test,y_test)

y_pred = model.predict(X_test)

def plot_importance(model, features, num=len(X), save=False):
    feature_imp = pd.DataFrame({'Value': model.feature_importances_, 'Feature': features.columns})
    plt.figure(figsize=(10, 10))
    sns.set(font_scale=0.5)
    sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value",ascending=False)[0:num])
    plt.title('Features')
    plt.tight_layout()
    plt.show()
    if save:
        plt.savefig('importances.png')

plot_importance(model, X)

plt.figure(figsize=(5,5))
sns.heatmap(confusion_matrix(y_test, y_pred), cmap='Blues', fmt='d',annot= True, annot_kws={"size": 10, "weight": "bold", "color":"red"})
plt.show()

print(classification_report(y_test, y_pred))

roc_auc_score(y_test, y_pred)

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>FEATURE EXTRACTION</font></div>"""

df.Disease.unique()

df['Disease'].value_counts()

#df.groupby(by='Disease').mean()

# Convert columns with numeric values to the appropriate data type.
# For example, if the 'Fever' column contains numeric values but is stored as an object:
df['Fever'] = pd.to_numeric(df['Fever'], errors='coerce')

# Calculate the mean for only numeric columns:
df.groupby(by='Disease').mean(numeric_only=True)

df.Disease.nunique()

np.where(df['Disease']=='Influenza'), np.where(df['Disease']=='Eczema')

df.head()

df["Fever_and_Cough"] = (df["Fever"] == "Yes") & (df["Cough"] == "Yes")
df["Fever_and_Fatigue"] = (df["Fever"] == "Yes") & (df["Fatigue"] == "Yes")
df["Fatigue_and_Cough"] = (df["Fatigue"] == "Yes") & (df["Cough"] == "Yes")
df["Fever_and_Fatigue_and_Cough"] = (df['Fever']== "Yes") & (df["Fatigue"] == "Yes") & (df["Cough"] == "Yes")

disease_counts = df["Disease"].value_counts()
df["Disease_Frequency"] = df["Disease"].map(disease_counts)

bins = [0, 18, 65, float('inf')]
labels = ['Child', 'Adult', 'Elderly']
df['Age_Group'] = pd.cut(df['Age'], bins=bins, labels=labels, right=False)

df['Risk_Score'] = df['Age'] * 0.1 + (df['CL'] == 'High') * 10

df["Age_Squared"] = df["Age"] ** 2

df

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>ENCODING FEATURES</font></div>"""

dfd = pd.get_dummies(df,columns=['Fever','Cough','Fatigue','DB','BP','CL','Gender','Age_Group'],drop_first=True)

dfd.head()

dfd.shape

np.where(dfd.isna())

dfd.columns.values

dfd.rename(columns={
    "Disease_Alzheimer's Disease": "Disease_Alzheimers_Disease",
    "Disease_Anxiety Disorders": "Disease_Anxiety_Disorders",
    "Disease_Autism Spectrum Disorder (ASD)": "Disease_Autism_Spectrum_Disorder",
    "Disease_Bipolar Disorder": "Disease_Bipolar_Disorder",
    "Disease_Bladder Cancer": "Disease_Bladder_Cancer",
    "Disease_Brain Tumor": "Disease_Brain_Tumor",
    "Disease_Breast Cancer": "Disease_Breast_Cancer",
    "Disease_Cerebral Palsy": "Disease_Cerebral_Palsy",
    "Disease_Chronic Kidney Disease": "Disease_Chronic_Kidney_Disease",
    "Disease_Chronic Obstructive Pulmonary Disease (COPD)": "Disease_Chronic_Obstructive_Pulmonary_Disease",
    "Disease_Chronic Obstructive Pulmonary...": "Disease_Chronic_Obstructive_Pulmonary_Disease_COPD",
    "Disease_Colorectal Cancer": "Disease_Colorectal_Cancer",
    "Disease_Common Cold": "Disease_Common_Cold",
    "Disease_Conjunctivitis (Pink Eye)": "Disease_Conjunctivitis_Pink_Eye",
    "Disease_Coronary Artery Disease": "Disease_Coronary_Artery_Disease",
    "Disease_Crohn's Disease": "Disease_Crohns_Disease",
    "Disease_Cystic Fibrosis": "Disease_Cystic_Fibrosis",
    "Disease_Dengue Fever": "Disease_Dengue_Fever",
    "Disease_Down Syndrome": "Disease_Down_Syndrome",
    "Disease_Eating Disorders (Anorexia,...": "Disease_Eating_Disorders_Anorexia",
    "Disease_Ebola Virus": "Disease_Ebola_Virus",
    "Disease_Esophageal Cancer": "Disease_Esophageal_Cancer",
    "Disease_Hypertensive Heart Disease": "Disease_Hypertensive_Heart_Disease",
    "Disease_Kidney Cancer": "Disease_Kidney_Cancer",
    "Disease_Kidney Disease": "Disease_Kidney_Disease",
    "Disease_Klinefelter Syndrome": "Disease_Klinefelter_Syndrome",
    "Disease_Liver Cancer": "Disease_Liver_Cancer",
    "Disease_Liver Disease": "Disease_Liver_Disease",
    "Disease_Lung Cancer": "Disease_Lung_Cancer",
    "Disease_Lyme Disease": "Disease_Lyme_Disease",
    "Disease_Marfan Syndrome": "Disease_Marfan_Syndrome",
    "Disease_Multiple Sclerosis": "Disease_Multiple_Sclerosis",
    "Disease_Muscular Dystrophy": "Disease_Muscular_Dystrophy",
    "Disease_Myocardial Infarction (Heart...": "Disease_Myocardial_Infarction_Heart",
    "Disease_Obsessive-Compulsive Disorde...": "Disease_Obsessive_Compulsive_Disorder",
    "Disease_Otitis Media (Ear Infection)": "Disease_Otitis_Media_Ear_Infection",
    "Disease_Ovarian Cancer": "Disease_Ovarian_Cancer",
    "Disease_Pancreatic Cancer": "Disease_Pancreatic_Cancer",
    "Disease_Parkinson's Disease": "Disease_Parkinsons_Disease",
    "Disease_Pneumocystis Pneumonia (PCP)": "Disease_Pneumocystis_Pneumonia_PCP",
    "Disease_Polycystic Ovary Syndrome (PCOS)": "Disease_Polycystic_Ovary_Syndrome_PCOS",
    "Disease_Prader-Willi Syndrome": "Disease_Prader_Willi_Syndrome",
    "Disease_Prostate Cancer": "Disease_Prostate_Cancer",
    "Disease_Rheumatoid Arthritis": "Disease_Rheumatoid_Arthritis",
    "Disease_Sickle Cell Anemia": "Disease_Sickle_Cell_Anemia",
    "Disease_Sleep Apnea": "Disease_Sleep_Apnea",
    "Disease_Spina Bifida": "Disease_Spina_Bifida",
    "Disease_Systemic Lupus Erythematosus...": "Disease_Systemic_Lupus_Erythematosus",
    "Disease_Testicular Cancer": "Disease_Testicular_Cancer",
    "Disease_Thyroid Cancer": "Disease_Thyroid_Cancer",
    "Disease_Tourette Syndrome": "Disease_Tourette_Syndrome",
    "Disease_Turner Syndrome": "Disease_Turner_Syndrome",
    "Disease_Typhoid Fever": "Disease_Typhoid_Fever",
    "Disease_Ulcerative Colitis": "Disease_Ulcerative_Colitis",
    "Disease_Urinary Tract Infection": "Disease_Urinary_Tract_Infection",
    "Disease_Urinary Tract Infection (UTI)": "Disease_Urinary_Tract_Infection_UTI",
    "Disease_Williams Syndrome": "Disease_Williams_Syndrome",
    "Disease_Zika Virus": "Disease_Zika_Virus"
}, inplace=True)

le = LabelEncoder()
dfd['Results'] = le.fit_transform(dfd['Results'])
dfd['Fever_and_Cough'] = le.fit_transform(dfd['Fever_and_Cough'])
dfd['Fever_and_Fatigue'] = le.fit_transform(dfd['Fever_and_Fatigue'])
dfd['Fatigue_and_Cough'] = le.fit_transform(dfd['Fatigue_and_Cough'])
dfd['Fever_and_Fatigue_and_Cough'] = le.fit_transform(dfd['Fever_and_Fatigue_and_Cough'])
dfd['Fever_and_Cough'] = le.fit_transform(dfd['Fever_and_Cough'])

dfd.head()

dfd.drop('Disease',axis=1,inplace=True)

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>ML MODELS</font></div>"""

y = dfd['Results']
X = dfd.drop('Results',axis=1)

X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)

X_train

y_train

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>SCALING</font></div>"""

scaler = MinMaxScaler()
dfd[["Age","Age_Squared","Disease_Frequency","Risk_Score"]] = scaler.fit_transform(dfd[["Age","Age_Squared","Disease_Frequency","Risk_Score"]])
dfd.head()

models = [('LR', LogisticRegression()),
          ('KNN', KNeighborsClassifier()),
          ('CART', DecisionTreeClassifier()),
          ('RF', RandomForestClassifier()),
          ('GBM', GradientBoostingClassifier()),
          ("XGBoost", XGBClassifier()),
          ("LightGBM", LGBMClassifier(verbose=-1)),
          ("CatBoost", CatBoostClassifier(verbose=False))]

acclist=[]
for name, model in models:
    acc = np.mean(cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy"))
    acclist.append([name,acc])
    print(f"ACC: {round(acc, 4)} ({name}) ")

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>CATBOOST</font></div>"""

cat = CatBoostClassifier(verbose=False)
model1 = cat.fit(X_train,y_train)
model1.score(X_test,y_test)

y_pred = model1.predict(X_test)

y_pred

y_test

accuracy_score(y_test, y_pred)

def plot_importance(model, features, num=len(X), save=False):
    feature_imp = pd.DataFrame({'Value': model.feature_importances_, 'Feature': features.columns})
    plt.figure(figsize=(10, 10))
    sns.set(font_scale=0.5)
    sns.barplot(x="Value", y="Feature", data=feature_imp.sort_values(by="Value",ascending=False)[0:num])
    plt.title('Features')
    plt.tight_layout()
    plt.show()
    if save:
        plt.savefig('importances.png')

plot_importance(model1, X)

plt.figure(figsize=(5,5))
sns.heatmap(confusion_matrix(y_test, y_pred), cmap='Blues', fmt='d',annot= True, annot_kws={"size": 10, "weight": "bold", "color":"red"})
plt.show()

print(classification_report(y_test, y_pred))

"""# <div style="border-radius:10px; border:#5E5772 solid; padding: 12px; background-color: #1111; font-size:100%; font-family:Comic Sans MS; font-family:Comic Sans MS; text-align:center;"><font color='#5113' size=5%>CATBOOST WITH CV</font></div>"""

catboost = CatBoostClassifier(verbose=False, random_state=42)

param_grid = {
    'learning_rate': [0.01, 0.05, 0.1],
    'depth': [4, 6, 8],
    'iterations': [200, 300,500]
}

grid_search = GridSearchCV(estimator=catboost, param_grid=param_grid, cv=3, scoring='accuracy', n_jobs=-1).fit(X_train, y_train)

best_params = grid_search.best_params_
best_params

final_cat = catboost.set_params(**best_params).fit(X_train, y_train)

y_pred_cat = final_cat.predict(X_test)
acc = round(accuracy_score(y_test,y_pred_cat), 4)*100
print("Accuacy:", acc)

plt.figure(figsize=(5,5))
sns.heatmap(confusion_matrix(y_test, y_pred_cat), cmap='Blues', fmt='d',annot= True, annot_kws={"size": 10, "weight": "bold", "color":"red"})
plt.show()

print(classification_report(y_test, y_pred_cat))
