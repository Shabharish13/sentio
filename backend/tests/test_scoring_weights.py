from app.scoring.weights import (
    load_business_model,
    load_geography,
    load_headcount_bands,
    load_industry,
    load_thresholds,
    load_titles,
)


def test_thresholds_loaded_sorted_desc():
    assert load_thresholds() == [("A", 60), ("B", 30), ("C", 0)]


def test_headcount_bands_loaded():
    bands = load_headcount_bands()
    assert (100, 300, 25) in bands
    assert (51, 99, 10) in bands
    assert len(bands) == 4


def test_industry_map_loaded():
    table = load_industry()
    assert table[("computer software", "")] == 20
    assert table[("financial services", "saas")] == 15
    assert table[("financial services", "nonsaas")] == 5


def test_titles_sorted_by_priority_with_stakeholder():
    rows = load_titles()
    assert rows[0][0] == 1
    assert rows[0][2] == 20
    assert rows[0][3] == "champion"
    assert "vp of customer success" in rows[0][1]


def test_geography_and_business_model_loaded():
    assert load_geography()["united states"] == 15
    assert load_business_model()["b2b"] == 10
    assert load_business_model()["saas"] == 5
