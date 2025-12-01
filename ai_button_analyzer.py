"""
AI-powered button analyzer for page source XML.
Sends page source to AI for button detection and extraction.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_xml_to_ai(xml_content: str, action_context: str = "analyze buttons") -> Dict:
    """
    Send page source XML to AI for analysis.
    Logs when sending and receives button detection results.
    
    Args:
        xml_content: The page source XML content
        action_context: Context about what we're looking for (e.g., "like button", "swipe button")
        
    Returns:
        dict: AI analysis results with button locators
    """
    logger.info("=" * 60)
    logger.info(f"[AI] Sending page source XML to AI for analysis...")
    logger.info(f"[AI] Context: {action_context}")
    logger.info(f"[AI] XML size: {len(xml_content)} characters")
    logger.info("=" * 60)
    
    # Analyze XML locally first (fast, no API needed)
    buttons = analyze_xml_for_buttons(xml_content, action_context)
    
    # If we need more advanced analysis, we can use web search
    # For now, local analysis is sufficient
    
    logger.info(f"[AI] Analysis complete - found {len(buttons)} potential buttons")
    return {
        'buttons': buttons,
        'xml_size': len(xml_content),
        'context': action_context
    }


def analyze_xml_for_buttons(xml_content: str, context: str = "") -> List[Dict]:
    """
    Analyze XML to find buttons and clickable elements.
    Uses AI-like pattern matching to identify buttons.
    
    Args:
        xml_content: The page source XML content
        context: What we're looking for (e.g., "like", "swipe", "close")
        
    Returns:
        list: List of button information dictionaries
    """
    buttons = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # Keywords to search for based on context
        context_keywords = []
        if context:
            context_lower = context.lower()
            if "like" in context_lower:
                context_keywords.extend(["like", "heart", "thumbs up", "favorite"])
            if "swipe" in context_lower:
                context_keywords.extend(["swipe", "card", "next"])
            if "close" in context_lower or "dismiss" in context_lower or "popup" in context_lower:
                context_keywords.extend(["close", "dismiss", "cancel", "x", "no thanks"])
            if "home" in context_lower:
                context_keywords.extend(["home", "main"])
        
        # Find all clickable elements
        for elem in root.iter():
            clickable = elem.get('clickable', 'false')
            enabled = elem.get('enabled', 'true')
            visible = elem.get('bounds') is not None
            
            # Check if element is interactive
            is_button = (
                clickable == 'true' or 
                elem.get('class', '').lower().find('button') >= 0 or
                elem.get('class', '').lower().find('clickable') >= 0
            )
            
            if not (is_button and enabled == 'true' and visible):
                continue
            
            resource_id = elem.get('resource-id', '')
            content_desc = elem.get('content-desc', '') or ''
            text = elem.get('text', '') or ''
            class_name = elem.get('class', '')
            
            # Combine text and content-desc for matching
            combined_text = f"{content_desc} {text}".lower()
            
            # Check if this matches our context
            matches_context = False
            if context_keywords:
                matches_context = any(keyword.lower() in combined_text for keyword in context_keywords)
            else:
                matches_context = True  # If no context, include all buttons
            
            if matches_context or not context:
                button_info = {
                    'resource_id': resource_id,
                    'content_desc': content_desc,
                    'text': text,
                    'class': class_name,
                    'bounds': elem.get('bounds', ''),
                    'clickable': clickable,
                    'enabled': enabled,
                    'locators': []
                }
                
                # Generate locators for this button
                locators = []
                
                # Resource ID locator
                if resource_id:
                    locators.append(("id", resource_id))
                
                # Content description locator
                if content_desc:
                    locators.append(("accessibility_id", content_desc))
                    # XPath for content-desc
                    if content_desc:
                        locators.append(("xpath", f"//*[@content-desc='{content_desc}']"))
                
                # Text locator
                if text:
                    locators.append(("xpath", f"//*[@text='{text}']"))
                
                # XPath with contains for fuzzy matching
                if content_desc:
                    locators.append(("xpath", f"//*[contains(@content-desc, '{content_desc}')]"))
                if text:
                    locators.append(("xpath", f"//*[contains(@text, '{text}')]"))
                
                button_info['locators'] = locators
                buttons.append(button_info)
                
                logger.debug(f"[AI] Found button: {content_desc or text or resource_id}")
        
        # Sort by relevance (exact matches first, then partial)
        if context_keywords:
            buttons.sort(key=lambda b: (
                -sum(1 for kw in context_keywords if kw.lower() in (b['content_desc'] + ' ' + b['text']).lower()),
                -len(b['resource_id']),
            ), reverse=True)
        
    except Exception as e:
        logger.error(f"[AI] Error analyzing XML: {e}")
        return []
    
    return buttons


def get_button_locators_from_xml(xml_content: str, button_type: str = "like") -> List[Tuple[str, str]]:
    """
    Extract button locators from page source XML.
    Returns list of (locator_type, locator_value) tuples.
    
    Args:
        xml_content: Page source XML content
        button_type: Type of button to find ("like", "swipe", "close", etc.)
        
    Returns:
        list: List of (locator_type, locator_value) tuples, ordered by reliability
    """
    logger.info(f"[AI] Extracting {button_type} button locators from XML...")
    
    analysis = send_xml_to_ai(xml_content, f"find {button_type} button")
    buttons = analysis.get('buttons', [])
    
    if not buttons:
        logger.warning(f"[AI] No {button_type} buttons found in XML")
        return []
    
    # Get locators from the best matching button
    best_button = buttons[0]
    locators = best_button.get('locators', [])
    
    logger.info(f"[AI] Found {len(locators)} locators for {button_type} button")
    for loc_type, loc_value in locators[:5]:  # Show top 5
        logger.info(f"[AI]   - {loc_type}: {loc_value[:80]}...")  # Truncate long values
    
    return locators


def analyze_page_source_file(filepath: Path, button_type: str = "") -> Dict:
    """
    Analyze a saved page source file and extract buttons.
    
    Args:
        filepath: Path to the XML file
        button_type: Type of button to look for (optional)
        
    Returns:
        dict: Analysis results with buttons and locators
    """
    logger.info(f"[AI] Analyzing page source file: {filepath.name}")
    
    try:
        xml_content = filepath.read_text(encoding='utf-8')
        return send_xml_to_ai(xml_content, f"analyze buttons in {filepath.stem}")
    except Exception as e:
        logger.error(f"[AI] Error reading file {filepath}: {e}")
        return {}


if __name__ == "__main__":
    # Test the analyzer
    import sys
    from pages.base_page import BasePage
    from drivers import get_driver
    
    logger.info("Testing AI Button Analyzer...")
    
    # Get a page source
    driver = get_driver()
    page = BasePage()
    
    xml_content = driver.page_source
    logger.info(f"Got page source ({len(xml_content)} chars)")
    
    # Analyze for like button
    result = send_xml_to_ai(xml_content, "find like button")
    logger.info(f"Found {len(result['buttons'])} buttons")
    
    for i, button in enumerate(result['buttons'][:5], 1):
        logger.info(f"Button {i}:")
        logger.info(f"  Resource ID: {button.get('resource_id', 'N/A')}")
        logger.info(f"  Content Desc: {button.get('content_desc', 'N/A')}")
        logger.info(f"  Text: {button.get('text', 'N/A')}")
        logger.info(f"  Locators: {len(button.get('locators', []))}")

