import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re

class QuestionProcessor:
    def __init__(self, ontology_parser):
        nltk.download('punkt')
        nltk.download('stopwords')
        nltk.download('averaged_perceptron_tagger')
        self.nlp = spacy.load('en_core_web_sm')
        self.ontology_parser = ontology_parser
        self.all_concepts = set(ontology_parser.get_all_concepts())
        
        # Define question patterns
        self.question_patterns = {
            'definition': r'what is|define|meaning of|definition of',
            'category': r'which category|what type|what category|what class',
            'references': r'where can i find|references|links|resources|more information',
            'acronym': r'what is the acronym|abbreviation|short form',
            'alternative_names': r'other names|alternative names|also known as|also called',
            'subclass': r'what are the types of|what are the kinds of|what subclasses|subcategories',
            'superclass': r'what is the parent|superclass|category of|type of',
            'related': r'what is related to|connection between|relationship|how is it related',
            'comments': r'what additional information|tell me more|additional details|more about'
        }
        
    def process_question(self, question):
        """Process the question and extract relevant information"""
        # Extract key concepts
        concepts = self.extract_concepts(question.lower())
        
        # Get all requested information types
        question_types = set()
        question_lower = question.lower()
        ref_type = None
        
        # Check for definition requests
        if any(word in question_lower for word in ['what is', 'define', 'definition', 'meaning']):
            question_types.add('definition')
            
        # Check for acronym requests
        if any(word in question_lower for word in ['acronym', 'abbreviation']):
            question_types.add('acronym')
            
        # Check for link/reference requests with specific types
        ref_type_keywords = {
            'pdf': ['pdf', 'document', 'qb pdf', 'qb_pdf_link'],
            'doi': ['doi'],
            'url': ['url', 'link', 'website'],
            'wiki': ['wiki', 'wikipedia', 'link', 'links'],
            'paper': ['paper', 'article', 'publication']
        }
        
        # First check for specific reference types
        for type_key, keywords in ref_type_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                question_types.add('references')
                ref_type = type_key
                break
        
        # Then check for general references if no specific type found
        if not ref_type and any(word in question_lower for word in ['reference', 'where can i find']):
            question_types.add('references')
            
        # Check for alternative names
        if any(phrase in question_lower for phrase in ['also known as', 'alternative names', 'other names']):
            question_types.add('alternative_names')
            
        # If no specific types found, default to definition
        if not question_types:
            question_types.add('definition')
        
        return {
            'concepts': concepts,
            'question_types': list(question_types),
            'text': question_lower,
            'ref_type': ref_type
        }
    
    def _determine_question_type(self, question):
        """Determine the type of question being asked"""
        question = question.lower().strip()
        
        # Check each pattern in order of priority
        for q_type, pattern in self.question_patterns.items():
            if re.search(pattern, question, re.IGNORECASE):
                return q_type
                
        # If no specific pattern is matched, check for common question words
        if any(word in question for word in ['what is', 'define', 'meaning']):
            return 'definition'
            
        # Default to definition if no other type is matched
        return 'definition'
        
    def extract_concepts(self, text):
        """Extract key concepts from text using NER and POS tagging"""
        doc = self.nlp(text.lower())
        concepts = []
        
        # First try to find exact matches with ontology concepts
        text_lower = text.lower()
        matched_concepts = [concept for concept in self.all_concepts 
                          if concept in text_lower]
        
        # Sort by length (descending) to prefer longer matches
        matched_concepts.sort(key=len, reverse=True)
        
        if matched_concepts:
            # If we found exact matches in ontology, use them
            concepts.extend(matched_concepts)
        else:
            # If no exact matches, try NLP-based extraction
            # Get noun phrases (longest matches)
            noun_phrases = set([chunk.text for chunk in doc.noun_chunks])
            concepts.extend(noun_phrases)
            
            # Get named entities that aren't part of noun phrases
            for ent in doc.ents:
                if not any(ent.text in phrase for phrase in noun_phrases):
                    concepts.append(ent.text)
            
            # Only get individual nouns if they're not part of any larger phrase
            for token in doc:
                if token.pos_ in ['NOUN', 'PROPN'] and not token.is_stop:
                    if not any(token.text in phrase for phrase in concepts):
                        concepts.append(token.text)
        
        # Clean concepts
        cleaned_concepts = []
        for concept in concepts:
            # Remove common question words and stop words
            if not any(word in concept for word in ['what', 'who', 'where', 'when', 'how', 'why', 'which']):
                cleaned = concept.strip()
                if len(cleaned) > 1:  # Keep only meaningful concepts
                    cleaned_concepts.append(cleaned)
        
        # Remove duplicates while preserving order
        seen = set()
        return [x for x in cleaned_concepts if not (x in seen or seen.add(x))]
        
    def get_question_focus(self, question):
        """Extract the main focus/topic of the question"""
        doc = self.nlp(question.lower())
        
        # Try to find focus after question words or in the beginning
        focus_words = []
        found_question_word = False
        
        for token in doc:
            if token.text in ['what', 'who', 'where', 'when', 'how', 'why', 'which']:
                found_question_word = True
                continue
                
            if found_question_word and token.pos_ in ['NOUN', 'PROPN']:
                focus_words.append(token.text)
                
        # If no focus found after question word, try noun chunks
        if not focus_words:
            focus_words = [chunk.text for chunk in doc.noun_chunks]
            
        return ' '.join(focus_words) if focus_words else None