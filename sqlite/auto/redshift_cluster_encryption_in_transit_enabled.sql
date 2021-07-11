with pg_with_ssl as (
 select
  name as pg_name,
  json_extract(p.value,'$.ParameterName') as parameter_name,
  json_extract(p.value,'$.ParameterValue') as parameter_value
from
  aws_redshift_parameter_group,
  json_each(parameters) as p
where
  json_extract(p.value,'$.ParameterName') = 'require_ssl'
  and json_extract(p.value,'$.ParameterValue') = 'true'
)
select
  -- Required Columns
  'arn:aws:redshift:' || region || ':' || account_id || ':' || 'cluster' || ':' || cluster_identifier as resource,
  case
    when json_extract(cpg.value,'$.ParameterGroupName') in (select pg_name from pg_with_ssl ) then 'ok'
    else 'alarm'
  end as status,
  case
    when json_extract(cpg.value,'$.ParameterGroupName') in (select pg_name from pg_with_ssl ) then title || ' encryption in transit enabled.'
    else title || ' encryption in transit disabled.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_redshift_cluster,
  json_each(cluster_parameter_groups) as cpg;