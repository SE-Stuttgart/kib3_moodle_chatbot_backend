###############################################################################
#
# Copyright 2020, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

""" This module provides a logger for configurable output on different levels. """
import datetime
import logging
import os
import sys


def exception_logging_hook(exc_type, exc_value, exc_traceback):
    """ Used as a hook to log exceptions. """
    logging.getLogger('error_log').error("Uncaught exception",
                                       exc_info=(exc_type, exc_value, exc_traceback))


class MultilineFormatter(logging.Formatter):
    """ A formatter for the logger taking care of multiline messages. """

    def format(self, record: logging.LogRecord):
        save_msg = record.msg
        output = ""
        for idx, line in enumerate(save_msg.splitlines()):
            if idx > 0:
                output += "\n"
            record.msg = line
            output += super().format(record)
        record.msg = save_msg
        record.message = output
        return output


def configure_error_logger(log_level: str = "WARNING"):
    # create logger
    error_logger = logging.getLogger("error_log")
    error_logger.setLevel(log_level)

    # configure file handler
    logfile_folder = "./logs"
    os.makedirs(os.path.realpath(logfile_folder), exist_ok=True)
    log_file_name = 'errors_' + str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + '.log'
    log_file_path = os.path.join(os.path.realpath(logfile_folder), log_file_name)
    file_handler = logging.FileHandler(log_file_path, mode='w')
    file_handler.setLevel(log_level)
    fh_formatter = MultilineFormatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(fh_formatter)
    error_logger.addHandler(file_handler)

    # configure output to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    # ch_formatter = MultilineFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch_formatter = MultilineFormatter('logger: %(message)s')
    console_handler.setFormatter(ch_formatter)
    error_logger.addHandler(console_handler)

    # log exceptions
    sys.excepthook = exception_logging_hook
