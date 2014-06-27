import struct
import bson
from bson.errors import InvalidBSON
import pymongo
import base64
from logging import getLogger

LOG = getLogger(__name__)


def mongodb_decode_wire_protocol(message, deep_decode=True):
    """ http://www.mongodb.org/display/DOCS/Mongo+Wire+Protocol """
    MONGO_OPS = {
        1000: 'msg',
        2001: 'update',
        2002: 'insert',
        2003: 'reserved',
        2004: 'query',
        2005: 'get_more',
        2006: 'delete',
        2007: 'kill_cursors',
    }

    msg_len, msg_id, _, opcode = struct.unpack('<iiii', message[:16])
    # truncate the getlasterror if it's appended here.
    message = message[0:msg_len]
    op = MONGO_OPS.get(opcode, 'unknown')
    zidx = 16

    params = {'op': op,
            'msg_id': msg_id}
    func = _DECODERS.get(op)
    if func:
        try:
            params.update(func(message[zidx:], deep_decode))
        except Exception, e:
            params['error'] = str(e)
            LOG.warning("Unable to decode %s, %r", base64.b64encode(message), params)
    return params


def _decode_docs(message, deep_decode):
    try:
        if deep_decode:
            return bson.decode_all(message)
        return [dict(not_decoded=True)]
    except InvalidBSON, e:
        return [dict(decode_error='invalid bson:  %s' % e)]


def _decode_query_body(message, deep_decode):
    zidx = 0
    options, = struct.unpack('<i', message[zidx:zidx + 4])
    zidx += 4
    collection_name, zidx = _decode_collection_name(message, zidx)
    skip, limit = struct.unpack('<ii', message[zidx:zidx + 8])
    zidx += 8
    msg = _decode_docs(message[zidx:], deep_decode)[0]
    if isinstance(msg, dict):
        try:
            msg = msg['$query']
        except KeyError:
            pass
    return dict(collection=collection_name, query=msg,
                skip=skip, limit=limit, options=options)


def _decode_update_body(message, deep_decode):
    zidx = 0 + len(pymongo.message._ZERO_32)
    collection_name, zidx = _decode_collection_name(message, zidx)
    options, = struct.unpack('<i', message[zidx:zidx + 4])
    msg = _decode_docs(message[zidx + 4:], deep_decode)
    if len(msg) == 1:
        msg.append(msg[0])

    return dict(collection=collection_name, upsert=options & 1,
                multi=options & 2,
                query=msg[0], update=msg[1])


def _decode_insert_body(message, deep_decode):
    zidx = 0
    options, = struct.unpack('<i', message[zidx:zidx + 4])
    zidx += 4
    collection_name, zidx = _decode_collection_name(message, zidx)
    msg = _decode_docs(message[zidx:], deep_decode)

    return dict(continue_on_error=options & 1,
                collection=collection_name,
                docs=msg)


def _decode_delete_body(message, deep_decode):
    zidx = 0 + len(pymongo.message._ZERO_32)
    collection_name, zidx = _decode_collection_name(message, zidx)
    zidx += len(pymongo.message._ZERO_32)
    msg = _decode_docs(message[zidx:], deep_decode)
    return dict(collection=collection_name,
                spec=msg[0])


def _decode_collection_name(message, zidx):
    collection_name_size = message[zidx:].find('\0')
    collection_name = message[zidx:zidx + collection_name_size]
    zidx += collection_name_size + 1
    return collection_name, zidx


_DECODERS = {
             'update': _decode_update_body,
             'insert': _decode_insert_body,
             'query': _decode_query_body,
             'delete': _decode_delete_body,
}
