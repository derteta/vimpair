Vimpair
=======

[![Build Status](https://travis-ci.org/derteta/vimpair.svg?branch=master)](https://travis-ci.org/derteta/vimpair)

A vim plugin for remote pair programing between 2 computers.

In a Vimpair session, one computer acts as the server providing the files to edit; the other computer is a client receiving the files' contents. Each paticipant will take either of 2 roles: the *Editor* and the *Observer*. Changes to the current file made by the *Editor* are sent to the *Observer*. Roles can be switched at any time, the *Editor* only needs to hand over control to the *Observer*. Should the *Observer* edit the file, changes are not sent back and will be overwritten by the next update from the *Editor*.

Installation
============
You can use your favorite plugin manager to install Vimpair.

Usage
=====
The server is started by calling `:VimpairServerStart`. The client is started in a similar fashion; however, the server's address should be specified: `:VimpairClientStart "127.0.0.1"`. If the address is ommitted, the client will look for a server on the same computer (`localhost`).

During the session, control can be handed over with `:VimpairHandover`.

Vimpair defines some variables that can be tweaked to alter its behavior:

 - `let g:VimpairShowStatusMessages = 1` - set this to `0` if you don't want Vimpair to show you status messages.
 - `let g:VimpairTimerInterval = 200` - Vimpair's timer is used to wait for clients or updates from the *Editor*. Setting this to a lower value (in Milliseconds) will result in more fluent updates but also in higher CPU usage.

Both participants can leave the session at any time calling `:VimpairServerStop` or `:VimpairClientStop`.

FAQ
===
###Why are there only 2 participants in a session?
Vimpair is developed as a simple solution for pair programming. Involving more than 2 participants would need a more complex management of control.

###Can Vimpair connect to editors other than Vim?
Currently, there are no other implementations of the protocol Vimpair uses. It should, however, be possible to port it to other editors.
