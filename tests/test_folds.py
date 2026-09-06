from research_methodology.credibility import CredEvent, fold
from research_methodology.constants import VolatilityClass as V, AuthorityClass as A


def _fb(eid, ts, positive=True, explicit=False, cluster="c", vc=V.MODERATE, ac=A.MEDIUM):
    return CredEvent(eid, ts, "feedback", positive, explicit, vc, ac, cluster)


def test_fold_is_idempotent_by_event_id():
    e = _fb("e1", 0.0, explicit=True)
    once = fold([e], now_days=0.0)
    twice = fold([e, e], now_days=0.0)
    assert once.score == twice.score


def test_explicit_weighted_triple_implicit():
    s_impl = fold([_fb("i", 0.0, explicit=False)], now_days=0.0).score
    s_expl = fold([_fb("x", 0.0, explicit=True)], now_days=0.0).score
    assert s_expl == 3.0 * s_impl


def test_blocklist_is_last_writer_wins():
    block = CredEvent("b", 1.0, "blocklist", True, True, V.MODERATE, A.LOW, "")
    unblock = CredEvent("u", 2.0, "unblock", True, True, V.MODERATE, A.LOW, "")
    assert fold([block], now_days=2.0).blocked is True
    assert fold([block, unblock], now_days=3.0).blocked is False


def test_high_confidence_requires_class_min_evidence_and_an_explicit_cluster():
    # MODERATE/MEDIUM needs >=4 clusters incl >=1 explicit.
    three = [_fb(f"e{i}", 0.0, explicit=True, cluster=f"c{i}") for i in range(3)]
    assert fold(three, now_days=0.0).confidence == "provisional"
    four = three + [_fb("e3", 0.0, explicit=True, cluster="c3")]
    assert fold(four, now_days=0.0).confidence == "high"


def test_implicit_only_cannot_reach_high_confidence():
    many = [_fb(f"e{i}", 0.0, explicit=False, cluster=f"c{i}") for i in range(6)]
    assert fold(many, now_days=0.0).confidence == "provisional"


def test_decay_reduces_older_evidence_score():
    fresh = fold([_fb("e", 0.0, explicit=True)], now_days=0.0).score
    aged = fold([_fb("e", 0.0, explicit=True)], now_days=180.0).score  # one half-life
    assert aged == fresh * 0.5
