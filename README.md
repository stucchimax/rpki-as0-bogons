# rpki-as0-bogons

SLURM file generator for bogons with AS0 as origin.

This script generates a JSON file compatible with [RFC8416](https://www.rfc-editor.org/rfc/rfc8416.txt) to be used for a local validator.

The script takes bogon files from the [Team Cymru Bogon Reference](https://www.team-cymru.com/bogon-reference.html) or builds a list of all the networks not assigned according to the official [NRO Delegated Statistics](https://www.nro.net/about/rirs/statistics/) file, and turns them into a SLURM file.  All the networks are added to the SLURM file with origin: AS0 and with a default MaxPrefix of 32 for IPv4 and 128 for IPv6.

Once loaded in a validator, this file will suggest the validating software to create "fake" ROAs for these networks.  If your network performs origin validation and applies "Invalid: Reject" policies, any BGP announcement of these networks coming from your peers or upstreams should be discarded.

## Installation

You can find the software on PyPi, so you can install it easily via pip.

```shell
# pip3 install rpki-as0-bogon
```

## Usage

```shell
usage: slurm.py [-h] [-f DEST_FILE] [-N]

A script to generate a SLURM file for all bogons with origin AS0

optional arguments:
  -h, --help    show this help message and exit
  -f DEST_FILE  File to be created with all the SLURM content (default is
                /usr/local/etc/slurm.json)
  -N            Use the NRO delegated stats instead of Team Cymru's bogon list

Version 0.2
```

By default the Team Cymru lists is used, but if you want to include any network that's not assigned or allocated at the moment, it's better to use the NRO file.

## Using it with a validator

### Routinator

You should start routinator with the *-x* switch, providing the path to the file (the file is saved by the tool into */usr/local/etc/slurm.json*)

### RIPE NCC Validator 3

You can use curl to supply the file to the validator:

```shell
/usr/local/bin/curl -X POST -F "file=slurm.json" localhost:8080/api/slurm/upload
```

### Forth

Use the *--slurm* option when running the software.

## Recommendations

Since the bogon files are updated daily, a daily run via cron is suggested for this tool.

