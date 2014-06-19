# coding=utf-8
"""
Tests for AI algorithm implementations.
"""
import unittest
import json
import mock
from openassessment.test_utils import CacheResetTest
from openassessment.assessment.worker.algorithm import (
    AIAlgorithm, FakeAIAlgorithm, EaseAIAlgorithm,
    TrainingError, InvalidClassifier
)


EXAMPLES = [
    AIAlgorithm.ExampleEssay(u"Mine's a tale that can't be told, my ƒяєє∂σм I hold dear.", 2),
    AIAlgorithm.ExampleEssay(u"How years ago in days of old, when 𝒎𝒂𝒈𝒊𝒄 filled th air.", 1),
    AIAlgorithm.ExampleEssay(u"Ṫ'ẅäṡ in the darkest depths of Ṁöṛḋöṛ, I met a girl so fair.", 1),
    AIAlgorithm.ExampleEssay(u"But goﾚﾚuﾶ, and the evil one crept up and slipped away with her", 0),
    AIAlgorithm.ExampleEssay(u"", 4),
    AIAlgorithm.ExampleEssay(u".!?", 4),
    AIAlgorithm.ExampleEssay(u"no punctuation", 4),
    AIAlgorithm.ExampleEssay(u"one", 4),
]

INPUT_ESSAYS = [
    u"Good times, 𝑩𝒂𝒅 𝑻𝒊𝒎𝒆𝒔, you know I had my share",
    u"When my woman left home for a 𝒃𝒓𝒐𝒘𝒏 𝒆𝒚𝒆𝒅 𝒎𝒂𝒏",
    u"Well, I still don't seem to 𝒄𝒂𝒓𝒆",
    u"",
    u".!?",
    u"no punctuation",
    u"one",
]


class AIAlgorithmTest(CacheResetTest):
    """
    Base class for testing AI algorithm implementations.
    """
    ALGORITHM_CLASS = None

    def setUp(self):
        self.algorithm = self.ALGORITHM_CLASS()   # pylint:disable=E1102

    def _scores(self, classifier, input_essays):
        """
        Use the classifier to score multiple input essays.

        Args:
            input_essays (list of unicode): The essays to score.

        Returns:
            list of int: The scores

        """
        cache = {}
        return [
            self.algorithm.score(input_essay, classifier, cache)
            for input_essay in input_essays
        ]


class FakeAIAlgorithmTest(AIAlgorithmTest):
    """
    Test for the fake AI algorithm implementation.
    """
    ALGORITHM_CLASS = FakeAIAlgorithm

    def test_train_and_score(self):
        classifier = self.algorithm.train_classifier(EXAMPLES)
        expected_scores = [2, 0, 0, 0, 4, 2, 4]
        scores = self._scores(classifier, INPUT_ESSAYS)
        self.assertEqual(scores, expected_scores)

    def test_score_classifier_missing_key(self):
        with self.assertRaises(InvalidClassifier):
            self.algorithm.score(u"Test input", {}, {})

    def test_score_classifier_no_scores(self):
        with self.assertRaises(InvalidClassifier):
            self.algorithm.score(u"Test input", {'scores': []}, {})


# Try to import EASE -- if we can't, then skip the tests that require it
try:
    import ease # pylint: disable=F0401,W0611
    EASE_INSTALLED = True
except ImportError:
    EASE_INSTALLED = False


@unittest.skipUnless(EASE_INSTALLED, "EASE library required")
class EaseAIAlgorithmTest(AIAlgorithmTest):
    """
    Test for the EASE AI library wrapper.
    """
    ALGORITHM_CLASS = EaseAIAlgorithm

    def test_train_and_score(self):
        classifier = self.algorithm.train_classifier(EXAMPLES)
        scores = self._scores(classifier, INPUT_ESSAYS)

        # Check that we got scores in the correct range
        valid_scores = set(example.score for example in EXAMPLES)
        for score in scores:
            self.assertIn(score, valid_scores)

        # Check that the scores are consistent when we re-run the algorithm
        repeat_scores = self._scores(classifier, INPUT_ESSAYS)
        self.assertEqual(scores, repeat_scores)

    def test_all_examples_have_same_score(self):
        examples = [
            AIAlgorithm.ExampleEssay(u"Test ëṡṡäÿ", 1),
            AIAlgorithm.ExampleEssay(u"Another test ëṡṡäÿ", 1),
        ]
        # No assertion -- just verifying that this does not raise an exception
        classifier = self.algorithm.train_classifier(examples)
        self._scores(classifier, INPUT_ESSAYS)

    def test_most_examples_have_same_score(self):
        # All training examples have the same score except for one
        examples = [
            AIAlgorithm.ExampleEssay(u"Test ëṡṡäÿ", 1),
            AIAlgorithm.ExampleEssay(u"Another test ëṡṡäÿ", 1),
            AIAlgorithm.ExampleEssay(u"Different score", 0),
        ]
        classifier = self.algorithm.train_classifier(examples)
        scores = self._scores(classifier, INPUT_ESSAYS)

        # Check that we got scores back.
        # This is not a very rigorous assertion -- we're mainly
        # checking that we got this far without an exception.
        self.assertEqual(len(scores), len(INPUT_ESSAYS))

    def test_no_examples(self):
        with self.assertRaises(TrainingError):
            self.algorithm.train_classifier([])

    def test_json_serializable(self):
        classifier = self.algorithm.train_classifier(EXAMPLES)
        serialized = json.dumps(classifier)
        deserialized = json.loads(serialized)

        # This should not raise an exception
        scores = self._scores(deserialized, INPUT_ESSAYS)
        self.assertEqual(len(scores), len(INPUT_ESSAYS))

    @mock.patch('openassessment.assessment.worker.algorithm.pickle')
    def test_pickle_serialize_error(self, mock_pickle):
        mock_pickle.dumps.side_effect = Exception("Test error!")
        with self.assertRaises(TrainingError):
            self.algorithm.train_classifier(EXAMPLES)

    def test_pickle_deserialize_error(self):
        classifier = self.algorithm.train_classifier(EXAMPLES)
        with mock.patch('openassessment.assessment.worker.algorithm.pickle.loads') as mock_call:
            mock_call.side_effect = Exception("Test error!")
            with self.assertRaises(InvalidClassifier):
                self.algorithm.score(u"Test ëṡṡäÿ", classifier, {})

    def test_serialized_classifier_not_a_dict(self):
        with self.assertRaises(InvalidClassifier):
            self.algorithm.score(u"Test ëṡṡäÿ", "not a dict", {})
