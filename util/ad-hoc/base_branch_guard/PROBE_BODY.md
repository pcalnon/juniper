Fail-path probe for the PR base-branch guard.

This PR targets a NON-default base branch on purpose, to exercise the guard failure arm
that 137 prior runs never reached. Expected: `Guard PR base branch` FAILS with the
remediation annotation.

Throwaway - close and delete both branches once observed. ml#434.
