"""Add permission management tables

Revision ID: xxx
Revises: yyy
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'xxx'
down_revision = 'yyy'
branch_labels = None
depends_on = None

def upgrade():
    # Crear enum para recursos de permisos
    op.execute("""
        CREATE TYPE permissionresource AS ENUM (
            'user', 'user_profile', 'department', 'strategic_plan',
            'strategic_axis', 'strategic_objective', 'diagnostic_analysis',
            'poa', 'activity', 'task', 'resource', 'kpi', 'kpi_measurement',
            'kpi_alert', 'report', 'report_template', 'system_setting',
            'audit_log', 'notification'
        )
    """)
    
    # Crear enum para acciones de permisos
    op.execute("""
        CREATE TYPE permissionaction AS ENUM (
            'create', 'read', 'update', 'delete', 'approve',
            'export', 'import', 'manage', 'view', 'execute'
        )
    """)
    
    # Crear enum para ámbitos de permisos
    op.execute("""
        CREATE TYPE permissionscope AS ENUM (
            'system', 'department', 'project', 'personal'
        )
    """)
    
    # Crear tabla custom_permissions
    op.create_table('custom_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        
        # Identificación
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Definición del permiso
        sa.Column('resource', sa.Enum('user', 'user_profile', 'department', 'strategic_plan',
                                     'strategic_axis', 'strategic_objective', 'diagnostic_analysis',
                                     'poa', 'activity', 'task', 'resource', 'kpi', 'kpi_measurement',
                                     'kpi_alert', 'report', 'report_template', 'system_setting',
                                     'audit_log', 'notification',
                                     name='permissionresource'), nullable=False),
        sa.Column('action', sa.Enum('create', 'read', 'update', 'delete', 'approve',
                                   'export', 'import', 'manage', 'view', 'execute',
                                   name='permissionaction'), nullable=False),
        sa.Column('scope', sa.Enum('system', 'department', 'project', 'personal',
                                  name='permissionscope'), nullable=False),
        
        # Control
        sa.Column('is_system', sa.Boolean(), nullable=False),
        
        # Metadata
        sa.Column('module', sa.String(length=100), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Crear índices para custom_permissions
    op.create_index(op.f('ix_custom_permissions_code'), 'custom_permissions', ['code'], unique=True)
    op.create_index(op.f('ix_custom_permissions_name'), 'custom_permissions', ['name'], unique=True)
    op.create_index(op.f('ix_custom_permissions_id'), 'custom_permissions', ['id'], unique=False)
    
    # Crear tabla role_permissions
    op.create_table('role_permissions',
        sa.Column('role', sa.Enum('super_admin', 'admin', 'strategic_manager', 
                                 'department_manager', 'team_leader', 'collaborator', 
                                 'viewer', name='userrole'), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.ForeignKeyConstraint(['permission_id'], ['custom_permissions.id'], ),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('role', 'permission_id')
    )
    
    # Crear tabla user_custom_permissions
    op.create_table('user_custom_permissions',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['permission_id'], ['custom_permissions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'permission_id')
    )
    
    # Crear tabla department_custom_permissions
    op.create_table('department_custom_permissions',
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.ForeignKeyConstraint(['permission_id'], ['custom_permissions.id'], ),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('department_id', 'permission_id')
    )
    

def downgrade():
    op.drop_table('department_custom_permissions')
    op.drop_table('user_custom_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index(op.f('ix_custom_permissions_id'), table_name='custom_permissions')
    op.drop_index(op.f('ix_custom_permissions_name'), table_name='custom_permissions')
    op.drop_index(op.f('ix_custom_permissions_code'), table_name='custom_permissions')
    op.drop_table('custom_permissions')
    
    op.execute('DROP TYPE permissionresource')
    op.execute('DROP TYPE permissionaction')
    op.execute('DROP TYPE permissionscope')
