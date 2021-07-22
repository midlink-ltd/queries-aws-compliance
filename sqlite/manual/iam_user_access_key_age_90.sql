select
  -- Required Columns
  'arn:' || partition || ':iam::' || account_id || ':user/' || user_name || '/accesskey/' || access_key_id as resource,
  case
    when create_date <= datetime('now', '-90 day') then 'alarm'
    else 'ok'
  end status,
  user_name || ' ' || access_key_id || ' created ' || date(create_date) ||
    ' (' || ROUND(JULIANDAY('now') - JULIANDAY(create_date)) || ' days).'
  as reason,
  -- Additional Dimensions
  account_id
from
  aws_iam_access_key;
