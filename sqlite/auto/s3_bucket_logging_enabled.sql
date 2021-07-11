select
  -- Required Columns
  arn as resource,
  case
    when json_extract(logging,'$.TargetBucket') is null then 'alarm'
    else 'ok'
  end as status,
  case
    when json_extract(logging,'$.TargetBucket') is null then title || ' logging disabled.'
    else title || ' logging enabled.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_s3_bucket;