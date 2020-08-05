import ckanext.spc.utils as utils


def test_normalize_res():
    original = dict(name="a", description="b", format="c", size=1, url="d")
    expected = dict(
        title="a", description="b", format="c", byteSize=1, accessURL="d"
    )

    assert expected == utils._normalize_res(original)


def test_normalize_to_dcat():
    pkg = dict(
        id="a",
        notes="b",
        name="c",
        tags=[dict(name="x"), dict(name="y")],
        frequency="d",
        metadata_created="e",
        metadata_modified="f",
    )
    expected = dict(
        identifier="a",
        description="b",
        landingPage="http://test.ckan.net/dataset/c",
        keyword=["x", "y"],
        accrualPeriodicity="d",
        issued="e",
        modified="f",
        contactPoint="",
        publisher={"name": "", "mbox": ""},
        distribution=[],
        temporal=[None, None],
        name="c",
    )

    assert expected == utils.normalize_to_dcat(pkg)


def test_normalize_search_query():
    assert "a a" == utils._normalize_search_query("A A")
    assert "a a" == utils._normalize_search_query("a a")
    assert "a a" == utils._normalize_search_query("      a            A    ")
