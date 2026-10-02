import os
import time
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models_saved')
DEFAULT_CSV_PATH = os.path.join(os.path.dirname(__file__), 'data.csv')

CATEGORICAL_COLS = [
    'State', 'City', 'Locality', 'Property_Type', 'Furnished_Status',
    'Public_Transport_Accessibility', 'Parking_Space', 'Security',
    'Amenities', 'Facing', 'Owner_Type', 'Availability_Status'
]

NUMERICAL_COLS = [
    'BHK', 'Size_in_SqFt', 'Year_Built', 'Floor_No', 'Total_Floors',
    'Age_of_Property', 'Nearby_Schools', 'Nearby_Hospitals'
]

FEATURE_COLS = NUMERICAL_COLS + CATEGORICAL_COLS
TARGET_COL = 'Price_in_Lakhs'

class MLEngine:
    def __init__(self, data_path=DEFAULT_CSV_PATH):
        self.data_path = data_path
        self.models_dir = MODELS_DIR
        os.makedirs(self.models_dir, exist_ok=True)
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.feature_names = []
        self.categorical_options = {}

    def load_and_preprocess_data(self, sample_size=30000):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset not found at {self.data_path}")
        
        df = pd.read_csv(self.data_path)
        
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        else:
            df_sample = df.copy()

        if 'Age_of_Property' not in df_sample.columns or df_sample['Age_of_Property'].isnull().any():
            current_year = 2025
            df_sample['Age_of_Property'] = current_year - df_sample['Year_Built']

        # Build complete Location Hierarchy: State -> City -> Locality
        location_hierarchy = {}
        for (state, city), group in df.groupby(['State', 'City']):
            if state not in location_hierarchy:
                location_hierarchy[state] = {}
            location_hierarchy[state][city] = sorted(group['Locality'].unique().tolist())

        self.categorical_options['States'] = sorted(list(location_hierarchy.keys()))
        self.categorical_options['Location_Hierarchy'] = location_hierarchy

        # Save categorical dropdown options for frontend
        for col in CATEGORICAL_COLS:
            self.categorical_options[col] = sorted(df[col].astype(str).unique().tolist())

        # Encode categorical variables
        df_encoded = df_sample.copy()
        for col in CATEGORICAL_COLS:
            le = LabelEncoder()
            df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
            self.label_encoders[col] = le

        X = df_encoded[FEATURE_COLS]
        y = df_encoded[TARGET_COL]
        self.feature_names = FEATURE_COLS

        # Fit Scaler
        X_scaled = self.scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=FEATURE_COLS)

        return X_scaled_df, y, df_sample

    def train_models(self, sample_size=30000):
        X, y, raw_df = self.load_and_preprocess_data(sample_size=sample_size)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        models = {
            'Linear Regression': LinearRegression(),
            'Decision Tree': DecisionTreeRegressor(max_depth=15, min_samples_split=10, random_state=42),
            'Random Forest': RandomForestRegressor(n_estimators=100, max_depth=15, n_jobs=-1, random_state=42),
            'XGBoost': xgb.XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.08, n_jobs=-1, random_state=42)
        }

        evaluation_results = {}
        feature_importance_dict = {}

        for name, model in models.items():
            start_time = time.time()
            model.fit(X_train, y_train)
            train_time = round(time.time() - start_time, 3)

            y_pred = model.predict(X_test)
            r2 = round(r2_score(y_test, y_pred), 4)
            mae = round(mean_absolute_error(y_test, y_pred), 4)
            rmse = round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4)

            # Save model artifact
            joblib.dump(model, os.path.join(self.models_dir, f"{name.lower().replace(' ', '_')}.joblib"))

            # Calculate Feature Importances
            importances = []
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_.tolist()
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_).tolist()

            if importances:
                total_imp = sum(importances) or 1.0
                norm_importances = [round(float(imp / total_imp), 4) for imp in importances]
                feature_importance_dict[name] = dict(zip(FEATURE_COLS, norm_importances))

            sample_actual = [round(float(v), 2) for v in y_test.iloc[:50].values]
            sample_predicted = [round(float(v), 2) for v in y_pred[:50]]

            evaluation_results[name] = {
                'r2': r2,
                'mae': mae,
                'rmse': rmse,
                'train_time': train_time,
                'actual_sample': sample_actual,
                'pred_sample': sample_predicted
            }

        # Save preprocessor artifacts
        preprocessor_data = {
            'label_encoders': self.label_encoders,
            'scaler': self.scaler,
            'feature_names': FEATURE_COLS,
            'categorical_options': self.categorical_options
        }
        joblib.dump(preprocessor_data, os.path.join(self.models_dir, 'preprocessor.joblib'))

        metrics_payload = {
            'evaluation': evaluation_results,
            'feature_importance': feature_importance_dict,
            'total_dataset_rows': len(raw_df),
            'training_sample_rows': len(X_train) + len(X_test),
            'last_trained': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(os.path.join(self.models_dir, 'metrics.json'), 'w') as f:
            json.dump(metrics_payload, f, indent=4)

        return metrics_payload

    def match_amenities(self, requested_amenities, available_classes):
        """Find best matching encoded Amenities category based on selected checkbox list"""
        if not requested_amenities:
            return available_classes[0]

        if isinstance(requested_amenities, list):
            req_set = set([a.strip() for a in requested_amenities if a.strip()])
        else:
            req_set = set([a.strip() for a in str(requested_amenities).split(',') if a.strip()])

        if not req_set:
            return available_classes[0]

        best_match = None
        best_score = -1

        for cls in available_classes:
            cls_set = set([a.strip() for a in cls.split(',') if a.strip()])
            if cls_set == req_set:
                return cls
            # Calculate Jaccard similarity score
            intersection = len(req_set.intersection(cls_set))
            union = len(req_set.union(cls_set))
            score = intersection / union if union > 0 else 0

            if score > best_score:
                best_score = score
                best_match = cls

        return best_match or available_classes[0]

    def predict(self, input_dict, algorithm='All'):
        prep_path = os.path.join(self.models_dir, 'preprocessor.joblib')
        if not os.path.exists(prep_path):
            self.train_models()

        prep_data = joblib.load(prep_path)
        label_encoders = prep_data['label_encoders']
        scaler = prep_data['scaler']

        data_row = {}
        for col in NUMERICAL_COLS:
            data_row[col] = float(input_dict.get(col, 0))

        for col in CATEGORICAL_COLS:
            val = input_dict.get(col, '')
            le = label_encoders[col]

            if col == 'Amenities':
                matched_val = self.match_amenities(val, le.classes_)
                encoded_val = le.transform([matched_val])[0]
            else:
                val_str = str(val)
                if val_str in le.classes_:
                    encoded_val = le.transform([val_str])[0]
                else:
                    encoded_val = 0
            data_row[col] = encoded_val

        input_df = pd.DataFrame([data_row])[FEATURE_COLS]
        input_scaled = scaler.transform(input_df)
        input_scaled_df = pd.DataFrame(input_scaled, columns=FEATURE_COLS)

        algorithms_to_run = ['Linear Regression', 'Decision Tree', 'Random Forest', 'XGBoost']
        if algorithm != 'All' and algorithm in algorithms_to_run:
            algorithms_to_run = [algorithm]

        predictions = {}
        size_sqft = float(input_dict.get('Size_in_SqFt', 1000))
        if size_sqft <= 0:
            size_sqft = 1000

        for algo in algorithms_to_run:
            model_filename = f"{algo.lower().replace(' ', '_')}.joblib"
            model_path = os.path.join(self.models_dir, model_filename)
            
            if not os.path.exists(model_path):
                self.train_models()

            model = joblib.load(model_path)
            pred_lakhs = float(model.predict(input_scaled_df)[0])
            pred_lakhs = max(1.0, round(pred_lakhs, 2))

            pred_total_inr = round(pred_lakhs * 100000, 2)
            pred_price_per_sqft = round(pred_total_inr / size_sqft, 2)

            predictions[algo] = {
                'Price_in_Lakhs': pred_lakhs,
                'House_Price_INR': pred_total_inr,
                'Price_per_SqFt': pred_price_per_sqft,
                'Formatted_Price': f"₹ {pred_lakhs:,.2f} Lakhs",
                'Formatted_INR': f"₹ {int(pred_total_inr):,}",
                'Formatted_Per_SqFt': f"₹ {pred_price_per_sqft:,.2f} / SqFt"
            }

        return predictions

    def get_categorical_options(self):
        prep_path = os.path.join(self.models_dir, 'preprocessor.joblib')
        if os.path.exists(prep_path):
            prep_data = joblib.load(prep_path)
            return prep_data['categorical_options']
        else:
            self.load_and_preprocess_data(sample_size=1000)
            return self.categorical_options

    def get_metrics(self):
        metrics_path = os.path.join(self.models_dir, 'metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                return json.load(f)
        else:
            return self.train_models()

if __name__ == '__main__':
    engine = MLEngine()
    print("Re-training ML Models with Location Hierarchy and Amenities Matcher...")
    results = engine.train_models(sample_size=25000)
    print("Complete!")
