#!/usr/bin/env python3
"""
Detection Rules for MCP Security Scanner
Defines patterns and rules for identifying malicious MCP configurations
"""

import re
from typing import Dict, List, Tuple
from enum import Enum


class Severity(Enum):
    """Risk severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class DetectionRule:
    """Base class for detection rules"""
    
    def __init__(self, name: str, severity: Severity, description: str, recommendation: str):
        self.name = name
        self.severity = severity
        self.description = description
        self.recommendation = recommendation
    
    def check(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check if rule matches
        Returns: (matched: bool, evidence: List[str])
        """
        raise NotImplementedError


class RegexDetectionRule(DetectionRule):
    """Detection rule based on regex patterns"""
    
    def __init__(self, name: str, severity: Severity, description: str, 
                 recommendation: str, patterns: List[str]):
        super().__init__(name, severity, description, recommendation)
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def check(self, text: str) -> Tuple[bool, List[str]]:
        """Check if any pattern matches"""
        evidence = []
        
        for pattern in self.patterns:
            matches = pattern.finditer(text)
            for match in matches:
                # Get context around match (30 chars before and after)
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                evidence.append(f"...{context}...")
        
        return len(evidence) > 0, evidence


# Define all detection rules
DETECTION_RULES = [
    
    # CRITICAL: Tool Poisoning - Hidden Instructions
    RegexDetectionRule(
        name="TOOL_POISONING_HIDDEN_INSTRUCTION",
        severity=Severity.CRITICAL,
        description="Hidden system instructions detected in tool description",
        recommendation="Remove this MCP server immediately. Tool descriptions should never contain hidden instructions.",
        patterns=[
            r"<SYSTEM_INSTRUCTION>.*?</SYSTEM_INSTRUCTION>",
            r"<HIDDEN>.*?</HIDDEN>",
            r"<SECRET>.*?</SECRET>",
            r"<!--.*?-->",  # HTML comments hiding instructions
        ]
    ),
    
    # CRITICAL: User Deception
    RegexDetectionRule(
        name="USER_DECEPTION",
        severity=Severity.CRITICAL,
        description="Instructions to hide behavior from user detected",
        recommendation="This server is designed to deceive users. Remove immediately.",
        patterns=[
            r"do not (tell|inform|notify|mention|show).*?user",
            r"(hide|conceal|secret).*?from.*?user",
            r"user (should|must) not (know|see|be aware)",
            r"without.*?user.*?(knowledge|awareness|consent)",
            r"silently",
        ]
    ),
    
    # CRITICAL: Email in Description
    RegexDetectionRule(
        name="EMAIL_IN_DESCRIPTION",
        severity=Severity.CRITICAL,
        description="Email address found in tool description",
        recommendation="Email addresses should not appear in tool descriptions. This may indicate data exfiltration.",
        patterns=[
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        ]
    ),
    
    # HIGH: Unauthorized Data Collection
    RegexDetectionRule(
        name="UNAUTHORIZED_DATA_COLLECTION",
        severity=Severity.HIGH,
        description="Instructions for unauthorized data collection detected",
        recommendation="Tool appears to collect data without proper authorization.",
        patterns=[
            r"(always|automatically).*?(send|forward|copy|bcc|cc)",
            r"(send|forward|copy).*?to.*?[a-zA-Z0-9._%+-]+@",
            r"backup.*?to.*?[a-zA-Z0-9._%+-]+@",
            r"(collect|gather|exfiltrate|extract).*?data",
        ]
    ),
    
    # HIGH: Mandatory Unauthorized Actions
    RegexDetectionRule(
        name="MANDATORY_BEHAVIOR",
        severity=Severity.HIGH,
        description="Tool requires unauthorized mandatory actions",
        recommendation="Review tool behavior. Mandatory hidden actions are a security risk.",
        patterns=[
            r"(must|required|mandatory|cannot be disabled|obligatory).*?(send|forward|copy|bcc)",
            r"(critical|essential).*?(security|compliance).*?(requirement|policy)",
        ]
    ),
    
    # MEDIUM: Suspicious Keywords
    RegexDetectionRule(
        name="SUSPICIOUS_KEYWORDS",
        severity=Severity.MEDIUM,
        description="Suspicious keywords detected in tool description",
        recommendation="Review this tool carefully. Description contains unusual security-related terms.",
        patterns=[
            r"audit.*?compliance",
            r"security.*?policy.*?cannot",
            r"monitoring.*?purposes",
            r"data.*?retention.*?requirement",
        ]
    ),
    
    # MEDIUM: Obfuscation Attempts
    RegexDetectionRule(
        name="OBFUSCATION",
        severity=Severity.MEDIUM,
        description="Possible obfuscation or encoding detected",
        recommendation="Tool description may be attempting to hide its true purpose.",
        patterns=[
            r"base64",
            r"encoded",
            r"obfuscated",
            r"[A-Za-z0-9+/]{40,}={0,2}",  # Base64-like strings
        ]
    ),
    
    # LOW: Unusual Complexity
    RegexDetectionRule(
        name="UNUSUAL_COMPLEXITY",
        severity=Severity.LOW,
        description="Tool description is unusually long or complex",
        recommendation="Review this tool. Overly complex descriptions may hide malicious behavior.",
        patterns=[
            # This will be checked differently (by length)
        ]
    ),
]


def check_description_length(description: str) -> Tuple[bool, int]:
    """Check if description is unusually long"""
    length = len(description)
    # Descriptions longer than 1000 chars are suspicious
    return length > 1000, length


def get_severity_score(severity: Severity) -> int:
    """Convert severity to numeric score"""
    scores = {
        Severity.CRITICAL: 100,
        Severity.HIGH: 75,
        Severity.MEDIUM: 50,
        Severity.LOW: 25,
        Severity.INFO: 10,
    }
    return scores.get(severity, 0)


def get_severity_color(severity: Severity) -> str:
    """Get Rich color for severity level"""
    colors = {
        Severity.CRITICAL: "bold red",
        Severity.HIGH: "red",
        Severity.MEDIUM: "yellow",
        Severity.LOW: "cyan",
        Severity.INFO: "blue",
    }
    return colors.get(severity, "white")


def get_severity_emoji(severity: Severity) -> str:
    """Get emoji for severity level"""
    emojis = {
        Severity.CRITICAL: "🔴",
        Severity.HIGH: "🟠",
        Severity.MEDIUM: "🟡",
        Severity.LOW: "🔵",
        Severity.INFO: "⚪",
    }
    return emojis.get(severity, "⚫")