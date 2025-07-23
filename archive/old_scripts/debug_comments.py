#!/usr/bin/env python3
"""
Debug-Script um zu sehen wo die Kommentare stehen
"""

from src.parsers.docx_parser import DocxParser
import re

def find_comments_in_document():
    corrected_path = '/Users/max/Korrekturtool BA/Volltext_BA_Max Thomsen Kopie_korrigiert.docx'
    
    parser = DocxParser(corrected_path)
    chunks = parser.parse()
    full_text = parser.full_text
    
    print("=== KOMMENTAR-DEBUG ===\n")
    
    # Finde alle Kommentare mit Kontext
    pattern = r'(.{0,50})\[([^\]]+)\](.{0,50})'
    matches = re.finditer(pattern, full_text)
    
    comments_found = 0
    for match in matches:
        comments_found += 1
        before = match.group(1).strip()
        comment = match.group(2)
        after = match.group(3).strip()
        
        print(f"Kommentar {comments_found}:")
        print(f"  Vorher: ...{before}")
        print(f"  KOMMENTAR: [{comment}]")
        print(f"  Nachher: {after}...")
        print(f"  Position: {match.start()}-{match.end()}")
        print("-" * 50)
        
        if comments_found >= 5:  # Zeige nur ersten 5
            break
    
    print(f"\nGesamt gefundene Kommentare: {full_text.count('[')}")
    
    # Analysiere Absätze mit Kommentaren
    print("\n=== ABSÄTZE MIT KOMMENTAREN ===")
    for i, chunk in enumerate(chunks):
        if '[' in chunk.text:
            print(f"\nAbsatz {i+1}: {chunk.element_type}")
            print(f"Text: {chunk.text[:100]}...")
            comment_count = chunk.text.count('[')
            print(f"Kommentare in diesem Absatz: {comment_count}")


if __name__ == "__main__":
    find_comments_in_document()