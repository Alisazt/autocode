-- Simplified schema for CrewAI AutoDev prototype

CREATE TYPE execution_status AS ENUM (
    'queued', 'planning', 'architecture', 'architecture_review',
    'development', 'testing', 'release_review', 'deploying',
    'completed', 'failed', 'cancelled'
);

CREATE TYPE job_status AS ENUM (
    'queued', 'running', 'succeeded', 'failed', 'retrying'
);

CREATE TYPE hitl_status AS ENUM (
    'pending', 'approved', 'rejected', 'timeout', 'rework'
);

CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    status execution_status NOT NULL DEFAULT 'queued',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    team_config TEXT NOT NULL CHECK (team_config IN ('full', 'compact')),
    template_id TEXT
);

CREATE TABLE execution_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    task_id TEXT NOT NULL,
    agent TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    status job_status NOT NULL DEFAULT 'queued',
    attempts INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 2,
    timeout_sec INTEGER DEFAULT 900,
    cost_budget_usd DECIMAL(8,3) DEFAULT 0.5,
    model TEXT DEFAULT 'gpt-4o-mini',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd DECIMAL(8,3) DEFAULT 0,
    CONSTRAINT unique_idempotency_key UNIQUE (idempotency_key),
    CONSTRAINT unique_task_per_execution UNIQUE (execution_id, task_id)
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    content_type TEXT NOT NULL,
    storage_url TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    checksum TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    parent_version INTEGER,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated BOOLEAN DEFAULT FALSE,
    validation_schema TEXT,
    CONSTRAINT unique_artifact_version UNIQUE (execution_id, path, version)
);

CREATE TABLE hitl_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('architecture_review', 'code_review', 'release_approval')),
    status hitl_status NOT NULL DEFAULT 'pending',
    reviewer_id UUID,
    reason TEXT,
    due_at TIMESTAMPTZ NOT NULL,
    approved_at TIMESTAMPTZ,
    artifact_ids JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_pending_hitl UNIQUE (execution_id, type) WHERE status = 'pending'
);

-- Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_executions_project_status ON executions(project_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_execution_status ON execution_jobs(execution_id, status);
CREATE INDEX IF NOT EXISTS idx_artifacts_execution_path ON artifacts(execution_id, path);
CREATE INDEX IF NOT EXISTS idx_hitl_due_at ON hitl_checkpoints(due_at) WHERE status = 'pending';
