clusterName: ${clusterName}
repoUrl: ${repoUrl}
region: ${region}
targetRevision: ${targetRevision}
awsLoadBalancerController:
  createNamespace: true
  enable: true
  enableCertManager: true
  serviceAccount:
    create: true
    name: ${gitops_metadata["aws_load_balancer_controller_service_account"]}
    annotations:
      eks.amazonaws.com/role-arn: ${gitops_metadata["aws_load_balancer_controller_iam_role_arn"]}
  podDisruptionBudget:
    maxUnavailable: "10%"
clusterAutoscaler:
  enable: true
  serviceAccountName: ${gitops_metadata["cluster_autoscaler_service_account"]}
  rbac:
    serviceAccount:
      create: true
      annotations:
        eks.amazonaws.com/role-arn: ${gitops_metadata["cluster_autoscaler_iam_role_arn"]}
  podDisruptionBudget:
    maxUnavailable: "10%"
externalDns:
  enable: true
  serviceAccountName: ${gitops_metadata["external_dns_service_account"]}
  serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: ${gitops_metadata["external_dns_iam_role_arn"]}
  domainFilters:
    - ${zoneName}
  triggerLoopOnEvent: true
  interval: 5m
  aws:
    batchChangeSize: 2
    zonesCacheDuration: "3h"
  extraArgs:
    aws-batch-change-interval: "10s"
  podDisruptionBudget:
    maxUnavailable: "10%"
