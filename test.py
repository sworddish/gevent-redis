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
    print redis_client.info()
    for msg in redis_client.monitor():
        print msg
        break
    redis_client.bgsave()
    redis_client.save()
    redis_client.config_get()
    redis_client.dbsize()
    redis_client.set('foo', 'bar')
    gevent.sleep(0.1)
    ret = redis_client.get('foo')
    print ret
    if ret != 'bar':
        raise ValueError('Failed to get or set.  Expected "bar" but got %s' % ret)

    redis_client.flushall()
    gevent.sleep(0.1)
    #imperfect check.  Should switch DB to see if that was effected.
    if None != redis_client.get('foo'):
        raise ValueError('Flush failed')
    
    redis_client.set('foo', 'bar')
    redis_client.flushdb()
    gevent.sleep(0.1)
    if None != redis_client.get('foo'):
        raise ValueError('FlushDB failed')
    
    redis_client.lastsave()
    redis_client.ping()
    redis_client.append('foo', 'bar')
    redis_client.append('foo', '2bar')
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
    
    redis_client.setbit('bool', 1, False)
    redis_client.setbit('bool', 2, True)
    gevent.sleep(0.1)
    if redis_client.getbit('bool', 1) or not redis_client.getbit('bool', 2):
        raise ValueError('setbit or getbit failed')
        
    if redis_client.getset('foo', 'xxx') != 'bar':
        raise ValueError('getset failed')
        
    if redis_client.getset('newfoo', 'newbar') != 'newbar':
        raise ValueError('getset failed')
        
    redis_client.keys()
    redis_client.mget('n')
    redis_client.mset({'n':'5', 'o':'6'})
    if '6' != redis_client.get('o'):
        raise ValueError('mset failed')
    
    redis_client.msetnx({'o':'7', 'p':'8'})
    if '7' == redis_client.get('o'):
        raise ValueError('msetnx failed')
    if '8' != redis_client.get('p'):
        raise ValueError('msetnx failed')
    
    redis_client.setex('o', 'newval', 1)
    redis_client.persist('o')
    redis_client.randomkey()
    redis_client.rename('foo', 'newfoo')
    if not redis_client.get('newfoo'):
        raise ValueError('rename failed')
    
    redis_client.set('newfoo', 'newbar')
    redis_client.set('foo', 'bar')
    redis_client.renamenx('foo', 'newfoo')
    if 'bar' == redis_client.get('newfoo'):
        raise ValueError('renamenx failed')
        
    redis_client.flushdb()
    redis_client.setnx('foo', 'bar')
    redis_client.setnx('foo', 'oops')
    if 'bar' != redis_client.get('foo'):
        raise ValuError('setnx failed')
        
    if 3 != redis_client.strlen('foo'):
        raise ValueError('strlen failed')
        
    if 'ar' != redis_client.substr('foo', 1):
        raise ValueError('substr failed')
    if 'ba' != redis_client.substr('foo', 0, 1):
        raise ValueError('substr failed')
        
    redis_client.ttl('foo')
    if 'string' != redis_client.type('foo'):
        raise ValueError('type failed')
        
    ## Skip a lot
    
    ## Hash commands
    redis_client.hset('hoo', 'foo', 'bar')
    if 'bar' != redis_client.hget('hoo', 'foo'):
        raise ValueError('hset/hget failed')
        
    if ['foo'] != redis_client.hkeys('hoo'):
        raise ValueError('hkeys failed')
    if not redis_client.hexists('hoo', 'foo'):
        raise ValueError('hexists failed')
        
    if 1 != redis_client.hlen('hoo'):
        raise ValueError('hlen failed')
        
    redis_client.hdel('hoo', 'foo')
    if 0 != redis_client.hlen('hoo'):
        raise ValueError('hdel or hlen failed')
        
    redis_client.hmset('hoo', {'foo':'bar', 'foo2':'bar2'})
    redis_client.hsetnx('hoo', {'foo':'oops', 'foo3':'bar3'})
    r = redis_client.hmget('hoo', ['foo', 'foo2', 'foo3'])
    if r != ['bar', 'bar2', 'bar3']:
        raise ValueError('hmset, hsetnx or hmget failed')
    
    redis_client.hset('hoo2', 'hoo2foo', 'hoo2bar')
    if ['hoo2bar'] != redis_client.hvals('hoo2'):
        raise ValueError('hvals failed')
        
    
    

if __name__ == '__main__':
    test()
