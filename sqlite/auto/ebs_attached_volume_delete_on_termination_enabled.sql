select
  -- Required Columns
  arn as resource,
  case
    when state != 'in-use' then 'skip'
    when json_extract(attachment.value,'$.DeleteOnTermination') = 'true' then 'ok'
    else 'alarm'
  end as status,
  case
    when state != 'in-use' then title || ' not attached to EC2 instance.'
    when json_extract(attachment.value,'$.DeleteOnTermination') = 'true' then title || ' attached to ' || (json_extract(attachment.value,'$.InstanceId')) || ', delete on termination enabled.'
    else title || ' attached to ' || (json_extract(attachment.value,'$.InstanceId')) || ', delete on termination disabled.'
  end as reason,
  -- Additional Dimensions
  region,
  account_id
from
  aws_ebs_volume
  left join json_each(attachments) as attachment on true;
