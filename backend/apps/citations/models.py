from django.db import models


class CitationFormat(models.TextChoices):
    """Supported citation formats"""
    APA7 = 'apa7', 'APA 7th Edition'
    MLA9 = 'mla9', 'MLA 9th Edition'
    CHICAGO17 = 'chicago17', 'Chicago 17th Edition'
    BIBTEX = 'bibtex', 'BibTeX'
    IEEE = 'ieee', 'IEEE'
    HARVARD = 'harvard', 'Harvard'
