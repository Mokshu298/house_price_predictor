# ProphetAI - House Price Predictor Web Application

A full-stack Machine Learning web application built with **Flask**, **Scikit-Learn**, **XGBoost**, and **HTML/CSS/JS** to predict real estate house prices, price per square foot, and Lakh valuation.

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Framework](https://img.shields.io/badge/Framework-Flask-green.svg)
![ML](https://img.shields.io/badge/ML-Scikit--Learn%20%7C%20XGBoost-orange.svg)

---

## 🌟 Key Features

- **Multi-Model Regression Pipeline**:
  - Linear Regression
  - Decision Tree Regressor
  - Random Forest Regressor
  - XGBoost Regressor
- **Dual Target Predictions**:
  - `House Price` (Formatted in ₹ Lakhs & Indian Currency format)
  - `Price_per_SqFt` (Price per Square Foot in ₹)
  - `Price_in_Lakhs` (Primary target variable)
- **Hierarchical Location Filtering**:
  - Dynamic step-by-step location selection (`State` $\rightarrow$ `City` $\rightarrow$ `Locality`).
- **Independent Amenities Selection**:
  - Individual checkboxes for `Clubhouse`, `Gym`, `Pool`, `Playground`, and `Garden`.
- **User Authentication**:
  - Session-based Registration & Login powered by SQLite and Werkzeug password hashing.
- **Model Evaluation Analytics**:
  - Scorecard ($R^2$, MAE, RMSE, Train Latency) + Chart.js visual graphs ($R^2$ Bar Chart, Error Metrics, Actual vs Predicted, Feature Importance).
- **Custom Dataset Ingestion**:
  - Drag-and-drop CSV dataset upload & live table previewer.

---

## 📊 Dataset Parameters Analyzed

1. `ID`
2. `State`
3. `City`
4. `Locality`
5. `Property_Type`
6. `BHK`
7. `Size_in_SqFt`
8. `Price_in_Lakhs` (Target)
9. `Price_per_SqFt` (Target)
10. `Year_Built`
11. `Furnished_Status`
12. `Floor_No`
13. `Total_Floors`
14. `Age_of_Property`
15. `Nearby_Schools`
16. `Nearby_Hospitals`
17. `Public_Transport_Accessibility`
18. `Parking_Space`
19. `Security`
20. `Amenities`
21. `Facing`
22. `Owner_Type`
23. `Availability_Status`

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.9+
- Git

### 2. Installation & Setup
```bash
# Clone repository
git clone https://github.com/Mokshu298/house_price_predictor.git
cd house_price_predictor

# Install required dependencies
pip install flask scikit-learn xgboost pandas numpy joblib werkzeug
```

### 3. Train ML Models & Run Web Server
```bash
# Train ML Models (Generates preprocessor and model artifacts in models_saved/)
python ml_engine.py

# Launch Flask Web Server
python app.py
```

Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 📁 Project Structure

```
house_price_predictor/
│
├── app.py                  # Main Flask application & route handlers
├── ml_engine.py            # Preprocessing, ML model training & inference engine
├── database.py             # SQLite user authentication database module
├── data.csv                # 250,000 record real estate benchmark dataset
│
├── models_saved/           # Saved trained joblib model artifacts & metrics.json
├── static/
│   ├── css/styles.css      # Dark glassmorphic modern UI design system
│   └── js/main.js          # Interactive wizard, AJAX & Chart.js engine
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── upload.html
│   ├── evaluation.html
│   ├── predict.html
│   └── about.html
└── README.md
```

---

## 🛡️ License
Distributed under the MIT License.
