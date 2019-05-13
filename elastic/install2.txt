#install java
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt install openjdk-8-jre -y


#elastic 
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-6.x.list
sudo apt-get update
sudo apt-get install -y elasticsearch
sudo python -m pip  install elasticsearch==5.2.0

sudo ufw allow 9200
sudo systemctl enable elasticsearch
sudo systemctl start elasticsearch
curl -X GET "localhost:9200"

