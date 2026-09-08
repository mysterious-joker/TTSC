from __future__ import annotations

import unittest

from conversational_search.questions import QUESTION_TEXT, WILDCARD_OTHER_POLICY
from conversational_search.ranking import FUSED_ONLY_RANKING_POLICY
from conversational_search.retrieval import RetrievalResult, RetrievalTrace
from conversational_search.service import ConversationalSearchAgent


class _Retriever:
    def __init__(self, ids=("A", "B"), *, fallback=False, fail=False):
        self.ids = ids
        self.fallback = fallback
        self.fail = fail

    def search_with_trace(self, *_args, **_kwargs):
        if self.fail:
            raise RuntimeError("search unavailable")
        ranked = () if self.fallback else self.ids
        return RetrievalResult(
            self.ids,
            RetrievalTrace(
                bm25_ids=ranked,
                dense_ids=ranked,
                fused_ids=ranked,
                bm25_status="empty" if self.fallback else "ok",
                dense_status="empty" if self.fallback else "ok",
                used_fallback=self.fallback,
            ),
        )


def _respond(retriever, turn):
    agent = ConversationalSearchAgent(
        "unused.jsonl",
        retriever=retriever,
        ranking_policy=FUSED_ONLY_RANKING_POLICY,
        question_policy=WILDCARD_OTHER_POLICY,
    )
    agent.reset("shopper", {})
    return agent.respond("shopper", "Color: blue", turn, 10), agent.session_state("shopper")


class ResponseWordingTest(unittest.TestCase):
    def test_catalog_fallback_is_disclosed_without_changing_decision_or_state(self):
        for turn in (1, 10):
            with self.subTest(turn=turn):
                ordinary, ordinary_state = _respond(_Retriever(), turn)
                fallback, fallback_state = _respond(_Retriever(fallback=True), turn)
                prefix = (
                    "I couldn't establish reliable matches for your current preferences. "
                    "Here are some catalog options to review."
                )
                expected = prefix + (" " + QUESTION_TEXT["other"] if turn < 10 else "")
                self.assertEqual(fallback["message"], expected)
                self.assertEqual(
                    {key: value for key, value in ordinary.items() if key != "message"},
                    {key: value for key, value in fallback.items() if key != "message"},
                )
                self.assertEqual(ordinary_state, fallback_state)

    def test_empty_and_failed_retrieval_do_not_claim_to_show_matches(self):
        for fail in (False, True):
            for turn in (1, 10):
                with self.subTest(fail=fail, turn=turn):
                    response, state = _respond(_Retriever((), fallback=True, fail=fail), turn)
                    prefix = "I couldn't find any products to show for your current request."
                    expected = prefix + (" " + QUESTION_TEXT["other"] if turn < 10 else "")
                    self.assertEqual(response["message"], expected)
                    self.assertEqual(response["recommendations"], [])
                    self.assertEqual(response["ask_attribute"], "other" if turn < 10 else None)
                    self.assertEqual(state.last_turn, turn)

    def test_successful_retrieval_wording_is_unchanged(self):
        response, _state = _respond(_Retriever(), 1)
        self.assertEqual(
            response["message"],
            "Here are the closest matches so far. " + QUESTION_TEXT["other"],
        )
        response, _state = _respond(_Retriever(), 10)
        self.assertEqual(
            response["message"],
            "Here are the closest matches based on your current preferences.",
        )


if __name__ == "__main__":
    unittest.main()
