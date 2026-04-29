import json

from alcove_dux.cli import main


def test_scan_writes_alcove_dux_report(tmp_path, capsys):
    suspicious = tmp_path / "suspicious.txt"
    source = tmp_path / "source.txt"
    report = tmp_path / "scan.alcove-dux"
    html_report = tmp_path / "scan.html"
    review_report = tmp_path / "scan-review.html"
    copied = "Alpha beta gamma delta epsilon zeta eta theta iota."
    suspicious.write_text(f"Intro. {copied} Outro.", encoding="utf-8")
    source.write_text(f"Source. {copied} Tail.", encoding="utf-8")

    result = main(
        [
            "scan",
            str(suspicious),
            str(source),
            "--out",
            str(report),
            "--html",
            str(html_report),
            "--review-html",
            str(review_report),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert result == 0
    assert captured.out == ""
    assert payload["matches"]
    assert payload["schema_version"] == 1
    assert payload["matches"][0]["kind"] == "exact_token_sequence"
    assert len(payload["suspicious_document_sha256"]) == 64
    assert len(payload["source_document_sha256"]) == 64
    assert payload["runtime_config"]["embedding_model_id"] == "baai_bge_small_en_v1_5"
    assert "Alcove Dux evidence report" in html_report.read_text(encoding="utf-8")
    assert "<mark>" in review_report.read_text(encoding="utf-8")


def test_catalog_prints_json(capsys):
    result = main(["catalog"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert result == 0
    assert payload["schema_version"] == 1


def test_scan_uses_calibration_profile_threshold(tmp_path):
    suspicious = tmp_path / "suspicious.txt"
    source = tmp_path / "source.txt"
    report = tmp_path / "scan.alcove-dux"
    profile = tmp_path / "profile.json"
    suspicious.write_text("Alpha beta gamma delta zeta", encoding="utf-8")
    source.write_text("Alpha beta gamma delta epsilon", encoding="utf-8")
    profile.write_text(
        json.dumps(
            {
                "dataset_id": "toy",
                "detector_id": "baseline_lexical",
                "selected_threshold": 0.50,
                "selection_metric": "f1",
                "scores": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "scan",
            str(suspicious),
            str(source),
            "--min-score",
            "0.95",
            "--calibration-profile",
            str(profile),
            "--out",
            str(report),
        ]
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert result == 0
    assert payload["matches"]
    assert payload["runtime_config"]["baseline_lexical_threshold"] == 0.50


def test_scan_corpus_writes_report(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "source.txt").write_text(
        "Alpha beta gamma delta epsilon zeta eta theta iota.",
        encoding="utf-8",
    )
    suspicious = tmp_path / "suspicious.txt"
    suspicious.write_text(
        "Intro. Alpha beta gamma delta epsilon zeta eta theta iota. Outro.",
        encoding="utf-8",
    )
    report = tmp_path / "scan.alcove-dux"
    html_report = tmp_path / "scan.html"
    review_report = tmp_path / "scan-review.html"

    result = main(
        [
            "scan-corpus",
            str(suspicious),
            str(corpus),
            "--out",
            str(report),
            "--html",
            str(html_report),
            "--review-html",
            str(review_report),
            "--embedding-model",
            "sentence_transformers_all_minilm_l6_v2",
            "--language",
            "es",
            "--dataset",
            "plagbench",
        ]
    )

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert result == 0
    assert payload["matches"]
    assert payload["source_document_id"] == "corpus:1"
    assert len(payload["source_documents"]) == 1
    assert payload["runtime_config"]["embedding_model_id"] == (
        "sentence_transformers_all_minilm_l6_v2"
    )
    assert payload["runtime_config"]["language"] == "es"
    assert payload["runtime_config"]["enabled_dataset_ids"] == ["plagbench"]
    assert "corpus:1" in html_report.read_text(encoding="utf-8")
    assert "<mark>" in review_report.read_text(encoding="utf-8")
