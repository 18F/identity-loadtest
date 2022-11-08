#!/bin/sh
#
# This ought to work up to 19200 users?  Or more?
#
# Make sure that you have <clustername> going already, and that you have run this:
#   aws-vault exec sandbox-admin -- aws eks --region us-west-2  update-kubeconfig --name clustername
#

echo "scale the nodes in the cluster up to 126 or so, and the max to 250"
echo "change the locust-worker replicas in locust.yaml to 350, push it up there and wait until 350 are running"

echo "<press return once you have done this> "
read line

echo "scaling up pods"
aws-vault exec sandbox-admin -- kubectl scale deployment coredns --replicas=51 --namespace=kube-system
aws-vault exec sandbox-admin -- kubectl scale deployment oidc-sinatra --replicas=1000 --namespace=oidc-sinatra
