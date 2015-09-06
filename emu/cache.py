'''Direct-mapped, write-back/allocate data memory cache.
'''

# ADDR_BITS = 32
# CACHE_BYTES = 256
# WORD_BYTES = 4
# BLOCK_BYTES = 16

import binascii
import logging as log

ADDR_BITS = 32
WORD_BYTES = 4

# tiny cache c:
CACHE_BYTES = 32
BLOCK_BYTES = 8

num_blocks = CACHE_BYTES / BLOCK_BYTES
index_len = (num_blocks-1).bit_length()
index_mask = num_blocks - 1
offset_len = (BLOCK_BYTES-1).bit_length()
offset_mask = BLOCK_BYTES - 1


def block_base(addr):
    return addr & ~offset_len


def will_straddle(offset):
    return offset + WORD_BYTES > BLOCK_BYTES


class Block(object):
    def __init__(self):
        self.valid = False
        self.dirty = False
        self.tag = 0
        self.data = bytearray([0] * BLOCK_BYTES)


class CacheAddr(object):
    def __init__(self, addr):
        self.raw = addr
        self.offset = addr & offset_mask
        self.index = (addr >> offset_len) & index_mask
        self.tag = addr >> (index_len + offset_len)


class Cache(object):
    def __init__(self, dmem):
        self.cache = [Block() for i in xrange(num_blocks)]
        self.dmem = dmem

    def read(self, addr):
        """Return word at addr, deferring to main mem if necessary."""

        caddr = CacheAddr(addr)
        block = self.cache[caddr.index]
        if block.valid and block.tag == caddr.tag:
            # cache hit
            word = block.data[caddr.offset:caddr.offset+WORD_BYTES]
            if will_straddle(caddr.offset):
                # word was straddling blocks
                try:
                    # TODO this is totally incorrect straddling behavior
                    raise NotImplementedError('straddling read hit not impl')
                    next_block = self.cache[caddr.index+1]
                    word += next_block.data[:WORD_BYTES-len(word)]
                    return word
                except IndexError:
                    # fell off the end of cache, cache miss
                    pass
            else:
                print 'hit cache!'
                return word

        # cache miss

        # write back to cache
        block.valid = True
        block.dirty = False
        block.tag = caddr.tag

        # retrieve block from main memory. need to mask off addr offset to
        # to retrieve correctly aligned block
        block.data = self.dmem.read(block_base(addr), BLOCK_BYTES)
        if will_straddle(caddr.offset):
            # TODO
            raise NotImplementedError('straddling read miss not impl')

        return block.data[caddr.offset:caddr.offset+WORD_BYTES]

    def write(self, addr, word):
        '''Write word into addr, using write-back/allocate strategy.'''

        assert len(word) == WORD_BYTES, \
            'Cache write must be given word sized buffer'

        caddr = CacheAddr(addr)
        block = self.cache[caddr.index]

        if block.valid and block.tag == caddr.tag:
            # cache hit!

            # redundant if this is the second write to this block
            block.dirty = True

            if will_straddle(caddr.offset):
                # straddling blocks
                # TODO
                raise NotImplementedError('straddling write hit not impl')

            block.data[caddr.offset:caddr.offset+WORD_BYTES] = word
        else:
            # cache miss
            if block.valid and block.dirty:
                # need to evict
                self.dmem.write(block_base(addr), block.data)
            # redundant if clean valid block
            block.valid = True
            block.dirty = False
            block.tag = caddr.tag
            block.data = self.dmem.read(block_base(addr), BLOCK_BYTES)
            if will_straddle(caddr.offset):
                # TODO straddle
                raise NotImplementedError('straddling write miss not impl')
            block.data[caddr.offset:caddr.offset+WORD_BYTES] = word

    def dump(self):
        log.info('Total Size: {} bytes'.format(CACHE_BYTES))
        log.info('Block Size: {} bytes'.format(BLOCK_BYTES))
        log.info('Blocks: {}\n'.format(num_blocks))
        log.info('block\tvalid\tdirty\ttag\tdata')
        log.info('-'*40)
        for i, block in enumerate(self.cache):
            log.info('{}\t{}\t{}\t{}\t{}'.format(i, block.valid, block.dirty,
                                                 block.tag, binascii.hexlify(block.data)))
