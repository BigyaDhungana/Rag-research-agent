"""add gin index for code_chunks

Revision ID: 8b1dc0a8cb59
Revises: 30dcf1494ae4
Create Date: 2026-08-31 01:50:56.563759

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8b1dc0a8cb59"
down_revision: Union[str, None] = "30dcf1494ae4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        "CREATE INDEX idx_code_chunks_content_fts ON code_chunks USING gin (to_tsvector('english', content))"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_code_chunks_content_fts")
