PYTHON ?= python3

.PHONY: help generate generate-ghcr validate test doctor export package build-dry-run clean

help:
	@echo "Vietnam Hosting — Universal Pterodactyl Egg System"
	@echo "  make generate       Generate all 147 Eggs, Dockerfiles, catalog.json, compatibility.json"
	@echo "  make generate-ghcr  Regenerate Egg JSONs targeting published ghcr.io/vietnam-hosting/yolks"
	@echo "  make validate       Run strict PTDL_v2 schema, script, and Dockerfile validation"
	@echo "  make test           Run automated unittest suite & generate test report"
	@echo "  make doctor         Inspect local tooling and repository health"
	@echo "  make export         Export import-ready PTDL_v2 JSON files to dist/eggs/"
	@echo "  make package        Build dist/vietnam-hosting-universal-eggs.zip + SHA256"
	@echo "  make build-dry-run  Preview multi-arch Docker Buildx commands"

generate:
	$(PYTHON) -m generator generate

generate-ghcr:
	$(PYTHON) -m generator generate --registry ghcr

validate:
	$(PYTHON) -m generator validate --strict

test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m generator test --report dist/test-report.json

doctor:
	$(PYTHON) -m generator doctor

export:
	$(PYTHON) -m generator export --output dist/eggs

package: validate export
	$(PYTHON) -m generator package --output dist/vietnam-hosting-universal-eggs.zip

build-dry-run:
	$(PYTHON) -m generator build --dry-run

clean:
	rm -rf dist/eggs dist/vietnam-hosting-universal-eggs.zip dist/vietnam-hosting-universal-eggs.zip.sha256 dist/package-manifest.json
