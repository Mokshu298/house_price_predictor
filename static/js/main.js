/* -------------------------------------------------------------
   House Price Predictor - Main Frontend Engine & Chart Integration
   ------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
    initHierarchicalLocationMapping();
    initPredictionForm();
    initEvaluationCharts();
    initFileUploadPreview();
});

/* -------------------------------------------------------------
   1. Hierarchical Location Mapping (State -> City -> Locality)
   ------------------------------------------------------------- */
function initHierarchicalLocationMapping() {
    const stateSelect = document.getElementById('select-state');
    const citySelect = document.getElementById('select-city');
    const localitySelect = document.getElementById('select-locality');

    if (!stateSelect || !citySelect || !localitySelect) return;

    const hierarchy = window.appOptions ? window.appOptions.Location_Hierarchy : null;
    if (!hierarchy) return;

    // State change handler
    stateSelect.addEventListener('change', () => {
        const selectedState = stateSelect.value;
        citySelect.innerHTML = '<option value="">-- Choose City --</option>';
        localitySelect.innerHTML = '<option value="">-- First Select City --</option>';
        citySelect.disabled = true;
        localitySelect.disabled = true;

        if (selectedState && hierarchy[selectedState]) {
            const cities = Object.keys(hierarchy[selectedState]).sort();
            cities.forEach(city => {
                const opt = document.createElement('option');
                opt.value = city;
                opt.textContent = city;
                citySelect.appendChild(opt);
            });
            citySelect.disabled = false;
        }
    });

    // City change handler
    citySelect.addEventListener('change', () => {
        const selectedState = stateSelect.value;
        const selectedCity = citySelect.value;

        localitySelect.innerHTML = '<option value="">-- Choose Locality --</option>';
        localitySelect.disabled = true;

        if (selectedState && selectedCity && hierarchy[selectedState] && hierarchy[selectedState][selectedCity]) {
            const localities = hierarchy[selectedState][selectedCity].sort();
            localities.forEach(locality => {
                const opt = document.createElement('option');
                opt.value = locality;
                opt.textContent = locality;
                localitySelect.appendChild(opt);
            });
            localitySelect.disabled = false;
        }
    });
}

/* -------------------------------------------------------------
   2. Prediction Form & Wizard Stepper Logic
   ------------------------------------------------------------- */
function initPredictionForm() {
    const form = document.getElementById('prediction-form');
    if (!form) return;

    let currentStep = 1;
    const totalSteps = 4;

    const stepElements = document.querySelectorAll('.form-step-content');
    const stepIndicators = document.querySelectorAll('.stepper-step');
    const prevBtn = document.getElementById('btn-prev-step');
    const nextBtn = document.getElementById('btn-next-step');
    const submitBtn = document.getElementById('btn-predict-submit');

    function updateStepVisibility() {
        stepElements.forEach(el => el.style.display = 'none');
        const activeContent = document.getElementById(`step-content-${currentStep}`);
        if (activeContent) activeContent.style.display = 'block';

        stepIndicators.forEach((ind, index) => {
            ind.classList.remove('active', 'completed');
            if (index + 1 === currentStep) {
                ind.classList.add('active');
            } else if (index + 1 < currentStep) {
                ind.classList.add('completed');
            }
        });

        if (prevBtn) prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none';
        if (nextBtn) nextBtn.style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
        if (submitBtn) submitBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            if (currentStep < totalSteps) {
                currentStep++;
                updateStepVisibility();
            }
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            if (currentStep > 1) {
                currentStep--;
                updateStepVisibility();
            }
        });
    }

    stepIndicators.forEach((ind, idx) => {
        ind.addEventListener('click', () => {
            currentStep = idx + 1;
            updateStepVisibility();
        });
    });

    // Form Submission via AJAX
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resultContainer = document.getElementById('prediction-result-container');
        const spinner = document.getElementById('prediction-loading-spinner');

        if (resultContainer) resultContainer.style.display = 'none';
        if (spinner) spinner.style.display = 'block';

        // Gather standard form fields
        const formData = new FormData(form);
        const payload = {};
        const checkedAmenities = [];

        formData.forEach((value, key) => {
            if (key === 'amenity_item') {
                checkedAmenities.push(value);
            } else {
                payload[key] = value;
            }
        });

        // Pass checked amenities as comma separated string or list
        payload['Amenities'] = checkedAmenities;

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (spinner) spinner.style.display = 'none';

            if (data.status === 'success') {
                renderPredictionResults(data.predictions, data.algorithm);
                if (resultContainer) {
                    resultContainer.style.display = 'block';
                    resultContainer.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                alert('Prediction Error: ' + (data.message || 'Unable to compute prediction'));
            }
        } catch (err) {
            if (spinner) spinner.style.display = 'none';
            alert('Server error processing prediction: ' + err.message);
        }
    });

    updateStepVisibility();
}

