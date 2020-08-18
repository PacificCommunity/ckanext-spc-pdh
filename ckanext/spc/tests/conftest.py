import pytest

from alembic import command
from alembic.config import Config

from ckan.cli.db import _resolve_alembic_config
from ckan.tests.pytest_ckan.fixtures import with_request_context


@pytest.fixture
def clean_db(reset_db, ckan_config):
    reset_db()
    alembic_ini = _resolve_alembic_config("spc")

    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_section_option(
        "alembic", "sqlalchemy.url", ckan_config.get("sqlalchemy.url")
    )

    command.upgrade(alembic_cfg, "head")
