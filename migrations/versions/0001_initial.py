"""Create user and task tables."""
from alembic import op
import sqlalchemy as sa
revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("email",sa.String(255),nullable=False),sa.Column("hashed_password",sa.String(255),nullable=False),sa.Column("is_active",sa.Boolean(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_users_email","users",["email"],unique=True)
    op.create_table("tasks",sa.Column("id",sa.String(36),primary_key=True),sa.Column("owner_id",sa.Integer(),nullable=False),sa.Column("name",sa.String(160),nullable=False),sa.Column("operation",sa.String(40),nullable=False),sa.Column("input_data",sa.JSON(),nullable=False),sa.Column("result_data",sa.JSON(),nullable=True),sa.Column("status",sa.Enum("PENDING","RUNNING","SUCCESS","FAILURE","RETRY",name="taskstatus"),nullable=False),sa.Column("error_message",sa.Text(),nullable=True),sa.Column("retry_count",sa.Integer(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.Column("started_at",sa.DateTime(timezone=True),nullable=True),sa.Column("finished_at",sa.DateTime(timezone=True),nullable=True),sa.ForeignKeyConstraint(["owner_id"],["users.id"],ondelete="CASCADE"))
    op.create_index("ix_tasks_owner_id","tasks",["owner_id"])
    op.create_index("ix_tasks_status","tasks",["status"])
    op.create_index("ix_tasks_created_at","tasks",["created_at"])
def downgrade():
    op.drop_table("tasks")
    op.drop_index("ix_users_email",table_name="users")
    op.drop_table("users")
