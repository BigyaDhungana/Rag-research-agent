"""add gin index for full text search

Revision ID: 6102ee8d7d55
Revises: 5a91bd2dbc77
Create Date: 2026-08-27 05:28:58.530851

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "6102ee8d7d55"
down_revision: Union[str, None] = "5a91bd2dbc77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the functional GIN index on the to_tsvector expression
    op.execute("""
        CREATE INDEX idx_document_chunks_content_fts 
        ON document_chunks 
        USING gin (to_tsvector('english', content));
        """)


def downgrade() -> None:
    # Drop the index if we need to rollback
    op.execute("""
        DROP INDEX idx_document_chunks_content_fts;
        """)
