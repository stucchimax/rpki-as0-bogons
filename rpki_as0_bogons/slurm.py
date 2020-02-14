#!/usr/bin/env python3
# Copyright (c) 2020, Massimiliano Stucchi
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
#2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import json
import requests

def main():

    parser = argparse.ArgumentParser(
            description='A script to generate a SLURM file for all bogons with origin AS0',
            epilog="Version 0.1.1")

    parser.add_argument("-f",
            dest='dest_file',
            default="/usr/local/etc/slurm.json",
            help="File to be created with all the SLURM content (default is /usr/local/etc/slurm.json)")
            
    args = parser.parse_args()

    output = {}

    output['slurmVersion'] = 1
    output["validationOutputFilters"] = {}
    output["validationOutputFilters"]["prefixFilters"] = []
    output["validationOutputFilters"]["bgpsecFilter"] = []
    output["locallyAddedAssertions"] = {}
    output["locallyAddedAssertions"]["prefixAssertions"] = []
    output["locallyAddedAssertions"]["bgpsecAssertions"] = []

    ipv4_bogons = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv4.txt"
    ipv6_bogons = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv6.txt"

    roas = as0_roas_for(ipv4_bogons, 32) + as0_roas_for(ipv6_bogons, 128)

    output['locallyAddedAssertions']["prefixAssertions"] = roas

    with open(args.dest_file, "w") as f:
        f.write(json.dumps(output, indent=2))

def as0_roas_for(url, maxLength):
    as0_roas = []

    r = requests.get(url)

    bogons = r.text.split("\n")

    # Remove the first and the last line
    bogons.pop(0)
    bogons.pop()

    for network in bogons:
        new_entry = {}
        new_entry['asn'] = 0
        new_entry['prefix'] = network
        new_entry['maxPrefixLength'] = maxLength

        as0_roas.append(new_entry)

    return as0_roas


if __name__ == "__main__":
    main()
