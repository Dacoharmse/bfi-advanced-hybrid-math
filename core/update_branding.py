#!/usr/bin/env python3
"""
Utility script to update branding across all template files
Removes AI references while maintaining intelligent system descriptions
"""

import os
import re
from pathlib import Path

def update_file_content(file_path, replacements):
    """Update file content with the provided replacements"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        original_content = content
        
        # Apply replacements
        for old_text, new_text in replacements:
            content = content.replace(old_text, new_text)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update all template files"""
    templates_dir = Path('/home/chronic/Projects/bfi-signals/core/templates')
    
    # General replacements for all files
    global_replacements = [
        # Page titles
        ('BFI Signals AI Dashboard', 'BFI Signals Platform'),
        ('BFI Signals AI', 'BFI Signals'),
        
        # Content replacements - more nuanced
        ('AI-powered', 'intelligent'),
        ('AI-enhanced', 'intelligent'),
        ('AI-generated', 'algorithmically generated'),
        ('your AI', 'the system'),
        ('the AI', 'the system'),
        ('AI learns', 'system learns'),
        ('AI learning', 'system learning'),
        ('AI confidence', 'confidence score'),
        ('AI Status', 'System Status'),
        ('Advanced AI & ML', 'Advanced Analytics'),
        ('AI Powered', 'Intelligent Analytics'),
        
        # Specific content updates
        ('Help your AI learn by adding trading outcomes. The more data you provide, the smarter your AI becomes!',
         'Help the system learn by adding trading outcomes. The more data you provide, the more accurate predictions become!'),
        
        ('Enter accurate profit/loss amounts. The AI uses this data to identify successful patterns and improve future predictions.',
         'Enter accurate profit/loss amounts. The system uses this data to identify successful patterns and improve future predictions.'),
        
        ('Add outcomes for both winning and losing trades. The AI learns from both successes and failures to improve risk assessment.',
         'Add outcomes for both winning and losing trades. The system learns from both successes and failures to improve risk assessment.'),
        
        ('Add outcomes regularly to keep the AI learning current market conditions and adapting to changing patterns.',
         'Add outcomes regularly to keep the system learning current market conditions and adapting to changing patterns.'),
        
        ('Each outcome helps the AI adjust probabilities, improve risk levels, and identify which strategies work best in different market conditions.',
         'Each outcome helps the system adjust probabilities, improve risk levels, and identify which strategies work best in different market conditions.'),
    ]
    
    # File-specific replacements
    file_specific_replacements = {
        'signals_modern.html': [
            ('Monitor and track your AI-generated trading signals with real-time performance metrics',
             'Monitor and track your algorithmically generated trading signals with real-time performance metrics'),
        ],
        'signals.html': [
            ('Complete history of all AI-enhanced trading signals with outcomes and performance tracking',
             'Complete history of all intelligent trading signals with outcomes and performance tracking'),
        ],
        'performance.html': [
            ('Your AI-enhanced system is performing very well',
             'Your intelligent system is performing very well'),
            ('Add more trading outcomes</a> for better AI learning',
             'Add more trading outcomes</a> for better system learning'),
        ],
        'settings_modern.html': [
            ('Configure your BFI Signals AI Dashboard preferences',
             'Configure your BFI Signals Platform preferences'),
        ],
        'components/footer.html': [
            ('BFI Signals AI Dashboard. All rights reserved.',
             'BFI Signals Platform. All rights reserved.'),
        ]
    }
    
    updated_files = []
    
    # Process all HTML files in templates directory
    for html_file in templates_dir.rglob('*.html'):
        relative_path = html_file.relative_to(templates_dir)
        
        # Apply global replacements
        replacements = global_replacements.copy()
        
        # Add file-specific replacements if they exist
        if str(relative_path) in file_specific_replacements:
            replacements.extend(file_specific_replacements[str(relative_path)])
        
        if update_file_content(html_file, replacements):
            updated_files.append(str(relative_path))
            print(f"✅ Updated {relative_path}")
    
    print(f"\n🎉 Successfully updated {len(updated_files)} template files:")
    for file in updated_files:
        print(f"   - {file}")
    
    if not updated_files:
        print("✨ All files are already up to date!")

if __name__ == '__main__':
    main()