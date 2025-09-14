"""merge_heads

Revision ID: c18de4026f72
Revises: 83f8895b24c2, device_groups_001
Create Date: 2025-08-15 13:23:52.531839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c18de4026f72'
down_revision: Union[str, None] = ('83f8895b24c2', 'device_groups_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
