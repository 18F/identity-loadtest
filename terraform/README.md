# Loadtest Setup!

To set up a new cluster, do something like this:
```
aws-vault exec sandbox-admin -- ./deploy.sh newclustername -s
```

## Kubectl Setup!

Make sure your kubeconfig is set up so you can issue
kubectl commands:
```
aws-vault exec sandbox-admin -- aws eks --region us-west-2  update-kubeconfig --name newclustername
```

After that is done, you will be able to issue kubectl commands
wrapped in aws-vault.


## Ongoing Deploys

After the initial setup is done, you can just deploy it without the -s
to push out changes:
```
aws-vault exec sandbox-admin -- ./deploy.sh newclustername
```

## Kubernetes Updates

After setup, you shouldn't have to deploy hardly anything.
Instead, ArgoCD will be watching this repo and deploying
everything that `../kustomization.yaml` has in it.  So you 
can change what is running by editing the files referenced in
there and pushing them up to main, and they should get
applied to the cluster automatically.

## ArgoCD

If you would like to look at ArgoCD, run this command wrapped in aws-vault:
```
kubectl port-forward service/argo-cd-argocd-server 8443:443 -n argocd
```
And then point your browser at https://localhost:8443/.

You can find the `admin` password by issuing this command wrapped in aws-vault:
```
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d ;echo
```

## Locust

To get to the locust server, run this command wrapped in aws-vault:
```
kubectl port-forward service/locust 8089:8089 -n locust
```
And then point your browser at http://localhost:8089/.

Have fun!!

