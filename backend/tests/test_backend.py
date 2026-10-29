import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, validate_feature_frame
from config import FEATURE_COLUMNS
from generate_dataset import generate_dataset, validate_dataset


class DatasetTests(unittest.TestCase):
    def test_synthetic_dataset_has_valid_unique_records(self):
        frame = generate_dataset(500)
        validate_dataset(frame)
        self.assertEqual(len(frame), 500)
        self.assertEqual(frame["accident_id"].nunique(), 500)
        self.assertTrue((pd.to_datetime(frame["date"]).dt.day_name() == frame["day_of_week"]).all())
        self.assertTrue(frame["severity"].isin([1, 2, 3, 4]).all())
        self.assertTrue((frame["severity"].value_counts(normalize=True) > 0.1).all())


class ApiValidationTests(unittest.TestCase):
    def test_feature_validation_accepts_expected_inputs(self):
        example = {
            "number_of_vehicles": 2,
            "number_of_casualties": 1,
            "speed_limit": 40,
            "road_type": "Single carriageway",
            "weather_conditions": "Fine",
            "road_surface": "Dry",
            "light_conditions": "Daylight",
            "traffic_density": "Medium",
            "junction_type": "T-junction",
            "urban_or_rural": "Urban",
            "driver_age": 35,
            "vehicle_type": "Car",
            "visibility_km": 15,
            "hour": 14,
            "day_of_week": "Wednesday",
        }
        prepared = validate_feature_frame(pd.DataFrame([example]))
        self.assertEqual(list(prepared.columns), FEATURE_COLUMNS)

    def test_feature_validation_rejects_out_of_range_value(self):
        example = {column: 1 for column in FEATURE_COLUMNS}
        example.update({column: values[0] for column, values in __import__("config").CATEGORY_VALUES.items()})
        example["number_of_vehicles"] = 11
        with self.assertRaisesRegex(ValueError, "number_of_vehicles"):
            validate_feature_frame(pd.DataFrame([example]))

    def test_health_endpoint(self):
        response = app.test_client().get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
