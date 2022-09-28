
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = var.cluster_name
  }
}

resource "aws_subnet" "subnet1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-subnet1"
  }
}

resource "aws_subnet" "subnet2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-subnet2"
  }
}

resource "aws_subnet" "subnet3" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.3.0/24"
  availability_zone       = data.aws_availability_zones.available.names[2]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.cluster_name}-subnet3"
  }
}

module "loadtest" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints?ref=v4.11.0"

  # EKS Cluster VPC and Subnet mandatory config
  vpc_id             = aws_vpc.main.id
  private_subnet_ids = [aws_subnet.subnet1.id, aws_subnet.subnet2.id, aws_subnet.subnet3.id]

  # EKS CLUSTER VERSION
  cluster_version = "1.23"

  cluster_name = var.cluster_name

  # EKS MANAGED NODE GROUPS
  managed_node_groups = {
    mg_5 = {
      node_group_name = "${var.cluster_name}-managed-ondemand"
      instance_types  = ["m5.large"]
      min_size        = "2"
    }
  }
}

# Add-ons
module "kubernetes_addons" {
  source = "github.com/aws-ia/terraform-aws-eks-blueprints//modules/kubernetes-addons?ref=v4.11.0"

  eks_cluster_id = module.loadtest.eks_cluster_id

  # EKS Add-ons
  enable_amazon_eks_vpc_cni            = true
  enable_amazon_eks_coredns            = true
  enable_amazon_eks_kube_proxy         = true
  enable_amazon_eks_aws_ebs_csi_driver = true

  # Self-managed Add-ons
  enable_aws_for_fluentbit            = true
  enable_aws_load_balancer_controller = true
  enable_aws_efs_csi_driver           = true
  enable_cluster_autoscaler           = true
  enable_metrics_server               = true
}
