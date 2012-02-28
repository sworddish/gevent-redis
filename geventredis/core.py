"""
"""

from cStringIO import StringIO
from errno import EINTR
from gevent.socket import socket, error
from gevent import coros

class RedisError(Exception):
    pass

class RedisSocket(socket):

    def __init__(self, *args, **kwargs):
        socket.__init__(self, *args, **kwargs)
        self._rbuf = StringIO()
        self._semaphore = coros.Semaphore()

    def _read(self, size):
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        # Read until size bytes or EOF seen, whichever comes first
        buf_len = buf.tell()
        if buf_len >= size:
            # Already have size bytes in our buffer?  Extract and return.
            buf.seek(0)
            rv = buf.read(size)
            self._rbuf = StringIO()
            self._rbuf.write(buf.read())
            return rv

        self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
        self_recv = self.recv
        buf_write = buf.write
        while True:
            left = size - buf_len
            try:
                data = self_recv(left)
            except error, e:
                if e.args[0] == EINTR:
                    continue
                raise
            if not data:
                break
            n = len(data)
            if n == size and not buf_len:
                return data
            if n == left:
                buf_write(data)
                del data  # explicit free
                break
            assert n <= left, "recv(%d) returned %d bytes" % (left, n)
            buf_write(data)
            buf_len += n
            del data  # explicit free
            #assert buf_len == buf.tell()
        return buf.getvalue()

    def _readline(self):
        buf = self._rbuf
        buf.seek(0, 2)  # seek end
        if buf.tell() > 0:
            # check if we already have it in our buffer
            buf.seek(0)
            bline = buf.readline()
            if bline.endswith('\n'):
                self._rbuf = StringIO()
                self._rbuf.write(buf.read())
                return bline
            del bline
        # Read until \n or EOF, whichever comes first
        buf.seek(0, 2)  # seek end
        self._rbuf = StringIO()  # reset _rbuf.  we consume it via buf.
        self__rbuf_write = self._rbuf.write
        self_recv = self.recv
        buf_write = buf.write
        while True:
            try:
                data = self_recv(8192)
            except error, e:
                if e.args[0] == EINTR:
                    continue
                raise
            if not data:
                break
            nl = data.find('\n')
            if nl >= 0:
                nl += 1
                buf_write(data[:nl])
                self__rbuf_write(data[nl:])
                del data
                break
            buf_write(data)
        return buf.getvalue()


    ## Define the parsers for various messages we may receive
    # +(message)
    def _response_single_line(self, response):
        return response[1:-2]
        
    # -(message)
    def _response_error(self, response):
        return RedisError(response[1:-2])
    
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
            return RedisError('Did not understand response: %s' % response)
    

    def _execute_command(self, *args):
        """Executes a redis command and return a result"""
        data = '*%d\r\n' % len(args) + ''.join(['$%d\r\n%s\r\n' % (len(str(x)), x) for x in args])
        self._semaphore.acquire()
        self.send(data)
        response = self._read_response()
        self._semaphore.release()
        return response

    def _execute_yield_command(self, *args):
        """Executes a redis command and yield multiple results"""
        data = '*%d\r\n' % len(args) + ''.join(['$%d\r\n%s\r\n' % (len(str(x)), x) for x in args])
        self.send(data)
        while 1:
            yield self._read_response()