function renderPredictionResults(predictions, requestedAlgo) {
    const mainPriceEl = document.getElementById('res-main-price');
    const lakhsEl = document.getElementById('res-price-lakhs');
    const perSqFtEl = document.getElementById('res-price-sqft');
    const totalInrEl = document.getElementById('res-price-inr');
    const comparisonGrid = document.getElementById('model-comparison-grid');

    const modelKeys = Object.keys(predictions);
    const primaryAlgo = predictions[requestedAlgo] ? requestedAlgo : modelKeys[0];
    const primaryData = predictions[primaryAlgo];

    if (mainPriceEl) mainPriceEl.textContent = primaryData.Formatted_Price;
    if (lakhsEl) lakhsEl.textContent = `₹ ${primaryData.Price_in_Lakhs} Lakhs`;
    if (perSqFtEl) perSqFtEl.textContent = primaryData.Formatted_Per_SqFt;
    if (totalInrEl) totalInrEl.textContent = primaryData.Formatted_INR;

    if (comparisonGrid) {
        comparisonGrid.innerHTML = '';
        modelKeys.forEach(algo => {
            const item = predictions[algo];
            const isSelected = algo === primaryAlgo;
            const card = document.createElement('div');
            card.className = `prediction-sub-item ${isSelected ? 'badge-emerald' : ''}`;
            card.innerHTML = `
                <div style="font-size:0.85rem; color:var(--text-secondary); font-weight:600;">${algo} ${isSelected ? '(Selected)' : ''}</div>
                <div class="prediction-sub-val">${item.Formatted_Price}</div>
                <div style="font-size:0.8rem; color:var(--accent-cyan); margin-top:4px;">${item.Formatted_Per_SqFt}</div>
            `;
            comparisonGrid.appendChild(card);
        });
    }
}

/* -------------------------------------------------------------
   3. Model Evaluation Charts (Chart.js Integration)
   ------------------------------------------------------------- */
