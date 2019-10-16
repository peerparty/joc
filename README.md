# joc

Joc is the platform basis for WIN WIN 🌈.

WIN WIN is a discussion and participatory performance based on consensus and inspired simultaneously from the likes of digital algorithms like paxos, movements and flat hierarchical organizational structures like occupy, holacracy and sociocracy and borrows a bit from anarchist philosophy, the squatting movement and the dutch polder model.

WIN WIN does not promise consensus on a starting statement but rather uses a tree descent algorithm to uncover moments of consensus in a complex conversation.

## Starting joc

    $ ./server.sh

For example: "Friends who fly be shamed."

# Websocket messages

All messages between components and actors are delivered via web sockets in JSON packages.

## Screen messages

### SCREEN\_INIT

A screen is added to the system. Contains a list of past consensus statements to show, the next statement to be considered, the start time of the next session and the screens unique id.

    { 'cmd': 'SCREEN_INIT', 'data': [ <stmt 0>, <stmt 1> ], 'stmt': <stmt>, 'start_time': <time>, 'id': <server_id> }

### SCREEN\_CONSENSUS

Consensus has occured.

    { 'cmd': 'SCREEN_CONSENSUS', 'data': <stmt>, 'id': <server_id> }

### SCREEN\_START

A new session is starting.

    { 'cmd': 'SCREEN_START' }

### SCREEN\_TREE

A user has performed an action, the state of the system has changed.

    { 'cmd': 'SCREEN_TREE', 'data': <json object representing the state of the system> }

### SCREEN\_NOT\_ENOUGH

Not enough users joined the session.

    { 'cmd': 'SCREEN_NOT_ENOUGH' }

## User messages

### USER\_JOIN

A new user has joined.

    { 'cmd': 'USER_JOIN', 'count': <number of participating users> }

### USER\_WAIT

There are not enough users to begin, so tell user to wait.

    { 'cmd': 'USER_WAIT' }

### USER\_NOT\_ENOUGH

Not enough users joined the session, the current user will also need to join laster.

    { 'cmd': 'USER_NOT_ENOUGH' }

### USER\_DONE

The experience is over, either time expired or there is consensus on the starting statement.  `data` contains a list of statements where there was consensus during the experience.

    { 'cmd': 'USER_DONE', 'data': [ <stmt 0>, <stmt 1>, ... <stmt n> ]

### USER\_TUTORIAL

Start the tutorial animation.

    { 'cmd': 'USER_TUTOIAL' }

### USER\_QUESTION

User sees a statement for the sent amound of time.

    { 'cmd': 'USER_QUESTION', 'txt': <stmt> 'time': <time> }


# Development Environment setup

## Docker setup

You only ever do this once.

    $ docker run -p 80:80 --name winwin -it debian:latest

## Update apt

    $ apt update

## Install git

    $ apt install git

## Install nginx

    $ apt install nginx

## Install a text editor

    $ apt install nano

## Install python

    $ apt install python3

## Install python pip

    $ apt install python3-pip

## Install pip dependencies

### SimpleWebSocketServer

    $ pip3 install --user SimpleWebSocketServer

### anytree 

    $ pip3 install --user anytree

## Configure nginx

Edit the default site for nginx.

    $ nano /etc/nginx/sites-enabled/default

Add the follow: 

    map $http_upgrade $connection_upgrade {
            default upgrade;
            ''      close;
    }

    server {
            listen 80 default_server;
            listen [::]:80 default_server;

            root /var/www/html/winwin-app;

            location /ws/ {
                    proxy_pass http://127.0.0.1:8000;
                    proxy_http_version 1.1;
                    proxy_set_header Upgrade $http_upgrade;
                    proxy_set_header Connection $connection_upgrade;
                    proxy_read_timeout 86400;
            }

            location / {
                    try_files $uri $uri/ =404;
            }
    }

## Start nginx

    $ nginx

## Add your ssh keys to your container

    $ mkdir .ssh

*From another terminal*

    $ docker cp ~/.ssh/id_rsa winwin:/root/.ssh

    $ docker cp ~/.ssh/id_rsa.pub winwin:/root/.ssh

## Get the winwin-app html/js/css code

    $ cd /var/www/html

    $ git clone git@github.com:peerparty/winwin-app.git

## Get the joc python server code

    $ cd

    $ git clone git@github.com:peerparty/joc.git

## Run the python server

    $ cd joc

    $ ./server.py

## Open browser

    `http://localhost/`

### The screen

    `http://localhost/screen.html`

## Good stuff to know

### Stopping nginx

    $ nginx -s stop

### Starting your docker container

    $ docker start -i winwin

