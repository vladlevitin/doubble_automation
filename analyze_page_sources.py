"""
Analyze saved page source files to extract real screen indicators.
Uses AI analysis to understand the app structure, then updates the code.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def analyze_page_source_file(filepath: Path) -> dict:
    """
    Analyze a single page source XML file to extract element identifiers.
    
    Returns:
        dict: Extracted information about elements, IDs, content descriptions, etc.
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        analysis = {
            'resource_ids': set(),
            'content_descriptions': set(),
            'texts': set(),
            'class_names': set(),
            'clickable_elements': [],
            'all_elements': []
        }
        
        # Extract all element information
        for elem in root.iter():
            resource_id = elem.get('resource-id', '')
            content_desc = elem.get('content-desc', '')
            text = elem.get('text', '')
            class_name = elem.get('class', '')
            clickable = elem.get('clickable', 'false')
            
            if resource_id:
                analysis['resource_ids'].add(resource_id)
            if content_desc:
                analysis['content_descriptions'].add(content_desc)
            if text:
                analysis['texts'].add(text)
            if class_name:
                analysis['class_names'].add(class_name)
            
            if clickable == 'true':
                analysis['clickable_elements'].append({
                    'resource_id': resource_id,
                    'content_desc': content_desc,
                    'text': text,
                    'class': class_name
                })
            
            analysis['all_elements'].append({
                'resource_id': resource_id,
                'content_desc': content_desc,
                'text': text,
                'class': class_name
            })
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing {filepath}: {e}")
        return None


def analyze_all_page_sources(page_sources_dir: str = "page_sources") -> dict:
    """
    Analyze all saved page source files and group by action type.
    
    Returns:
        dict: Analysis grouped by action type (like_button_click, swipe_right, etc.)
    """
    page_sources_path = Path(page_sources_dir)
    
    if not page_sources_path.exists():
        logger.warning(f"Page sources directory not found: {page_sources_dir}")
        return {}
    
    # Group files by action type
    action_groups = defaultdict(list)
    
    for filepath in page_sources_path.glob("*.xml"):
        # Extract action name from filename (format: timestamp_actionname.xml)
        parts = filepath.stem.split('_')
        if len(parts) >= 2:
            action_name = '_'.join(parts[2:])  # Skip timestamp parts
            action_groups[action_name].append(filepath)
    
    logger.info(f"Found {len(action_groups)} different action types")
    
    # Analyze each group
    results = {}
    for action_name, filepaths in action_groups.items():
        logger.info(f"Analyzing {len(filepaths)} files for action: {action_name}")
        
        all_analyses = []
        for filepath in filepaths[:5]:  # Analyze first 5 files of each type
            analysis = analyze_page_source_file(filepath)
            if analysis:
                all_analyses.append(analysis)
        
        if all_analyses:
            # Merge analyses
            merged = {
                'resource_ids': set(),
                'content_descriptions': set(),
                'texts': set(),
                'class_names': set(),
                'clickable_elements': []
            }
            
            for analysis in all_analyses:
                merged['resource_ids'].update(analysis['resource_ids'])
                merged['content_descriptions'].update(analysis['content_descriptions'])
                merged['texts'].update(analysis['texts'])
                merged['class_names'].update(analysis['class_names'])
                merged['clickable_elements'].extend(analysis['clickable_elements'])
            
            results[action_name] = merged
    
    return results


