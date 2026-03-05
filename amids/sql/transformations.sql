-- Reusable SQL transformations and analytical views for AMIDS.

create view if not exists vw_daily_channel_performance as
select
    c.run_date,
    c.channel,
    c.region,
    sum(c.impressions) as impressions,
    sum(c.clicks) as clicks,
    sum(c.leads) as leads,
    sum(c.signups) as signups,
    sum(c.spend) as spend,
    sum(c.revenue) as revenue,
    case when sum(c.impressions) > 0 then sum(c.clicks) * 1.0 / sum(c.impressions) end as ctr,
    case when sum(c.clicks) > 0 then sum(c.leads) * 1.0 / sum(c.clicks) end as click_to_lead_rate,
    case when sum(c.spend) > 0 then sum(c.revenue) * 1.0 / sum(c.spend) end as roi
from campaign_performance_daily c
group by c.run_date, c.channel, c.region;


create view if not exists vw_revenue_trends as
with daily as (
    select
        run_date,
        sum(revenue) as daily_revenue
    from campaign_performance_daily
    group by run_date
)
select
    run_date,
    daily_revenue,
    avg(daily_revenue) over (
        order by run_date
        rows between 6 preceding and current row
    ) as revenue_ma7,
    lag(daily_revenue) over (order by run_date) as prev_day_revenue
from daily;


create view if not exists vw_risk_score_distribution as
with channel_day as (
    select
        c.run_date,
        c.channel,
        c.region,
        sum(c.spend) as spend,
        sum(c.revenue) as revenue,
        sum(c.leads) as leads,
        sum(c.signups) as signups,
        case when sum(c.leads) > 0 then sum(c.spend) * 1.0 / sum(c.leads) end as cac,
        case when sum(c.signups) > 0 then sum(c.revenue) * 1.0 / sum(c.signups) end as ltv
    from campaign_performance_daily c
    group by c.run_date, c.channel, c.region
),
scored as (
    select
        run_date,
        channel,
        region,
        min(100.0, (coalesce(cac, 0.0) / (coalesce(ltv, 1.0) + 1.0)) * 120.0) as risk_score
    from channel_day
)
select
    run_date,
    case
        when risk_score < 35 then 'low'
        when risk_score < 70 then 'medium'
        else 'high'
    end as risk_band,
    count(*) as segment_count,
    avg(risk_score) as avg_risk_score
from scored
group by run_date, risk_band;
