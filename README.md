# Connector CLI

This tool is a companion tool to sesampy.

## Init
```commandline
$ mkdir hubspot-connector
$ cd hubspot-connector
$ connector-py init
$ ls
manifest.json
```

## Expand and upload
```commandline
$ connector-py expand
$ cd .expanded
$ ls
test-env.json
pipes
systems
$ sesampy upload
```

## Development
Do your work with Management Studio and your dev node, e.g. add a system and add company and contact pipes.

## Download and collapse
```commandline
$ sesam-py download
$ cd ..
$ connector-py collapse
$ ls
manifest.json
templates
.expanded
$ ls templates
company.json
contact.json
system.json
```
