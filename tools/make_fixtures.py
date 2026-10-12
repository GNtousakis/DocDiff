"""Regenerate docdiff/fixtures/*.json (synthetic OCR results used by the stub engine and tests)."""
import json
from pathlib import Path

from docdiff.ocr.synthetic import combine, paragraph_lines, table

OUT = Path(__file__).resolve().parent.parent / "docdiff" / "fixtures"
COLS = [20.0, 260.0, 460.0]

GREEK = [
    "Η εταιρεία δηλώνει ότι θα παραδώσει τα",
    "προϊόντα εντός τριάντα ημερών από την",
    "υπογραφή της σύμβασης.",
    "Η πληρωμή θα γίνει σε δύο δόσεις.",
]
ENGLISH = [
    "The company declares that it will deliver the",
    "products within thirty days of signing",
    "the agreement.",
    "Payment will be made in two instalments.",
]
MIXED = [
    "Το λογισμικό DocDiff συγκρίνει δύο έγγραφα",
    "και επισημαίνει τις διαφορές, όπως το PDF",
    "ή το Word document, γρήγορα.",
]
TABLE_V1 = [["Είδος", "Ποσότητα", "Τιμή"], ["Μήλα", "10", "1,20"], ["Αχλάδια", "5", "2,00"], ["Πορτοκάλια", "8", "1,50"]]
TABLE_V2 = [["Είδος", "Ποσότητα", "Τιμή"], ["Μήλα", "12", "1,20"], ["Αχλάδια", "5", "2,00"], ["Πορτοκάλια", "8", "1,80"]]


def dump(name: str, result, language: str) -> None:
    data = {
        "language": language,
        "lines": [
            {"text": ln.text, "words": [{"text": w.text, "x": w.x, "y": w.y, "w": w.width, "h": w.height} for w in ln.words]}
            for ln in result.lines
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    dump("greek", paragraph_lines(GREEK), "el")
    dump("english", paragraph_lines(ENGLISH), "en")
    dump("mixed", paragraph_lines(MIXED), "el")
    dump("table_v1", table(TABLE_V1, COLS), "el")
    dump("table_v2", table(TABLE_V2, COLS), "el")
    dump("mixed_page", combine(paragraph_lines(GREEK[:3]), table(TABLE_V1, COLS), paragraph_lines(ENGLISH[:3])), "el")
