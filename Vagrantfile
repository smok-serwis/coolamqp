# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  config.vm.box = "debian/contrib-stretch64"

  # Rabbit MQ management
  config.vm.network "forwarded_port", guest: 15672, host: 15672, auto_correct: true

  # HTTP for viewing coverage reports
  config.vm.network "forwarded_port", guest: 80, host: 8765

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    
    # Python
    apt-get install -y htop curl python python-setuptools python-pip python-dev build-essential rabbitmq-server python3 python3-pip python3-setuptools
    sudo python -m pip install --upgrade pip setuptools
    sudo pip3 install --upgrade pip setuptools
    
    /usr/lib/rabbitmq/bin/rabbitmq-plugins enable rabbitmq_management
    sudo service rabbitmq-server restart
    rabbitmqctl add_user user user
    rabbitmqctl set_permissions -p / user ".*" ".*" ".*"
    rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"
    rabbitmqctl set_user_tags user administrator
    
    # Install deps
    sudo python -m pip install -r /vagrant/requirements.txt
    sudo python -m pip install nose coverage mock yapf
    sudo pip3 install -r /vagrant/requirements.txt
    sudo pip3 install nose2[coverage_plugin] coverage mock yapf nose2
    
    sudo pip3 install -r /vagrant/stress_tests/requirements.txt
    
    # HTTP server for viewing coverage reports
    apt-get -y install nginx
    rm -rf /var/www/html
    ln -s /vagrant/htmlcov /var/www/html
    
    # .bashrc for default user
    echo """# .bashrc
    cd /vagrant""" > /home/vagrant/.bashrc

  SHELL

end
