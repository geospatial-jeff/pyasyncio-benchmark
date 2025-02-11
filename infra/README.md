## Deployment

First make sure you have `aws-cli` configured with valid AWS credentials and default-region set to `us-west-1` (for data locality with S3 buckets).  Then:

```shell
# install AWS CDK
pip install -r requirements.txt

# bootstrap the CDK (only run once when setting up CDK)
cdk bootstrap

# deploy stack
cdk deploy
```

Go into AWS Systems Manager Parameter Store and look for the key name.  Should look like `/ec2/keypair/key-1234`, then download the key to your local with:

```shell
aws ssm get-parameter --name <key_name> --with-decryption --query "Parameter.Value" --output text > mykey.pem
chmod 400 mykey.pem
```

You can now SSH into the instance:

```shell
ssh -i "mykey.pem" ubuntu@<public_hostname>


## Instance Setup
Next we must get the benchmark running on the instance.  First install several system dependencies:

```shell
sudo apt-get update && apt-get upgrade -y
sudo apt-get install docker.io docker-compose-v2 -y
```

Next we must create a new user group with access to the underlying Unix socket used by Docker, which prevents
us from prefixing every docker command with sudo.

```shell
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

Now we can run the monitoring stack (Prometheus/cAdvisor):

```shell
docker compose -f docker-compose.monitoring.yml up
```

## Port Forwarding
The CDK stack contains a Security Group which exposes Prometheus and cAdvisor on ports 8080: and 9090:, respectively.  These ports may be forwarded via SSH tunnel as follows:

```shell
ssh -i "mykey.pem" -N -L 9090:localhost:9090 ubuntu@ec2-52-53-162-116.us-west-1.compute.amazonaws.com
```

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
