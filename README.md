Vimpair
=======

Plugin that enables remote pair programing

Installation
============

Usage
=====

TODO
====

Features
- Server able to show client its session (single buffer, no splits)
- Server can hand over control to client

Prioritize!
- Port connection
  -- How to inject fake connection for tests in the context of VimpairServerStart?
- Client!
  -- Needs to set up new buffer once first update is received
- [DONE] Move some tests to python

Protocol
- [DONE] Split contents update into parts if buffer contents is too big
- Connection handshake (Do I need that?)
- Handover of control
- Saving
- VimpairStatus

Technical
- [DONE] use ddt to reduce test code

Learnings
- Vimscript
  -- CursorMoved(I) not reported in the scope of a test (event loop?) -> doautocmd
  -- asserts in python calls don't populate v:error
