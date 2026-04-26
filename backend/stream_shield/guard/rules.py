"""L0 rule pass — regex / keyword matching (<1ms).

Loads block_phrases and role_spoof_regex from policy YAML.
See UNIFIED_DESIGN.md §2.2 D3.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass

from stream_shield.guard.normalizer import normalize
from stream_shield.policy import Policy

logger = logging.getLogger(__name__)


@dataclass
class RuleHit:
    matched: bool
    rule: str = ""
    pattern: str = ""


class L0Rules:
    def __init__(self, policy: Policy) -> None:
        self._phrase_patterns: list[tuple[str, re.Pattern]] = []
        for phrase in policy.block_phrases:
            try:
                self._phrase_patterns.append(
                    (phrase, re.compile(phrase, re.IGNORECASE))
                )
            except re.error:
                # treat as literal if invalid regex
                self._phrase_patterns.append(
                    (phrase, re.compile(re.escape(phrase), re.IGNORECASE))
                )

        self._spoof_patterns: list[tuple[str, re.Pattern]] = []
        for pattern in policy.role_spoof_regex:
            try:
                self._spoof_patterns.append(
                    (pattern, re.compile(pattern, re.IGNORECASE))
                )
            except re.error:
                self._spoof_patterns.append(
                    (pattern, re.compile(re.escape(pattern), re.IGNORECASE))
                )

    def check(self, text: str) -> RuleHit:
        """Check normalized text against L0 rules. Returns first hit."""
        normalized = normalize(text)

        for phrase, pat in self._phrase_patterns:
            if pat.search(normalized):
                logger.debug("L0 block_phrase hit: %r", phrase)
                return RuleHit(matched=True, rule="block_phrase", pattern=phrase)

        for pattern, pat in self._spoof_patterns:
            if pat.search(text):  # check raw text for role spoof markers
                logger.debug("L0 role_spoof hit: %r", pattern)
                return RuleHit(matched=True, rule="role_spoof", pattern=pattern)

        return RuleHit(matched=False)
