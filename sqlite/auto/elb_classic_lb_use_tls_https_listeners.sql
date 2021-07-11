select
  -- Required Columns
  'arn:' || partition || ':elasticloadbalancing:' || region || ':' || account_id || ':loadbalancer/' || title as resource,
  case
    when json_extract(listener_description.value,'$.Listener.Protocol') in ('HTTPS', 'SSL', 'TLS') then 'ok'
    else 'alarm'
  end as status,
  case
    when json_extract(listener_description.value,'$.Listener.Protocol') = 'HTTPS' then title || ' configured with HTTPS protocol.'
    when json_extract(listener_description.value,'$.Listener.Protocol') = 'SSL' then title || ' configured with TLS protocol.'
    else title || ' configured with ' || (json_extract(listener_description.value,'$.Listener.Protocol')) || ' protocol.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_ec2_classic_load_balancer,
  json_each(listener_descriptions) as listener_description;