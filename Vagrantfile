# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "debian/contrib-jessie64"

  # Rabbit MQ management
  config.vm.network "forwarded_port", guest: 15672, host: 15672

  # HTTP for viewing coverage reports
  config.vm.network "forwarded_port", guest: 80, host: 8765

  config.vm.provision "shell", inline: <<-SHELL
     apt-get update
     apt-get install -y htop curl python python-setuptools python-pip python-dev build-essential rabbitmq-server
     pip install --upgrade pip setuptools

     /usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_management
     sudo service rabbitmq-server restart
     rabbitmqctl add_user user user
     rabbitmqctl set_permissions -p / user ".*" ".*" ".*"
     rabbitmqctl set_user_tags user administrator

     # Install deps
     pip install -r /vagrant/requirements.txt
     pip install nose coverage

     # HTTP server for viewing coverage reports
    apt-get -y install nginx
    rm -rf /var/www/html
    ln -s /vagrant/htmlcov /var/www/html

    # .bashrc for default user
    echo """# .bashrc
    cd /vagrant""" > /home/vagrant/.bashrc

  SHELL

end
