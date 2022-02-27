#!/usr/bin/python

""" Class representing a stdout logger for the DBT pipeline object """
import logging


class DBTLogger:
    """
    Object representing a DBT logger
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    _loggertag = "[Beautiful DBT Runner]"
    _errortag = f"{_loggertag}(ERROR)"
    _logs = []

    def printlog(self, content: str) -> None:
        """ Prints a log to stdout and adds it to a log list """
        contentoutput = f"{self.loggertag} {content}"
        self._logs.append(contentoutput)
        logging.info(contentoutput)

    def printerror(self, content: str) -> None:
        """ Prints an error to stdout and adds it to a log list """
        contentoutput = f"{self.errortag} {content}"
        self._logs.append(contentoutput)
        logging.info(contentoutput)

    @property
    def logs(self) -> list:
        """Get log list"""
        return self._logs

    @property
    def loggertag(self) -> str:
        """Get log tag"""
        return self._loggertag

    @property
    def errortag(self) -> str:
        """Get error tag"""
        return self._errortag

    def __init__(self):
        pass
