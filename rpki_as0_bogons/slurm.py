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
import ipaddress
import json
import requests

def main():

    parser = argparse.ArgumentParser(
            description='A script to generate a SLURM file for all bogons with origin AS0',
            epilog="Version 0.3.1")

    parser.add_argument("-f",
            dest='dest_file',
            default="/usr/local/etc/slurm.json",
            help="File to be created with all the SLURM content (default is /usr/local/etc/slurm.json)")
    
    parser.add_argument("-P",
            dest='peeringDB_lans',
            default=False,
            action='store_true',
            help="Include the list of IXP LANs from PeeringDB. \
                    While some of them already have AS0 ROAs, not all of them do.  \
                    Overlapping ROAs are fine, so it will be okay to generate them anyway")


    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument("-N",
            dest='use_delegated_stats',
            default=False,
            action='store_true',
            help="Use the NRO delegated stats")
    
    group.add_argument("-C",
            dest='use_team_cymru',
            default=False,
            action='store_true',
            help="Use the Team Cymru's bogons list")
    
    args = parser.parse_args()

    roas = []
    if args.use_delegated_stats:
        
        delegated_stats_url = "https://www.nro.net/wp-content/uploads/apnic-uploads/delegated-extended"
        roas = nro_as0_roas(delegated_stats_url)
    elif args.use_team_cymru:

        ipv4_cymru_bogons_url = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv4.txt"
        ipv6_cymru_bogons_url = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv6.txt"

        roas = cymru_as0_roas(ipv4_cymru_bogons_url, 32) + cymru_as0_roas(ipv6_cymru_bogons_url, 128)

    if args.peeringDB_lans:
        roas += peeringDB_roas(32,128)
    
    ### Now build the output file structure, and add the ROAs at the end
    
    output = {}

    output['slurmVersion'] = 1
    output["validationOutputFilters"] = {}
    output["validationOutputFilters"]["prefixFilters"] = []
    output["validationOutputFilters"]["bgpsecFilters"] = []
    output["locallyAddedAssertions"] = {}
    output["locallyAddedAssertions"]["prefixAssertions"] = []
    output["locallyAddedAssertions"]["bgpsecAssertions"] = []

    output['locallyAddedAssertions']["prefixAssertions"] = roas

    with open(args.dest_file, "w") as f:
        f.write(json.dumps(output, indent=2))

def cymru_as0_roas(url, maxLength):
    bogons = requests.get(url).text.split("\n")
    # Remove the first and the last line
    bogons.pop(0) # # last updated 1581670201 (Fri Feb 14 08:50:01 2020 GMT)
    bogons.pop(0) # # Know your network!  Please rigorously test all filters!
    bogons.pop()  # <last empty line on the file>

    return as0_roas_for(bogons, maxLength)

def nro_as0_roas(url):
        delegations = requests.get(url).text.split("\n")
        # Remove header and summaries
        delegations.pop(0) # 2|nro|20200214|574416|19821213|20200214|+0000
        delegations.pop(0) # nro|*|asn|*|91534|summary
        delegations.pop(0) # nro|*|ipv4|*|214428|summary
        delegations.pop(0) # nro|*|ipv6|*|268454|summary
        delegations.pop()  # <last empty line on the file>

        roas = []

        for line in delegations:
            delegation = line.split("|")
            type = delegation[2]
            value = delegation[3]
            length = int(delegation[4])
            status = delegation[6]

            if status == "available" or status == "ianapool" or status == "ietf" or status == "reserved": # meaning !assigned
                if type == "ipv4":
                    v4networks = ipaddress.summarize_address_range(ipaddress.IPv4Address(value), ipaddress.IPv4Address(value)+(length-1))
                    roas += as0_roas_for(v4networks, 32)

                if type == "ipv6":
                    v6networks = [ipaddress.IPv6Network(value+"/"+str(length))]
                    roas += as0_roas_for(v6networks, 128)

        return roas


def peeringDB_roas(maxLength_v4, maxLength_v6):

    roas = []

    url = "https://peeringdb.com/api/ixlan?depth=2"

    s = requests.get(url)

    for i in s.json()['data']:

        for l in i['ixpfx_set']:
            new_entry = {}
            new_entry['asn'] = 0
            new_entry['prefix'] = str(l['prefix'])
            if l['protocol'] == "IPv6":
                new_entry['maxPrefixLength'] = maxLength_v6
            elif l['protocol'] == "IPv4":
                new_entry['maxPrefixLength'] = maxLength_v4

            roas.append(new_entry)

    return roas


def as0_roas_for(bogons, maxLength):
    as0_roas = []

    for network in bogons:
        new_entry = {}
        new_entry['asn'] = 0
        new_entry['prefix'] = str(network)
        new_entry['maxPrefixLength'] = maxLength
        as0_roas.append(new_entry)

    return as0_roas


if __name__ == "__main__":
    main()
