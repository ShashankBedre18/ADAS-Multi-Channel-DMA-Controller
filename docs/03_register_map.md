# 3. Register map (APB, 12-bit address, 32-bit data)

Reserved/unmapped addresses return `PSLVERR`. All registers are zero-wait-state.

## 3.1 Global registers

| Offset | Name | Access | Reset | Fields |
|---|---|---|---|---|
| 0x000 | GCTRL | RW | 0 | `[0]` EN (global enable) |
| 0x004 | GSTAT | RO | 0 | `[3:0]` channel active  `[8]` engine busy |
| 0x008 | IRQ_SUM | RO | 0 | `[3:0]` per-channel irq lines |
| 0x00C | VERSION | RO | 0x00010000 | |

## 3.2 Channel registers

Channel *n* window base = `0x100 + n * 0x40`  (CH0 0x100, CH1 0x140, CH2 0x180, CH3 0x1C0).

| Offset | Name | Access | Reset | Fields |
|---|---|---|---|---|
| +0x00 | CTRL | RW | 0 | `[0]` EN  `[1]` START (pulse, reads 0)  `[2]` SRC_STREAM (1 = sensor stream, 0 = memory)  `[5:4]` PRIO (3 = most critical)  `[11:8]` BLEN (beats-1: 0..15) |
| +0x04 | SRC | RW | 0 | source byte address (word aligned, ignored for streams) |
| +0x08 | DST | RW | 0 | destination byte address (word aligned) |
| +0x0C | LEN | RW | 0 | transfer length in **words** `[23:0]` (1..16 M) |
| +0x10 | INT_EN | RW | 0 | `[0]` DONE  `[1]` ERR |
| +0x14 | INT_STAT | RW1C | 0 | `[0]` DONE  `[1]` ERR |
| +0x18 | STATUS | RO | 0 | `[0]` ACTIVE  `[1]` IN_FLIGHT (a burst is on the bus)  `[4:2]` ERR_CODE  `[13:8]` FIFO_LEVEL |
| +0x1C | REMAIN | RO | 0 | words left in the current transfer |
| +0x20 | XFERRED | RO | 0 | words moved since the last START |

`ERR_CODE`: 0 none, 1 SLVERR, 2 DECERR, 3 illegal configuration.

## 3.3 Start-up sequence (software view)

```c
write(GCTRL,  1);                     // enable
// radar: sensor stream, priority 3, 4-beat bursts, 256 words
write(CH1_DST,    0x80100000);
write(CH1_LEN,    256);
write(CH1_INT_EN, 0b11);              // DONE | ERR
write(CH1_CTRL,   (3<<8) | (3<<4) | (1<<2) | (1<<1) | 1);   // BLEN=3 PRIO=3 STREAM START EN
// ... wait for irq ...
st = read(CH1_INT_STAT);  write(CH1_INT_STAT, st);           // acknowledge
```

## 3.4 Rules enforced by hardware

* `START` while a channel is already active is ignored.
* `START` with `EN=0`, `LEN=0`, an unaligned `DST`, or (memory source) an unaligned `SRC` sets `INT_STAT.ERR`, `ERR_CODE=3` and does nothing else.
* A new `START` clears `ERR_CODE`, `XFERRED`, and flushes the channel FIFO.
* If an interrupt event and a software clear of the same bit happen in the same cycle, the event wins.
