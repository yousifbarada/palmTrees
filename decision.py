# decision.py
import numpy as np
from collections import Counter

def get_final_decision_with_prob(pest_history, type_history, pest_classes, type_classes):
    results = {}

    for track_id in pest_history.keys():
        # MODEL 1: PEST / DISEASE
        pest_preds = np.array(pest_history[track_id])
        pest_avg = np.mean(pest_preds, axis=0)
        pest_idx_soft = np.argmax(pest_avg)
        pest_label = pest_classes[pest_idx_soft]
        pest_conf = float(pest_avg[pest_idx_soft])

        # MODEL 2: TYPE / SEVERITY
        if track_id in type_history and len(type_history[track_id]) > 0:
            type_preds = np.array(type_history[track_id])
            type_avg = np.mean(type_preds, axis=0)
            type_idx = np.argmax(type_avg)
            type_label = type_classes[type_idx]
            type_conf = float(type_avg[type_idx])
        else:
            type_label = "Unknown"
            type_conf = 0.0

        results[track_id] = {
            "pest": {"label": pest_label, "probability": pest_conf},
            "type": {"label": type_label, "probability": type_conf}
        }

    return results