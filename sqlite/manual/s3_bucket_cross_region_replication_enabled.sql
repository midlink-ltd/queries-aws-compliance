with bucket_with_replication as (
  select
    name,
    json_extract(r.value,'$.Status') as rep_status
  from
    aws_s3_bucket,
    json_each(replication, '$.Rules ') as r
)
select
  -- Required Columns
  b.arn as resource,
  case
    when b.name = bwr.name and bwr.rep_status = '"Enabled"' then 'ok'
    else 'alarm'
  end as status,
  case
    when b.name = bwr.name and bwr.rep_status = '"Enabled"' then b.title || ' enabled with cross-region replication.'
    else b.title || ' not enabled with cross-region replication.'
  end as reason,
  -- Additional Dimensions
  b.region,
  b.account_id
from
  aws_s3_bucket b
  left join bucket_with_replication bwr on b.name = bwr.name;

