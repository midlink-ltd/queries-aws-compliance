select
  -- Required Columns
  arn as resource,
  case
    when not encrypted then 'alarm'
    when not cast((json_extract(logging_status,'$.LoggingEnabled')) as bool)ean then 'alarm'
    else 'ok'
  end as status,
  case
    when not encrypted then title || ' not encrypted.'
    when not cast((json_extract(logging_status,'$.LoggingEnabled')) as bool)ean then title || ' audit logging not enabled.'
    else title || ' audit logging and encryption enabled.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_redshift_cluster;