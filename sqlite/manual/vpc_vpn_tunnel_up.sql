with filter_data as (
  select
    arn,
    count(json_extract(t.value,'$.Status')) as count
  from
    aws_vpc_vpn_connection,
    json_each(vgw_telemetry) as t
  where json_extract(t.value,'$.Status') = 'UP'
  group by arn 
)
select
  -- Required Columns
  a.arn as resource,
  case
    when b.count is null or b.count < 2 then 'alarm'
    else 'ok'
  end as status,
  case
    when b.count is null then a.title || ' has both tunnels offline.'
    when b.count = 1 then a.title || ' has one tunnel offline.'
    else a.title || ' has both tunnels online.'
  end as reason,
  -- Additional Dimensions
  a.region,
  a.account_id
from
  aws_vpc_vpn_connection as a
  left join filter_data as b on a.arn = b.arn;
