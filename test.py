#!/usr/bin/env python

import sys, os, re, time
import geventredis, gevent

def test():
    ## Not checked:
    # shutdown
    # expire
    # expireat
    # slaveof
    # config_set
    # bgwriteaof
    # move
    # setrange
    # watch
    # unwatch
    # No list commands
    # No set commands
    # No sorted set commands
    # publish/subscribe/monitor commands
    
    ## Not really verified:
    # setex
    # persist
    # info
    # save
    # config_get
    # dbsize
    # ttl
    

    reply = raw_input("Warning:  This test will flush any data out of the localhost Redis server!  Type OK:  ")
    if reply.upper() != 'OK':
        print("Not OK?  Sorry, I can't test.")
        return
    redis_client = geventredis.connect()
    x =  redis_client.info()
    #for msg in redis_client.monitor():
    #    print msg
    #    break
    print( "save: %s" % redis_client.save() )
    print( "bgsave: %s" % redis_client.bgsave() )
    x = redis_client.config_get()
    x = redis_client.dbsize()
    print( "set: %s" % redis_client.set('foo', 'bar') )
    gevent.sleep(0.1)
    ret = redis_client.get('foo')
    if ret != 'bar':
        raise ValueError('Failed to get or set.  Expected "bar" but got %s' % ret)

    print( "flushall: %s" % redis_client.flushall() )
    gevent.sleep(0.1)
    #imperfect check.  Should switch DB to see if that was effected.
    if None != redis_client.get('foo'):
        raise ValueError('Flush failed')
    
    x = redis_client.set('foo', 'bar')
    print( "flushdb: %s" % redis_client.flushdb() )
    gevent.sleep(0.1)
    if None != redis_client.get('foo'):
        raise ValueError('FlushDB failed')
    
    print( "lastsave: %s" % redis_client.lastsave() )
    print( "ping: %s" % redis_client.ping() )
    print( "append: %s" % redis_client.append('foo', 'bar') )
    x = redis_client.append('foo', '2bar')
    gevent.sleep(0.1)
    if 'bar2bar' != redis_client.get('foo'):
        raise ValueError('append failed')
    
    if 1 != redis_client.incr('n'):
        raise ValueError('incr failed')
    if -1 != redis_client.decr('-n'):
        raise ValueError('decr failed')
    gevent.sleep(0.1)

    if redis_client.exists('nope') or not redis_client.exists('n'):
        raise ValueError('exists failed')
    
    print( "setbit: %s" % redis_client.setbit('bool', 1, False) )
    x = redis_client.setbit('bool', 2, True)
    gevent.sleep(0.1)
    if redis_client.getbit('bool', 1) or not redis_client.getbit('bool', 2):
        raise ValueError('setbit or getbit failed')
        
    x = redis_client.set('foo', 'bar')
    ret = redis_client.getset('foo', 'newbar')
    if ret != 'bar':
        raise ValueError('getset failed.  Expected "bar", but %s' % ret)
    
    ret = redis_client.getset('foo', 'bar') 
    if ret != 'newbar':
        raise ValueError('getset failed.  Expected "newbar", got %s' % ret)
        
    x = redis_client.keys()
    x = redis_client.mget('n')
    print( "mset: %s" % redis_client.mset({'n':'5', 'o':'6'}) )
    if '6' != redis_client.get('o'):
        raise ValueError('mset failed')
    
    print( "msetnx: %s" % redis_client.msetnx({'o':'7', 'p':'8'}) )
    ret = redis_client.get('o')
    if '7' == ret:
        raise ValueError('msetnx failed.  Expected "6" but got %s' % ret)
    ret = redis_client.get('p')
    if ret:
        raise ValueError('msetnx failed.  Expected None but got %s' % ret)
    
    print( "setex: %s" % redis_client.setex('o', 'newval', 1) )
    print( "persist: %s" % redis_client.persist('o') )
    print( "randomkey: %s" % redis_client.randomkey() )
    print( "rename: %s" % redis_client.rename('foo', 'newfoo') )
    if not redis_client.get('newfoo'):
        raise ValueError('rename failed')
    
    x = redis_client.set('newfoo', 'newbar')
    x = redis_client.set('foo', 'bar')
    print( "renamex: %s" % redis_client.renamenx('foo', 'newfoo') )
    if 'bar' == redis_client.get('newfoo'):
        raise ValueError('renamenx failed')
        
    redis_client.flushdb()
    print( "setnx: %s" % redis_client.setnx('foo', 'bar') )
    redis_client.setnx('foo', 'oops')
    if 'bar' != redis_client.get('foo'):
        raise ValuError('setnx failed')
        
    if 3 != redis_client.strlen('foo'):
        raise ValueError('strlen failed')
        
    if 'ar' != redis_client.substr('foo', 1):
        raise ValueError('substr failed')
    if 'ba' != redis_client.substr('foo', 0, 1):
        raise ValueError('substr failed')
        
    print( "ttl: %s" % redis_client.ttl('foo') )
    
    ret =  redis_client.type('foo')
    if 'string' != ret:
        raise ValueError('type failed.  Expected "string" got %s'%ret)
        
    ## Skip a lot
    
    ## Hash commands
    print( "hset: %s" % redis_client.hset('hoo', 'foo', 'bar') )
    if 'bar' != redis_client.hget('hoo', 'foo'):
        raise ValueError('hset/hget failed')
        
    if ['foo'] != redis_client.hkeys('hoo'):
        raise ValueError('hkeys failed')
    if not redis_client.hexists('hoo', 'foo'):
        raise ValueError('hexists failed')
        
    if 1 != redis_client.hlen('hoo'):
        raise ValueError('hlen failed')
        
    print( "hdel: %s" % redis_client.hdel('hoo', 'foo') )
    if 0 != redis_client.hlen('hoo'):
        raise ValueError('hdel or hlen failed')
        
    print( "hmset: %s" % redis_client.hmset('hoo', {'foo':'bar', 'foo2':'bar2'}) )
    print( "hsetnx: %s" % redis_client.hsetnx('hoo', 'foo', 'oops') )
    r = redis_client.hmget('hoo', ['foo', 'foo2', 'foo3'])
    if r != ['bar', 'bar2', None]:
        raise ValueError('hmset, hsetnx or hmget failed.  Expected ["bar", "bar2", None] but got %s' % r)
    
    x = redis_client.hset('hoo2', 'hoo2foo', 'hoo2bar')
    if ['hoo2bar'] != redis_client.hvals('hoo2'):
        raise ValueError('hvals failed')
    
    # try saving data with embedded \r\n
    print("set with tough data: %s" % redis_client.set('foo', 'bar\r\nbar') )
    ret = redis_client.get('foo')
    if ret != 'bar\r\nbar':
        raise ValueError('set/get failed with embedded termination')
    
    # try to break with spurious data
    print("\ntest spurious data...")
    try:
        print("sending 'bad command!'")
        ret = redis_client._execute_command('bad command!')
    except geventredis.RedisError as e:
        print("correctly caught bad command: %s" % e)
    else:
        raise ValueError('failed to catch bad command. Excpeted RedisError exception, got %s', ret)
        
    redis_client.send('PING\r\n')
    gevent.sleep(0.1)
    print( "set: %s" % redis_client.set('foo', 'bar') )
    ret = redis_client.get('foo')
    if ret != 'bar':
        raise ValueError('get or set failed with spurious data.')
    
    print( "\nflushing all test data: %s" % redis_client.flushall() )

    
    print "\nAll tests passed."

if __name__ == '__main__':
    test()
