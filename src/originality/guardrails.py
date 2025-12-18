# src/originality/guardrails.py
"""
Originality Guardrail System - Prevents plagiarism and ensures novelty.
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class OriginalityCheckResult:
    """Result of an originality check"""
    is_original: bool
    similarity_score: float
    similar_content: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[str]] = None
    violation_type: Optional[str] = None

class SimilarityChecker(ABC):
    """Abstract base class for similarity checking"""
    
    @abstractmethod
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        pass
    
    @abstractmethod
    def find_similar_content(self, text: str, corpus: List[str]) -> List[Dict[str, Any]]:
        """Find similar content in a corpus"""
        pass

class TFIDFSimilarityChecker(SimilarityChecker):
    """TF-IDF based similarity checker"""
    
    def __init__(self, ngram_range=(1, 3), max_features=5000):
        self.vectorizer = TfidfVectorizer(
            ngram_range=ngram_range,
            max_features=max_features,
            stop_words='english'
        )
        self.corpus_vectors = None
        self.corpus_texts = None
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        try:
            vectors = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def find_similar_content(self, text: str, corpus: List[str]) -> List[Dict[str, Any]]:
        """Find similar content in corpus"""
        if not corpus:
            return []
        # Fit vectorizer on corpus + query text
        all_texts = corpus + [text]
        vectors = self.vectorizer.fit_transform(all_texts)
        query_vector = vectors[-1]
        corpus_vectors = vectors[:-1]
        similarities = cosine_similarity(query_vector, corpus_vectors)[0]
        results = []
        for idx, similarity in enumerate(similarities):
            if similarity > 0.1:
                results.append({
                    'text': corpus[idx],
                    'similarity': float(similarity),
                    'index': idx
                })
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:10]

class OriginalityGuardrailSystem:
    """Main guardrail system that prevents plagiarism and ensures novelty."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.checkers = {
            'text': TFIDFSimilarityChecker(),
            'hypothesis': TFIDFSimilarityChecker(ngram_range=(1, 2)),
            'methodology': TFIDFSimilarityChecker(ngram_range=(2, 3)),
            'code': None  # Placeholder for code similarity checker
        }
        self.thresholds = {
            'hypothesis': self.config.get('hypothesis_threshold', 0.8),
            'methodology': self.config.get('methodology_threshold', 0.7),
            'result': self.config.get('result_threshold', 0.6),
            'text': self.config.get('text_threshold', 0.15),
            'code': self.config.get('code_threshold', 0.3)
        }
        self.checked_cache = {}
        self.stats = {
            'checks_performed': 0,
            'violations_found': 0,
            'rewrites_triggered': 0
        }
    
    def validate_topic_originality(
        self,
        topic: str,
        domain: str,
        keywords: List[str]
    ) -> Dict[str, Any]:
        """Validate if a research topic is original."""
        logger.info(f"Validating topic originality: {topic}")
        similar_topics = self._query_similar_topics(topic, domain, keywords)
        max_similarity = 0.0
        similar_works = []
        if similar_topics:
            checker = self.checkers['text']
            for similar_topic in similar_topics:
                similarity = checker.calculate_similarity(topic, similar_topic['title'])
                if similarity > max_similarity:
                    max_similarity = similarity
                if similarity > 0.5:
                    similar_works.append({
                        'title': similar_topic['title'],
                        'similarity': similarity,
                        'source': similar_topic.get('source', 'unknown'),
                        'year': similar_topic.get('year', 'unknown')
                    })
        is_original = max_similarity < self.thresholds['text']
        return {
            'is_original': is_original,
            'max_similarity': max_similarity,
            'similar_works': similar_works,
            'originality_score': 1.0 - max_similarity,
            'threshold_used': self.thresholds['text'],
            'assessment': 'sufficiently_original' if is_original else 'too_similar'
        }
    
    def check_hypothesis_originality(
        self,
        hypothesis: str
    ) -> Tuple[OriginalityCheckResult, Optional[Dict]]:
        """Check if a hypothesis is original."""
        self.stats['checks_performed'] += 1
        cache_key = hashlib.md5(f"hypothesis:{hypothesis}".encode()).hexdigest()
        if cache_key in self.checked_cache:
            return self.checked_cache[cache_key]
        similar_hypotheses = self._query_similar_hypotheses(hypothesis)
        max_similarity = 0.0
        most_similar = None
        checker = self.checkers['hypothesis']
        for similar in similar_hypotheses:
            similarity = checker.calculate_similarity(hypothesis, similar['text'])
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar = similar
        threshold = self.thresholds['hypothesis']
        is_original = max_similarity < threshold
        result = OriginalityCheckResult(
            is_original=is_original,
            similarity_score=max_similarity,
            similar_content=[most_similar] if most_similar else None,
            recommendations=self._generate_hypothesis_recommendations(
                hypothesis, max_similarity, most_similar
            ) if not is_original else None,
            violation_type='hypothesis_plagiarism' if not is_original else None
        )
        violation = None
        if not is_original:
            self.stats['violations_found'] += 1
            violation = {
                'type': 'hypothesis_similarity',
                'original_hypothesis': hypothesis,
                'similar_hypothesis': most_similar,
                'similarity_score': max_similarity,
                'threshold': threshold,
                'suggested_actions': [
                    "Reformulate the hypothesis to emphasize novelty",
                    "Add domain-specific constraints or conditions",
                    "Combine multiple existing hypotheses in a novel way"
                ]
            }
        self.checked_cache[cache_key] = (result, violation)
        return result, violation
    
    def check_text_originality(self, text: str, context: Optional[str] = None) -> str:
        """Check text for originality and rewrite if necessary."""
        self.stats['checks_performed'] += 1
        if len(text.split()) < 10:
            return text
        # Placeholder implementation – simply returns original text
        return text
    
    # Placeholder private methods for querying databases
    def _query_similar_topics(self, topic, domain, keywords):
        # In a real implementation, query academic databases/APIs
        return []
    
    def _query_similar_hypotheses(self, hypothesis):
        return []
    
    def _generate_hypothesis_recommendations(self, hypothesis, similarity, similar):
        return []
