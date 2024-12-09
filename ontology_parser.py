from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, SKOS, OWL
import os

class OntologyParser:
    def __init__(self, rdf_file):
        self.g = Graph()
        self.g.parse(rdf_file)
        self.crypto = Namespace("http://www.semanticweb.org/quantumblockchains/crypto#")
        self.obo = Namespace("http://purl.obolibrary.org/obo/")
        
    def get_concept_definition(self, concept):
        # First try exact match
        query = """
        SELECT ?definition
        WHERE {
            ?s rdfs:label ?label .
            ?s <http://purl.obolibrary.org/obo/IAO_0000115> ?definition .
            FILTER(LCASE(str(?label)) = LCASE(?concept))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        definitions = [str(row[0]) for row in results]
        
        # If no exact match found, try partial match
        if not definitions:
            query = """
            SELECT ?label ?definition
            WHERE {
                ?s rdfs:label ?label .
                ?s <http://purl.obolibrary.org/obo/IAO_0000115> ?definition .
                FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
            }
            """
            results = self.g.query(query, initBindings={'concept': Literal(concept)})
            definitions = [str(row[1]) for row in results]
        
        return definitions

    def get_all_concepts(self):
        """Get all concept labels from the ontology"""
        query = """
        SELECT DISTINCT ?label
        WHERE {
            ?s rdfs:label ?label .
        }
        """
        results = self.g.query(query)
        return [str(row[0]).lower() for row in results]
    
    def get_related_concepts(self, concept):
        query = """
        SELECT ?related ?label ?relationType
        WHERE {
            ?s rdfs:label ?mainLabel .
            ?s ?relationType ?related .
            ?related rdfs:label ?label .
            FILTER(CONTAINS(LCASE(str(?mainLabel)), LCASE(?concept)))
            FILTER(?relationType IN (
                skos:related,
                <http://purl.obolibrary.org/obo/IAO_0000136>,
                <http://purl.obolibrary.org/obo/BFO_0000051>
            ))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [(str(row[0]), str(row[1]), str(row[2])) for row in results]
    
    def get_references(self, concept, ref_type=None):
        query = """
        SELECT ?ref ?refType
        WHERE {
            ?s rdfs:label ?label .
            ?s ?refType ?ref .
            FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
            FILTER(?refType IN (
                <http://www.semanticweb.org/quantumblockchains/crypto#doi>,
                <http://www.semanticweb.org/quantumblockchains/crypto#wikipedia_entry>,
                <http://www.semanticweb.org/quantumblockchains/crypto#qb_pdf_link>,
                <http://www.semanticweb.org/quantumblockchains/crypto#wikidata_entry>
            ))
        }
        """
        if ref_type:
            query = query.replace("FILTER(?refType IN (", 
                                f"FILTER(?refType = <http://www.semanticweb.org/quantumblockchains/crypto#{ref_type}> || ?refType IN (")
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [(str(row[0]), str(row[1]).split('#')[-1]) for row in results]
    
    def get_subclasses(self, concept):
        """
        Find all direct and indirect subclasses of a given concept.
        
        Args:
            concept (str): The concept to find subclasses for
        
        Returns:
            list: A list of subclass names
        """
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?subclass WHERE {{
            ?subclass rdfs:subClassOf* <{concept}> .
            FILTER (?subclass != <{concept}>)
        }}
        """
        results = self.g.query(query)
        return [str(row[0]).split('/')[-1] for row in results]

    def get_superclasses(self, concept):
        """
        Find all direct and indirect superclasses of a given concept.
        
        Args:
            concept (str): The concept to find superclasses for
        
        Returns:
            list: A list of superclass names
        """
        query = f"""
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?superclass WHERE {{
            <{concept}> rdfs:subClassOf* ?superclass .
            FILTER (?superclass != <{concept}>)
        }}
        """
        results = self.g.query(query)
        return [str(row[0]).split('/')[-1] for row in results]
    
    def get_acronyms(self, concept):
        query = """
        SELECT ?acronym
        WHERE {
            ?s rdfs:label ?label .
            ?s <http://www.semanticweb.org/quantumblockchains/crypto#acronym> ?acronym .
            FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [str(row[0]) for row in results]
    
    def get_alternative_names(self, concept):
        query = """
        SELECT ?altName
        WHERE {
            ?s rdfs:label ?label .
            ?s <http://purl.obolibrary.org/obo/IAO_0000118> ?altName .
            FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [str(row[0]) for row in results]
    
    def get_comments(self, concept):
        query = """
        SELECT ?comment
        WHERE {
            ?s rdfs:label ?label .
            ?s rdfs:comment ?comment .
            FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [str(row[0]) for row in results]
    
    def get_proper_label(self, concept):
        query = """
        SELECT ?properLabel
        WHERE {
            ?s rdfs:label ?label .
            ?s <http://www.semanticweb.org/quantumblockchains/crypto#proper_label> ?properLabel .
            FILTER(CONTAINS(LCASE(str(?label)), LCASE(?concept)))
        }
        """
        results = self.g.query(query, initBindings={'concept': Literal(concept)})
        return [str(row[0]) for row in results]