this file has no H1 heading, so markdownlint MD041 fails and the Pre-commit
gate goes red. that is deliberate: it guarantees this probe PR can never merge
while auto-merge is armed on it. throwaway for the D4 expectedHeadOid test.
