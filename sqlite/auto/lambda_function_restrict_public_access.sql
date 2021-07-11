select
  -- Required Columns
  arn as resource,
  case
    when json_extract(policy_std,'$.Statement.Effect') = 'Allow'
    and (
      json_extract(policy_std,'$.Statement.Prinipal') = '*'
      or ( json_extract(policy_std,'$.Principal.AWS') ) = '*'
    ) then 'alarm'
    else 'ok'
  end status,
  case
    when policy_std is null then title || ' has no policy.'
    when json_extract(policy_std,'$.Statement.Effect') = 'Allow'
    and (
      json_extract(policy_std,'$.Statement.Prinipal') = '*'
      or ( json_extract(policy_std,'$.Principal.AWS') ) = '*'
    ) then title || ' allows public access.'
    else title || ' does not allow public access.'
  end reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_lambda_function;
