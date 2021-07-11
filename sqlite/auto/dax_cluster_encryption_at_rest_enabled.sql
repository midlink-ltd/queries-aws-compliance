select
  -- Required Columns
  arn as resource,
  case
    when json_extract(sse_description,'$.Status') = 'ENABLED' then 'ok'
    else 'alarm'
  end as status,
  case
    when json_extract(sse_description,'$.Status') = 'ENABLED' then title || ' encryption at rest enabled.'
    else title || ' encryption at rest not enabled.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_dax_cluster;