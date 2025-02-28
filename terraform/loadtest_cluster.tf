locals {
  azs      = slice(data.aws_availability_zones.available.names, 0, 3)
  vpc_cidr = "10.0.0.0/16"
}

data "aws_route53_zone" "loadtest" {
  name = var.dnszone
}

module "loadtest" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints?ref=v4.32.1"

  # EKS Cluster VPC and Subnet mandatory config
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnets

  # EKS CLUSTER VERSION
  cluster_version = "1.32"

  cluster_name = var.cluster_name

  # EKS MANAGED NODE GROUPS
  managed_node_groups = {
    # spot = {
    #   node_group_name = "${var.cluster_name}-managed-spot"
    #   min_size        = 1
    #   max_size        = 40
    #   desired_size    = 2
    #   subnet_ids      = module.vpc.private_subnets
    #   capacity_type   = "SPOT"
    #   instance_types  = ["m5.large", "m4.large", "m6a.large", "m5a.large", "m5d.large"]    // Instances with same specs for memory and CPU so Cluster Autoscaler scales efficiently
    #   disk_size       = 100                                                                # disk_size will be ignored when using Launch Templates
    #   k8s_taints      = [{key= "spot", value="true", effect="NO_SCHEDULE"}]
    # }
    bigspot = {
      node_group_name = "${var.cluster_name}-managed-bigspot"
      min_size        = 1
      max_size        = 10
      desired_size    = 2
      subnet_ids      = module.vpc.private_subnets
      capacity_type   = "SPOT"
      instance_types  = ["m6a.2xlarge", "m5.2xlarge", "m4.2xlarge", "m5a.2xlarge"] // Instances with same specs for memory and CPU so Cluster Autoscaler scales efficiently
      disk_size       = 100                                                        # disk_size will be ignored when using Launch Templates
    }
    ondemand = {
      node_group_name = "${var.cluster_name}-managed-ondemand"
      min_size        = 1
      max_size        = 250
      desired_size    = 9
      subnet_ids      = module.vpc.private_subnets
      capacity_type   = "ON_DEMAND"
      instance_types  = ["m5.large", "m4.large", "m6a.large", "m5a.large", "m5d.large"] // Instances with same specs for memory and CPU so Cluster Autoscaler scales efficiently
      disk_size       = 100                                                             # disk_size will be ignored when using Launch Templates
    }
  }
}

# Add-ons
module "eks_blueprints_addons" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "~> 1.20.0"

  cluster_name      = module.loadtest.eks_cluster_id
  cluster_endpoint  = module.loadtest.eks_cluster_endpoint
  cluster_version   = module.loadtest.eks_cluster_version
  oidc_provider_arn = module.loadtest.eks_oidc_provider_arn

  eks_addons = {
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.cluster_name}-ebs-csi-controller"
    }
    coredns = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
  }

  # EKS Blueprints Addons
  enable_cluster_autoscaler           = true
  enable_external_dns                 = true
  enable_aws_load_balancer_controller = true
  enable_cert_manager                 = true
  external_dns_route53_zone_arns      = [data.aws_route53_zone.loadtest.arn]
  enable_metrics_server               = true
}

module "gitops_bridge" {
  depends_on = [module.loadtest]
  source     = "github.com/gitops-bridge-dev/gitops-bridge-argocd-bootstrap-terraform?ref=v2.0.0"
  cluster = {
    name        = var.cluster_name
    metadata    = module.eks_blueprints_addons.gitops_metadata
    environment = var.cluster_name
  }

  argocd = {
    create_namespace = true
    chart_version    = "5.55.0"
    values = [templatefile("${path.module}/templates/argocd-values.yaml.tpl", {
    })]
  }

  apps = {
    loadtest-apps = templatefile("${path.module}/templates/application-kustomize.yaml.tpl", {
      name           = "loadtest-apps"
      path           = "."
      repoURL        = "https://github.com/18F/identity-loadtest.git"
      targetRevision = "stages/agnes"
    })
    # Below are all magic add-ons that you can see how to configure here:
    # https://github.com/aws-ia/terraform-aws-eks-blueprints/tree/main/docs/add-ons
    addons = templatefile("${path.module}/templates/application.yaml.tpl", {
      name           = "addons"
      targetRevision = "main"
      path           = "chart"
      repoURL        = "https://github.com/aws-samples/eks-blueprints-add-ons.git"
      helmValues = templatefile("${path.module}/helm-values/addons.yaml.tpl", {
        region          = var.region,
        clusterName     = var.cluster_name,
        repoUrl         = "https://github.com/aws-samples/eks-blueprints-add-ons.git",
        targetRevision  = "main",
        zoneName        = var.dnszone,
        gitops_metadata = module.eks_blueprints_addons.gitops_metadata # All our roles, service account names we setup with eks_addons
      })
      valueFiles = []
    })
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = var.cluster_name
  cidr = local.vpc_cidr

  azs             = local.azs
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 2, k + 1)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true

  # Manage so we can name
  manage_default_network_acl    = true
  default_network_acl_tags      = { Name = "${var.cluster_name}-default" }
  manage_default_route_table    = true
  default_route_table_tags      = { Name = "${var.cluster_name}-default" }
  manage_default_security_group = true
  default_security_group_tags   = { Name = "${var.cluster_name}-default" }

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/elb"                    = 1
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb"           = 1
  }

  tags = {
    Name = "${var.cluster_name}-vpcstuff"
  }
}

# this is to ensure that the loadtest dns zone has been set up already by hand
data "aws_route53_zone" "primary" {
  name         = var.dnszone
  private_zone = false
}

module "acm-cert-fake-server" {
  source = "github.com/18F/identity-terraform//acm_certificate?ref=6cdd1037f2d1b14315cc8c59b889f4be557b9c17"
  #source = "../../../identity-terraform/acm_certificate"
  domain_name               = "fake-server.${var.dnszone}"
  subject_alternative_names = []
  validation_zone_id        = data.aws_route53_zone.primary.id
}

module "acm-cert-oidc-sinatra" {
  source = "github.com/18F/identity-terraform//acm_certificate?ref=6cdd1037f2d1b14315cc8c59b889f4be557b9c17"
  #source = "../../../identity-terraform/acm_certificate"
  domain_name               = "oidc-sinatra.${var.dnszone}"
  subject_alternative_names = []
  validation_zone_id        = data.aws_route53_zone.primary.id
}
