#  Copyright (c) 2023, CRS4
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of
#  this software and associated documentation files (the "Software"), to deal in
#  the Software without restriction, including without limitation the rights to
#  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#  the Software, and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import argparse, sys, ezomero
from importlib import import_module

from promort_tools.libs.utils.logger import get_logger, LOG_LEVELS

SUBMODULES_NAMES = ["slide_path_resolver"]

SUBMODULES = [
    import_module("{0}.{1}".format("promort_tools.ome_adapters", n))
    for n in SUBMODULES_NAMES
]


class OMEAdapter(object):
    def __init__(self):
        self.supported_modules = []
        for m in SUBMODULES:
            m.register(self.supported_modules)

    def make_parser(self):
        parser = argparse.ArgumentParser(description="OMERO adapter for ProMort tools")
        parser.add_argument("--host", type=str, required=True, help="ProMort host")
        parser.add_argument("--port", type=int, default=4064, help="OMERO server port")
        parser.add_argument("--user", type=str, required=True, help="ProMort user")
        parser.add_argument(
            "--passwd", type=str, required=True, help="ProMost password"
        )
        parser.add_argument(
            "--log-level",
            type=str,
            choices=LOG_LEVELS,
            default="INFO",
            help="logging level (default=INFO)",
        )
        parser.add_argument(
            "--log-file", type=str, default=None, help="log file (default=stderr)"
        )
        subparsers = parser.add_subparsers()
        for k, h, addp, impl in self.supported_modules:
            subparser = subparsers.add_parser(k, help=h)
            addp(subparser)
            subparser.set_defaults(func=impl)
        return parser


def main(argv=None):
    app = OMEAdapter()
    parser = app.make_parser()
    args = parser.parse_args(argv)
    logger = get_logger(args.log_level, args.log_file)
    try:
        ome_connection = ezomero.connect(
            host=args.host,
            port=args.port,
            secure=True,
            user=args.user,
            password=args.passwd,
            group="",
        )
        args.func(ome_connection, logger, args)
    except argparse.ArgumentError as arg_err:
        logger.critical(arg_err)
        sys.exit(arg_err)


if __name__ == "__main__":
    main(sys.argv[1:])
