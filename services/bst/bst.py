###############################################################################
#
# Copyright 2019, University of Stuttgart: Institute for Natural Language Processing (IMS)
#
# This file is part of Adviser.
# Adviser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3.
#
# Adviser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Adviser.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from typing import List, Set

from services.service import PublishSubscribe
from services.service import Service
from utils.beliefstate import BeliefState
from utils.useract import UserActionType, UserAct


class HandcraftedBST(Service):
    """
    A rule-based approach on belief state tracking.
    The state is basically a dictionary of keys.
    """
    BELIEFSTATE = "beliefstate"

    def __init__(self, domain=None, logger=None):
        Service.__init__(self, domain=domain)
        self.logger = logger

    @PublishSubscribe(sub_topics=["user_acts"], pub_topics=["beliefstate"])
    def update_bst(self, user_id: str = "default", user_acts: List[UserAct] = None) \
            -> dict(beliefstate=BeliefState):
        """
            Function for updating the current dialog belief state (which tracks the system's
            knowledge about what has been said in the dialog) based on the user actions generated
            from the user's utterances

            Args:
                belief_state (BeliefState): this should be None
                user_acts (list): a list of UserAct objects mapped from the user's last utterance
                sys_act (SysAct): this should be None

            Returns:
                (dict): a dictionary with the key "beliefstate" and the value the updated
                        BeliefState object

        """
        # save last turn to memory
        bs = self.get_state(user_id, HandcraftedBST.BELIEFSTATE)
        bs.start_new_turn()
        if user_acts:
            self._reset_informs(bs, user_acts)
            self._reset_requests(bs)
            bs["user_acts"] = self._get_all_usr_action_types(bs, user_acts)

            self._handle_user_acts(bs, user_acts)

            num_entries, discriminable = bs.get_num_dbmatches()
            bs["num_matches"] = num_entries
            bs["discriminable"] = discriminable

        self.set_state(user_id, HandcraftedBST.BELIEFSTATE, bs)
        return {'beliefstate': bs}

    def dialog_start(self, user_id: str):
        """
            Restets the belief state so it is ready for a new dialog

            Returns:
                (dict): a dictionary with a single entry where the key is 'beliefstate'and
                        the value is a new BeliefState object
        """
        # initialize belief state
        self.set_state(user_id, HandcraftedBST.BELIEFSTATE, BeliefState(self.domain))

    def _reset_informs(self, bs: BeliefState, acts: List[UserAct]):
        """
            If the user specifies a new value for a given slot, delete the old
            entry from the beliefstate
        """

        slots = {act.slot for act in acts if act.type == UserActionType.Inform}
        for slot in [s for s in bs['informs']]:
            if slot in slots:
                del bs['informs'][slot]

    def _reset_requests(self, bs: BeliefState):
        """
            gets rid of requests from the previous turn
        """
        bs['requests'] = {}

    def _get_all_usr_action_types(self, bs: BeliefState, user_acts: List[UserAct]) -> Set[UserActionType]:
        """ Returns a set of all different user action types in user_acts.

        Args:
            user_acts: list of UsrAct objects

        Returns:
            set of UserActionType objects
        """
        action_type_set = set()
        for act in user_acts:
            action_type_set.add(act.type)
        return action_type_set

    def _handle_user_acts(self, bs: BeliefState, user_acts: List[UserAct]):

        """
            Updates the belief state based on the information contained in the user act(s)

            Args:
                beliefstate (BeliefState): the belief state to be updated
                user_act (list[UserAct]): the list of user acts to use to update the belief state

        """
        # TODO: should requests have a score at all? For now I'm leaving that out, but might be
        # worth revisiting later

        # reset any offers if the user informs any new information
        if self.domain.get_primary_key() in bs['informs'] \
                and UserActionType.Inform in bs["user_acts"]:
            del bs['informs'][self.domain.get_primary_key()]

        # We choose to interpret switching as wanting to start a new dialog and do not support
        # resuming an old dialog
        elif UserActionType.SelectDomain in bs["user_acts"]:
            bs["informs"] = {}
            bs["requests"] = {}

        # Handle user acts
        for act in user_acts:
            if act.type == UserActionType.Request:
                bs['requests'][act.slot] = act.score
            elif act.type == UserActionType.Inform:
                # add informs and their scores to the beliefstate
                if act.slot in bs["informs"]:
                    bs['informs'][act.slot][act.value] = act.score
                else:
                    bs['informs'][act.slot] = {act.value: act.score}
            elif act.type == UserActionType.NegativeInform:
                # reset mentioned value to zero probability
                if act.slot in bs['informs']:
                    if act.value in bs['informs'][act.slot]:
                        del bs['informs'][act.slot][act.value]
            elif act.type == UserActionType.RequestAlternatives:
                # This way it is clear that the user is no longer asking about that one item
                if self.domain.get_primary_key() in bs['informs']:
                    del bs['informs'][self.domain.get_primary_key()]
