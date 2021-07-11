select
  -- Required Columns
  arn as resource,
  case
    when json_extract(vpc_options,'$.VPCId') is null then 'alarm'
    else 'ok'
  end status,
  case
    when json_extract(vpc_options,'$.VPCId') is null then title || ' not in VPC.'
    else title || ' in VPC ' || (json_extract(vpc_options,'$.VPCId')) || '.'
  end reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_elasticsearch_domain;