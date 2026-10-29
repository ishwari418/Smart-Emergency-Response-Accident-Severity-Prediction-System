"""Flask API for synthetic accident analytics and severity predictions."""

import io
import json
import os
import shutil
from datetime import datetime
from flask_cors import CORS

import joblib
import pandas as pd
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from config import (
    CATEGORY_VALUES,
    DATASET_PATH,
    FEATURE_COLUMNS,
    METRICS_PATH,
    MODEL_DIR,
    MODEL_PATH,
    NUMERIC_RANGES,
    SEVERITY_LABELS,
)

app = Flask(__name__)
CORS(
    app,
    resources={r"/api/*": {"origins": [
        "https://smart-emergency-response-accident.onrender.com"
    ]}}
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
allowed_origins = os.environ.get(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")
CORS(app, resources={r"/api/*": {"origins": [origin.strip() for origin in allowed_origins if origin.strip()]}})
MAX_BATCH_ROWS = 5_000
TABLE_PAGE_SIZE = 25
_dataset_cache = None
_dataset_mtime = None
_model_cache = None


def dataset():
    global _dataset_cache, _dataset_mtime
    if not DATASET_PATH.exists():
        raise FileNotFoundError("Dataset is missing. Run `python generate_dataset.py` from the backend folder.")
    mtime = DATASET_PATH.stat().st_mtime
    if _dataset_cache is None or _dataset_mtime != mtime:
        _dataset_cache = pd.read_csv(DATASET_PATH)
        _dataset_mtime = mtime
    return _dataset_cache


def model():
    global _model_cache
    if not MODEL_PATH.exists():
        raise FileNotFoundError("Model is not trained. Run `python train_model.py` from the backend folder.")
    if _model_cache is None:
        _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


def load_metrics():
    if not METRICS_PATH.exists():
        raise FileNotFoundError("Model metrics are unavailable. Run `python train_model.py` from the backend folder.")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


def json_records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def validate_feature_frame(frame, require_all=True):
    absent = [column for column in FEATURE_COLUMNS if column not in frame.columns]
    if absent and require_all:
        raise ValueError(f"Missing required feature columns: {', '.join(absent)}")
    prepared = frame.reindex(columns=FEATURE_COLUMNS).copy()
    errors = []
    for column, (minimum, maximum) in NUMERIC_RANGES.items():
        converted = pd.to_numeric(prepared[column], errors="coerce")
        invalid_text = prepared[column].notna() & converted.isna()
        out_of_range = converted.notna() & ~converted.between(minimum, maximum)
        if invalid_text.any():
            errors.append(f"{column} must be numeric.")
        if out_of_range.any():
            errors.append(f"{column} must be between {minimum} and {maximum}.")
        prepared[column] = converted
    for column, allowed in CATEGORY_VALUES.items():
        invalid = prepared[column].notna() & ~prepared[column].astype(str).isin(allowed)
        if invalid.any():
            examples = prepared.loc[invalid, column].astype(str).drop_duplicates().head(3).tolist()
            errors.append(f"{column} contains unsupported values: {', '.join(examples)}.")
    if errors:
        raise ValueError(" ".join(errors))
    return prepared


def filtered_data():
    frame = dataset()
    severity = request.args.get("severity")
    if severity:
        try:
            severity_number = int(severity)
        except ValueError as error:
            raise ValueError("severity filter must be one of 1, 2, 3, or 4.") from error
        if severity_number not in SEVERITY_LABELS:
            raise ValueError("severity filter must be one of 1, 2, 3, or 4.")
        frame = frame[frame["severity"] == severity_number]
    for query_key, column in [("weather", "weather_conditions"), ("road_type", "road_type")]:
        value = request.args.get(query_key)
        if value:
            frame = frame[frame[column] == value]
    for query_key, column in [("date_from", "date"), ("date_to", "date")]:
        value = request.args.get(query_key)
        if value:
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as error:
                raise ValueError(f"{query_key} must use YYYY-MM-DD format.") from error
            frame = frame[frame[column] >= value] if query_key == "date_from" else frame[frame[column] <= value]
    return frame


def group_counts(frame, column):
    counts = frame[column].value_counts(dropna=False)
    return [{"name": str(name), "count": int(count)} for name, count in counts.items()]


@app.errorhandler(FileNotFoundError)
def missing_resource(error):
    return jsonify({"error": str(error)}), 503


@app.errorhandler(ValueError)
def invalid_request(error):
    return jsonify({"error": str(error)}), 400


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "Upload is too large. Maximum CSV size is 10 MB."}), 413



