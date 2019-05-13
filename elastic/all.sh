#install python
sudo ufw allow "OpenSSH"
sudo ufw enable
sudo apt-get update
sudo apt-get install -y python
sudo apt-get install -y python-pip


#install cassandra
echo "deb http://www.apache.org/dist/cassandra/debian 22x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
echo "deb-src http://www.apache.org/dist/cassandra/debian 22x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
sudo apt-get update
gpg --keyserver pgp.mit.edu --recv-keys F758CE318D77295D
gpg --export --armor F758CE318D77295D | sudo apt-key add -
gpg --keyserver pgp.mit.edu --recv-keys 2B5C1B00
gpg --export --armor 2B5C1B00 | sudo apt-key add -
gpg --keyserver pgp.mit.edu --recv-keys 0353B12C
gpg --export --armor 0353B12C | sudo apt-key add -
sudo apt-get update
sudo apt-get install cassandra
sudo service cassandra start

#install apache
sudo apt-get update
sudo apt-get install -y apache2 libapache2-mod-wsgi
sudo a2enmod wsgi 
sudo ufw allow "Apache Full"
sudo apt-get install -y curl


#install Mongo
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.4.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl enable mongod
sudo systemctl start mongod
sudo ufw allow 27017

#install java
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt install openjdk-8-jre -y
java -version

#install cassandra
echo "deb http://www.apache.org/dist/cassandra/debian 22x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
echo "deb-src http://www.apache.org/dist/cassandra/debian 22x main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
sudo apt-get update
gpg --keyserver pgp.mit.edu --recv-keys F758CE318D77295D
gpg --export --armor F758CE318D77295D | sudo apt-key add -
gpg --keyserver pgp.mit.edu --recv-keys 2B5C1B00
gpg --export --armor 2B5C1B00 | sudo apt-key add -
gpg --keyserver pgp.mit.edu --recv-keys 0353B12C
gpg --export --armor 0353B12C | sudo apt-key add -
sudo apt-get update
sudo apt-get install -y cassandra
sudo service cassandra start


#install Flask 
sudo python -m pip install flask
sudo python -m pip install pymongo
sudo python -m pip install flask_cors
sudo python -m pip install flask_mail
sudo python -m pip install cassandra-driver
sudo python -m pip install uwsgi


sudo apt-get install -y sendmail

