with base as (
    select
        c.run_date,
        c.channel,
        c.region,
        sum(c.spend) as spend,
        sum(c.leads) as leads,
        sum(c.signups) as customers,
        sum(c.revenue) as revenue
    from campaign_performance_daily c
    group by c.run_date, c.channel, c.region
),
mom as (
    select
        b.*,
        lag(revenue) over (partition by channel, region order by run_date) as prev_revenue
    from base b
),
with_kpis as (
    select
        run_date,
        channel,
        region,
        case when leads > 0 then spend * 1.0 / leads else null end as cac,
        case when customers > 0 then revenue * 1.0 / customers else null end as ltv,
        case when leads > 0 and spend > 0 then (revenue * 1.0 / spend) end as channel_roi,
        case when leads > 0 then customers * 1.0 / leads end as conversion_rate,
        case when prev_revenue is not null and prev_revenue <> 0
            then (revenue - prev_revenue) * 1.0 / prev_revenue
        end as revenue_growth
    from mom
)
insert into kpi_summary_daily (
    run_date,
    channel,
    region,
    cac,
    ltv,
    ltv_cac_ratio,
    conversion_rate,
    funnel_dropoff,
    retention_rate,
    revenue_growth,
    channel_roi,
    campaign_rank,
    mom_performance
)
select
    run_date,
    channel,
    region,
    cac,
    ltv,
    case when cac > 0 then ltv * 1.0 / cac end as ltv_cac_ratio,
    conversion_rate,
    null as funnel_dropoff,
    null as retention_rate,
    revenue_growth,
    channel_roi,
    dense_rank() over (partition by run_date order by channel_roi desc) as campaign_rank,
    revenue_growth as mom_performance
from with_kpis;

