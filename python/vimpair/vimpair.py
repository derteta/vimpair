import os
from functools import partial

from protocol import (
    generate_contents_update_messages,
    generate_cursor_position_message,
    generate_file_change_message,
    generate_take_control_message,
    generate_save_file_message,
)
from vim_interface import (
    apply_contents_update,
    apply_cursor_position,
    get_current_contents,
    get_current_filename,
    get_current_path,
    get_cursor_position,
    save_current_file,
    show_status_message,
    switch_to_buffer,
)


connector = None


class SendFileChange(object):

    enabled = True
    should_conceal_path = lambda: True

    def __call__(self):
        if self.enabled:
            message = generate_file_change_message(
                get_current_filename(),
                folderpath=get_current_path(),
                conceal_path=self.should_conceal_path(),
            )
            connector.connection.send_message(message)
            update_contents_and_cursor()


def send_contents_update():
    contents = get_current_contents()
    messages = generate_contents_update_messages(contents)
    for message in messages:
        connector.connection.send_message(message)

def send_cursor_position():
    line, column = get_cursor_position()
    connector.connection.send_message(generate_cursor_position_message(line, column))

def update_contents_and_cursor():
    send_contents_update()
    send_cursor_position()

def send_save_file():
    message = generate_save_file_message()
    connector.connection.send_message(message)

send_file_change = SendFileChange()

def check_for_new_client():
    if not connector.is_waiting_for_connection:
        update_contents_and_cursor()
        return True
    return False

def hand_over_control():
    if connector.is_waiting_for_connection:
        show_status_message('No client connected')
        return False
    else:
        show_status_message('Handing over control')
        connector.connection.send_message(generate_take_control_message())
        return True


class VimCallbacks(object):

    def __init__(self, take_control=None, session=None):
        self._take_control = take_control
        self._session = session
        self.update_contents = apply_contents_update
        self.apply_cursor_position = apply_cursor_position

    def take_control(self):
        show_status_message('You are in control now!')
        self._take_control()

    def file_changed(self, filename=None):
        switch_to_buffer(self._session.prepend_folder(filename))

    def save_file(self):
        filename = get_current_filename()
        if filename:
            path = get_current_path()
            if not os.path.exists(path):
                os.makedirs(path)
            filename_and_path = os.path.join(path, filename)
            show_status_message('Saving file "%s"' % filename_and_path)
            save_current_file(filename_and_path)
