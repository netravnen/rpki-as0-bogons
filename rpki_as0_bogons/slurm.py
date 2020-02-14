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
import ipaddress

def main():

    parser = argparse.ArgumentParser(
            description='A script to generate a SLURM file for all bogons with origin AS0')

    parser.add_argument("-f",
            dest='dest_file',
            default="/usr/local/etc/bogons.slurm.txt",
            help="File to be created with all the SLURM content")

    parser.add_argument("--use-delegated-stats",
            dest='use_delegated_stats',
            default=False,
            action='store_true',
            help="Enable the use of NRO delegated stats (EXPERIMENTAL - default bogons list will not be taken in consideration)")

    args = parser.parse_args()


#ipaddress.summarize_address_range(
#     ipaddress.IPv4Address('192.0.2.0'),
#     ipaddress.IPv4Address('192.0.2.130'))]


    if args.use_delegated_stats:
        delegated_stats = "https://www.nro.net/wp-content/uploads/apnic-uploads/delegated-extended"
        r = requests.get(delegated_stats)

        bogons = r.text.split("\n")
        # Remove header and summaries
        print(bogons.pop(0))
        print(bogons.pop(0))
        print(bogons.pop(0))
        print(bogons.pop(0))
        print(bogons.pop())
        print("----------------")

        roas = []

        for line in bogons:
            delegation = line.split("|")
            status = delegation[6]
            type = delegation[2]
            value = delegation[3]
            length = int(delegation[4])
            if status != "assigned":
                if type == "ipv4":
                    ipv4s = ipaddress.summarize_address_range(ipaddress.IPv4Address(value), ipaddress.IPv4Address(value)+(length-1))
                    for ipv4 in ipv4s:
                        new_entry = {}
                        new_entry['asn'] = 0
                        new_entry['prefix'] = str(ipv4.exploded)
                        new_entry['maxPrefixLength'] = 32

                        roas.append(new_entry)

                if type == "ipv6":
                    ipv6 = ipaddress.IPv6Network(value+"/"+str(length))
                    new_entry = {}
                    new_entry['asn'] = 0
                    new_entry['prefix'] = str(ipv6.exploded)
                    new_entry['maxPrefixLength'] = 128

                    roas.append(new_entry)

#             print(status+"-"+type+"-"+value+"-"+length)
#         print(bogons)
    else:
        ipv4_bogons = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv4.txt"
        ipv6_bogons = "https://www.team-cymru.org/Services/Bogons/fullbogons-ipv6.txt"

        roas = as0_roas_for(ipv4_bogons, 32) + as0_roas_for(ipv6_bogons, 128)

    output = {}

    output['slurmVersion'] = 1
    output["validationOutputFilters"] = {}
    output["validationOutputFilters"]["prefixFilters"] = []
    output["validationOutputFilters"]["bgpsecFilter"] = []
    output["locallyAddedAssertions"] = {}
    output["locallyAddedAssertions"]["prefixAssertions"] = []
    output["locallyAddedAssertions"]["bgpsecAssertions"] = []

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
