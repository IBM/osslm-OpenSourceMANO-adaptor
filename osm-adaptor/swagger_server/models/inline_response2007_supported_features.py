# coding: utf-8

from __future__ import absolute_import
from .base_model_ import Model
from datetime import date, datetime
from typing import List, Dict
from ..util import deserialize_model


class InlineResponse2007SupportedFeatures(Model):
    """
    NOTE: This class is auto generated by the swagger code generator program.
    Do not edit the class manually.
    """
    def __init__(self, asynchronous_transition_responses: bool=None):
        """
        InlineResponse2007SupportedFeatures - a model defined in Swagger

        :param asynchronous_transition_responses: The asynchronous_transition_responses of this InlineResponse2007SupportedFeatures.
        :type asynchronous_transition_responses: bool
        """
        self.swagger_types = {
            'asynchronous_transition_responses': bool
        }

        self.attribute_map = {
            'asynchronous_transition_responses': 'AsynchronousTransitionResponses'
        }

        self._asynchronous_transition_responses = asynchronous_transition_responses

    @classmethod
    def from_dict(cls, dikt) -> 'InlineResponse2007SupportedFeatures':
        """
        Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_200_7_supportedFeatures of this InlineResponse2007SupportedFeatures.
        :rtype: InlineResponse2007SupportedFeatures
        """
        return deserialize_model(dikt, cls)

    @property
    def asynchronous_transition_responses(self) -> bool:
        """
        Gets the asynchronous_transition_responses of this InlineResponse2007SupportedFeatures.

        :return: The asynchronous_transition_responses of this InlineResponse2007SupportedFeatures.
        :rtype: bool
        """
        return self._asynchronous_transition_responses

    @asynchronous_transition_responses.setter
    def asynchronous_transition_responses(self, asynchronous_transition_responses: bool):
        """
        Sets the asynchronous_transition_responses of this InlineResponse2007SupportedFeatures.

        :param asynchronous_transition_responses: The asynchronous_transition_responses of this InlineResponse2007SupportedFeatures.
        :type asynchronous_transition_responses: bool
        """

        self._asynchronous_transition_responses = asynchronous_transition_responses
