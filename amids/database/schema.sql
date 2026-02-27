-- Core AMIDS schema (SQLite compatible)

create table if not exists campaign_performance_daily (
    id integer primary key autoincrement,
    run_date text not null,
    campaign_id text not null,
    channel text not null,
    region text not null,
    impressions integer not null,
    clicks integer not null,
    spend real not null,
    leads integer not null,
    opportunities integer not null,
    signups integer not null,
    revenue real not null
);

create index if not exists idx_campaign_perf_run_date
    on campaign_performance_daily (run_date);


create table if not exists crm_leads_daily (
    id integer primary key autoincrement,
    run_date text not null,
    segment text not null,
    leads integer not null,
    opportunities integer not null,
    customers integer not null,
    revenue real not null
);


create table if not exists revenue_daily (
    id integer primary key autoincrement,
    run_date text not null,
    channel text not null,
    region text not null,
    revenue real not null
);


create table if not exists kpi_summary_daily (
    id integer primary key autoincrement,
    run_date text not null,
    channel text,
    region text,
    segment text,
    cac real,
    ltv real,
    ltv_cac_ratio real,
    conversion_rate real,
    funnel_dropoff real,
    retention_rate real,
    revenue_growth real,
    channel_roi real,
    campaign_rank integer,
    mom_performance real
);

create index if not exists idx_kpi_run_date
    on kpi_summary_daily (run_date);


create table if not exists anomaly_log (
    id integer primary key autoincrement,
    detected_at text not null default (datetime('now')),
    run_date text not null,
    metric text not null,
    dimension text,
    anomaly_type text not null,
    current_value real,
    expected_value real,
    z_score real,
    details text
);


create table if not exists root_cause_summary (
    id integer primary key autoincrement,
    anomaly_id integer,
    factor_type text not null,
    factor_value text not null,
    impact_score real not null,
    rank integer not null
);


create table if not exists forecast_summary (
    id integer primary key autoincrement,
    created_at text not null default (datetime('now')),
    horizon_weeks integer not null,
    metric text not null,
    scenario text not null,
    forecast text not null
);


create table if not exists execution_log (
    id integer primary key autoincrement,
    started_at text not null default (datetime('now')),
    finished_at text,
    status text not null,
    details text
);

