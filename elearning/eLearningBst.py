
from typing import List

from services.service import PublishSubscribe
from services.service import Service
from utils.beliefstate import BeliefState
from utils.useract import UserAct


class ELearningBST(Service):
    def __init__(self, domain=None):
        Service.__init__(self, domain=domain)
        self.state = self._init_state()

    def _init_state(self):
        """
        Create empty beliefstate
        """
        return {"module_id": None, "section_id": None}

    @PublishSubscribe(sub_topics=["user_acts"], pub_topics=["beliefstate"])
    def update_bst(self, user_id: str, user_acts: List[UserAct] = None) \
            -> dict(beliefstate=BeliefState):
        # TODO beatrice: store relevant information from user acts here
        print("TODO Beatrice: eLearningBst.py: hier Informationen aus User Acts in BST schreiben")
        return {'beliefstate': self.state}

    def dialog_start(self, user_id: str):
        """
        Restets the belief state so it is ready for a new dialog
        """
        # initialize belief state
        self.state = self._init_state()