def identify_screen_indicators(analysis_results: dict) -> dict:
    """
    Use pattern analysis to identify which elements indicate which screen.
    Analyzes saved page sources to extract real identifiers.
    
    Returns:
        dict: Screen indicators organized by screen type
    """
    screen_indicators = {
        'swipe': {'ids': [], 'content_descs': [], 'texts': [], 'xpaths': []},
        'home': {'ids': [], 'content_descs': [], 'texts': [], 'xpaths': []},
        'login': {'ids': [], 'content_descs': [], 'texts': [], 'xpaths': []}
    }
    
    # Analyze like_button_click and swipe_right actions (these are on swipe screen)
    swipe_actions = ['like_button_click', 'swipe_right', 'initial_state']
    swipe_elements = set()
    
    for action in swipe_actions:
        if action in analysis_results:
            data = analysis_results[action]
            
            # Collect all unique identifiers from swipe screen
            swipe_elements.update(data['content_descriptions'])
            swipe_elements.update(data['resource_ids'])
            swipe_elements.update(data['texts'])
            
            # Look for like-related elements (most reliable indicator)
            for content_desc in data['content_descriptions']:
                if 'like' in content_desc.lower() and content_desc.strip():
                    screen_indicators['swipe']['content_descs'].append(content_desc)
            
            # Look for swipe-related elements
            for content_desc in data['content_descriptions']:
                if 'swipe' in content_desc.lower() and content_desc.strip():
                    screen_indicators['swipe']['content_descs'].append(content_desc)
            
            # Extract resource IDs that might be swipe screen indicators
            for resource_id in data['resource_ids']:
                if resource_id and 'doubble' in resource_id.lower():
                    if any(keyword in resource_id.lower() for keyword in ['swipe', 'like', 'card', 'profile', 'match']):
                        screen_indicators['swipe']['ids'].append(resource_id)
            
            # Look for clickable elements that might be buttons
            for elem in data['clickable_elements']:
                if elem.get('content_desc') and 'like' in elem['content_desc'].lower():
                    screen_indicators['swipe']['content_descs'].append(elem['content_desc'])
                if elem.get('resource_id') and 'doubble' in elem['resource_id'].lower():
                    if any(kw in elem['resource_id'].lower() for kw in ['like', 'swipe', 'button']):
                        screen_indicators['swipe']['ids'].append(elem['resource_id'])
    
    # Remove duplicates and keep unique values
    for screen_type in screen_indicators:
        for key in screen_indicators[screen_type]:
            screen_indicators[screen_type][key] = list(set(screen_indicators[screen_type][key]))
    
    return screen_indicators


def update_screen_detection_code(screen_indicators: dict, output_file: str = "pages/doubble_screens.py"):
    """
    Update the screen detection code with real indicators found from analysis.
    Uses AI-extracted patterns to update the code automatically.
    """
    logger.info("Updating screen detection code with analyzed indicators...")
    
    # Read current file
    filepath = Path(output_file)
    if not filepath.exists():
        logger.error(f"File not found: {output_file}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    
    # Build new indicator lists (prioritize most reliable)
    swipe_indicators = []
    
    # Priority 1: Content descriptions with "Like" (most reliable for swipe screen)
    like_content_descs = [desc for desc in screen_indicators['swipe']['content_descs'] if 'like' in desc.lower()]
    for content_desc in like_content_descs[:2]:  # Top 2
        swipe_indicators.append(f'        ("accessibility_id", "{content_desc}"),')
    
    # Priority 2: XPath for like button (works well)
    if like_content_descs:
        swipe_indicators.append('        ("xpath", "//*[contains(@content-desc, \'Like\') or contains(@content-desc, \'like\')]"),')
    
    # Priority 3: Content descriptions with "Swipe"
    swipe_content_descs = [desc for desc in screen_indicators['swipe']['content_descs'] if 'swipe' in desc.lower()]
    for content_desc in swipe_content_descs[:2]:  # Top 2
        swipe_indicators.append(f'        ("accessibility_id", "{content_desc}"),')
        swipe_indicators.append(f'        ("xpath", "//*[contains(@content-desc, \'{content_desc}\')]"),')
    
    # Priority 4: Resource IDs (if found)
    for resource_id in screen_indicators['swipe']['ids'][:3]:  # Top 3
        swipe_indicators.append(f'        ("id", "{resource_id}"),')
    
    # If no indicators found, keep existing ones
    if not swipe_indicators:
        logger.warning("No new swipe indicators found - keeping existing ones")
        return False
    
    # Find and replace SWIPE_SCREEN_INDICATORS
    pattern = r'(SWIPE_SCREEN_INDICATORS = \[)(.*?)(\])'
    
    new_swipe_indicators = 'SWIPE_SCREEN_INDICATORS = [\n' + '\n'.join(swipe_indicators) + '\n    ]'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_swipe_indicators, content, flags=re.DOTALL)
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"✓ Updated {output_file} with {len(swipe_indicators)} real indicators")
        logger.info("The code now uses actual identifiers from your app!")
        return True
    else:
        logger.warning("Could not find SWIPE_SCREEN_INDICATORS to update")
        return False


