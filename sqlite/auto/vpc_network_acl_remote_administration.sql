with bad_rules as (
  select
    network_acl_id,
    count(*) as num_bad_rules
  from
    aws_vpc_network_acl,
    json_each(entries) as att
  where
    json_extract(att.value,'$.Egress') = 'false' -- as per aws egress = false indicates the ingress
    and (
      json_extract(att.value,'$.CidrBlock') = '0.0.0.0/0'
      or json_extract(att.value,'$.Ipv6CidrBlock') =  '::/0'
    )
    and json_extract(att.value,'$.RuleAction') = 'allow'
    and (
      (
        json_extract(att.value,'$.Protocol') = '-1' -- all traffic
        and json_extract(att.value,'$.PortRange') is null
      )
      or (
        cast((json_extract(att.value,'$.PortRange.From')) as int) <= 22
        and cast((json_extract(att.value,'$.PortRange.To')) as int) >= 22
        and json_extract(att.value,'$.Protocol') in('6', '17')  -- TCP or UDP
      )
      or (
        cast((json_extract(att.value,'$.PortRange.From')) as int) <= 3389
        and cast((json_extract(att.value,'$.PortRange.To')) as int) >= 3389
        and json_extract(att.value,'$.Protocol') in('6', '17')  -- TCP or UDP
    )
  )
  group by
    network_acl_id
)

select
  -- Required Columns
  'arn:' || acl.partition || ':ec2:' || acl.region || ':' || acl.account_id || ':network-acl/' || acl.network_acl_id  as resource,
  case
    when bad_rules.network_acl_id is null then 'ok'
    else 'alarm'
  end as status,
  case
    when bad_rules.network_acl_id is null then acl.network_acl_id || ' does not allow ingress to port 22 or 3389 from 0.0.0.0/0 or ::/0.'
    else acl.network_acl_id || ' contains ' || bad_rules.num_bad_rules || ' rule(s) allowing ingress to port 22 or 3389 from 0.0.0.0/0 or ::/0.'
  end as reason,
  -- Additional Dimensions
  acl.region,
  acl.account_id
from	
  aws_vpc_network_acl as acl
  left join bad_rules on bad_rules.network_acl_id = acl.network_acl_id
