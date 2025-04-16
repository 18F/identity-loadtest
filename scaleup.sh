#!/bin/sh
#
# This ought to work up to 19200 users or more
#
# Make sure that you have <clustername> going already, and that you have run this:
#   aws-vault exec sandbox-admin -- aws eks --region us-west-2  update-kubeconfig --name clustername
#

echo "make sure that the obproxy ASGs are scaled out! At least 4, maybe 10 depending on load"
echo "make sure the idp and worker ASGs have the proper number of instances.  20-40 each"
echo "make sure the idp and worker dbs are scaled up properly 16xl for worker, 24xl for idp"
echo "make sure the idp elasticache redis is scaled up too"
echo "scale the nodes in the cluster up to 126 or so, and the max to 250"
echo "change the locust-worker replicas in locust.yaml to 350, push it up there and wait until 350 are running"

#echo "<press return once you have done this> "
#read line

echo "scaling up pods"
aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-server --replicas=4 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-repo-server --replicas=4 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment coredns --replicas=110 --namespace=kube-system
aws-vault exec sandbox-admin -- kubectl scale deployment pt-oidc-sinatra --replicas=820 --namespace=pt
aws-vault exec sandbox-admin -- kubectl scale deployment fake-server --replicas=24 --namespace=fake-server
aws-vault exec sandbox-admin -- kubectl scale deployment pt-locust-worker --replicas=440 --namespace=pt
aws-vault exec sandbox-admin -- kubectl scale deployment pt-locust-master --replicas=1 --namespace=pt