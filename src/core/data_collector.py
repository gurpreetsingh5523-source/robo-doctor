
"""
AMRIT DataCollector - Multi-source research data collection
ArXiv, PubMed, NASA, OpenAlex, SemanticScholar, CrossRef
"""
import requests
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET

@dataclass
class Paper:
    title: str
    authors: List[str]
    abstract: str
    doi: Optional[str]
    url: str
    source: str
    published_date: Optional[str]
    citations: int = 0
    keywords: List[str] = None
    full_text: Optional[str] = None

class DataCollector:
    """
    Multi-source research paper collector
    """

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.session = requests.Session()

        # API endpoints
        self.endpoints = {
            'arxiv': 'http://export.arxiv.org/api/query',
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/',
            'openalex': 'https://api.openalex.org/',
            'semantic_scholar': 'https://api.semanticscholar.org/graph/v1/',
            'crossref': 'https://api.crossref.org/works'
        }

    def _rate_limited_request(self, url: str, params: Dict = None, headers: Dict = None) -> requests.Response:
        """Make rate-limited API request"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        response = self.session.get(url, params=params, headers=headers, timeout=30)
        self.last_request_time = time.time()
        return response

    def search_arxiv(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search ArXiv for papers"""
        params = {
            'search_query': f'all:{query}',
            'start': 0,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }

        try:
            response = self._rate_limited_request(self.endpoints['arxiv'], params)
            root = ET.fromstring(response.content)

            papers = []
            for entry in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                title = entry.find('{http://www.w3.org/2005/Atom}title')
                summary = entry.find('{http://www.w3.org/2005/Atom}summary')
                published = entry.find('{http://www.w3.org/2005/Atom}published')
                id_elem = entry.find('{http://www.w3.org/2005/Atom}id')

                authors = []
                for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                    name = author.find('{http://www.w3.org/2005/Atom}name')
                    if name is not None:
                        authors.append(name.text)

                papers.append(Paper(
                    title=title.text if title is not None else 'Unknown',
                    authors=authors,
                    abstract=summary.text if summary is not None else '',
                    doi=None,
                    url=id_elem.text if id_elem is not None else '',
                    source='ArXiv',
                    published_date=published.text if published is not None else None
                ))

            return papers
        except Exception as e:
            print(f"ArXiv search error: {e}")
            return []

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search PubMed for papers"""
        try:
            # Search for IDs
            search_url = f"{self.endpoints['pubmed']}esearch.fcgi"
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': max_results,
                'retmode': 'json'
            }

            response = self._rate_limited_request(search_url, search_params)
            data = response.json()
            idlist = data.get('esearchresult', {}).get('idlist', [])

            if not idlist:
                return []

            # Fetch details
            fetch_url = f"{self.endpoints['pubmed']}efetch.fcgi"
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(idlist),
                'retmode': 'xml'
            }

            response = self._rate_limited_request(fetch_url, fetch_params)
            # Parse XML (simplified)
            root = ET.fromstring(response.content)

            papers = []
            for article in root.findall('.//PubmedArticle'):
                title = article.find('.//ArticleTitle')
                abstract = article.find('.//Abstract/AbstractText')

                authors = []
                for author in article.findall('.//Author'):
                    lastname = author.find('LastName')
                    forename = author.find('ForeName')
                    if lastname is not None:
                        name = lastname.text
                        if forename is not None:
                            name = f"{forename.text} {name}"
                        authors.append(name)

                pmid = article.find('.//PMID')

                papers.append(Paper(
                    title=title.text if title is not None else 'Unknown',
                    authors=authors,
                    abstract=abstract.text if abstract is not None else '',
                    doi=None,
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid.text}/" if pmid is not None else '',
                    source='PubMed',
                    published_date=None
                ))

            return papers
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def search_openalex(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search OpenAlex for papers"""
        try:
            url = f"{self.endpoints['openalex']}works"
            params = {
                'search': query,
                'per-page': max_results,
                'filter': 'has_abstract:true'
            }

            response = self._rate_limited_request(url, params)
            data = response.json()

            papers = []
            for work in data.get('results', []):
                authors = []
                for authorship in work.get('authorships', []):
                    author = authorship.get('author', {})
                    authors.append(author.get('display_name', 'Unknown'))

                papers.append(Paper(
                    title=work.get('display_name', 'Unknown'),
                    authors=authors,
                    abstract=work.get('abstract', '') or '',
                    doi=work.get('doi'),
                    url=work.get('id', ''),
                    source='OpenAlex',
                    published_date=work.get('publication_date'),
                    citations=work.get('cited_by_count', 0)
                ))

            return papers
        except Exception as e:
            print(f"OpenAlex search error: {e}")
            return []

    def search_semantic_scholar(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search Semantic Scholar for papers"""
        try:
            url = f"{self.endpoints['semantic_scholar']}paper/search"
            params = {
                'query': query,
                'limit': max_results,
                'fields': 'title,authors,abstract,year,citationCount,externalIds,url'
            }

            response = self._rate_limited_request(url, params)
            data = response.json()

            papers = []
            for paper in data.get('data', []):
                authors = [a.get('name', 'Unknown') for a in paper.get('authors', [])]

                papers.append(Paper(
                    title=paper.get('title', 'Unknown'),
                    authors=authors,
                    abstract=paper.get('abstract', '') or '',
                    doi=paper.get('externalIds', {}).get('DOI'),
                    url=paper.get('url', ''),
                    source='SemanticScholar',
                    published_date=str(paper.get('year')),
                    citations=paper.get('citationCount', 0)
                ))

            return papers
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")
            return []

    def search_crossref(self, query: str, max_results: int = 10) -> List[Paper]:
        """Search CrossRef for papers"""
        try:
            params = {
                'query': query,
                'rows': max_results,
                'sort': 'relevance',
                'order': 'desc'
            }

            response = self._rate_limited_request(self.endpoints['crossref'], params)
            data = response.json()

            papers = []
            for item in data.get('message', {}).get('items', []):
                authors = []
                for author in item.get('author', []):
                    name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                    authors.append(name)

                papers.append(Paper(
                    title=item.get('title', ['Unknown'])[0] if isinstance(item.get('title'), list) else item.get('title', 'Unknown'),
                    authors=authors,
                    abstract=item.get('abstract', '') or '',
                    doi=item.get('DOI'),
                    url=item.get('URL', ''),
                    source='CrossRef',
                    published_date=item.get('published-print', {}).get('date-parts', [[None]])[0][0]
                ))

            return papers
        except Exception as e:
            print(f"CrossRef search error: {e}")
            return []

    def unified_search(self, query: str, sources: List[str] = None, 
                      max_results_per_source: int = 10) -> Dict:
        """
        Search across all configured sources
        """
        if sources is None:
            sources = ['arxiv', 'pubmed', 'openalex', 'semantic_scholar', 'crossref']

        results = {}

        for source in sources:
            try:
                if source == 'arxiv':
                    results['arxiv'] = self.search_arxiv(query, max_results_per_source)
                elif source == 'pubmed':
                    results['pubmed'] = self.search_pubmed(query, max_results_per_source)
                elif source == 'openalex':
                    results['openalex'] = self.search_openalex(query, max_results_per_source)
                elif source == 'semantic_scholar':
                    results['semantic_scholar'] = self.search_semantic_scholar(query, max_results_per_source)
                elif source == 'crossref':
                    results['crossref'] = self.search_crossref(query, max_results_per_source)
            except Exception as e:
                results[source] = []
                print(f"Error searching {source}: {e}")

        # Deduplicate by title
        all_papers = []
        seen_titles = set()
        for source_papers in results.values():
            for paper in source_papers:
                if paper.title.lower() not in seen_titles:
                    all_papers.append(paper)
                    seen_titles.add(paper.title.lower())

        # Sort by citations
        all_papers.sort(key=lambda p: p.citations, reverse=True)

        return {
            'query': query,
            'total_results': len(all_papers),
            'by_source': {k: len(v) for k, v in results.items()},
            'papers': all_papers[:50]  # Top 50 overall
        }

    def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """Fetch paper by DOI"""
        try:
            url = f"https://doi.org/{doi}"
            headers = {'Accept': 'application/json'}
            response = self._rate_limited_request(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                return Paper(
                    title=data.get('title', 'Unknown'),
                    authors=[a.get('name', 'Unknown') for a in data.get('author', [])],
                    abstract=data.get('abstract', ''),
                    doi=doi,
                    url=data.get('URL', ''),
                    source='DOI Resolver',
                    published_date=data.get('published', {}).get('date-parts', [[None]])[0][0]
                )
        except Exception as e:
            print(f"DOI fetch error: {e}")

        return None
