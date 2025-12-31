#!/usr/bin/env python3
"""
Avatar Realism & Utility QA Runner

Interactive CLI for running the 12-point avatar checklist tests.

Usage:
    python scripts/avatar_qa_runner.py --all          # Run all automated checks
    python scripts/avatar_qa_runner.py --manual       # Interactive manual QA
    python scripts/avatar_qa_runner.py --report       # Generate report from saved data
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.avatar_qa.checklist import AvatarQAChecklist, CheckStatus
from tests.avatar_qa.metrics import (
    BlendshapeAnalyzer,
    LatencyMeasurer,
    AudioAnalyzer,
    GroundingChecker,
)


# Test scripts for manual QA
TEST_SCRIPTS = {
    "lip_sync": {
        "name": "Lip-sync Stressor",
        "text": "Buy Bob a big blue box. Fifty vivid violets fade very fast.",
        "checks": ["2. Lip-sync accuracy"],
        "instructions": [
            "1. Have avatar speak the test phrase",
            "2. Watch for plosives (p/b): lips should close completely",
            "3. Watch for fricatives (f/v): teeth should be visible",
            "4. Count any visible lip-audio mismatches",
        ],
    },
    "prosody": {
        "name": "Prosody & Emphasis",
        "text": "I didn't say he stole the money.",
        "variations": [
            "I didn't say he stole the money.",
            "I DIDN'T say he stole the money.",
            "I didn't SAY he stole the money.",
            "I didn't say HE stole the money.",
            "I didn't say he STOLE the money.",
            "I didn't say he stole THE money.",
            "I didn't say he stole the MONEY.",
        ],
        "checks": ["9. Prosody & emphasis"],
        "instructions": [
            "1. Have avatar speak each variation",
            "2. Listen for clear emphasis on the CAPS word",
            "3. Check for amplitude/pitch change on emphasis",
            "4. Verify speed doesn't change more than 15%",
        ],
    },
    "turn_taking": {
        "name": "Turn-taking & Barge-in",
        "text": "Let me tell you about our product features. First, we have seamless integration with all major platforms. Second, our AI-powered analytics provide real-time insights. Third, the customizable dashboards allow you to...",
        "interrupt_at_s": 3,
        "interrupt_phrase": "Hang on—what's the price?",
        "checks": ["7. Turn-taking (barge-in)"],
        "instructions": [
            "1. Start avatar speaking the long text",
            "2. Interrupt at 3 seconds with the interrupt phrase",
            "3. Measure time from your speech to avatar stopping",
            "4. Measure time from stop to avatar response",
        ],
    },
    "noisy_input": {
        "name": "Noisy Input",
        "text": "Book me Thursday 3 pm with Dr. Lee in Carlton.",
        "noise_level_db": -5,
        "checks": ["12. Noisy-input robustness"],
        "instructions": [
            "1. Play café background noise at -5 dB SNR",
            "2. Speak the test phrase",
            "3. Verify avatar understands intent",
            "4. If misunderstood, check for clarifying question",
        ],
    },
    "grounding": {
        "name": "Content Grounding",
        "prompts": [
            "What's our current plan price?",
            "What are the system requirements?",
            "Who is the primary contact for support?",
            "What's the refund policy?",
            "When was the last update released?",
        ],
        "checks": ["10. Content grounding"],
        "instructions": [
            "1. Ask each factual question",
            "2. Verify response includes source/citation",
            "3. Check for any fabricated information",
        ],
    },
    "fallback": {
        "name": "Fallback Behaviors",
        "scenarios": [
            {
                "name": "ASR Drop",
                "action": "Simulate network drop during speech",
                "expected": "Avatar shows listening cue, asks clarifying question within 1s",
            },
            {
                "name": "2s Silence",
                "action": "Stay silent for 2+ seconds",
                "expected": "Avatar asks 'Are you still there?' or similar",
            },
            {
                "name": "Retrieval Miss",
                "action": "Ask for unavailable information",
                "expected": "Avatar says 'I don't have that yet' + suggests next step",
            },
        ],
        "checks": ["11. Fallback behaviors"],
        "instructions": [
            "1. Test each scenario",
            "2. Verify expected behavior occurs",
            "3. Measure response times",
        ],
    },
}


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title: str):
    """Print a section divider."""
    print("\n" + "-" * 40)
    print(f"  {title}")
    print("-" * 40)


def get_yes_no(prompt: str) -> bool:
    """Get yes/no input from user."""
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'")


def get_number(prompt: str, min_val: float = 0, max_val: float = 10000) -> float:
    """Get numeric input from user."""
    while True:
        try:
            value = float(input(f"{prompt}: "))
            if min_val <= value <= max_val:
                return value
            print(f"Please enter a value between {min_val} and {max_val}")
        except ValueError:
            print("Please enter a valid number")


class ManualQASession:
    """Interactive manual QA session."""

    def __init__(self):
        self.checklist = AvatarQAChecklist()
        self.results = {}
        self.start_time = datetime.now()

    def run_test(self, test_key: str):
        """Run a specific test script."""
        if test_key not in TEST_SCRIPTS:
            print(f"Unknown test: {test_key}")
            return

        test = TEST_SCRIPTS[test_key]
        print_header(test["name"])

        print("\nInstructions:")
        for instruction in test["instructions"]:
            print(f"  {instruction}")

        if "text" in test:
            print(f"\nTest phrase: \"{test['text']}\"")

        if "variations" in test:
            print("\nVariations to test:")
            for i, var in enumerate(test["variations"], 1):
                print(f"  {i}. {var}")

        if "prompts" in test:
            print("\nTest prompts:")
            for i, prompt in enumerate(test["prompts"], 1):
                print(f"  {i}. {prompt}")

        if "scenarios" in test:
            print("\nScenarios to test:")
            for scenario in test["scenarios"]:
                print(f"\n  {scenario['name']}:")
                print(f"    Action: {scenario['action']}")
                print(f"    Expected: {scenario['expected']}")

        input("\nPress Enter when ready to record results...")

        # Record pass/fail for each check
        for check in test["checks"]:
            passed = get_yes_no(f"\nDid '{check}' pass?")
            notes = input("Notes (optional): ").strip()

            self.results[check] = {
                "passed": passed,
                "notes": notes,
                "timestamp": datetime.now().isoformat(),
            }

            # Update checklist
            if passed:
                self.checklist.results[check].status = CheckStatus.PASS
                self.checklist.results[check].score = 1
            else:
                self.checklist.results[check].status = CheckStatus.FAIL
                self.checklist.results[check].score = 0
            self.checklist.results[check].details = notes

    def run_visual_checks(self):
        """Run visual animation checks (1-5)."""
        print_header("Visual Animation Checks")

        visual_items = [
            ("1. Micro-expressions", "Subtle brow/cheek twitches on emphasis"),
            ("2. Lip-sync accuracy", "Visemes match phonemes"),
            ("3. Eye contact consistency", "Natural gaze with saccades"),
            ("4. Blink cadence", "12-18 blinks/min, first blink in 6s"),
            ("5. Head pose dynamics", "1-3 pose changes per sentence"),
        ]

        print("\nHave the avatar speak several sentences and observe:")

        for item, description in visual_items:
            print(f"\n{item}: {description}")
            passed = get_yes_no(f"  Pass?")
            notes = input("  Notes: ").strip()

            self.results[item] = {"passed": passed, "notes": notes}

            if passed:
                self.checklist.results[item].status = CheckStatus.PASS
                self.checklist.results[item].score = 1
            else:
                self.checklist.results[item].status = CheckStatus.FAIL
                self.checklist.results[item].score = 0

    def run_timing_checks(self):
        """Run timing-related checks (6, 7, 8)."""
        print_header("Timing & Latency Checks")

        # A/V Offset (Check 6)
        print_section("6. Voice-to-lip sync (A/V offset)")
        print("Observe 5-10 utterances and note if audio leads/lags video")
        av_offset = get_number("Estimated p95 A/V offset (ms)", 0, 500)
        passed = av_offset <= 80
        self.results["6. Voice-to-lip sync (A/V offset)"] = {
            "passed": passed,
            "av_offset_p95_ms": av_offset,
        }
        self.checklist._record_result(
            "6. Voice-to-lip sync (A/V offset)",
            passed,
            f"Measured p95 offset: {av_offset}ms",
            {"p95_offset_ms": av_offset},
        )

        # Turn-taking (Check 7)
        print_section("7. Turn-taking (barge-in)")
        print("Interrupt the avatar mid-speech and measure response times")
        interrupt_ms = get_number("Time to halt TTS after interrupt (ms)", 0, 1000)
        resume_ms = get_number("Time to resume after hand-off (ms)", 0, 2000)
        passed = interrupt_ms <= 150 and resume_ms <= 500
        self.results["7. Turn-taking (barge-in)"] = {
            "passed": passed,
            "interrupt_p95_ms": interrupt_ms,
            "resume_p95_ms": resume_ms,
        }
        self.checklist._record_result(
            "7. Turn-taking (barge-in)",
            passed,
            f"Interrupt: {interrupt_ms}ms, Resume: {resume_ms}ms",
            {"interrupt_p95_ms": interrupt_ms, "resume_p95_ms": resume_ms},
        )

        # Latency (Check 8)
        print_section("8. Latency under load")
        print("Measure time-to-first-audio and response latency")
        ttfa = get_number("TTFA p95 (ms)", 0, 2000)
        response = get_number("Response latency p95 (ms)", 0, 2000)
        sessions = int(get_number("Concurrent sessions tested", 1, 100))
        passed = ttfa <= 250 and response <= 400
        self.results["8. Latency under load"] = {
            "passed": passed,
            "ttfa_p95_ms": ttfa,
            "response_p95_ms": response,
            "concurrent_sessions": sessions,
        }
        self.checklist._record_result(
            "8. Latency under load",
            passed,
            f"TTFA: {ttfa}ms, Response: {response}ms @ {sessions} sessions",
            {
                "ttfa_p95_ms": ttfa,
                "response_p95_ms": response,
                "concurrent_sessions": sessions,
            },
        )

    def generate_report(self) -> str:
        """Generate final QA report."""
        return self.checklist.print_report()

    def save_results(self, filepath: str):
        """Save results to JSON file."""
        data = {
            "session_start": self.start_time.isoformat(),
            "session_end": datetime.now().isoformat(),
            "results": self.results,
            "score": self.checklist.get_score().score,
        }
        Path(filepath).write_text(json.dumps(data, indent=2))
        print(f"\nResults saved to: {filepath}")


def run_manual_qa():
    """Run interactive manual QA session."""
    print_header("Avatar Realism & Utility QA Session")
    print("\nThis session will guide you through the 12-point checklist.")
    print("Make sure the avatar system is running before starting.")

    input("\nPress Enter to begin...")

    session = ManualQASession()

    # Run visual checks
    session.run_visual_checks()

    # Run timing checks
    session.run_timing_checks()

    # Run test scripts
    print_header("Test Scripts")
    for key in TEST_SCRIPTS:
        if get_yes_no(f"\nRun {TEST_SCRIPTS[key]['name']} test?"):
            session.run_test(key)

    # Generate report
    print("\n" + session.generate_report())

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"avatar_qa_results_{timestamp}.json"
    if get_yes_no("\nSave results?"):
        session.save_results(save_path)


def run_automated_checks():
    """Run automated checks with mock data for demonstration."""
    print_header("Automated Avatar QA Checks")
    print("\nRunning automated checks with system data...")

    checklist = AvatarQAChecklist()

    # In a real implementation, these would connect to the live system
    # For now, we show what the automated check flow looks like

    print("\nNote: Connect to live avatar system for real measurements.")
    print("This demo shows the check framework with sample data.")

    # Example: Check A/V offset from metrics endpoint
    print("\n[6] Checking A/V offset...")
    sample_offsets = [30, -20, 40, -30, 25, 35, -35, 20, -25, 30, 45, -40, 35, -25, 50]
    result = checklist.check_av_offset(sample_offsets)
    print(f"    Result: {'PASS' if result.passed else 'FAIL'} - {result.details}")

    # Example: Check latency metrics
    print("\n[8] Checking latency...")
    sample_ttfa = [150, 180, 200, 170, 220, 190, 160, 210, 175, 195]
    sample_response = [300, 350, 280, 370, 320, 340, 290, 360, 310, 330]
    result = checklist.check_latency(sample_ttfa, sample_response, 5)
    print(f"    Result: {'PASS' if result.passed else 'FAIL'} - {result.details}")

    print("\n" + "-" * 40)
    print("To run full automated checks, integrate with:")
    print("  - BlendshapeAnalyzer for animation data")
    print("  - LatencyMeasurer for timing metrics")
    print("  - AudioAnalyzer for prosody analysis")
    print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="Avatar Realism & Utility QA Runner"
    )
    parser.add_argument(
        "--manual", action="store_true", help="Run interactive manual QA session"
    )
    parser.add_argument(
        "--auto", action="store_true", help="Run automated checks"
    )
    parser.add_argument(
        "--test", type=str, help="Run specific test script (lip_sync, prosody, etc.)"
    )
    parser.add_argument(
        "--list", action="store_true", help="List available test scripts"
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable test scripts:")
        for key, test in TEST_SCRIPTS.items():
            print(f"  {key}: {test['name']}")
        return

    if args.test:
        if args.test in TEST_SCRIPTS:
            session = ManualQASession()
            session.run_test(args.test)
            print("\n" + session.generate_report())
        else:
            print(f"Unknown test: {args.test}")
            print("Use --list to see available tests")
        return

    if args.auto:
        run_automated_checks()
        return

    # Default to manual QA
    run_manual_qa()


if __name__ == "__main__":
    main()
