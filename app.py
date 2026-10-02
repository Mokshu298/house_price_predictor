import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.utils import secure_filename

from database import init_db, register_user, verify_user
from ml_engine import MLEngine, FEATURE_COLS, DEFAULT_CSV_PATH

app = Flask(__name__)
app.secret_key = 'super_secret_house_price_prediction_key_prophet_ai'

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB max file size

# Initialize database and ML engine
init_db()
ml_engine = MLEngine()

# -------------------------------------------------------------
# Authentication Routes (Register, Login, Logout)
# -------------------------------------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not all([full_name, username, email, password]):
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        success, msg = register_user(username, email, password, full_name)
        if success:
            flash(msg, "success")
            return redirect(url_for('login'))
        else:
            flash(msg, "error")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '').strip()

        user = verify_user(username_or_email, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username/email or password.", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))

# -------------------------------------------------------------
# Navigation Pages
# -------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_dataset():
    if 'file' not in request.files:
        flash("No file part provided.", "error")
        return redirect(url_for('upload_page'))

    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "error")
        return redirect(url_for('upload_page'))

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        try:
            # Retrain ML models on newly uploaded dataset
            custom_engine = MLEngine(data_path=save_path)
            custom_engine.train_models(sample_size=25000)
            flash("Dataset uploaded successfully! ML models retrained with updated features.", "success")
        except Exception as e:
            flash(f"Error processing dataset: {str(e)}", "error")

        return redirect(url_for('upload_page'))
    else:
        flash("Invalid file format. Please upload a valid CSV file.", "error")
        return redirect(url_for('upload_page'))

@app.route('/evaluation')
def evaluation_page():
    metrics = ml_engine.get_metrics()
    return render_template('evaluation.html', metrics=metrics)

@app.route('/predict')
def predict_page():
    options = ml_engine.get_categorical_options()
    return render_template('predict.html', options=options)

@app.route('/about')
def about_page():
    return render_template('about.html')

# -------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------
@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        data = request.json or request.form.to_dict()
        algorithm = data.get('Algorithm', 'All')
        predictions = ml_engine.predict(data, algorithm=algorithm)
        return jsonify({
            'status': 'success',
            'algorithm': algorithm,
            'predictions': predictions
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/evaluation-data')
def api_evaluation_data():
    try:
        metrics = ml_engine.get_metrics()
        return jsonify({
            'status': 'success',
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/sample-dataset')
def download_sample():
    if os.path.exists(DEFAULT_CSV_PATH):
        return send_file(DEFAULT_CSV_PATH, as_attachment=True, download_name="house_prices_sample.csv")
    else:
        flash("Sample dataset file not found.", "error")
        return redirect(url_for('upload_page'))

if __name__ == '__main__':
    print("Starting ProphetAI House Price Predictor Flask Web Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
