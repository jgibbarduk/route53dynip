# Route 53 Dynamic IP
A simple Python script running in a Docker container to maintain an A record
in Route 53 for a dynamic IP. Why pay (more) for DDNS services?

## What It Does
When it starts, this Python script takes the FQDN you've passed in and
attempts to find the ZoneId of the Route 53 hosted zone to add the entry
to. It does this by iteratively stripping the left-most label from the FQDN
(starting with the FQDN, in case you want your A record at a zone apex) until
it finds a hosted zone whose name matches. If it cannot find one, it prints
out an error message and exits.

After getting the ZoneId, the script executes the following in an infinite
loop:
1. It makes a call to http://ipinfo.io/json to get your current
IP address. If it cannot retrieve the IP (rate limiting?), skip to step 4.
2. It looks up the FQDN in the hosted zone and compares the current IP address
to the one looked up in step 1. If they match, skip to step 4.
3. It executes `Route53.ChangeResourceRecordSets` to UPSERT an A record with
a 5 minute TTL pointing to the current IP address.
4. Sleep for 30 minutes.

### Rate Limits at http://ipinfo.io
This service currently rate-limits you to 1000 requests a day. I chose to poll
on a 30 minute interval. If your IP address is changing more often than that,
you either need to change ISPs, consider paying them for a static IP, or host
whatever you're hosting at AWS directly and leverage other AWS features like
Route 53 Alias Records and ALBs/ELBs. 

### Providing Credentials
You need to provide AWS credentials to the Python script in order to run this.
You can do this in one of two ways: environment variables, or mounting an
AWS `credentials` file as a volume. If you create a separate profile in your
credentials file, you can specify the `AWS_PROFILE` environment variable to
use it.

```bash
# Pass credentials directly via environment variables
$ docker run -d -e AWS_ACCESS_KEY_ID={YOUR_KEY} -e AWS_SECRET_ACCESS_KEY=\
{YOUR_SECRET_KEY} jburks725/route53dynip mydynamic.hostname.com
# OR use a credentials file with a profile (named route53 in the example)
# and mount your credentials into the container
$ docker run -d -e AWS_PROFILE=route53 -v $HOME/.aws:/.aws \
jburks725/route53dynip mydynamic.hostname.com
```

### IAM Policy
It's recommended that you create a separate IAM user for running this, and
that you grant it only the permissions necessary to create the A record
you want.

You'll want to look up the Route 53 ZoneId of the target Hosted Zone (easiest
to do that via the console), and substitute it into the policy below. This
allows listing your zones, and modifications to only the appropriate zone).

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ListHostedZones",
                "route53:ListHostedZonesByName"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "route53:ListResourceRecordSets",
                "route53:ChangeResourceRecordSets"
            ],
            "Resource": [
                "arn:aws:route53:::hostedzone/#{ZoneIdHere}"
            ]
        }
    ]
}
```

Once you've created that policy, create a new IAM user and generate a keypair
for it. You may create a profile in your `~/.aws/credentials` file, or pass
the credentials directly via environment variables.

## Building the Docker image
The `Dockerfile` in this repo will build an image based on `python:alpine`
from DockerHub. It copies the Python script into `/`, and executes as user
`nobody`.

The latest version of this image should be available on DockerHub

## Running the Docker container
The Python script is the `ENTRYPOINT`, so you need only specify the
FQDN you want added to Route 53 Hosted Zone as an argument to the `docker run`
command.

# TODO
1. Allow customization of TTL
2. Allow custom polling interval (currently 30 minutes)
3. Maybe some logging verbosity control?
4. Learn Python better!
