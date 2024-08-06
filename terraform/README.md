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

## Kubernetes Dashboard

To access the kubernetes dashboard to see pods and cpu/memory usage stuff:
```
aws-vault exec sandbox-admin -- kubectl -n kubernetes-dashboard create token admin-user
aws-vault exec sandbox-admin -- kubectl port-forward service/kubernetes-dashboard 4443:443 -n kubernetes-dashboard
```
Then open up https://localhost:4443/ and use the token you just got to log in.

## Updating locust container images in ECR from the locustio/locust source

```
docker pull locustio/locust:2.29.1
aws-vault exec sandbox-admin -- aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 894947205914.dkr.ecr.us-west-2.amazonaws.com
docker tag locustio/locust:2.29.1 894947205914.dkr.ecr.us-west-2.amazonaws.com/locustio/locust:2.29.1
docker push 894947205914.dkr.ecr.us-west-2.amazonaws.com/locustio/locust:2.29.1
```

Have fun!!
