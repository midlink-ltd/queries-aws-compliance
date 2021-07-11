with bad_policies as (
  select
    arn,
    count(*) as num_bad_statements
  from
    aws_iam_policy,
    json_each(policy_std, '$.Statement') as s,
    json_each(s.value, '$.Resource') as resource,
    json_each(s.value, '$.Action') as action
  where
    json_extract(s.value,'$.Effect') = 'Allow'
    and resource.value = '*'
    and (
      (action.value = '*'
      or action.value = '*:*'
      )
  )
  group by
    arn
)
select
  -- Required Columns
  p.arn as resource.value,
  case
    when bad.arn is null then 'ok'
    else 'alarm'
  end status,
  p.name || ' contains ' || coalesce(bad.num_bad_statements,0)  ||
     ' statements that allow action.value "*" on resource.value "*".' as reason,
  -- Additional Dimensions
  p.account_id
from
  aws_iam_policy as p
  left join bad_policies as bad on p.arn = bad.arn
where
  p.arn not like 'arn:aws:iam::aws:policy%'
