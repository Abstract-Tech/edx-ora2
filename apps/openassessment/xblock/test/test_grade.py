# -*- coding: utf-8 -*-
"""
Tests for grade handlers in Open Assessment XBlock.
"""
import copy
import json
from openassessment.assessment import peer_api, self_api
from .base import XBlockHandlerTestCase, scenario


class TestGrade(XBlockHandlerTestCase):

    ASSESSMENTS = [
        {
            'options_selected': {u'𝓒𝓸𝓷𝓬𝓲𝓼𝓮': u'ﻉซƈﻉɭɭﻉกՇ', u'Form': u'Fair'},
            'feedback': u'єאςєɭɭєภՇ ฬ๏гк!',
        },
        {
            'options_selected': {u'𝓒𝓸𝓷𝓬𝓲𝓼𝓮': u'ﻉซƈﻉɭɭﻉกՇ', u'Form': u'Fair'},
            'feedback': u'Good job!',
        },
    ]

    SUBMISSION = u'ՇﻉรՇ รપ๒๓ٱรรٱѻก'

    @scenario('data/grade_scenario.xml', user_id='Greggs')
    def test_render_grade(self, xblock):

        # Create a submission from the user
        student_item = xblock.get_student_item_dict()
        submission = xblock.create_submission(student_item, self.SUBMISSION)
        xblock.get_workflow_info()
        scorer_submissions = []
        for scorer_name, assessment in zip(['McNulty', 'Freamon'], self.ASSESSMENTS):
            # Create a submission for each scorer
            scorer = copy.deepcopy(student_item)
            scorer['student_id'] = scorer_name
            scorer_sub = xblock.create_submission(scorer, self.SUBMISSION)
            xblock.get_workflow_info()
            submission = peer_api.get_submission_to_assess(scorer, 2)
            # Store the scorer's submission so our user can assess it later
            scorer_submissions.append(scorer_sub)

            # Create an assessment of the user's submission
            peer_api.create_assessment(
                submission['uuid'], scorer_name,
                assessment, {'criteria': xblock.rubric_criteria}
            )

        # Since xblock.create_submission sets the xblock's submission_uuid,
        # we need to set it back to the proper user for this test.
        xblock.submission_uuid = submission["uuid"]

        # Have our user make assessments (so she can get a score)
        for _ in range(2):
            new_submission = peer_api.get_submission_to_assess(student_item, 2)
            peer_api.create_assessment(
                new_submission['uuid'], 'Greggs',
                self.ASSESSMENTS[0], {'criteria': xblock.rubric_criteria}
            )

        # Have the user submit a self-assessment (so she can get a score)
        self_api.create_assessment(
            submission['uuid'], 'Greggs',
            self.ASSESSMENTS[0]['options_selected'],
            {'criteria': xblock.rubric_criteria}
        )

        # Render the view
        resp = self.request(xblock, 'render_grade', json.dumps(dict()))

        # Verify that feedback from each scorer appears in the view
        self.assertIn(u'єאςєɭɭєภՇ ฬ๏гк!', resp.decode('utf-8'))
        self.assertIn(u'Good job!', resp.decode('utf-8'))
