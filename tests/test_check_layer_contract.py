import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_layer_contract():
    spec = importlib.util.spec_from_file_location(
        "check_layer_contract", ROOT / "scripts" / "check_layer_contract.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plant(mod, monkeypatch, tmp_path):
    project = tmp_path / "dbt_project"
    models = project / "models"
    tests = project / "tests"
    scripts = tmp_path / "scripts"
    for d in (models / "3_core", models / "5_marts", tests, scripts, project / "seeds",
              project / "macros", project / "target"):
        d.mkdir(parents=True)
    reader = models / "3_core" / "dim_league.sql"
    reader.write_text("select * from {{ ref('competition_registry') }}", encoding="utf-8")
    (project / "seeds" / "schema.yml").write_text("to: ref('dim_league')", encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "DBT_PROJECT", project)
    monkeypatch.setattr(mod, "DBT_MODELS", models)
    monkeypatch.setattr(mod, "DBT_TESTS", tests)
    monkeypatch.setattr(mod, "SCRIPTS_DIR", scripts)
    monkeypatch.setattr(mod, "REGISTRY_SEED_READER", reader)
    return models, tests, scripts


def _errors(mod):
    errors: list[str] = []
    mod.check_registry_seed_readers(errors)
    return errors


def test_the_repo_has_one_reader_of_the_registry_seed():
    assert _errors(_load_layer_contract()) == []


def test_dim_league_alone_passes(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    _plant(mod, monkeypatch, tmp_path)
    assert _errors(mod) == []


def test_a_mart_reading_the_seed_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models / "5_marts" / "mart_x.sql").write_text(
        "select * from {{ ref( \"competition_registry\" ) }}", encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "mart_x.sql" in errors[0]


def test_a_yml_relationship_to_the_seed_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models / "5_marts" / "marts.yml").write_text(
        "to: ref('competition_registry')", encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "marts.yml" in errors[0]


def test_a_singular_test_reading_the_seed_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    _, tests, _ = _plant(mod, monkeypatch, tmp_path)
    (tests / "assert_x.sql").write_text(
        "select 1 from {{ ref('competition_registry') }}", encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "assert_x.sql" in errors[0]


def test_a_macro_reading_the_seed_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models.parent / "macros" / "m.sql").write_text(
        "{{ ref('competition_registry') }}", encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "m.sql" in errors[0]


def test_a_seed_relationship_test_reading_the_seed_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models.parent / "seeds" / "schema.yml").write_text(
        "to: ref('competition_registry')", encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "schema.yml" in errors[0]


def test_the_two_argument_ref_form_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models / "5_marts" / "mart_y.sql").write_text(
        "select * from {{ ref('football', 'competition_registry') }}", encoding="utf-8"
    )
    assert len(_errors(mod)) == 1


def test_compiled_target_files_are_ignored(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    models, _, _ = _plant(mod, monkeypatch, tmp_path)
    (models.parent / "target" / "compiled.sql").write_text(
        "{{ ref('competition_registry') }}", encoding="utf-8"
    )
    assert _errors(mod) == []


def test_an_export_querying_the_seed_table_fails(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    _, _, scripts = _plant(mod, monkeypatch, tmp_path)
    (scripts / "export_x.py").write_text(
        'SQL = "join `p.dbt_analytics.competition_registry` as r"', encoding="utf-8"
    )
    errors = _errors(mod)
    assert len(errors) == 1 and "export_x.py" in errors[0]


def _export_errors(mod, monkeypatch, tmp_path, source):
    export = tmp_path / "export_site_data.py"
    export.write_text(source, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "EXPORT_SITE_DATA", export)
    errors: list[str] = []
    mod.check_export_reads_marts_only(errors)
    return errors


_MARTS = 'MARTS_DATASET = "marts"\n'


def test_the_repo_export_reads_marts_only():
    errors: list[str] = []
    _load_layer_contract().check_export_reads_marts_only(errors)
    assert errors == []


def test_an_export_reading_marts_passes(monkeypatch, tmp_path):
    source = _MARTS + 'SQL = f"select * from `{GCP_PROJECT}.{MARTS_DATASET}.mart_x`"\n'
    assert _export_errors(_load_layer_contract(), monkeypatch, tmp_path, source) == []


def test_an_export_reading_core_fails(monkeypatch, tmp_path):
    source = _MARTS + 'SQL = f"select * from `{GCP_PROJECT}.core.dim_team`"\n'
    errors = _export_errors(_load_layer_contract(), monkeypatch, tmp_path, source)
    assert len(errors) == 1 and ":2:" in errors[0]


def test_an_export_reading_a_seed_dataset_fails(monkeypatch, tmp_path):
    source = _MARTS + 'SQL = f"join `{GCP_PROJECT}.{SEEDS_DATASET}.confederations`"\n'
    assert len(_export_errors(_load_layer_contract(), monkeypatch, tmp_path, source)) == 1


def test_a_hardcoded_non_mart_table_fails(monkeypatch, tmp_path):
    source = _MARTS + 'SQL = "select * from `football-data-pipeline-gcp.core.dim_team`"\n'
    assert len(_export_errors(_load_layer_contract(), monkeypatch, tmp_path, source)) == 1


def test_a_marts_dataset_pointing_elsewhere_fails(monkeypatch, tmp_path):
    source = 'MARTS_DATASET = "core"\n'
    assert len(_export_errors(_load_layer_contract(), monkeypatch, tmp_path, source)) == 1


def test_naming_the_registry_file_in_an_export_passes(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    _, _, scripts = _plant(mod, monkeypatch, tmp_path)
    (scripts / "export_x.py").write_text(
        'REGISTRY_PATH = "docs/competition_registry.yml"', encoding="utf-8"
    )
    assert _errors(mod) == []


def _aggregate_errors(mod, monkeypatch, tmp_path, relpath, sql):
    project = tmp_path / "dbt_project"
    path = project / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(sql, encoding="utf-8")
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "DBT_PROJECT", project)
    errors: list[str] = []
    mod.check_no_nondeterministic_aggregates(errors)
    return errors


def test_the_repo_has_no_nondeterministic_aggregate():
    errors: list[str] = []
    _load_layer_contract().check_no_nondeterministic_aggregates(errors)
    assert errors == []


@pytest.mark.parametrize("call", ["ANY_VALUE (a)", "any_value(a)", "approx_quantiles(a, 4)"])
@pytest.mark.parametrize("relpath", ["models/5_marts/mart_x.sql", "tests/assert_x.sql",
                                     "macros/m.sql"])
def test_a_banned_aggregate_fails(monkeypatch, tmp_path, call, relpath):
    errors = _aggregate_errors(_load_layer_contract(), monkeypatch, tmp_path, relpath,
                               f"select {call} from t group by b")
    assert len(errors) == 1 and relpath.rsplit("/", 1)[-1] in errors[0]


def test_main_fails_on_a_planted_banned_aggregate(monkeypatch, tmp_path):
    mod = _load_layer_contract()
    project = tmp_path / "dbt_project"
    (project / "models").mkdir(parents=True)
    (project / "models" / "mart_x.sql").write_text("select any_value(a) from t", encoding="utf-8")
    monkeypatch.setattr(mod, "DBT_PROJECT", project)
    assert mod.main() == 1


def test_a_commented_mention_passes(monkeypatch, tmp_path):
    sql = "-- any_value(a) is banned\n{# approx_quantiles(a, 4) #}\nselect min(a) from t"
    assert _aggregate_errors(_load_layer_contract(), monkeypatch, tmp_path,
                             "macros/m.sql", sql) == []


def test_compiled_target_sql_is_ignored(monkeypatch, tmp_path):
    assert _aggregate_errors(_load_layer_contract(), monkeypatch, tmp_path,
                             "target/compiled.sql", "select any_value(a) from t") == []
