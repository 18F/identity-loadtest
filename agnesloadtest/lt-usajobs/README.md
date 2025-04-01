# Loadtest Environments

To set up a agnes environment, you should be able to look at the changes in
https://gitlab.login.gov/lg-public/identity-eks-control/-/merge_requests/120 and
edit your environment to create all the users you need and to set up `application.yml`
to have the proper things in it.

Then, `cp -rp agnes yoursp` and edit all the files in there and edit all the files
so that they have the proper env in it either by hand, or with a command like
```
find yourenv -type f -exec sed -i '' 's/agnesloadtest/your_loadtest_cluster_name/g' '{}' \;
find yourenv -type f -exec sed -i '' 's/agnes/yourenv/g' '{}' \;
find yourenv -type f -exec sed -i '' 's/lt-usajobs/yoursp/g' '{}' \;
find yourenv -type f -exec sed -i '' 's/urn:gov:gsa:openidconnect.profiles:sp:sso:opm:lt-usajobs:prod/yoururn/g' '{}' \;
```

Then edit all the files to set up the particular tests and # of users and so on that
you want by editing the `patch-locust.yaml` file.

Create an MR with this, and once it is merged in, the `yourenv` resources should
launch and once AWS does it's thing, you should be able to see your
`yourenv-oidc-sinatra.agnes.identitysandbox.gov` host in dns, and things should
be ready for you.

## Locust Access

```
aws-vault exec sandbox-admin -- kubectl port-forward service/yourenv-locust 8089:8089 -n yourenv
```

Then go to http://localhost:8089/ and locust away.

## ArgoCD Access

```
aws-vault exec sandbox-admin -- kubectl port-forward  8443:443 -n argocd
```

Then go to https://localhost:8443/ and find the `yourenv` resources.

