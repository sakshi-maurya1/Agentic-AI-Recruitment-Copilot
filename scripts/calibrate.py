"""
Run this once to calibrate the FAISS distance threshold used in
rag/skill_matcher.py before trusting the default value.
 
Usage (from the project root, AIRecruitmentCopilot):
    python scripts/calibrate.py
"""
 
import os
import sys
 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
 
from rag.skill_matcher import calibrate_threshold
 
calibrate_threshold([
    ("ML", "Machine Learning"),
    ("React.js", "React"),
    ("NLP", "Natural Language Processing"),
    ("Docker", "Photoshop"),   # unrelated pair — should show a much larger distance
])
 