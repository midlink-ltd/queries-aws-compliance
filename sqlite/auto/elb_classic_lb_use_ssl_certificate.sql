with detailed_classic_listeners as (
  select
    name
  from
    aws_ec2_classic_load_balancer,
    json_each(listener_descriptions) as listener_description
  where
    json_extract(listener_description.value,'$.Listener.Protocol') in ('HTTPS', 'SSL', 'TLS')
    and json_extract(listener_description.value,'$.Listener.SSLCertificateId') like 'arn:aws:acm%'
)
select
  -- Required Columns
  'arn:' || a.partition || ':elasticloadbalancing:' || a.region || ':' || a.account_id || ':loadbalancer/' || a.name as resource,
  case
    when a.listener_descriptions is null then 'skip'
    when b.name is not null then 'alarm'
    else 'ok'
  end as status,
  case
    when a.listener_descriptions is null then a.title || ' has no listener.'
    when b.name is not null then a.title || ' not uses certificates provided by ACM.'
    else a.title || ' uses certificates provided by ACM.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_ec2_classic_load_balancer as a
  left join detailed_classic_listeners as b on a.name = b.name;