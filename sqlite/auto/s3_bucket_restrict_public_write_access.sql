with data as (
  select
    distinct name
  from
    aws_s3_bucket,
    json_each(acl, '$.Grants') as grants
  where
    json_extract(grants.value,'$.Grantee.URI') = '"http://acs.amazonaws.com/groups/global/AllUsers"'
    and (
      json_extract(grants.value,'$.Permission') = '"FULL_CONTROL"'
      or json_extract(grants.value,'$.Permission') = '"WRITE_ACP"'
    )
  )
select
  -- Required Columns
  b.arn as resource,
  case
    when d.name is null then 'ok'
    else 'alarm'
  end status,
  case
    when d.name is null then b.title || ' not publicly writable.'
    else b.title || ' publicly writable.'
  end reason,
  -- Additional Dimensions
  b.region,
  b.account_id
from
  aws_s3_bucket as b
  left join data as d on b.name = d.name;