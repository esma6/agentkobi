"""
Alembic migration ortamı.

Bizim Alembic kurulumumuzun özelliği: app modellerimiz SQLAlchemy 2.0
async kullanıyor ama Alembic migration'lar senkron çalışır. Bu yüzden:
- DATABASE_URL_SYNC kullanırız (psycopg2 sürücüsü).
- target_metadata olarak modellerimizin Base.metadata'sını veririz.
- autogenerate destekli — şema değişikliğinde otomatik diff alır.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Uygulamanın config'i ve Base'i
from app.core.config import settings
from app.models.base import Base
# ÖNEMLİ: tüm modelleri import ediyoruz; autogenerate metadata'yı bu sayede görür.
from app.models import orm  # noqa: F401

config = context.config

# alembic.ini içindeki sqlalchemy.url'i Python'dan override ediyoruz.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """SQL üretip dosyaya yazmak için (online connection kurmaz)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online: gerçek bir veritabanı bağlantısı üzerinden çalışır."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # tip değişikliklerini de yakala
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
