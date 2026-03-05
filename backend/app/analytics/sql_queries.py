REVENUE_TREND_QUERY = """
with daily as (
    select
        c.run_date,
        sum(c.revenue) as revenue,
        sum(c.spend) as spend,
        sum(c.clicks) as clicks,
        sum(c.impressions) as impressions
    from campaign_performance_daily c
    where c.run_date >= date('now', ?)
    group by c.run_date
),
trend as (
    select
        run_date,
        revenue,
        spend,
        case
            when impressions > 0 then clicks * 1.0 / impressions
        end as ctr,
        avg(revenue) over (
            order by run_date
            rows between 6 preceding and current row
        ) as revenue_ma7
    from daily
)
select run_date, revenue, spend, ctr, revenue_ma7
from trend
order by run_date
"""


ENGAGEMENT_PERFORMANCE_QUERY = """
with perf as (
    select
        c.run_date,
        c.channel,
        c.region,
        sum(c.impressions) as impressions,
        sum(c.clicks) as clicks,
        sum(c.leads) as leads,
        sum(c.revenue) as revenue,
        sum(c.spend) as spend
    from campaign_performance_daily c
    where c.run_date >= date('now', ?)
    group by c.run_date, c.channel, c.region
),
joined as (
    select
        p.run_date,
        p.channel,
        p.region,
        p.impressions,
        p.clicks,
        p.leads,
        p.revenue,
        p.spend,
        k.cac,
        k.ltv,
        k.channel_roi,
        rank() over (
            partition by p.run_date
            order by k.channel_roi desc
        ) as roi_rank
    from perf p
    left join kpi_summary_daily k
        on p.run_date = k.run_date
       and p.channel = k.channel
       and p.region = k.region
)
select
    run_date,
    channel,
    region,
    impressions,
    clicks,
    leads,
    revenue,
    spend,
    cac,
    ltv,
    channel_roi,
    roi_rank
from joined
order by run_date desc, roi_rank asc
"""


RISK_DISTRIBUTION_QUERY = """
with signals as (
    select
        run_date,
        channel,
        region,
        sum(leads) as leads,
        sum(signups) as signups,
        sum(spend) as spend,
        sum(revenue) as revenue,
        case when sum(leads) > 0 then sum(spend) * 1.0 / sum(leads) end as cac,
        case when sum(signups) > 0 then sum(revenue) * 1.0 / sum(signups) end as ltv
    from campaign_performance_daily
    where run_date >= date('now', ?)
    group by run_date, channel, region
),
scored as (
    select
        run_date,
        channel,
        region,
        coalesce(cac, 0.0) as cac,
        coalesce(ltv, 0.0) as ltv,
        min(100.0, (coalesce(cac, 0.0) / (coalesce(ltv, 1.0) + 1.0)) * 120.0) as risk_score
    from signals
)
select
    case
        when risk_score < 35 then 'low'
        when risk_score < 70 then 'medium'
        else 'high'
    end as risk_band,
    count(*) as segments,
    round(avg(risk_score), 2) as avg_risk_score
from scored
group by risk_band
order by avg_risk_score
"""


SUMMARY_STATS_QUERY = """
select
    count(*) as row_count,
    round(avg(revenue), 2) as avg_revenue,
    round(avg(spend), 2) as avg_spend,
    round(avg(clicks), 2) as avg_clicks,
    round(avg(leads), 2) as avg_leads
from (
    select
        run_date,
        sum(revenue) as revenue,
        sum(spend) as spend,
        sum(clicks) as clicks,
        sum(leads) as leads
    from campaign_performance_daily
    where run_date >= date('now', ?)
    group by run_date
) daily
"""