async function initEvaluationCharts() {
    const r2ChartCtx = document.getElementById('chart-r2-metrics');
    if (!r2ChartCtx) return;

    try {
        const response = await fetch('/api/evaluation-data');
        const data = await response.json();
        if (data.status !== 'success') return;

        const evalData = data.metrics.evaluation;
        const featureImpData = data.metrics.feature_importance;

        const algoNames = Object.keys(evalData);
        const r2Scores = algoNames.map(name => evalData[name].r2);
        const maeScores = algoNames.map(name => evalData[name].mae);
        const rmseScores = algoNames.map(name => evalData[name].rmse);

        // Chart 1: R2 Score Comparison
        new Chart(r2ChartCtx, {
            type: 'bar',
            data: {
                labels: algoNames,
                datasets: [{
                    label: 'R² Score (Higher is Better)',
                    data: r2Scores,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(6, 182, 212, 0.7)',
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(139, 92, 246, 0.7)'
                    ],
                    borderColor: ['#10B981', '#06B6D4', '#6366F1', '#8B5CF6'],
                    borderWidth: 1.5,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { labels: { color: '#F9FAFB', font: { family: 'Inter' } } }
                },
                scales: {
                    x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });

        // Chart 2: MAE & RMSE Error Comparison
        const errorCtx = document.getElementById('chart-error-metrics');
        if (errorCtx) {
            new Chart(errorCtx, {
                type: 'bar',
                data: {
                    labels: algoNames,
                    datasets: [
                        {
                            label: 'MAE (Mean Absolute Error)',
                            data: maeScores,
                            backgroundColor: 'rgba(6, 182, 212, 0.6)',
                            borderColor: '#06B6D4',
                            borderWidth: 1,
                            borderRadius: 6
                        },
                        {
                            label: 'RMSE (Root Mean Squared Error)',
                            data: rmseScores,
                            backgroundColor: 'rgba(239, 68, 68, 0.6)',
                            borderColor: '#EF4444',
                            borderWidth: 1,
                            borderRadius: 6
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#F9FAFB' } } },
                    scales: {
                        x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }

        // Chart 3: Sample Predictions vs Actuals (XGBoost / Best Model)
        const predVsActualCtx = document.getElementById('chart-actual-vs-pred');
        if (predVsActualCtx) {
            const bestAlgo = algoNames[0];
            const actuals = evalData[bestAlgo].actual_sample;
            const preds = evalData[bestAlgo].pred_sample;
            const sampleLabels = actuals.map((_, i) => `Property #${i+1}`);

            new Chart(predVsActualCtx, {
                type: 'line',
                data: {
                    labels: sampleLabels,
                    datasets: [
                        {
                            label: 'Actual Price (Lakhs)',
                            data: actuals,
                            borderColor: '#10B981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            fill: true,
                            tension: 0.3
                        },
                        {
                            label: 'Predicted Price (Lakhs)',
                            data: preds,
                            borderColor: '#6366F1',
                            borderDash: [5, 5],
                            backgroundColor: 'transparent',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: '#F9FAFB' } } },
                    scales: {
                        x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }

        // Chart 4: Feature Importance Radar/Bar Chart
        const featCtx = document.getElementById('chart-feature-importance');
        if (featCtx && featureImpData['XGBoost']) {
            const featDict = featureImpData['XGBoost'];
            const featLabels = Object.keys(featDict);
            const featValues = Object.values(featDict);

            new Chart(featCtx, {
                type: 'bar',
                data: {
                    labels: featLabels,
                    datasets: [{
                        label: 'Feature Importance Weight',
                        data: featValues,
                        backgroundColor: 'rgba(139, 92, 246, 0.7)',
                        borderColor: '#8B5CF6',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: { legend: { labels: { color: '#F9FAFB' } } },
                    scales: {
                        x: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                    }
                }
            });
        }

    } catch (e) {
        console.error("Failed to load evaluation charts:", e);
    }
}

/* -------------------------------------------------------------
   4. File Upload & Table Preview
   ------------------------------------------------------------- */
function initFileUploadPreview() {
    const fileInput = document.getElementById('csv-file-input');
    const previewContainer = document.getElementById('csv-preview-container');
    const tableHeader = document.getElementById('preview-table-header');
    const tableBody = document.getElementById('preview-table-body');
    const rowCountBadge = document.getElementById('preview-row-count');

    if (!fileInput || !previewContainer) return;

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            const lines = text.split('\n').filter(line => line.trim().length > 0);
            if (lines.length === 0) return;

            const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
            const dataRows = lines.slice(1, 11).map(line => line.split(',').map(c => c.trim().replace(/^"|"$/g, '')));

            if (tableHeader) {
                tableHeader.innerHTML = headers.map(h => `<th>${h}</th>`).join('');
            }

            if (tableBody) {
                tableBody.innerHTML = dataRows.map(row => 
                    `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`
                ).join('');
            }

            if (rowCountBadge) {
                rowCountBadge.textContent = `${lines.length - 1} total rows detected`;
            }

            previewContainer.style.display = 'block';
        };

        reader.readAsText(file.slice(0, 50000));
    });
}
