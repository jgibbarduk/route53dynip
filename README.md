# Route 53 Dynamic IP
A simple Python script running in a Docker container to maintain an A record
in Route 53 for a dynamic IP. Why pay (more) for DDNS services?

## Building the Docker image
The `Dockerfile` in this repo will build an image based on `python:alpine`
from DockerHub. It copies the Python script into `/`, and executes as user
`nobody`.

## Running the Docker container
The Python script is the `ENTRYPOINT`, so you need only specify the
FQDN you want added to Route 53 Hosted Zone as an argument to the `docker run`
command.

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

## IAM Policy
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
