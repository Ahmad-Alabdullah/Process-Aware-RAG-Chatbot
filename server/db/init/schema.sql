create schema if not exists ragrun;

create table if not exists ragrun.eval_runs (
  id bigserial primary key,
  name text not null unique,
  created_at timestamptz not null default now(),
  config_json jsonb not null,
  notes text,
  git_sha text
);

create table if not exists ragrun.queries (
  id bigserial primary key,
  dataset_name text not null,
  query_id text not null,
  text text not null,
  process_name text,
  process_id text,
  roles text[],
  current_node_id text,
  definition_id text,
  query_type text not null default 'mixed',
  expected_source text not null default 'both',
  unique (dataset_name, query_id)
);

create table if not exists ragrun.gold_evidence (
  id bigserial primary key,
  query_pk bigint not null references ragrun.queries(id) on delete cascade,
  chunk_id text not null,
  document_id text,
  relevance smallint not null default 1,
  qrels_version text not null default '1800',
  unique (query_pk, chunk_id, qrels_version)
);

create table if not exists ragrun.gold_gating (
  query_pk bigint primary key references ragrun.queries(id) on delete cascade,
  expected_lane_ids text[] not null default '{}',
  expected_node_ids text[] not null default '{}',
  expected_lane_names text[] not null default '{}',
  expected_task_names text[] not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists ragrun.gold_answers (
  query_pk bigint primary key references ragrun.queries(id) on delete cascade,
  answers jsonb not null,
  explanation text
);

create table if not exists ragrun.eval_run_items (
  run_id bigint not null references ragrun.eval_runs(id) on delete cascade,
  query_pk bigint not null references ragrun.queries(id) on delete cascade,
  status text not null default 'ok',
  request_json jsonb,
  response_json jsonb,
  answer_text text,
  citations jsonb,
  latency_ms integer,
  token_in integer,
  token_out integer,
  confidence double precision,
  whitelist_violation boolean,
  decision text,
  meta jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  primary key (run_id, query_pk)
);

create table if not exists ragrun.retrieval_logs (
  run_id bigint not null references ragrun.eval_runs(id) on delete cascade,
  query_pk bigint not null references ragrun.queries(id) on delete cascade,
  rank int not null,
  source text not null, -- bm25/dense/rrf/ce
  chunk_id text not null,
  document_id text,
  score double precision,
  meta jsonb,
  primary key (run_id, query_pk, rank, source)
);

create index if not exists ix_retrieval_logs_run_query on ragrun.retrieval_logs(run_id, query_pk, rank);

create table if not exists ragrun.scores (
  run_id bigint not null references ragrun.eval_runs(id) on delete cascade,
  query_pk bigint not null references ragrun.queries(id) on delete cascade,
  metric text not null,
  value double precision not null,
  details jsonb,
  primary key (run_id, query_pk, metric)
);

create table if not exists ragrun.aggregates (
  run_id bigint not null references ragrun.eval_runs(id) on delete cascade,
  metric text not null,
  value double precision not null,
  ci_low double precision,
  ci_high double precision,
  n int,
  primary key (run_id, metric)
);