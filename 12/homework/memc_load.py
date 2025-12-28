#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import glob
import gzip
import logging
import os
import queue
import sys
import threading
from dataclasses import dataclass, field
from optparse import OptionParser

import appsinstalled_pb2
import memcache

NORMAL_ERR_RATE = 0.01
TASK_QUEUE_MAX_SIZE = 10000
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_appsinstalled(memc_addr, memc, appsinstalled, dry_run=False):
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()
    try:
        if dry_run:
            ...
            # logging.debug("%s - %s -> %s" % (memc_addr, key, str(ua).replace("\n", " ")))
        else:
            memc.set(key, packed)
    except Exception as e:
        logging.exception("Cannot write to memc %s: %s" % (memc_addr, e))
        return False
    return True


def parse_appsinstalled(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.strip().isdigit()]
        logging.info("Not all user apps are digits: `%s`" % line.strip())
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line.strip())
        return
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


@dataclass
class Stats:
    processed: int = 0
    errors: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def inc_processed(self):
        with self.lock:
            self.processed += 1

    def inc_errors(self, count=1):
        with self.lock:
            self.errors += count


def worker(task_queue, dry_run):
    clients = {}
    while True:
        task = task_queue.get()
        if task is None:
            task_queue.task_done()
            break
        memc_addr, appsinstalled, stats = task
        memc = clients.get(memc_addr)
        if memc is None:
            memc = memcache.Client([memc_addr])
            clients[memc_addr] = memc
        ok = insert_appsinstalled(memc_addr, memc, appsinstalled, dry_run)
        if ok:
            stats.inc_processed()
        else:
            stats.inc_errors()
        task_queue.task_done()


def main(options):
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }
    if options.workers < 1:
        logging.warning("Workers must be >= 1, falling back to 1")
        options.workers = 1
    task_queue = queue.Queue(maxsize=TASK_QUEUE_MAX_SIZE)
    workers = []
    for _ in range(options.workers):
        thread = threading.Thread(target=worker, args=(task_queue, options.dry))
        thread.daemon = True
        thread.start()
        workers.append(thread)

    for fn in sorted(glob.iglob(options.pattern)):
        stats = Stats()
        logging.info("Processing %s" % fn)
        with gzip.open(fn, "rt", encoding="utf-8", errors="ignore") as fd:
            for line in fd:
                line = line.strip()
                if not line:
                    continue
                appsinstalled = parse_appsinstalled(line)
                if not appsinstalled:
                    stats.inc_errors()
                    continue
                memc_addr = device_memc.get(appsinstalled.dev_type)
                if not memc_addr:
                    stats.inc_errors()
                    logging.error("Unknown device type: %s" % appsinstalled.dev_type)
                    continue
                task_queue.put((memc_addr, appsinstalled, stats))

        task_queue.join()
        if not stats.processed:
            dot_rename(fn)
            continue

        err_rate = float(stats.errors) / stats.processed
        if err_rate < NORMAL_ERR_RATE:
            logging.info("Acceptable error rate (%s). Successfull load" % err_rate)
        else:
            logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
        dot_rename(fn)

    for _ in workers:
        task_queue.put(None)
    task_queue.join()


def prototest():
    sample = "idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\ngaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424"
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="/data/appsinstalled/*.tsv.gz")
    op.add_option("--workers", action="store", type="int", default=4)
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log,
        level=logging.INFO if not opts.dry else logging.DEBUG,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
