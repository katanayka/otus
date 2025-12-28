from memc_load import AppsInstalled, parse_appsinstalled


def test_parse_valid_line():
    line = "idfa\tdev-1\t55.5\t42.0\t1,2,3"
    result = parse_appsinstalled(line)
    assert result == AppsInstalled("idfa", "dev-1", 55.5, 42.0, [1, 2, 3])


def test_parse_invalid_apps():
    line = "gaid\tdev-2\t1.0\t2.0\t1,foo,3"
    result = parse_appsinstalled(line)
    assert result.apps == [1, 3]


def test_parse_invalid_coords():
    line = "gaid\tdev-3\tbad\t2.0\t1"
    assert parse_appsinstalled(line) is None


def test_parse_invalid_line():
    assert parse_appsinstalled("broken line") is None
