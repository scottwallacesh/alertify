#!/usr/bin/python3
"""
Main entrypoint to run Alertify
"""

import argparse
import logging
import os
import sys

from src import alertify

if __name__ == '__main__':

    def parse_cli():
        """
        Function to parse the CLI
        """
        maxlen = max([len(key) for key in alertify.Config.defaults()])
        defaults = [
            f'  * {key.upper().ljust(maxlen)} (default: {val if val != "" else "None"})'
            for key, val in alertify.Config.defaults().items()
        ]

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Bridge between Prometheus Alertmanager and Gotify\n',
            epilog='The following environment variables will override any config or default:\n'
            + '\n'.join(defaults),
        )

        parser.add_argument(
            '-c',
            '--config',
            default=f'{os.path.splitext(__file__)[0]}.yaml',
            help=f'path to config YAML.  (default: {os.path.splitext(__file__)[0]}.yaml)',
        )

        parser.add_argument(
            '-H',
            '--healthcheck',
            action='store_true',
            help='simply exit with 0 for healthy or 1 when unhealthy',
        )

        return parser.parse_args()

    def main():
        """
        main()
        """
        logging.basicConfig(
            format='%(levelname)s: %(message)s',
            level=logging.INFO,
        )

        args = parse_cli()

        # forwarder = alertify.Alertify(args.config)
        forwarder = alertify.Alertify()

        # -----------------------------
        # Calculate logging level
        # -----------------------------
        # Config  :: Verbose:   0 = WARNING,  1 = INFO,  2 = DEBUG
        # Logging :: Loglevel: 30 = WARNING, 20 = INFO, 10 = DEBUG
        logger = logging.getLogger()
        logger.setLevel(30 - (forwarder.config.verbose * 10))
        # -----------------------------

        if args.healthcheck:
            # Invert the sense of 'healthy' for Unix CLI usage
            return not forwarder.healthcheck.report()

        logging.info('Version: %s', alertify.__version__)

        if forwarder.config.verbose:
            logging.debug('Parsed config:')
            for key, val in forwarder.config.items():
                logging.debug('%s: %s', key, val)

        forwarder.server.listen_and_run()

        return 0

    sys.exit(main())
