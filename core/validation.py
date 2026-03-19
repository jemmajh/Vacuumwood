from typing import Dict, List

def validate_inputs(
    shares: Dict[str, float],
    floors: int,
    discount_rate: float,
    year1_eff: float,
    eff_gain: float,
    years: int,
) -> List[str]:
    errors = []

    s = sum(shares.values())
    if abs(s - 1.0) > 1e-6:
        errors.append(f"Crop shares must sum to 100%. Currently: {s*100:.2f}%")

    if floors < 1:
        errors.append("Floors must be at least 1.")

    if not (0.0 <= discount_rate <= 1.0):
        errors.append("Discount rate must be between 0 and 1.")

    if not (0.0 <= year1_eff <= 1.0):
        errors.append("Year 1 efficiency must be between 0 and 1.")

    if eff_gain < 0:
        errors.append("Annual efficiency gain cannot be negative.")

    if years < 1:
        errors.append("Forecast years must be at least 1.")

    return errors