from sqlalchemy import (
    NVARCHAR, create_engine, MetaData, Table, Column, Integer, String, Text, ForeignKey, DateTime, func, Index
)
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv
import logging
from sqlalchemy.types import Enum

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details
host = os.getenv('HOST')
port = os.getenv('PORT', '1433')
database = os.getenv('DATABASE')
user = os.getenv('USER')
password = os.getenv('PASSWORD')
password = quote_plus(password)  # Secure password encoding

# Database URL for MSSQL
DATABASE_URL = f"mssql+pyodbc://{user}:{password}@{host},{port}/{database}?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

# Initialize database connection
engine = create_engine(DATABASE_URL, echo=True)  # Echo flag to show queries

metadata = MetaData()

master_projects = Table(
    "Master_Projects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Index('ix_projects_name', 'name'),  # Index for performance
)


# Clusters table
clusters = Table(
    "Clusters",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Column("teleration", NVARCHAR(None), server_default="'No nodeselector'"),
    Column("nodeselector", NVARCHAR(None), server_default="'{}'")
)

# Clusters table
Dep_config = Table(
    "Dep_config",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("deployment_id", Integer, ForeignKey(
        "Deployments.id", ondelete="CASCADE"), nullable=False),
    Column("config_key", String(255), nullable=False),
    Column("config_value", Text, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
)


# Projects table
projects = Table(
    "Projects",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Column("project_id", Integer, ForeignKey(
        "Master_Projects.id", ondelete="CASCADE"), nullable=False),
    Index('ix_projects_name', 'name'),  # Index for performance
)

# Repositories table
repositories = Table(
    "Repositories",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("project_id", Integer, ForeignKey(
        "Projects.id", ondelete="CASCADE"), nullable=False),
    Column("deployment_id", Integer, ForeignKey(
        "Deployments.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Index('ix_repositories_project_id', 'project_id'),  # Index for foreign key
    Index('ix_repositories_deployment_id',
          'deployment_id'),  # Index for foreign key
)

# Branches table
branches = Table(
    "Branches",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("repository_id", Integer, ForeignKey(
        "Repositories.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    # Index for foreign key
    Index('ix_branches_repository_id', 'repository_id'),
    Column("namespace_id", Integer, ForeignKey(
        "Namespaces.id", ondelete="CASCADE"), nullable=False),

)

# Namespaces table
namespaces = Table(
    "Namespaces",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("cluster_id", Integer, ForeignKey(
        "Clusters.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Column("registry", String(255), nullable=True),
    Column("nodeselector", NVARCHAR(None)),
    Column("toleration", NVARCHAR(None)),
    Index('ix_namespaces_cluster_id', 'cluster_id'),  # Index for foreign key
)

user_namespace_subscriptions = Table(
    "UserNamespaceSubscriptions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("Users.id", ondelete="CASCADE"), nullable=False),
    Column("namespace_id", Integer, ForeignKey("Namespaces.id", ondelete="CASCADE"), nullable=False),
    Column("subscription_date", DateTime, server_default=func.getdate()),  # Default to current timestamp
    Index("ix_user_namespace", "user_id", "namespace_id", unique=True)  # Unique constraint for user-namespace pairs
)

# Deployments table
deployments = Table(
    "Deployments",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("namespace_id", Integer, ForeignKey(
        "Namespaces.id", ondelete="CASCADE"), nullable=False),
    Column("application_name", String(255), nullable=False),
    Column("description", String(255), nullable=False),
    Column("image", String(255), nullable=True),
    Column("replica_count", Integer, nullable=False, default=1),
    Column("replica_number", Integer, nullable=False, default=1),
    Column("container_port", Integer, nullable=False),
    Column("limit_cpu", String(50), nullable=True),
    Column("limit_memory", String(50), nullable=True),
    Column("config_map_name", String(50), nullable=True),
    Column("request_cpu", String(50), nullable=True),
    Column("request_memory", String(50), nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    Column("seperate_cofig", String(250), nullable=True),
    Column("managed_indentity", String(250), nullable=True),
    # Index for foreign key
    Index('ix_deployments_namespace_id', 'namespace_id'),
)

serviceaccounts = Table(
    "serviceaccounts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
)

service_account_subscriptions = Table(
    "service_account_subscriptions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("namespace_id", Integer, ForeignKey(
        "Namespaces.id", ondelete="CASCADE"), nullable=False),
    Column("service_account_id",Integer, ForeignKey(
        "serviceaccounts.id", ondelete="CASCADE"), nullable=False),
)

# Services table
services = Table(
    "Services",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("deployment_id", Integer, ForeignKey(
        "Deployments.id", ondelete="CASCADE"), nullable=False),
    Column("service_name", String(255), nullable=False),
    Column("application_name", String(255), nullable=False),
    Column("port", Integer, nullable=False),
    Column("target_port", Integer, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    # Index for foreign key
    Index('ix_services_deployment_id', 'deployment_id'),
)

# ConfigMaps table
config_maps = Table(
    "ConfigMaps",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("namespace_id", Integer, ForeignKey(
        "Namespaces.id", ondelete="CASCADE"), nullable=False),
    Column("config_key", String(255), nullable=False),
    Column("config_value", Text, nullable=False),
    Column("description", Text, nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate()),
    # Index for foreign key
    Index('ix_config_maps_namespace_id', 'namespace_id'),
)

pipelines = Table(
    "Pipelines",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(255), nullable=False),
    Column("project_id", Integer, ForeignKey(
        "Projects.id", ondelete="CASCADE")),
    Column("status", String(50), nullable=False),
    # Git event that triggers the pipeline
    Column("trigger_event", String(255), nullable=True),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate())
)

users = Table(
    "Users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(255), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("role", Enum("user", "admin", name="user_roles"),
           nullable=False, server_default="user"),
    Column("created_at", DateTime, server_default=func.getdate()),
    Column("updated_at", DateTime, onupdate=func.getdate())
)

try:
    engine = create_engine(DATABASE_URL, echo=True)
    logger.info("Database connection successful.")
except Exception as e:
    logger.error(f"Database connection failed: {e}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get the database session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
