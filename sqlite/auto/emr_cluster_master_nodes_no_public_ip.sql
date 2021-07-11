select
  -- Required Columns
  c.cluster_arn as resource,
  case
    when json_extract(c.status,'$.State') not in ('RUNNING', 'WAITING') then 'skip'
    when s.map_public_ip_on_launch then 'alarm'
    else 'ok'
  end as status,
  case
    when json_extract(c.status,'$.State') not in ('RUNNING', 'WAITING') then c.title || ' is in ' || (json_extract(c.status,'$.State')) || ' state.'
    when s.map_public_ip_on_launch then c.title || ' master nodes assigned with public IP.'
    else c.title || ' master nodes not assigned with public IP.'
  end as reason,
  -- Additional Dimensions
  c.region,
  c.account_id
from
  aws_emr_cluster as c
  left join aws_vpc_subnet as s on json_extract(c.ec2_instance_attributes,'$.Ec2SubnetId') = s.subnet_id;
