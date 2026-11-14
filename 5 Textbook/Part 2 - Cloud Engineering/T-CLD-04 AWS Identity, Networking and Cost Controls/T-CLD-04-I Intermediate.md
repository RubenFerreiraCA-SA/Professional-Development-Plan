# T-CLD-04-I — Intermediate Practice

*Chapter: [T-CLD-04 — AWS Identity, Networking and Cost Controls](README.md) · Part 2 — Cloud Engineering*

<a id="t-cld-04-i"></a>
#### T-CLD-04-I — Intermediate Practice

**Two human principals, two purposes.** Create a *training administrator* (broad rights inside the training account only, MFA required) and a *demo operator* (read-mostly: describe resources, read logs, call the public health URL; no `iam:*`, no unrestricted `ec2:*`). Prefer customer-managed policies you can read over broad managed ones. If the demo needs one mutating action (scaling a service), add just that action on that resource ARN.

**Prove the happy path is not admin — without side effects.** Do not test denial by creating a real user. Use the policy simulator:

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::<account>:user/demo-operator \
  --action-names iam:CreateUser ec2:DescribeVpcs \
  --profile training-admin \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table
```

Expect `iam:CreateUser` to be `implicitDeny` and `ec2:DescribeVpcs` to be `allowed`. A non-mutating alternative is running `aws iam list-users` as the demo operator and expecting `AccessDenied`.

**VPC edge for a service.** A minimal design: one VPC (for example `10.50.0.0/16`); two public subnets in different AZs for the load balancer; one security group for the load balancer that allows inbound HTTP/HTTPS from the internet; one security group for tasks that allows inbound *only from the load-balancer security group*; no open SSH. A NAT gateway is a cost decision; document it.

```hcl
resource "aws_security_group" "app" {
  name   = "orders-app"
  vpc_id = aws_vpc.main.id
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]   # only the load balancer
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Training deployments sometimes place tasks in public subnets to avoid NAT charges; that is a cost trade-off, not a production blueprint.

**Workload identity.** Services need identities too. In a container service there are two different roles: the *execution role* (pulls the image, writes logs) and the *task role* (what the application code may call). They are distinct trust boundaries, and neither should be broad. Check an application role with the simulator, and record human operator, task role and execution role separately.

**Apply the reachability diagnostics to the cloud endpoint.** DNS name of the load balancer, route from your location, TCP port, then HTTP (or TLS if configured) and status. A timeout often points to a security group or subnet route; "refused" to nothing listening or the wrong port; `502`/`503` to unhealthy targets.

**Cost guardrails document**

| Item | Value |
| --- | --- |
| Monthly budget | e.g. a small fixed amount |
| Alert threshold | e.g. 50% and 80% |
| Notification | A monitored mailbox |
| Idle policy | Stop or destroy within N hours |
| Forbidden by default | Always-on NAT, public databases, unused load balancers |

**Exercise.** Draw the network, create or import the security groups, write the identity baseline (principals, evidence of allowed and denied actions) and a services map.
