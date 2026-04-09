y  := 5786
m  := 02_iyar
mc := Iyar
n  := $(y)_$(m)

JSONL_RAW   := data/$(n).jsonl.raw
JSONL       := data/$(n).jsonl
HTML        := data/$(n).html
PDF         := data/$(n).pdf
TANYA_DONE  := data/.$(n).tanya_done
RAMBAM_DONE := data/.$(n).rambam_done

HTM_FILES := $(wildcard data/*.htm)

.PHONY: all open

all: $(PDF)

$(JSONL_RAW): $(HTM_FILES)
	./src/parse_month.sh $(mc) $@

$(JSONL): $(JSONL_RAW)
	cp $< $@

$(TANYA_DONE): $(JSONL)
	python src/add_tanya.py $(JSONL)
	touch $@

$(RAMBAM_DONE): $(JSONL)
	python src/add_rambam.py $(JSONL)
	touch $@

$(HTML): $(TANYA_DONE) $(RAMBAM_DONE)
	python src/jsonl2html.py $(JSONL) --title "Chitas Checklist $(mc) $(y)" > $@

$(PDF): $(HTML)
	DYLD_LIBRARY_PATH=/opt/homebrew/lib python src/html2pdf.py $(HTML)

open: $(PDF)
	open $(PDF)
