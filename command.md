yuttana76.dev1@gmail.com
Bom@41121225

AWS

### SSH

ssh -i "dev1_aws.pem" ubuntu@ec2-43-207-211-62.ap-northeast-1.compute.amazonaws.com
ssh -i "dev1_aws.pem" ubuntu@ec2-18-179-45-29.ap-northeast-1.compute.amazonaws.com

### Install Docker 

Install docker frolm this link
https://chonladet.medium.com/iot-ep-4-%E0%B8%95%E0%B8%B4%E0%B8%94%E0%B8%95%E0%B8%B1%E0%B9%89%E0%B8%87-docker-%E0%B9%81%E0%B8%A5%E0%B8%B0-docker-compose-%E0%B8%9A%E0%B8%99-ubuntu-%E0%B8%81%E0%B8%B1%E0%B8%99%E0%B8%84%E0%B8%A3%E0%B8%B1%E0%B8%9A-5d1aeab73c1d

sudo yum update -y
sudo apt update -y

sudo yum install -y docker

sudo systemctl enable docker.service
sudo systemctl start docker.service
sudo systemctl status docker.service

### Add user to docker group
sudo usermod -aG docker ec2-user
sudo usermod -aG docker ubuntu

### Logout and login gain to take effect


### Generrate SSH key for deploy key
ssh-keygen -t ed25519 -C "GitHub Deploy Key"
cat ~/.ssh/id_ed25519.pub 
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIL81mTJVOoXFXtl5GgijszrkCBw2yrj/BNiG4bKFTaf1 GitHub Deploy Key



To git hub>settings>Deploy keys>New deploy key

### To AWS server
git clone git@github.com:yuttana76/django-https-aws.git

### Domain name 
django.holidaystudio.club

holidaystudio.club
DOMAIN=holidaystudio.club


### Getting the first certificate

1.
docker-compose -f docker-compose.deploy.yml run --rm certbot /opt/certify-init.sh
docker-compose -f docker-compose.deploy.yml run certbot /opt/certify-init.sh


docker-compose -f docker-compose.deploy.yml down
docker-compose -f docker-compose.deploy.yml build
docker-compose -f docker-compose.deploy.yml up


### Docker 
To remove all Docker images, use the following command:

docker rmi $(docker images -a -q)

docker rmi $(docker images --filter "dangling=true" -q)

docker image prune --all
