#!/bin/bash

VIRTUALENV_PATH=/home/application/.top

if [ ! -d $VIRTUALENV_PATH ]
then
	virtualenv $VIRTUALENV_PATH
fi

$VIRTUALENV_PATH/bin/pip install -r /home/application/current/requirements.txt
