with cross_account_buckets as (
  select
    distinct arn
  from
    aws_s3_bucket,
    json_each(policy_std, '$.Statement') as s,
    json_each(s.value, '$.Principal.AWS') as p,
    string_to_array(p.value, ':') as pa,
    json_each(s.value, '$.Action') as a
  where
    json_extract(s.value,'$.Effect') = 'Allow'
    and (
      pa [5] != account_id
      or p.value = '*'
    )
    and a.value in (
      's3:deletebucketpolicy',
      's3:putbucketacl',
      's3:putbucketpolicy',
      's3:putencryptionconfiguration',
      's3:putobjectacl'
    )
)
select
  -- Required Columns
  a.value.arn as resource,
  case
    when b.arn is null then 'ok'
    else 'alarm'
  end as status,
  case
    when b.arn is null then title || ' restricts cross-account bucket access.'
    else title || ' allows cross-account bucket access.'
  end as reason,
  -- Additionl Dimensions
  a.value.region,
  a.value.account_id
from
  aws_s3_bucket a.value
  left join cross_account_buckets b on a.value.arn = b.arn;