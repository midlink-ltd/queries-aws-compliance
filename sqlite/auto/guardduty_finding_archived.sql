select
  -- Required Columns
  arn as resource,
  case
    when json_extract(service,'$.Archived') = 'false' then 'alarm'
    else 'ok'
  end as status,
  case
    when json_extract(service,'$.Archived') = 'false' then title || ' not archived.'
    else title || ' archived.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_guardduty_finding;
