#!/usr/bin/env python
'''Script to connect Muse 2016 by Bluetooth and stream data from it through
LSL. This will create an outlet for EEG in LSL and start pushing samples
through it.'''

import argparse
import logging
import time

# from pylsl import StreamInfo, StreamOutlet, local_clock
import pylsl

# from muse import Muse
import muse


def main(args):
    logging.basicConfig(level=args.loglevel or logging.INFO)

    info = pylsl.StreamInfo(
        name='Muse',
        type='EEG',
        channel_count=5,
        nominal_srate=256,
        channel_format='float32',
        source_id='Muse%s' % args.address)

    info.desc().append_child_value("manufacturer", "Muse")
    channels = info.desc().append_child("channels")

    for c in ['TP9', 'AF7', 'AF8', 'TP10', 'Right AUX']:
        channels.append_child("channel") \
                .append_child_value("label", c) \
                .append_child_value("unit", "microvolts") \
                .append_child_value("type", "EEG")

        outlet = pylsl.StreamOutlet(info, 12, 360)

    def process(data, timestamps):
        for ii in range(12):
            outlet.push_sample(data[:, ii], timestamps[ii])

    m = muse.Muse(
        address=args.address,
        callback=process,
        backend=args.backend,
        time_func=pylsl.local_clock,
        interface=args.interface,
        name=args.name)

    return m


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-v',
        '--verbose',
        help='verbose (debug) logging',
        action='store_const',
        const=logging.DEBUG,
        dest='loglevel')
    parser.add_argument(
        "-a",
        "--address",
        help="device MAC address",
        action='store',
        dest="address",
        default=None,
        type=str)
    parser.add_argument(
        "-n",
        "--name",
        help="name of the device",
        action='store',
        dest="name",
        default=None,
        type=str)
    parser.add_argument(
        "-b",
        "--backend",
        help="pygatt backend to use, can be auto, gatt or bgapi",
        action='store',
        dest="backend",
        default="auto",
        choices=['auto', 'gatt', 'bgapi'],
        type=str)
    parser.add_argument(
        "-i",
        "--interface",
        help="interface to use, 'hci0' for 'gatt' or a com port for bgapi",
        action='store',
        dest="interface",
        default=None,
        type=str)

    args = parser.parse_args()

    muse = main(args)
    muse.connect()
    print('Muse%s connected.' % args.address)
    muse.start()
    print('Muse streaming started.')

    while True:
        try:
            time.sleep(1)
        except:
            break
        finally:
            muse.stop()
            muse.disconnect()
            logging.info('Muse disconnected.')
