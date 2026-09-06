# tests/test_faithfulness.py
from research_methodology.faithfulness import check


SOURCE = "The maximum working pressure for a 1/2-inch type-L copper pipe is 850 psi at 100F."


def test_grounded_claim_passes():
    span = "maximum working pressure for a 1/2-inch type-L copper pipe is 850 psi"
    claim = "A 1/2-inch type-L copper pipe has a maximum working pressure of 850 psi."
    res = check(claim, span, SOURCE)
    assert res.a_span_unaltered and res.c_no_unsupported_specifics and res.verdict


def test_span_not_in_source_fails_a():
    span = "the pressure is 1200 psi"  # not present verbatim in SOURCE
    claim = "The pipe handles 1200 psi."
    res = check(claim, span, SOURCE)
    assert res.a_span_unaltered is False and res.verdict is False


def test_claim_with_unsupported_number_fails_c():
    span = "maximum working pressure for a 1/2-inch type-L copper pipe is 850 psi"
    claim = "The maximum working pressure is 850 psi at 250F."  # 250 not in span
    res = check(claim, span, SOURCE)
    assert res.c_no_unsupported_specifics is False and res.verdict is False
