from alcove_dux.datasets.pairs import parse_plagbench_csv


def test_parse_plagbench_csv():
    examples = parse_plagbench_csv(
        "\n".join(
            [
                "source_doc,susp_doc,label,plagiarism_type,generation,genre",
                "source text,suspicious text,yes,paraphrase,human,essay",
                "other source,other suspicious,no,none,llm,news",
            ]
        )
    )

    assert len(examples) == 2
    assert examples[0].id == "plagbench:0"
    assert examples[0].label is True
    assert examples[0].metadata["plagiarism_type"] == "paraphrase"
    assert examples[1].label is False


def test_parse_plagbench_csv_limit():
    examples = parse_plagbench_csv(
        "\n".join(
            [
                "source_doc,susp_doc,label",
                "a,b,yes",
                "c,d,no",
            ]
        ),
        limit=1,
    )

    assert [example.id for example in examples] == ["plagbench:0"]
