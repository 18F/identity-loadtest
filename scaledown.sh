#!/bin/sh
#
# Make sure that you have <clustername> going already, and that you have run this:
#   aws-vault exec sandbox-admin -- aws eks --region us-west-2  update-kubeconfig --name clustername
#

echo "scaling down pods"

aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-server --replicas=1 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment argo-cd-argocd-repo-server --replicas=1 --namespace=argocd
aws-vault exec sandbox-admin -- kubectl scale deployment coredns --replicas=2 --namespace=kube-system
aws-vault exec sandbox-admin -- kubectl scale deployment pt-oidc-sinatra --replicas=1 --namespace=pt
aws-vault exec sandbox-admin -- kubectl scale deployment fake-server --replicas=1 --namespace=fake-server
aws-vault exec sandbox-admin -- kubectl scale deployment pt-locust-worker --replicas=1 --namespace=pt
aws-vault exec sandbox-admin -- kubectl scale deployment pt-locust-master --replicas=1 --namespace=pt

echo "scale the nodes in the cluster down to 6 or so, and make the max be 10."
echo "change the locust-worker replicas in locust.yaml to 5, push it up there."
