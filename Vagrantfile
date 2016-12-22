# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "debian/contrib-jessie64"
  config.vm.network "forwarded_port", guest: 15672, host: 15672

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
     pip install nose
  SHELL

end
