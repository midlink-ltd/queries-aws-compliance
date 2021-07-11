
select
  -- Required Columns
  arn as resource,
  case
    when json_extract(cluster_snapshot.value,'$.AttributeValues') = '["all"]' then 'alarm'
    else 'ok'
  end status,
  case
    when json_extract(cluster_snapshot.value,'$.AttributeValues') = '["all"]' then title || ' publicly restorable.'
    else title || ' not publicly restorable.'
  end reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_rds_db_cluster_snapshot,
  json_each(db_cluster_snapshot_attributes) as cluster_snapshot

union

select
  -- Required Columns
  arn as resource,
  case
    when json_extract(database_snapshot.value,'$.AttributeValues') = '["all"]' then 'alarm'
    else 'ok'
  end status,
  case
    when json_extract(database_snapshot.value,'$.AttributeValues') = '["all"]' then title || ' publicly restorable.'
    else title || ' not publicly restorable.'
  end reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_rds_db_snapshot,
  json_each(db_snapshot_attributes) as database_snapshot
;
