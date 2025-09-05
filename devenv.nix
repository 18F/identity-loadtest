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
    detect-secrets
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

  git-hooks.hooks = {
    detect-secrets = {
      enable = true;
      name = "detect-secrets";
      description = "Detects high entropy strings that are likely to be passwords.";
      entry = "detect-secrets-hook";
      language = "python";
      args = [
        "--baseline"
        ".secrets.baseline"
      ];
    };
  };
}
