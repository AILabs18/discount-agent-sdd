from agent import run_pricing_agent


def test_agent_against_spec() -> None:
    print("Running SDD verification...")

    # Test Case 1: The Safety Cap (VIP $3000)
    result = run_pricing_agent("VIP", 3000)
    assert result["discount"] == 500, "Failed: Safety cap not respected!"

    # Test Case 2: The Gold Threshold (Gold $50)
    result = run_pricing_agent("Gold", 50)
    assert result["discount"] == 0, "Failed: Gold threshold ignored!"

    print("All spec criteria passed. Ready for deployment.")


if __name__ == "__main__":
    test_agent_against_spec()
