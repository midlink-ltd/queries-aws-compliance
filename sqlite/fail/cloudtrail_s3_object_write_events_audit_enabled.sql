with s3_selectors as
(
  select
    name as trail_name,
    is_multi_region_trail,
    bucket_selector.value
  from
    aws_cloudtrail_trail,
    json_each(event_selectors) as event_selector,
    json_each(event_selector.value, '$.DataResources') as data_resource,
    json_each(data_resource.value, '$.Values') as bucket_selector
  where
    is_multi_region_trail
    and json_extract(data_resource.value,'$.Type') = 'AWS::S3::Object'
    and json_extract(event_selector.value,'$.ReadWriteType') in
    (
      'WriteOnly',
      'All'
    )
)
select
  -- Required columns
  b.arn as resource,
  case
    when count(bucket_selector.value) > 0 then 'ok'
    else 'alarm'
  end as status,
  case
    when count(bucket_selector.value) > 0 then b.name || ' object-level write events logging enabled.'
    else b.name || ' object-level write events logging disabled.'
  end as reason,
  -- Additional columns
  region,
  account_id
from
  aws_s3_bucket as b
  left join
    s3_selectors
    on bucket_selector.value like (b.arn || '%')
    or bucket_selector.value = 'arn:aws:s3'
group by
  b.account_id, b.region, b.arn, b.name;