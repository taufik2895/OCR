import re


class ValidationService:
    def validate(self, text: str) -> list[str]:
        warnings: list[str] = []
        if not text.strip():
            warnings.append("No text was extracted")
        if "\ufffd" in text:
            warnings.append("Invalid replacement characters detected")
        unusual = re.findall(r"[^\w\s.,:;!?@%/()\-]", text, flags=re.UNICODE)
        if len(unusual) > max(5, len(text) * 0.1):
            warnings.append("Unusually high number of special characters")
        return warnings
