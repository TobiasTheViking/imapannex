imapannex
=========

Hook program for gitannex to use imap as backend

# Requirements:

    python2

# Install
Clone the git repository in your home folder.

    git clone git://github.com/TobiasTheViking/imapannex.git 

This should make a ~/imapannex folder

# Setup
Make the file executable, and link it into PATH

    cd ~/imapannex; chmod +x git-annex-remote-imap; sudo ln -sf `pwd`/git-annex-remote-imap /usr/local/bin/git-annex-remote-imap

# Commands for gitannex:

    USERNAME="username@provider.com" PASSWORD="password" git annex initremote imap type=external externaltype=imap encryption=shared folder=gitannex method="Normal password" ssl="SSL/TLS" host="imap.host.com" port="993"
    git annex describe imap "the imap library"
