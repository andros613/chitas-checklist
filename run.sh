y="5786"
m="12_adar"
mc="Adar"
n=${y}_${m}

./src/parse_month.sh $mc data/$n.jsonl.raw

cp data/$n.jsonl.raw data/$n.jsonl
python src/add_tanya.py data/$n.jsonl
python src/add_rambam.py data/$n.jsonl

exit 1

python src/jsonl2html.py data/$n.jsonl --title "Chitas Checklist $mc $y" > data/$n.html
python src/html2pdf.py data/$n.html
open data/$n.pdf
