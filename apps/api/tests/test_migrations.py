from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect


def alembic_config() -> Config:
    api_root = Path(__file__).resolve().parents[1]
    config = Config(api_root / "alembic.ini")
    config.set_main_option("script_location", str(api_root / "migrations"))
    return config


def test_alembic_has_single_head() -> None:
    scripts = ScriptDirectory.from_config(alembic_config())

    assert scripts.get_heads() == ["20260811_0004"]
    assert scripts.get_revision("20260811_0004").down_revision == "20260810_0003"


def test_migrations_upgrade_and_downgrade() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    config = alembic_config()

    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        assert set(inspect(connection).get_table_names()) == {
            "alembic_version",
            "cluster_keywords",
            "clusters",
            "discovery_runs",
            "keyword_analyses",
            "keyword_observations",
            "keywords",
            "monthly_search_volumes",
            "opportunities",
            "product_hypotheses",
            "seeds",
            "workspaces",
        }

        command.downgrade(config, "base")
        assert inspect(connection).get_table_names() == ["alembic_version"]
