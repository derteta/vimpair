from os import path
from shutil import rmtree
from tempfile import mkdtemp


class Session(object):

  IGNORE_ERRORS = True

  def __init__(self):
    self._session_folder = mkdtemp('Vimpair')

  def end(self):
    rmtree(self._session_folder, self.IGNORE_ERRORS)
    self._session_folder = None

  def prepend_folder(self, filename):
    return path.join(self._session_folder, filename)
