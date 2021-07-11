select
  -- Required Columns
  arn as resource,
  case
    when json_extract(o.value,'$.DomainName') not like '%s3.amazonaws.com' then 'skip'
    when json_extract(o.value,'$.DomainName') like '%s3.amazonaws.com'
    and json_extract(o.value,'$.S3OriginConfig.OriginAccessIdentity') = '' then 'alarm'
    else 'ok'
  end as status,
  case
    when json_extract(o.value,'$.DomainName') not like '%s3.amazonaws.com' then title || ' origin type is not s3.'
    when json_extract(o.value,'$.DomainName') like '%s3.amazonaws.com'
    and json_extract(o.value,'$.S3OriginConfig.OriginAccessIdentity') = '' then title || ' origin access identity not configured.'
    else title || ' origin access identity configured.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_cloudfront_distribution,
  json_each(origins) as o;
