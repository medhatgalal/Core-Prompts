"""Synthetic PUBLIC release help. No publish path is implemented."""
import argparse
p = argparse.ArgumentParser(description="Create a local package; publishing is a separate reviewed job.")
p.add_argument("--build", action="store_true", help="describe local package creation only")
p.parse_args()
print("No network publication; this fixture only describes packaging.")
