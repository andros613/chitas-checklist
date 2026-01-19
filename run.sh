python src/jsonl2html.py data/5786_11_shevat.jsonl.with_tanya.final --title 'Chitas Checklist Shevat 5786' > data/5786_11_shevat.html
python src/html2pdf.py data/5786_11_shevat.html
open data/5786_11_shevat.pdf
