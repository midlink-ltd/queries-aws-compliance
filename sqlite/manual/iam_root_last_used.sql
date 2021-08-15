select
  -- Required Columns
  user_arn as resource,
  case
    when date(password_last_used) > date('now', '-3 months') then 'alarm'
    when date(access_key_1_last_used_date) <= date('now', '-3 months') then 'alarm'
    when date(access_key_2_last_used_date) <= date('now', '-3 months') then 'alarm'
    else 'ok'
  end as status,
  case
    when password_last_used is null then 'Root never logged in with password.'
    else 'Root password used ' || password_last_used || ' (' || round(julianday('now') - julianday(password_last_used)) || ' days).'
  end ||
  case
    when access_key_1_last_used_date is null then ' Access Key 1 never used.'
    else ' Access Key 1 used ' || access_key_1_last_used_date || ' (' || round(julianday('now') - julianday(access_key_1_last_used_date)) || ' days).'
  end ||
    case
    when access_key_2_last_used_date is null then ' Access Key 2 never used.'
    else ' Access Key 2 used ' || access_key_2_last_used_date || ' (' || round(julianday('now') - julianday(access_key_2_last_used_date)) || ' days).'
  end as reason,
  account_id
from
  aws_iam_credential_report
where
  user_name = '<root_account>';
