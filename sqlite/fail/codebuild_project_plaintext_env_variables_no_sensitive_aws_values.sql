with invalid_key_name as (
  select
    distinct arn,
    name
  from
    aws_codebuild_project,
    json_each(environment, '$.EnvironmentVariables') as env
  where
    json_extract(env.value,'$.Name') ilike any (ARRAY['%AWS_ACCESS_KEY_ID%', '%AWS_SECRET_ACCESS_KEY%', '%PASSWORD%'])
    and json_extract(env.value,'$.Type') = 'PLAINTEXT'
)
select
  -- Required Columns
  a.arn as resource,
  case
    when b.arn is null then 'ok'
    else 'alarm'
  end as status,
  case
    when b.arn is null then a.title || ' has no plaintext environment variables with sensitive AWS values.'
    else a.title || ' has plaintext environment variables with sensitive AWS values.'
  end as reason,
  -- Additional Dimensions
  a.region,
  a.account_id
from
  aws_codebuild_project a
  left join invalid_key_name b on a.arn = b.arn;
