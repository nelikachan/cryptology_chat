class AnswerGenerator:
    def __init__(self, ontology_parser):
        self.parser = ontology_parser
        
    def generate_answer(self, processed_question):
        concepts = processed_question['concepts']
        question_types = processed_question.get('question_types', ['definition'])
        text = processed_question.get('text', '')
        ref_type = processed_question.get('ref_type', None)
        
        if not concepts:
            return "👋 Hello! I'm sorry, I couldn't identify any specific concepts in your question. Could you please rephrase it?"
        
        # Remove duplicates and normalize concepts
        concepts = list(set([c.lower().strip() for c in concepts]))
        
        all_answers = []
        is_first_question = True  # Flag to track if this is the first question
        
        for concept in concepts:
            concept_answers = []
            
            # Start with greeting for the first question
            if is_first_question:
                concept_answers.append(f"👋 Of course, here's the information about '{concept}':")
                is_first_question = False
            
            # Handle each requested information type
            for q_type in question_types:
                method = getattr(self, f'_handle_{q_type}_question', self._handle_definition_question)
                if q_type == 'references' and ref_type:
                    answer = method(concept, text, ref_type)
                else:
                    answer = method(concept, text)
                if answer:
                    # Add newline before each type except the first one
                    if concept_answers and not answer.startswith('\n'):
                        concept_answers.append('')  # Add empty line between different types
                    concept_answers.append(answer)
            
            if concept_answers:
                all_answers.append('\n'.join(concept_answers))
        
        if not all_answers:
            return "👋 I'm sorry, I couldn't find the requested information in my knowledge base. Could you please rephrase your question or ask about a different concept?"
        
        # Format the final answer with proper spacing and structure
        final_answer = "\n\n".join(all_answers)
        if final_answer:
            final_answer += "\nWould you like to know anything else? 😊"
        
        return final_answer
    
    def _handle_definition_question(self, concept, text):
        """Handle definition questions"""
        definitions = self.parser.get_concept_definition(concept)
        comments = self.parser.get_comments(concept)  # Get comments using rdfs:comment
        
        if not definitions and not comments:
            return None
            
        answer = []
        if definitions:
            answer.append(f"📚 Definition:")
            for definition in definitions:
                answer.append(f"{definition}")
                
        if comments:
            if answer:  # If we had definitions, add a line break
                answer.append("")
            answer.append(f"💭 Additional Information:")
            for comment in comments:
                answer.append(f"• {comment}")
                
        return "\n".join(answer)
        
    def _handle_category_question(self, concept, text):
        superclasses = self.parser.get_superclasses(concept)
        if not superclasses:
            return None
            
        answer = [f"🔍 Categories that '{concept}' belongs to:"]
        added = set()  # To prevent duplicate categories
        for _, label in superclasses:
            if label not in added:
                answer.append(f"• {label}")
                added.add(label)
        return "\n".join(answer)
    
    def _handle_acronym_question(self, concept, text):
        """Handle acronym questions"""
        acronyms = self.parser.get_acronyms(concept)
        if not acronyms:
            return None
            
        answer = [f"💡 Acronym:"]
        for acronym in acronyms:
            answer.append(f"{acronym}")
        return "\n".join(answer)
        
    def _handle_references_question(self, concept, text, ref_type=None):
        """Handle questions about references and links"""
        references = self.parser.get_references(concept)
        if not references:
            return None
            
        # Filter references by type if specified
        if ref_type:
            type_map = {
                'pdf': ['pdf', 'document', 'qb_pdf_link'],
                'doi': ['doi'],
                'url': ['url', 'link'],
                'wiki': ['wikipedia', 'wiki'],
                'paper': ['paper', 'article']
            }
            
            filtered_refs = []
            keywords = type_map.get(ref_type, [])
            for ref, ref_type_str in references:
                ref_type_lower = ref_type_str.lower()
                if any(keyword in ref_type_lower or keyword in ref.lower() for keyword in keywords):
                    filtered_refs.append((ref, ref_type_str))
            
            if not filtered_refs:
                return None
            references = filtered_refs
        
        answer = [f"🔗 References:"]
        added = set()  # To prevent duplicate references
        
        # Group references by type
        refs_by_type = {}
        for ref, ref_type_str in references:
            if ref_type_str not in refs_by_type:
                refs_by_type[ref_type_str] = []
            if ref not in added:
                refs_by_type[ref_type_str].append(ref)
                added.add(ref)
        
        # Format references by type
        for ref_type_str, refs in refs_by_type.items():
            # Clean up reference type name
            clean_type = ref_type_str.split('#')[-1].replace('_', ' ').title()
            for ref in refs:
                if 'wikipedia' in ref_type_str.lower():
                    answer.append(f"• Wikipedia Entry: <a href='{ref}' target='_blank'>{ref}</a>")
                elif 'qb_pdf_link' in ref_type_str.lower():
                    answer.append(f"• Documentation: <a href='{ref}' target='_blank'>{ref}</a>")
                else:
                    answer.append(f"• {clean_type}: <a href='{ref}' target='_blank'>{ref}</a>")
        
        return "\n".join(answer)
    
    def _handle_alternative_names_question(self, concept, text):
        alt_names = self.parser.get_alternative_names(concept)
        if not alt_names:
            return None
            
        answer = [f"🔤 Alternative names for '{concept}':"]
        added = set()  # To prevent duplicate names
        for name in alt_names:
            if name not in added:
                answer.append(f"• {name}")
                added.add(name)
        return "\n".join(answer)
    
    def _handle_subclass_question(self, concept, text):
        subclasses = self.parser.get_subclasses(concept)
        if not subclasses:
            return None
            
        answer = [f"📋 Types of '{concept}':"]
        added = set()  # To prevent duplicate subclasses
        for _, label in subclasses:
            if label not in added:
                answer.append(f"• {label}")
                added.add(label)
        return "\n".join(answer)
    
    def _handle_superclass_question(self, concept, text):
        return self._handle_category_question(concept, text)
    
    def _handle_related_question(self, concept, text):
        related = self.parser.get_related_concepts(concept)
        if not related:
            return None
            
        answer = [f"🔗 Concepts related to '{concept}':"]
        added = set()  # To prevent duplicate relations
        for _, label, rel_type in related:
            rel_type = rel_type.split('#')[-1]
            if (label, rel_type) not in added:
                answer.append(f"• {label} ({rel_type})")
                added.add((label, rel_type))
        return "\n".join(answer)
    
    def _handle_comments_question(self, concept, text):
        comments = self.parser.get_comments(concept)
        if not comments:
            return None
            
        answer = [f"💬 Additional information about '{concept}':"]
        added = set()  # To prevent duplicate comments
        for comment in comments:
            if comment not in added:
                answer.append(f"• {comment}")
                added.add(comment)
        return "\n".join(answer)