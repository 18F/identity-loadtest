#!/bin/sh
#
# This ought to work up to 19200 users?  Or more?
#
# Make sure that you have <clustername> going already, and that you have run this:
#   aws-vault exec sandbox-admin -- aws eks --region us-west-2  update-kubeconfig --name clustername
#

echo "make sure that the obproxy ASGs are scaled out! At least 4, maybe 10"
echo "make sure the idp and worker ASGs have the proper number of instances.  20-40 each"
echo "make sure the idp and worker dbs are scaled up properly 16xl for worker, 24xl for idp"
echo "make sure the idp elasticache redis is scaled up too"
echo "scale the nodes in the cluster up to 126 or so, and the max to 250"
echo "change the locust-worker replicas in locust.yaml to 350, push it up there and wait until 350 are running"

#echo "<press return once you have done this> "
#read line

echo "scaling up pods"
aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-server --replicas=5 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-repo-server --replicas=5 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment coredns --replicas=256 --namespace=kube-system
aws-vault exec sandbox-admin -- kubectl scale deployment oidc-sinatra --replicas=3072 --namespace=oidc-sinatra
aws-vault exec sandbox-admin -- kubectl scale deployment fake-server --replicas=4096 --namespace=fake-server
aws-vault exec sandbox-admin -- kubectl scale deployment locust-worker --replicas=320 --namespace=locust
aws-vault exec sandbox-admin -- kubectl scale deployment locust-master --replicas=1 --namespace=locust
