import fitz # PyMuPDF

def analyze_pdf(filepath, outpath):
    doc = fitz.open(filepath)
    with open(outpath, "w", encoding="utf-8") as f:
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for b in blocks:
                if "lines" in b:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            text = s["text"].strip()
                            if text:
                                f.write(f"Page {page_num+1} | Font: {s['font']} | Size: {round(s['size'], 1)} | Text: {text[:80]}\n")

if __name__ == "__main__":
    analyze_pdf("data/ct200_manual.pdf", "pdf_analysis.txt")
