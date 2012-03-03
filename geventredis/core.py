"""
"""

from cStringIO import StringIO
from errno import EINTR
from gevent.socket import socket, error
from gevent import coros, select, spawn

class RedisError(Exception):
    pass

class RedisSocket(socket):

    def __init__(self, *args, **kwargs):
        socket.__init__(self, *args, **kwargs)
        self._rbuf = StringIO()
        self._semaphore = coros.Semaphore()
        spawn( self._drain )

    def _read(self, size):
        return self.recv(size)
    
    def _readline(self):
        '''Read the receive buffer one char at a time until we find \n, return sans the trailing \r\n'''
        ret = []
        while True:
            ret.append( self.recv(1) )
            if ret[-1] == '\n':
                break
        return ''.join( ret )
        
    def _drain(self):
        '''Keep the socket clear when not expecting any callbacks'''
        while True:
            ready, w, x = select.select( [self], [], [] )
            if not self._semaphore.locked():
                '''We're here if there's data in the receive buffer but no one's reading'''
                junk = self.recv(1)
            else:
                self._semaphore.wait()
    

    ## Define the parsers for various messages we may receive
    # +(message)
    def _response_single_line(self, response):
        return response[1:-2]
        
    # -(message)
    def _response_error(self, response):
        raise RedisError(response[1:-2])
    
    # :nn
    def _response_integer(self, response):
        return int(response[1:])
    
    # $nn            length.  -1 = Null
    # (binary data)
    def _response_bulk(self, response):
        number = int(response[1:])
        if number == -1:
            return None
        else:
            return self._read(number+2)[:-2]

    # *nn            length.  -1 = Null
    # (any of the above messages)
    def _response_multi_bulk(self, response):
        number = int(response[1:])
        if number == -1:
            return none
        else:
            return [ self._read_response() for i in xrange(number) ]

    ## Create a dict to parse each message
    _response_dict = {
        '+': _response_single_line,
        '-': _response_error,
        ':': _response_integer,
        '$': _response_bulk,
        '*': _response_multi_bulk,
        }
    
    def _read_response(self):
        response = self._readline()
        try:
            return self._response_dict[ response[0] ]( self, response )
        except IndexError:
            raise RedisError('Did not understand response: %s' % response)
    

    def _execute_command(self, *args):
        """Executes a redis command and return a result"""
        data = '*%d\r\n' % len(args) + ''.join(['$%d\r\n%s\r\n' % (len(str(x)), x) for x in args])
        self._semaphore.acquire()
        self.send(data)
        try:
            response = self._read_response()
        finally:
            self._semaphore.release()
        return response

    def _execute_yield_command(self, *args):
        """Executes a redis command and yield multiple results"""
        data = '*%d\r\n' % len(args) + ''.join(['$%d\r\n%s\r\n' % (len(str(x)), x) for x in args])
        self._semaphore.acquire()
        self.send(data)
        while 1:
            yield self._read_response()
            
        #never gets here, but shown for completeness
        self._semaphore.release()