@app.get("/api/dashboard")
def dashboard():
    frame = filtered_data()
    severity_counts = group_counts(frame.assign(severity_name=frame["severity"].map(SEVERITY_LABELS)), "severity_name")
    return jsonify(
        {
            "total_accidents": int(len(frame)),
            "total_casualties": int(frame["number_of_casualties"].sum()),
            "average_vehicles": float(frame["number_of_vehicles"].mean()) if len(frame) else 0,
            "most_frequent_severity": severity_counts[0]["name"] if severity_counts else None,
            "severity": severity_counts,
            "by_day": group_counts(frame, "day_of_week"),
            "by_hour": [
                {"name": int(hour), "count": int(count)}
                for hour, count in frame["hour"].value_counts().sort_index().items()
            ],
            "by_weather": group_counts(frame, "weather_conditions"),
            "by_road_type": group_counts(frame, "road_type"),
            "by_light": group_counts(frame, "light_conditions"),
            "synthetic": True,
        }
    )


@app.get("/api/analytics")
def analytics():
    frame = filtered_data()
    search = request.args.get("search", "").strip().lower()
    if search:
        mask = frame.astype(str).apply(lambda column: column.str.lower().str.contains(search, regex=False)).any(axis=1)
        frame = frame[mask]
    total = int(len(frame))
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError as error:
        raise ValueError("page must be a positive integer.") from error
    start = (page - 1) * TABLE_PAGE_SIZE
    sample_columns = list(frame.columns)
    table = json_records(frame.iloc[start : start + TABLE_PAGE_SIZE][sample_columns])
    return jsonify(
        {
            "total_records": total,
            "page": page,
            "page_size": TABLE_PAGE_SIZE,
            "records": table,
            "severity": group_counts(frame.assign(severity_name=frame["severity"].map(SEVERITY_LABELS)), "severity_name"),
            "by_weather": group_counts(frame, "weather_conditions"),
            "by_road_type": group_counts(frame, "road_type"),
            "by_hour": [
                {"name": int(hour), "count": int(count)}
                for hour, count in frame["hour"].value_counts().sort_index().items()
            ],
            "by_day": group_counts(frame, "day_of_week"),
            "by_area": group_counts(frame, "urban_or_rural"),
            "by_vehicle": group_counts(frame, "vehicle_type"),
            "casualty_total": int(frame["number_of_casualties"].sum()),
        }
    )


@app.post("/api/predict")
def predict():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    features = validate_feature_frame(pd.DataFrame([body]))
    fitted_model = model()
    predicted = int(fitted_model.predict(features)[0])
    probabilities = fitted_model.predict_proba(features)[0]
    classes = fitted_model.named_steps["classifier"].classes_
    return jsonify(
        {
            "severity": predicted,
            "severity_label": SEVERITY_LABELS[predicted],
            "probabilities": [
                {"severity": int(label), "label": SEVERITY_LABELS[int(label)], "probability": float(probability)}
                for label, probability in zip(classes, probabilities)
            ],
            "disclaimer": "Educational prediction only; not an official emergency assessment.",
        }
    )


