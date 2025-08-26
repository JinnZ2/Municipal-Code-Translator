!/usr/bin/env python3
“””
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
“””

import requests
from bs4 import BeautifulSoup
import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import time
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path

@dataclass
class MunicipalTranslationResult:
original_text: str
plain_english: str
what_you_can_do: List[str]
what_you_cannot_do: List[str]
permits_required: List[str]
deadlines: List[str]
fees: List[str]
contact_info: List[str]
next_steps: List[str]
confidence_score: float
code_type: str
municipality: str

class MunicipalCodeTranslator:
def **init**(self):
self.municipal_jargon = self.load_municipal_jargon()
self.code_patterns = self.load_code_patterns()
self.zoning_codes = self.load_zoning_codes()
self.permit_keywords = self.load_permit_keywords()

```
def load_municipal_jargon(self) -> Dict[str, str]:
    """Municipal government jargon translation dictionary"""
    return {
        # Zoning terms
        'conditional use permit': 'special permission needed (requires application and possibly a hearing)',
        'variance': 'exception to the normal rules (hard to get)',
        'non-conforming use': 'something that was legal before but isn\'t now (usually can continue)',
        'setback requirements': 'how far from property lines you must build',
        'floor area ratio': 'limits on how big your building can be compared to your lot size',
        'density restrictions': 'limits on how many units you can have',
        'height restrictions': 'maximum height allowed for buildings',
        'lot coverage': 'percentage of your lot that can have buildings on it',
        'accessory dwelling unit': 'small apartment or guest house on your property',
        'planned unit development': 'special development with relaxed rules',
        
        # Building codes
        'certificate of occupancy': 'official permission to live in or use a building',
        'building permit': 'permission to construct or renovate',
        'right of way': 'public property (usually for roads/utilities)',
        'easement': 'someone else has rights to use part of your property',
        'egress requirements': 'rules about exits and escape routes',
        'fire separation': 'walls that slow down fire spread',
        'structural load': 'how much weight a building can safely hold',
        'code compliance': 'meets all the safety and legal requirements',
        
        # Administrative terms  
        'public hearing': 'meeting where residents can speak for/against proposal',
        'administrative review': 'staff decides (no public hearing)',
        'discretionary permit': 'decision depends on specific circumstances',
        'ministerial permit': 'automatic if you meet requirements',
        'site plan review': 'detailed review of your construction plans',
        'environmental review': 'study of environmental impact',
        'appeals process': 'how to challenge a decision',
        'vested rights': 'permission you already have that can\'t be taken away',
        
        # Fees and timing
        'impact fees': 'charges for effects on infrastructure',
        'processing time': 'how long approval takes',
        'renewal requirements': 'what you need to do to keep permits active',
        'expiration date': 'when permission runs out',
        'phased development': 'building in stages over time',
        
        # Business licensing
        'business license': 'permission to operate a business',
        'home occupation permit': 'permission to run business from home',
        'commercial use': 'business or retail activity',
        'industrial use': 'manufacturing or heavy business',
        'mixed use': 'combination of residential and commercial',
    }

def load_code_patterns(self) -> Dict[str, Dict]:
    """Patterns for different types of municipal codes"""
    return {
```

#!/usr/bin/env python3
“””
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
“””

import requests
from bs4 import BeautifulSoup
import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import time
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path

@dataclass
class MunicipalTranslationResult:
original_text: str
plain_english: str
what_you_can_do: List[str]
what_you_cannot_do: List[str]
permits_required: List[str]
deadlines: List[str]
fees: List[str]
contact_info: List[str]
next_steps: List[str]
confidence_score: float
code_type: str
municipality: str

class MunicipalCodeTranslator:
def **init**(self):
self.municipal_jargon = self.load_municipal_jargon()
self.code_patterns = self.load_code_patterns()
self.zoning_codes = self.load_zoning_codes()
self.permit_keywords = self.load_permit_keywords()

