with policy_with_decrypt_grant as (
  select
    distinct arn
  from
    aws_iam_policy,
    json_each(policy_std, '$.Statement') as statement
  where
    not is_aws_managed
    and json_extract(statement.value,'$.Effect') = 'Allow'
    and json_extract(statement.value,'$.Resource') ?| array['*', 'arn:aws:kms:*:' || account_id || ':key/*', 'arn:aws:kms:*:' || account_id || ':alias/*']
    and json_extract(statement.value,'$.Action') ?| array['*', 'kms:*', 'kms:decrypt', 'kms:reencryptfrom', 'kms:reencrypt*']
)
select
  -- Required Columns
  i.arn as resource,
  case
    when d.arn is null then 'ok'
    else 'alarm'
  end as status,
  case
    when d.arn is null then i.title || ' doesn''t allow decryption actions on all keys.'
    else i.title || ' allows decryption actions on all keys.'
  end as reason,
  -- Additional Dimensions
  i.account_id
from
  aws_iam_policy i
left join policy_with_decrypt_grant d on i.arn = d.arn
where
  not is_aws_managed;