{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  packages = with pkgs; [
    aws-iam-authenticator
    aws-vault
    awscli2
    bash
    git
    glab
    kubectl
    kubernetes-helm
    kustomize
    nixfmt-rfc-style
    tflint
    yq-go
    yubikey-manager
  ];

  languages = {
    python = {
      enable = true;
      version = "3.12";
      poetry.enable = true;
    };
    terraform = {
      enable = true;
    };
  };

  dotenv.enable = true;

  env = {
    AWS_VAULT_KEYCHAIN_NAME = "login";
    AWS_VAULT_PROMPT = "ykman";
  };
}