```
def load_municipal_jargon(self) -> Dict[str, str]:
    """Municipal government jargon translation dictionary"""
    return {
        # Zoning terms
        'conditional use permit': 'special permission needed (requires application and possibly a hearing)',
        'variance': 'exception to the normal rules (hard to get)',
        'non-conforming use': 'something that was legal before but isn\'t now (usually can continue)',
        'setback requirements': 'how far from property lines you must build',
        'floor area ratio': 'limits on how big your building can be compared to your lot size',
        'density restrictions': 'limits on how many units you can have',
        'height restrictions': 'maximum height allowed for buildings',
        'lot coverage': 'percentage of your lot that can have buildings on it',
        'accessory dwelling unit': 'small apartment or guest house on your property',
        'planned unit development': 'special development with relaxed rules',
        
        # Building codes
        'certificate of occupancy': 'official permission to live in or use a building',
        'building permit': 'permission to construct or renovate',
        'right of way': 'public property (usually for roads/utilities)',
        'easement': 'someone else has rights to use part of your property',
        'egress requirements': 'rules about exits and escape routes',
        'fire separation': 'walls that slow down fire spread',
        'structural load': 'how much weight a building can safely hold',
        'code compliance': 'meets all the safety and legal requirements',
        
        # Administrative terms  
        'public hearing': 'meeting where residents can speak for/against proposal',
        'administrative review': 'staff decides (no public hearing)',
        'discretionary permit': 'decision depends on specific circumstances',
        'ministerial permit': 'automatic if you meet requirements',
        'site plan review': 'detailed review of your construction plans',
        'environmental review': 'study of environmental impact',
        'appeals process': 'how to challenge a decision',
        'vested rights': 'permission you already have that can\'t be taken away',
        
        # Fees and timing
        'impact fees': 'charges for effects on infrastructure',
        'processing time': 'how long approval takes',
        'renewal requirements': 'what you need to do to keep permits active',
        'expiration date': 'when permission runs out',
        'phased development': 'building in stages over time',
        
        # Business licensing
        'business license': 'permission to operate a business',
        'home occupation permit': 'permission to run business from home',
        'commercial use': 'business or retail activity',
        'industrial use': 'manufacturing or heavy business',
        'mixed use': 'combination of residential and commercial',
    }

def load_code_patterns(self) -> Dict[str, Dict]:
    """Patterns for different types of municipal codes"""
    return {
```

#!/usr/bin/env python3
“””
Municipal Code Translator - Making Local Government Understandable

Translates zoning laws, building codes, permit requirements, and municipal ordinances
into plain English so regular people can understand what they can actually do.
“””

import requests
from bs4 import BeautifulSoup
import re
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import time
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path

@dataclass
class MunicipalTranslationResult:
original_text: str
plain_english: str
what_you_can_do: List[str]
what_you_cannot_do: List[str]
permits_required: List[str]
deadlines: List[str]
fees: List[str]
contact_info: List[str]
next_steps: List[str]
confidence_score: float
code_type: str
municipality: str

class MunicipalCodeTranslator:
def **init**(self):
self.municipal_jargon = self.load_municipal_jargon()
self.code_patterns = self.load_code_patterns()
self.zoning_codes = self.load_zoning_codes()
self.permit_keywords = self.load_permit_keywords()

```
def load_municipal_jargon(self) -> Dict[str, str]:
    """Municipal government jargon translation dictionary"""
    return {
        # Zoning terms
        'conditional use permit': 'special permission needed (requires application and possibly a hearing)',
        'variance': 'exception to the normal rules (hard to get)',
        'non-conforming use': 'something that was legal before but isn\'t now (usually can continue)',
        'setback requirements': 'how far from property lines you must build',
        'floor area ratio': 'limits on how big your building can be compared to your lot size',
        'density restrictions': 'limits on how many units you can have',
        'height restrictions': 'maximum height allowed for buildings',
        'lot coverage': 'percentage of your lot that can have buildings on it',
        'accessory dwelling unit': 'small apartment or guest house on your property',
        'planned unit development': 'special development with relaxed rules',
        
        # Building codes
        'certificate of occupancy': 'official permission to live in or use a building',
        'building permit': 'permission to construct or renovate',
        'right of way': 'public property (usually for roads/utilities)',
        'easement': 'someone else has rights to use part of your property',
        'egress requirements': 'rules about exits and escape routes',
        'fire separation': 'walls that slow down fire spread',
        'structural load': 'how much weight a building can safely hold',
        'code compliance': 'meets all the safety and legal requirements',
        
        # Administrative terms  
        'public hearing': 'meeting where residents can speak for/against proposal',
        'administrative review': 'staff decides (no public hearing)',
        'discretionary permit': 'decision depends on specific circumstances',
        'ministerial permit': 'automatic if you meet requirements',
        'site plan review': 'detailed review of your construction plans',
        'environmental review': 'study of environmental impact',
        'appeals process': 'how to challenge a decision',
        'vested rights': 'permission you already have that can\'t be taken away',
        
        # Fees and timing
        'impact fees': 'charges for effects on infrastructure',
        'processing time': 'how long approval takes',
        'renewal requirements': 'what you need to do to keep permits active',
        'expiration date': 'when permission runs out',
        'phased development': 'building in stages over time',
        
        # Business licensing
        'business license': 'permission to operate a business',
        'home occupation permit': 'permission to run business from home',
        'commercial use': 'business or retail activity',
        'industrial use': 'manufacturing or heavy business',
        'mixed use': 'combination of residential and commercial',
    }

def load_code_patterns(self) -> Dict[str, Dict]:
    """Patterns for different types of municipal codes"""
    return {
```
