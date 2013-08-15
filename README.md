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
Run the program once to set it up.

    cd ~/imapannex; python2 imapannex.py

# Commands for gitannex:

    git config annex.imap-hook '/usr/bin/python2 ~/imapannex/imapannex.py'
    git annex initremote imap type=hook hooktype=imap encryption=shared
    git annex describe imap "the imap library"
    git annex content imap exclude=largerthan=30mb
