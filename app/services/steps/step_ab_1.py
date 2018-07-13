from app.services.steps import Step
from flask import g

class Step_AB_1(Step):
    form_requirements = ['elections']
    step_requirements = []
    endpoint = '/ab/election_picker'
    prev_step = 'Step_0'
    next_step = None

    def run(self):
        if self.is_complete:
            return True

        if not self.verify_form_requirements():
            return False

        self.is_complete = True
        if g.registrant.completed_at:
            self.next_step = 'Step_VR_6'
        else:
            self.next_step = 'Step_AB_3'

        return True