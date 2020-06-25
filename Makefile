
TODAY ?= $(shell date --iso --utc)
CORDDATE ?= $(TODAY)
SHELL = /bin/bash
.SHELLFLAGS = -o pipefail -c

.PHONY: help
help: ## Print info about all commands
	@echo "Commands:"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[01;32m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: test
test: ## Run all tests and lints
	pipenv run pytest

.PHONY: dev 
dev: ## Run web interface locally
	pipenv run ./covid19_tool.py webface --debug

.PHONY: update-i18n
update-i18n: ## Re-extract and re-compile translation files
	pipenv run pybabel update -i extra/i18n/web_interface.pot -d fatcat_covid19/translations
	pipenv run pybabel compile -d fatcat_covid19/translations

metadata/$(CORDDATE)/cord19.csv:
	mkdir -p metadata/$(CORDDATE)
	@#wget -c "https://archive.org/download/s2-cord19-dataset/cord19.$(CORDDATE).csv" -O /tmp/cord19.$(CORDDATE).csv
	wget -c "https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/$(CORDDATE)/metadata.csv" -O /tmp/cord19.$(CORDDATE).csv
	mv /tmp/cord19.$(CORDDATE).csv $@

metadata/$(CORDDATE)/cord19.json: metadata/$(CORDDATE)/cord19.csv
	pipenv run ./covid19_tool.py parse-cord19 metadata/$(CORDDATE)/cord19.csv > $@.wip
	mv $@.wip $@

metadata/$(CORDDATE)/cord19.enrich.json: metadata/$(CORDDATE)/cord19.json
	cat metadata/$(CORDDATE)/cord19.json | pipenv run parallel -j10 --linebuffer --round-robin --pipe ./covid19_tool.py enrich-fatcat - | pv -l > $@.wip
	mv $@.wip $@

metadata/$(CORDDATE)/cord19.missing.json: metadata/$(CORDDATE)/cord19.enrich.json
	cat metadata/$(CORDDATE)/cord.enrich.json | jq 'select(.release_id == null) | .cord19_paper' -c > $@.wip
	mv $@.wip $@

metadata/$(TODAY)/fatcat_hits.enrich.json:
	mkdir -p metadata/$(TODAY)
	pipenv run ./covid19_tool.py query-fatcat | pv -l > $@.wip
	mv $@.wip $@

metadata/$(TODAY)/combined.enrich.json: metadata/$(CORDDATE)/cord19.enrich.json metadata/$(TODAY)/fatcat_hits.enrich.json
	cat metadata/$(TODAY)/fatcat_hits.enrich.json metadata/$(CORDDATE)/cord19.enrich.json| pipenv run ./covid19_tool.py dedupe | pv -l > $@.wip
	mv $@.wip $@

metadata/$(TODAY)/fatcat_web.log: metadata/$(TODAY)/combined.enrich.json
	cat metadata/$(TODAY)/combined.enrich.json | jq .fatcat_release -c | pipenv run parallel -j20 --linebuffer --round-robin --pipe ./bin/deliver_file2disk.py --disk-dir fulltext_web - | pv -l > $@.wip
	mv $@.wip $@

metadata/$(TODAY)/derivatives.stamp: metadata/$(TODAY)/fatcat_web.log
	pipenv run ./bin/make_dir_derivatives.sh fulltext_web
	touch $@

metadata/$(TODAY)/combined.fulltext.json: metadata/$(TODAY)/derivatives.stamp metadata/$(TODAY)/combined.enrich.json
	pipenv run ./covid19_tool.py enrich-derivatives metadata/$(TODAY)/combined.enrich.json --base-dir fulltext_web/ | pv -l > $@.wip
	mv $@.wip $@

.PHONY: corpus
corpus: metadata/$(TODAY)/combined.fulltext.json ## Run ingest, resulting in combined fulltext JSON corpus on disk
	@echo "Successfully built corpus for date (UTC): $(TODAY)"

.PHONY: create-es-index
create-es-index:
	http put :9200/covid19_fatcat_fulltext < schema/fulltext_schema.v00.json

.PHONY: load-es
load-es: metadata/$(TODAY)/combined.fulltext.json ## Push current corpus into elasticsearch index
	pipenv run ./covid19_tool.py transform-es metadata/$(TODAY)/combined.fulltext.json | pv -l | esbulk -verbose -size 1000 -id fatcat_ident -w 8 -index covid19_fatcat_fulltext -type release

.PHONY: daily-update
daily-update: load-es  ## Command to run every day: fetch corpus, load to elasticsearch

