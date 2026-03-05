-- Portfolio SQL queries for recruiter demos.
-- These statements intentionally showcase joins, group-by logic, and window functions.

-- 1) Revenue trend with moving average and day-over-day delta.
with daily_revenue as (
    select
        run_date,
        sum(revenue) as revenue
    from campaign_performance_daily
    group by run_date
)
select
    run_date,
    revenue,
    avg(revenue) over (
        order by run_date
        rows between 6 preceding and current row
    ) as revenue_ma7,
    revenue - lag(revenue) over (order by run_date) as revenue_delta
from daily_revenue
order by run_date;


-- 2) Engagement and funnel performance by channel and region.
select
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
    case when sum(c.leads) > 0 then sum(c.signups) * 1.0 / sum(c.leads) end as lead_to_signup_rate
from campaign_performance_daily c
group by c.channel, c.region
order by revenue desc;


-- 3) Join KPI outputs with campaign performance and rank by ROI.
with joined as (
    select
        k.run_date,
        k.channel,
        k.region,
        k.cac,
        k.ltv,
        k.channel_roi,
        c.revenue,
        c.spend,
        rank() over (
            partition by k.run_date
            order by k.channel_roi desc
        ) as roi_rank
    from kpi_summary_daily k
    join (
        select
            run_date,
            channel,
            region,
            sum(revenue) as revenue,
            sum(spend) as spend
        from campaign_performance_daily
        group by run_date, channel, region
    ) c
      on k.run_date = c.run_date
     and k.channel = c.channel
     and k.region = c.region
)
select
    run_date,
    channel,
    region,
    revenue,
    spend,
    cac,
    ltv,
    channel_roi,
    roi_rank
from joined
where roi_rank <= 3
order by run_date desc, roi_rank asc;


-- 4) Risk score distribution for campaign segments.
with segment_risk as (
    select
        c.run_date,
        c.channel,
        c.region,
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
    from segment_risk
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
group by run_date, risk_band
order by run_date, risk_band;
