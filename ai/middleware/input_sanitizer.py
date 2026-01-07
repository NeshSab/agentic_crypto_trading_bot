"""
Input Sanitization Middleware for AI agents.

This middleware provides comprehensive input sanitization including:
- Prompt injection detection and prevention
- Content moderation and inappropriate language filtering
- Input sanitization and normalization
- Security logging for monitoring
"""

import re
import logging
import unicodedata
from typing import Callable
from langchain_core.messages import BaseMessage, HumanMessage
from langchain.agents.middleware import AgentMiddleware


logger = logging.getLogger(__name__)


class InputSanitizerMiddleware(AgentMiddleware):
    """
    Middleware to sanitize user input, prevent prompt injections, and moderate content.
    """

    def __init__(
        self,
        max_input_length: int = 5000,
        enable_prompt_injection_detection: bool = True,
        enable_content_moderation: bool = True,
        enable_html_sanitization: bool = True,
        strict_mode: bool = False,
    ):
        """
        Initialize the input sanitizer middleware.

        Parameters
        ----------
        max_input_length : int
            Maximum allowed input length
        enable_prompt_injection_detection : bool
            Whether to detect and block prompt injection attempts
        enable_content_moderation : bool
            Whether to filter inappropriate content
        enable_html_sanitization : bool
            Whether to strip HTML/XML tags and dangerous characters
        strict_mode : bool
            Whether to use strict filtering (more aggressive)
        """
        self.max_input_length = max_input_length
        self.enable_prompt_injection_detection = enable_prompt_injection_detection
        self.enable_content_moderation = enable_content_moderation
        self.enable_html_sanitization = enable_html_sanitization
        self.strict_mode = strict_mode

        self.injection_patterns = [
            r"ignore\s+(?:previous|all|above|prior)\s+(?:instructions?|prompts?|rules?)",
            r"forget\s+(?:everything|all|previous|above)",
            r"new\s+(?:instructions?|prompts?|rules?|task)",
            r"(?:act|behave|pretend)\s+as\s+(?:if|though)",
            r"you\s+are\s+(?:no\s+longer|not\s+an?)\s+ai",
            r"(?:role|character)\s*[:=]\s*(?!user)",
            r"system\s*[:=]|assistant\s*[:=]",
            r"<\s*(?:system|assistant|user)\s*>",
            r"```\s*(?:system|assistant|user)",
            r"override\s+(?:previous|all|security|safety)",
            r"jailbreak|prompt\s+injection",
            r"\\n\\nuser:|\\n\\nsystem:|\\n\\nassistant:",
            r"repeat\s+(?:after|the\s+following)",
            r"translate\s+(?:this|the\s+following)\s+to",
            r"what\s+(?:are|were)\s+your\s+(?:instructions|rules|prompts)",
        ]

        self.inappropriate_words = [
            # Hate speech and slurs (partial list - you should expand this)
            r"\b(?:hate|nazi|terrorist|genocide|supremac(?:ist|y))\b",
            # Explicit content
            r"\b(?:explicit|nsfw|xxx|porn|sexual)\b",
            # Violence
            r"\b(?:kill|murder|violence|bomb|weapon|attack)\b",
            # Harassment
            r"\b(?:harass|stalk|threaten|abuse|bully)\b",
            # Profanity (basic examples)
            (
                r"\b(?:damn|hell|stupid|idiot)\b"
                if not self.strict_mode
                else r"\b(?:damn|hell|stupid|idiot|crap|suck)\b"
            ),
        ]

        # HTML/XML and dangerous character patterns
        self.html_patterns = [
            r"<[^>]+>",  # HTML tags
            r"&[a-zA-Z0-9]+;",  # HTML entities
            r"javascript:",  # JavaScript protocol
            r"data:",  # Data protocol
            r"vbscript:",  # VBScript protocol
            r"on\w+\s*=",  # Event handlers
        ]

        # Excessive repetition pattern
        self.repetition_pattern = r"(.)\1{10,}"

    def wrap_model_call(self, request, handler: Callable):
        """
        Wrap model calls to sanitize input messages before they reach the model.

        This follows the LangChain middleware signature pattern.
        """
        messages = getattr(request, "messages", [])

        try:
            sanitized_messages = self._sanitize_messages(messages)
            sanitized_request = request
            if hasattr(request, "messages"):
                sanitized_request = type(request)(
                    **{**request.__dict__, "messages": sanitized_messages}
                )

            return handler(sanitized_request)
        except Exception as e:
            import traceback

            traceback.print_exc()
            raise e

    def _sanitize_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        Process messages through the sanitization pipeline.

        Parameters
        ----------
        messages : list[BaseMessage]
            List of messages to process

        Returns
        -------
        List[BaseMessage]
            Sanitized messages
        """
        sanitized_messages = []

        for i, message in enumerate(messages):
            if isinstance(message, HumanMessage):
                try:
                    sanitized_content = self._sanitize_input(message.content)
                    if sanitized_content != message.content:
                        logger.info(
                            f"Input sanitized: {len(message.content)} "
                            f"-> {len(sanitized_content)} chars"
                        )

                    sanitized_message = HumanMessage(
                        content=sanitized_content,
                        additional_kwargs=(
                            message.additional_kwargs
                            if hasattr(message, "additional_kwargs")
                            else {}
                        ),
                    )
                    sanitized_messages.append(sanitized_message)
                except ValueError as e:
                    logger.warning(f"Input blocked by sanitizer: {e}")
                    sanitized_message = HumanMessage(
                        content="[Message blocked by content filter - please rephrase your request appropriately]"
                    )
                    sanitized_messages.append(sanitized_message)
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    raise e
            else:
                sanitized_messages.append(message)
        return sanitized_messages

    def _sanitize_input(self, text: str) -> str:
        """
        Comprehensive input sanitization pipeline.

        Parameters
        ----------
        text : str
            Input text to sanitize

        Returns
        -------
        str
            Sanitized text

        Raises
        ------
        ValueError
            If input is blocked by security filters
        """
        if not isinstance(text, str):
            text = str(text)

        if len(text) > self.max_input_length:
            logger.warning(f"Input too long: {len(text)} > {self.max_input_length}")
            raise ValueError(
                f"Input exceeds maximum length of {self.max_input_length} characters"
            )

        if not text.strip():
            return text

        text = unicodedata.normalize("NFKC", text)

        if self.enable_prompt_injection_detection:
            if self._detect_prompt_injection(text):
                logger.warning("Prompt injection attempt detected")
                raise ValueError("Input contains potential prompt injection")

        if self.enable_content_moderation:
            if self._detect_inappropriate_content(text):
                logger.warning("Inappropriate content detected")
                raise ValueError("Input contains inappropriate content")

        if self.enable_html_sanitization:
            text = self._sanitize_html_and_dangerous_chars(text)

        text = re.sub(self.repetition_pattern, r"\1\1\1", text, flags=re.IGNORECASE)

        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text

    def _detect_prompt_injection(self, text: str) -> bool:
        """
        Detect potential prompt injection attempts.

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        bool
            True if prompt injection detected
        """
        text_lower = text.lower()

        for pattern in self.injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
                logger.warning(f"Prompt injection pattern detected: {pattern}")
                return True

        suspicious_delimiters = ["---", "===", "***", "+++", "###"]
        delimiter_count = sum(
            text.count(delimiter) for delimiter in suspicious_delimiters
        )
        if delimiter_count > 3:
            logger.warning("Suspicious delimiter pattern detected")
            return True

        role_switches = len(
            re.findall(r"\b(?:user|assistant|system|human|ai)\s*:", text_lower)
        )
        if role_switches > 1:
            logger.warning("Multiple role switches detected")
            return True

        return False

    def _detect_inappropriate_content(self, text: str) -> bool:
        """
        Detect inappropriate content in the text.

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        bool
            True if inappropriate content detected
        """
        text_lower = text.lower()

        for pattern in self.inappropriate_words:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning("Inappropriate content detected: pattern matched")
                return True

        return False

    def _sanitize_html_and_dangerous_chars(self, text: str) -> str:
        """
        Remove HTML tags and dangerous characters.

        Parameters
        ----------
        text : str
            Text to sanitize

        Returns
        -------
        str
            Sanitized text
        """
        for pattern in self.html_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        dangerous_chars = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
            "\\": "&#x5C;",
            "&": "&amp;",
        }

        for char, replacement in dangerous_chars.items():
            text = text.replace(char, replacement)

        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")

        return text


def create_input_sanitizer_middleware_class(
    max_input_length: int = 5000,
    enable_prompt_injection_detection: bool = True,
    enable_content_moderation: bool = True,
    enable_html_sanitization: bool = True,
    strict_mode: bool = False,
) -> InputSanitizerMiddleware:
    """
    Factory function to create input sanitizer middleware class instance.

    Parameters
    ----------
    max_input_length : int
        Maximum allowed input length
    enable_prompt_injection_detection : bool
        Whether to detect and block prompt injection attempts
    enable_content_moderation : bool
        Whether to filter inappropriate content
    enable_html_sanitization : bool
        Whether to strip HTML/XML tags and dangerous characters
    strict_mode : bool
        Whether to use strict filtering

    Returns
    -------
    InputSanitizerMiddleware
        Configured middleware instance
    """
    return InputSanitizerMiddleware(
        max_input_length=max_input_length,
        enable_prompt_injection_detection=enable_prompt_injection_detection,
        enable_content_moderation=enable_content_moderation,
        enable_html_sanitization=enable_html_sanitization,
        strict_mode=strict_mode,
    )
