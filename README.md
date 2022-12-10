# Connector CLI

This tool is a companion tool to sesampy.

## Init
```commandline
$ mkdir hubspot-connector
$ cd hubspot-connector
$ connectorpy init
$ ls
manifest.json
```

## Expand and upload
```commandline
$ connectorpy expand
$ cd .expanded
$ ls
test-env.json
pipes
systems
$ sesampy upload
```

## OAuth2 setup
```commandline
$ oauthlogin.py --client_secret ZziobpmZ0DWC[..] --client_id gZLMgMG1[..] --service_url https://datahub-a6a45974.sesam.cloud/api --service_jwt eyJ0eXAiOiJKV1QiLCJhb[..]]

This tool will add oauth system secrets and add token_url to the environment variables:
  Service API: https://datahub-a6a45974.sesam.cloud/api
  System id: xxxxxx

To continue open the following link in your browser:
  Link: https://api.waveapps.com/oauth2/authorize/?client_id=gZLMgMG[..]

 * Serving Flask app 'oauthlogin' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5010/ (Press CTRL+C to quit)
Updated secret: oauth_access_token
Updated secret: oauth_refresh_token
Updated secret: oauth_client_id
Updated secret: oauth_client_secret
Updated environment variables
```

## Development
Do your work with Management Studio and your dev node, e.g. add a system and add company and contact pipes.

## Download and collapse
```commandline
$ sesampy download
$ cd ..
$ connectorpy collapse
$ ls
manifest.json
templates
.expanded
$ ls templates
company.json
contact.json
system.json
```