def ai_analyze_patterns(analysis_results: dict) -> dict:
    """
    Use AI analysis to understand patterns and extract screen indicators.
    This is the initial AI analysis step - results are then hardcoded into the detection.
    """
    logger.info("Using AI analysis to understand screen patterns...")
    
    # Analyze patterns in the data
    screen_indicators = identify_screen_indicators(analysis_results)
    
    # Additional AI-based pattern recognition
    # Look for common patterns across multiple page sources
    
    # For swipe screen: look for elements that appear consistently
    swipe_actions = ['like_button_click', 'swipe_right']
    common_swipe_elements = {}
    
    for action in swipe_actions:
        if action in analysis_results:
            data = analysis_results[action]
            # Count frequency of elements
            for content_desc in data['content_descriptions']:
                if content_desc:
                    common_swipe_elements[content_desc] = common_swipe_elements.get(content_desc, 0) + 1
    
    # Prioritize most common elements
    if common_swipe_elements:
        most_common = sorted(common_swipe_elements.items(), key=lambda x: x[1], reverse=True)
        logger.info(f"Most common elements on swipe screen: {most_common[:5]}")
        
        # Add most common to indicators
        for elem, count in most_common[:3]:
            if elem not in screen_indicators['swipe']['content_descs']:
                screen_indicators['swipe']['content_descs'].append(elem)
    
    return screen_indicators


def main():
    """Main analysis function."""
    logger.info("=" * 60)
    logger.info("AI-Powered Page Source Analysis")
    logger.info("Extracting Real Screen Indicators from Saved Page Sources")
    logger.info("=" * 60)
    
    # Step 1: Analyze all page source files
    logger.info("\n[Step 1/4] Analyzing saved page source files...")
    analysis_results = analyze_all_page_sources()
    
    if not analysis_results:
        logger.error("No page sources found to analyze!")
        logger.info("Run the automation script first to generate page source files.")
        logger.info("Page sources are saved in: page_sources/")
        return 1
    
    # Step 2: AI Analysis - Understand patterns
    logger.info("\n[Step 2/4] AI Analysis - Understanding screen patterns...")
    screen_indicators = ai_analyze_patterns(analysis_results)
    
    # Step 3: Display findings
    logger.info("\n" + "=" * 60)
    logger.info("[Step 3/4] Analysis Results - Extracted Indicators:")
    logger.info("=" * 60)
    
    for screen_type, indicators in screen_indicators.items():
        logger.info(f"\n{screen_type.upper()} Screen Indicators Found:")
        if indicators['ids']:
            logger.info(f"  Resource IDs ({len(indicators['ids'])}):")
            for rid in indicators['ids'][:5]:
                logger.info(f"    - {rid}")
        if indicators['content_descs']:
            logger.info(f"  Content Descriptions ({len(indicators['content_descs'])}):")
            for desc in indicators['content_descs'][:5]:
                logger.info(f"    - {desc}")
    
    # Step 4: Update code with real indicators
    logger.info("\n" + "=" * 60)
    logger.info("[Step 4/4] Updating code with analyzed indicators...")
    logger.info("=" * 60)
    
    if update_screen_detection_code(screen_indicators):
        logger.info("\n" + "=" * 60)
        logger.info("✓ Code updated successfully!")
        logger.info("Screen detection now uses REAL identifiers from your app.")
        logger.info("No more AI needed - code works with actual app structure!")
        logger.info("=" * 60)
    else:
        logger.warning("\nCould not update code automatically.")
        logger.info("Please manually update pages/doubble_screens.py with the indicators above.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

