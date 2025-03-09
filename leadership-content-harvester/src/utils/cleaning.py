import re
from loguru import logger

def normalize_turkish_text(text: str) -> str:
    """
    Normalize Turkish text by properly handling Unicode escape sequences
    and ensuring correct character encoding.
    
    Args:
        text: Text string that may contain Unicode escape sequences
        
    Returns:
        Normalized text with proper Turkish characters
    """
    # Handle already-escaped Unicode sequences
    if '\\u' in text:
        try:
            # Decode Unicode escape sequences
            text = text.encode().decode('unicode_escape')
        except UnicodeDecodeError:
            logger.warning("Failed to decode Unicode escape sequences in normalize_turkish_text")
    
    # Replace common Turkish characters if they're still in escaped form
    replacements = {
        '\\u0131': 'ı',  # dotless i
        '\\u0130': 'İ',  # dotted I
        '\\u015f': 'ş',  # s with cedilla
        '\\u015e': 'Ş',  # capital S with cedilla
        '\\u011f': 'ğ',  # g with breve
        '\\u011e': 'Ğ',  # capital G with breve
        '\\u00e7': 'ç',  # c with cedilla
        '\\u00c7': 'Ç',  # capital C with cedilla
        '\\u00f6': 'ö',  # o with diaeresis
        '\\u00d6': 'Ö',  # capital O with diaeresis
        '\\u00fc': 'ü',  # u with diaeresis
        '\\u00dc': 'Ü',  # capital U with diaeresis
    }
    
    for escape_seq, turkish_char in replacements.items():
        text = text.replace(escape_seq, turkish_char)
    
    return text

def clean_transcript_text(text: str) -> str:
    """
    Clean transcript text by removing redundant spaces,
    normalizing Turkish characters, and fixing common issues.
    
    Args:
        text: Raw transcript text
        
    Returns:
        Cleaned transcript text
    """
    # First normalize any Unicode escape sequences
    text = normalize_turkish_text(text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any remaining special characters or control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()