@app.post("/api/batch-predict")
def batch_predict():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Choose a CSV file to upload."}), 400
    if not uploaded.filename.lower().endswith(".csv"):
        return jsonify({"error": "Only .csv files are accepted."}), 400
    try:
        data = pd.read_csv(uploaded, nrows=MAX_BATCH_ROWS + 1)
    except (pd.errors.ParserError, UnicodeDecodeError) as error:
        return jsonify({"error": f"Could not read CSV: {error}"}), 400
    if len(data) > MAX_BATCH_ROWS:
        return jsonify({"error": f"CSV cannot contain more than {MAX_BATCH_ROWS:,} rows."}), 400
    if data.empty:
        return jsonify({"error": "CSV must contain at least one data row."}), 400
    try:
        features = validate_feature_frame(data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if features.isna().all(axis=1).any():
        return jsonify({"error": "Every row must contain at least one usable prediction feature."}), 400
    fitted_model = model()
    predictions = fitted_model.predict(features)
    probabilities = fitted_model.predict_proba(features)
    result = data.copy()
    result["predicted_severity"] = predictions.astype(int)
    result["predicted_severity_label"] = [SEVERITY_LABELS[int(value)] for value in predictions]
    classes = fitted_model.named_steps["classifier"].classes_
    for index, label in enumerate(classes):
        result[f"probability_{SEVERITY_LABELS[int(label)].lower().replace(' ', '_')}"] = probabilities[:, index]
    return jsonify({"row_count": int(len(result)), "columns": list(result.columns), "records": json_records(result)})


@app.post("/api/regenerate-demo")
def regenerate_demo():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or body.get("confirmation") != "REPLACE SYNTHETIC DATA":
        return jsonify({"error": "Confirmation text did not match."}), 400
    from generate_dataset import generate_dataset, validate_dataset

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = DATASET_PATH.with_name(f"accidents-backup-{timestamp}.csv")
    if DATASET_PATH.exists():
        shutil.copy2(DATASET_PATH, backup_path)
    regenerated = generate_dataset()
    validate_dataset(regenerated)
    regenerated.to_csv(DATASET_PATH, index=False)
    artifact_backups = []
    for artifact in (MODEL_PATH, METRICS_PATH):
        if artifact.exists():
            saved_copy = artifact.with_name(f"{artifact.stem}-backup-{timestamp}{artifact.suffix}")
            shutil.copy2(artifact, saved_copy)
            artifact_backups.append(saved_copy.name)
            artifact.unlink()
    global _dataset_cache, _dataset_mtime, _model_cache
    _dataset_cache = None
    _dataset_mtime = None
    _model_cache = None
    return jsonify(
        {
            "message": "Synthetic demo data regenerated. Train the model again before making predictions.",
            "rows": int(len(regenerated)),
            "dataset_backup": backup_path.name if backup_path.exists() else None,
            "artifact_backups": artifact_backups,
        }
    )


@app.get("/api/model-metrics")
def model_metrics():
    return jsonify(load_metrics())


@app.get("/api/data-summary")
def data_summary():
    frame = dataset()
    return jsonify(
        {
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "column_names": list(frame.columns),
            "missing_values": {key: int(value) for key, value in frame.isna().sum().items()},
            "duplicate_rows": int(frame.duplicated().sum()),
            "severity_distribution": group_counts(
                frame.assign(severity_name=frame["severity"].map(SEVERITY_LABELS)), "severity_name"
            ),
            "sample": json_records(frame.head(10)),
            "synthetic": True,
        }
    )


@app.get("/api/download-dataset")
def download_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError("Dataset is missing. Run `python generate_dataset.py` first.")
    return send_file(DATASET_PATH, mimetype="text/csv", as_attachment=True, download_name="accidents.csv")


@app.get("/api/export-csv")
def export_csv():
    frame = filtered_data()
    search = request.args.get("search", "").strip().lower()
    if search:
        mask = frame.astype(str).apply(
            lambda column: column.str.lower().str.contains(search, regex=False)
        ).any(axis=1)
        frame = frame[mask]
    output = io.StringIO()
    frame.to_csv(output, index=False)
    buffer = io.BytesIO(output.getvalue().encode("utf-8"))
    buffer.seek(0)
    return send_file(buffer, mimetype="text/csv", as_attachment=True, download_name="filtered-accidents.csv")


@app.get("/api/export-report")
def export_report():
    frame = filtered_data()
    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, title="Accident Severity Analytics Summary")
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("Smart Emergency Response & Accident Severity Prediction System", styles["Title"]),
        Spacer(1, 10),
        Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]),
        Paragraph(f"Dataset records in current filter: {len(frame):,}", styles["Normal"]),
        Paragraph(f"Total casualties in current filter: {int(frame['number_of_casualties'].sum()):,}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Severity distribution", styles["Heading2"]),
    ]
    severity_rows = [["Severity", "Records"]]
    counts = frame["severity"].value_counts().sort_index()
    severity_rows.extend([[SEVERITY_LABELS[int(label)], f"{int(count):,}"] for label, count in counts.items()])
    table = Table(severity_rows, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#15354b")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey), ("PADDING", (0, 0), (-1, -1), 7)]))
    elements.extend([table, Spacer(1, 12)])
    if METRICS_PATH.exists():
        metrics = load_metrics()
        elements.append(Paragraph("Held-out model evaluation", styles["Heading2"]))
        elements.append(
            Paragraph(
                f"{metrics['model_name']}: accuracy {metrics['accuracy']:.3f}, macro F1 {metrics['macro_f1']:.3f}, "
                f"weighted F1 {metrics['weighted_f1']:.3f} ({metrics['test_records']:,} test records).",
                styles["Normal"],
            )
        )
    elements.extend(
        [
            Spacer(1, 12),
            Paragraph(
                "This report summarizes a locally generated synthetic dataset for educational demonstration. "
                "It is not official historical accident data, does not establish causation, and is not an emergency assessment.",
                styles["BodyText"],
            ),
        ]
    )
    document.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name="accident-summary-report.pdf")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
