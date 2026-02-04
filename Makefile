.PHONY: install synth diff deploy destroy start test clean

PYTHON = python
CDK    = $(PYTHON) -m aws_cdk

# ── 의존성 설치 ───────────────────────────────────────────────
install:
	pip install -r requirements.txt
	pip install -r infrastructure/requirements.txt
	pip install pytest pyyaml boto3 --quiet

# ── CDK 명령 ─────────────────────────────────────────────────
synth:
	cd infrastructure && $(CDK) synth

diff:
	cd infrastructure && $(CDK) diff

deploy:
	cd infrastructure && $(CDK) deploy --require-approval false

destroy:
	cd infrastructure && $(CDK) destroy

# ── 파이프라인 수동 실행 ──────────────────────────────────────
start:
	$(PYTHON) scripts/start_pipeline.py --config config/book_config.yaml

start-dry:
	$(PYTHON) scripts/start_pipeline.py --config config/book_config.yaml --dry-run

# ── 테스트 ───────────────────────────────────────────────────
test:
	pytest tests/ -v

# ── 정리 ─────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>NUL; true
	find . -name "*.pyc" -delete 2>NUL; true
	rm -rf infrastructure/cdk.out
