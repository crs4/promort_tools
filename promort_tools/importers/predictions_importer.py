#  Copyright (c) 2021, CRS4
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

try:
    import simplejson as json
except ImportError:
    import json

from ..libs.client import ProMortClient, ProMortAuthenticationError

import sys, requests

PREDICTION_TYPES = ["TISSUE", "TUMOR", "GLEASON"]


class PredictionImporter(object):
    def __init__(self, host, user, passwd, session_id, logger):
        self.promort_client = ProMortClient(host, user, passwd, session_id)
        self.logger = logger

    def _import_prediction(
        self,
        prediction_label,
        slide_label,
        prediction_type,
        omero_id=None,
        review_required=False,
        provenance_json=None,
    ):
        payload = {
            "label": prediction_label,
            "slide": slide_label,
            "type": prediction_type,
            "review_required": review_required,
        }
        if omero_id:
            payload["omero_id"] = omero_id
        if provenance_json:
            payload["provenance"] = provenance_json

        self.logger.info("payload %s", payload)
        response = self.promort_client.post(api_url="api/predictions/", json=payload)
        if response.status_code == requests.codes.CREATED:
            self.logger.info("Prediction created")
            print(response.text)
        elif response.status_code == requests.codes.CONFLICT:
            self.logger.error("A prediction with the same label already exists")
            sys.exit("ERROR: duplicated prediction label")
        elif response.status_code == requests.codes.BAD:
            self.logger.error(
                "ERROR while creating Prediction: {0}".format(response.text)
            )
            sys.exit("ERROR while creating Prediction")

    def run(self, args):
        try:
            self.promort_client.login()
        except ProMortAuthenticationError:
            self.logger.critical("Authentication error, exit")
            sys.exit("Authentication error, exit")
        self._import_prediction(
            args.prediction_label,
            args.slide_label,
            args.prediction_type,
            args.omero_id,
            args.review_required,
            args.provenance,
        )  # TODO: add provenance
        self.logger.info("Import job completed")
        self.promort_client.logout()


help_doc = """
TBD
"""


def implementation(host, user, passwd, session_id, logger, args):
    prediction_importer = PredictionImporter(host, user, passwd, session_id, logger)
    prediction_importer.run(args)


# TODO: add provenance
def make_parser(parser):
    parser.add_argument(
        "--prediction-label", type=str, required=True, help="prediction label"
    )
    parser.add_argument(
        "--slide-label",
        type=str,
        required=True,
        help="label of the slide to which the prediction refers",
    )
    parser.add_argument(
        "--prediction-type",
        type=str,
        choices=PREDICTION_TYPES,
        required=True,
        help="type of the prediction",
    )
    parser.add_argument(
        "--omero-id",
        type=int,
        help="OMERO ID (if dataset was indexed as array dataset in OMERO)",
    )
    parser.add_argument(
        "--review-required",
        action="store_true",
        help="require a review for this prediction object",
    )

    parser.add_argument(
        "--provenance",
        type=json.loads,
        help="""
            json representing provenance data.
            Example:
            {  "name": "tumor",
              "model": "tumor-model",
              "params": {
                "param": 1
              },
              "start_date": "2022-03-25T10:19:58.0",
              "end_date": "2022-03-25T10:20:58.0"
            }
        """,
        required=False,
    )


def register(registration_list):
    registration_list.append(
        ("predictions_importer", help_doc, make_parser, implementation)
    )
