with ssl_ok as (
  select
    distinct name,
    arn,
    'ok' as status
  from
    aws_s3_bucket,
    json_each(policy_std, '$.Statement') as s,
    json_each(s.value, '$.Principal.AWS') as p,
    json_each(s.value, '$.Action') as a,
    json_each(s.value, '$.Resource') as r,
    json_each(
      s.value, '$.Condition.Bool.aws:securetransport
    ') as ssl
  where
    p.value = '*'
    and json_extract(s.value,'$.Effect') = 'Deny'
    and cast(ssl.value as bool) = false
)
select
  -- Required Columns
  b.arn as resource,
  case
    when ok.status = 'ok' then 'ok'
    else 'alarm'
  end status,
  case
    when ok.status = 'ok' then b.name || ' bucket policy enforces HTTPS.'
    else b.name || ' bucket policy does not enforce HTTPS.'
  end reason,
  -- Additional Dimensions
  b.region,
  b.account_id
from
  aws_s3_bucket as b
  left join ssl_ok as ok on ok.name = b.name;