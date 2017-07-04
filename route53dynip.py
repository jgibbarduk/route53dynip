#!/usr/bin/env python
# (c) 2017 - Jason Burks https://github.com/jburks725
import sys
import json
import urllib.request
import time
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

def get_ip():
    ''' get_ip() calls ipinfo.io/json to retrieve your current IP address

    Note that they rate limit to 1000 requests per day for free accounts
    '''
    r = urllib.request.urlopen('http://ipinfo.io/json')
    if r.getcode() != 200:
        if r.getcode() == 429:
            print("Warning: you have exceeded the daily rate limit for ipinfo.io")
        return None
    data = json.loads(r.read().decode(r.info().get_param('charset') or 'utf-8'))
    return data['ip']

def update_route_53(client, zone_id, fqdn, ip_address):
    ''' update_route_53(client, zone_id, fqdn, ip_address) updates the Route 53
    resource record set for fqdn to an A record with a 5 minute TTL pointing to
    the ip_address passed in. It uses an UPSERT change set for this.
    '''
    try:
        response = client.list_resource_record_sets(
            HostedZoneId = zone_id,
            StartRecordName = fqdn,
            StartRecordType = 'A',
            MaxItems = '1'
        )
    except ClientError as e:
        print("Error calling Route 53 API:", e.response['Error']['Message'])
        return
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        print("Error searching for Route 53 Resource Record Set. Aborting.")
        return
    if response['ResourceRecordSets'][0]['Name'] == fqdn:
        # check if the ip address matches and skip the UPSERT
        old_ip_address = \
            response['ResourceRecordSets'][0]['ResourceRecords'][0]['Value']
        if old_ip_address == ip_address:
            return
        print("%s: updating %s from %s to %s" %
            (datetime.now().strftime("%Y-%m-%d %X"), fqdn, old_ip_address,
            ip_address))

    try:
        response = client.change_resource_record_sets(
            HostedZoneId = zone_id,
            ChangeBatch = {
                'Comment': 'Record updated by route53dynip',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': fqdn,
                            'Type': 'A',
                            'TTL': 300,
                            'ResourceRecords': [
                                {
                                    'Value': ip_address
                                },
                            ]
                        }
                    }
                ]
            }
        )
    except ClientError as e:
        print("Error calling Route 53 API:", e.response['Error']['Message'])

    print("Route 53 Change Status:", response['ChangeInfo']['Status'])

def get_hosted_zone(client, name):
    ''' get_host_zone(client, name) gets the Route 53 hosted zone for your
    desired fully qualified domain name.

    It strips the labels from your FQDN one at a time until it finds a hosted
    zone that matches.
    '''
    labels = str.split(name, '.')
    for i in range(len(labels), 2, -1):
        ZoneGuess = '.'.join(labels[-i:])
        try:
            response = client.list_hosted_zones_by_name(
                DNSName = ZoneGuess,
                MaxItems = '1'
            )
        except ClientError as e:
            print("Error calling Route 53 API:", e.response['Error']['Message'])
            return None
        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            print("Error searching for Route 53 Hosted Zone. Aborting.")
            return None
        if response['HostedZones'][0]['Name'] == ZoneGuess:
            return str.split(response['HostedZones'][0]['Id'], '/')[-1]
    print("Error: Could not find a hosted zone for", name)

if len(sys.argv) != 2:
    sys.exit("Error: missing argument for FQDN")

fqdn = sys.argv[1]
if not fqdn.endswith('.'):
    fqdn = fqdn + '.'

client = boto3.client('route53')
zone_id = get_hosted_zone(client, fqdn)
if zone_id == None:
    sys.exit(1)

while True:
    ip = get_ip()
    if not ip == None:
        update_route_53(client, zone_id, fqdn, ip)
    else:
        print("%s: Could not get IP, skipping this interval",
            (datetime.now().strftime("%Y-%m-%d %X")))
    time.sleep(1800)
