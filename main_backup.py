# TruthLens MCP Server
from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import os
import wikipedia
import re
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

import sys
print("Python running from:", sys.executable, file=sys.stderr)
try:
    import requests
    print("requests module found", file=sys.stderr)
except ImportError:
    print("requests NOT FOUND", file=sys.stderr)

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Create an MCP server
mcp = FastMCP("TruthLens")

# Dictionary to store claims database (in-memory for demo purposes)
# In production this would be a real database
claims_db = {}

# --- Web Crawling & Data Ingestion Tools ---

@mcp.tool()
def ingest_url(url: str) -> Dict[str, Any]:
    """
    Fetch content from a given URL and parse it.
    
    Args:
        url: The URL to fetch content from
        
    Returns:
        Dictionary with extracted title, content, and metadata
    """
    try:
        headers = {
            "User-Agent": "TruthLens/0.1 (Research Project; contact@truthlens-demo.org)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract basic metadata
        title = soup.title.string if soup.title else "No title found"
        
        # Extract main content (basic approach)
        # A more sophisticated implementation would use specific extractors based on site
        main_content = ""
        for paragraph in soup.find_all('p'):
            main_content += paragraph.text + "\n\n"
        
        # Extract publication date (simple approach)
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            pub_date = date_meta.get('content', '')
        else:
            pub_date = datetime.now().isoformat()
            
        return {
            "url": url,
            "title": title,
            "content": main_content[:5000],  # Truncate for large pages
            "publication_date": pub_date,
            "source_domain": url.split("//")[-1].split("/")[0],
            "extraction_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "url": url,
            "error": str(e),
            "status": "failed"
        }


@mcp.tool()
def search_news(query: str, source: str = "newsapi", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for news articles on a specific topic.
    
    Args:
        query: Search query
        source: Source to search ("newsapi" or "reddit")
        limit: Maximum number of results
        
    Returns:
        List of articles with title, URL, and source
    """
    results = []
    
    if source == "newsapi":
        api_key = os.getenv("NEWSAPI_KEY", "demo_key")
        if api_key == "demo_key":
            # Simulated response for demo
            return [
                {
                    "title": f"Sample article about {query} #{i}",
                    "url": f"https://example.com/article{i}",
                    "source": f"News Source {i}",
                    "published_at": datetime.now().isoformat()
                }
                for i in range(1, min(limit + 1, 6))
            ]
        
        # Actual NewsAPI call when key is provided
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={api_key}&pageSize={limit}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for article in data.get("articles", [])[:limit]:
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", "")
                })
    
    elif source == "reddit":
        # Simulated Reddit results (would use PRAW in production)
        return [
            {
                "title": f"Reddit discussion about {query} #{i}",
                "url": f"https://reddit.com/r/news/comments/{i}",
                "source": "Reddit",
                "published_at": datetime.now().isoformat(),
                "comments": 10 * i
            }
            for i in range(1, min(limit + 1, 6))
        ]
    
    return results


# --- Claim Extraction & Analysis Tools ---

@mcp.tool()
def extract_claims(text: str, url: str = "") -> List[Dict[str, Any]]:
    """
    Extract factual claims from text using Gemini.
    
    Args:
        text: The text to extract claims from
        url: Optional source URL of the text
        
    Returns:
        List of extracted claims with metadata
    """
    extracted_claims = []
    claim_id = 1
    
    # Try using Gemini if API key is available
    if GEMINI_API_KEY:
        try:
            # Configure the model
            model = genai.GenerativeModel('gemini-pro')
            
            # Create prompt for claim extraction
            prompt = f"""
            Extract factual claims from the following text. A factual claim is an assertion 
            that can be verified as true or false. Return ONLY the claims, one per line.
            If no clear factual claims are found, return "No claims found."
            
            TEXT: {text[:4000]}  # Truncate to avoid token limits
            
            FACTUAL CLAIMS:
            """
            
            # Generate claims using Gemini
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                # Extract claims from response
                claims_text = response.text.strip().split('\n')
                
                # Process each claim
                for claim_text in claims_text:
                    claim_text = claim_text.strip()
                    # Skip empty lines or "No claims found"
                    if not claim_text or claim_text == "No claims found.":
                        continue
                        
                    # Remove numbering if present (e.g., "1. The claim")
                    claim_text = re.sub(r'^\d+\.\s*', '', claim_text)
                    
                    # Create claim object
                    claim = {
                        "id": f"claim_{claim_id}",
                        "text": claim_text,
                        "confidence": 0.85,  # Default confidence for LLM extraction
                        "extraction_method": "gemini",
                        "source_url": url,
                        "extraction_date": datetime.now().isoformat()
                    }
                    
                    extracted_claims.append(claim)
                    claim_id += 1
                    
                    # Store in our "database"
                    claims_db[claim["id"]] = claim
            
        except Exception as e:
            print(f"Error using Gemini API: {str(e)}")
            # Fall back to pattern matching
    
    # If Gemini failed or no API key, use pattern matching as fallback
    if not extracted_claims:
        print("Using pattern matching fallback for claim extraction")
        # Simple pattern matching to simulate claim extraction
        sentences = re.split(r'[.!?]', text)
        
        claim_patterns = [
            (r'(is|are|was|were)\s+([a-z]+ing|[a-z]+ed)', 0.7),  # Action statements
            (r'(cause[s]?|lead[s]? to)', 0.8),  # Causal claims
            (r'according to|study|research', 0.75),  # Referenced claims
            (r'all|none|every|always|never', 0.9),  # Universal claims
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
                
            confidence = 0.5  # Base confidence
            for pattern, conf_boost in claim_patterns:
                if re.search(pattern, sentence.lower()):
                    confidence = min(0.95, confidence + conf_boost)
                    
                    # Add to claims list
                    claim = {
                        "id": f"claim_{claim_id}",
                        "text": sentence,
                        "confidence": round(confidence, 2),
                        "extraction_method": "pattern_matching",
                        "source_url": url,
                        "extraction_date": datetime.now().isoformat()
                    }
                    extracted_claims.append(claim)
                    claim_id += 1
                    
                    # Store in our "database"
                    claims_db[claim["id"]] = claim
                    break
    
    # Add special claims for demonstration
    if "vaccine" in text.lower():
        demo_claim = {
            "id": f"claim_{claim_id}",
            "text": "Vaccines cause autism.",
            "confidence": 0.95,
            "extraction_method": "demo_hardcoded",
            "source_url": url,
            "extraction_date": datetime.now().isoformat()
        }
        extracted_claims.append(demo_claim)
        claims_db[demo_claim["id"]] = demo_claim
    
    return extracted_claims


@mcp.tool()
def verify_claim(claim_text: str, claim_id: str = None) -> Dict[str, Any]:
    """
    Verify a factual claim using external knowledge sources and Gemini.
    
    Args:
        claim_text: The claim to verify
        claim_id: Optional ID of a previously extracted claim
        
    Returns:
        Verification result with status, evidence, and confidence
    """
    # Get the full claim object if ID is provided
    claim_obj = None
    if claim_id and claim_id in claims_db:
        claim_obj = claims_db[claim_id]
        claim_text = claim_obj["text"]
    
    # Initialize verification result
    verification = {
        "claim": claim_text,
        "status": "Unverified",
        "confidence_score": 0.5,
        "evidence": [],
        "sources": [],
        "verification_date": datetime.now().isoformat(),
        "verification_method": "pattern_matching"  # Default method
    }
    
    # Try using Gemini for verification if API key is available
    if GEMINI_API_KEY:
        try:
            # Configure the model
            model = genai.GenerativeModel('gemini-pro')
            
            # Create prompt for claim verification
            prompt = f"""
            Analyze this claim and determine its veracity. Respond in JSON format with the following fields:
            status: "True", "False", "Partially True", or "Unverified"
            confidence_score: A number between 0 and 1
            evidence: List of evidence supporting your conclusion (1-3 items)
            reasoning: Brief explanation of your conclusion
            
            Claim: "{claim_text}"
            
            JSON response:
            """
            
            # Generate verification using Gemini
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text'):
                try:
                    # Try to parse JSON from response
                    verification_data = json.loads(response.text.strip())
                    
                    # Update verification with Gemini response
                    verification.update({
                        "status": verification_data.get("status", "Unverified"),
                        "confidence_score": verification_data.get("confidence_score", 0.5),
                        "evidence": verification_data.get("evidence", []),
                        "reasoning": verification_data.get("reasoning", ""),
                        "verification_method": "gemini"
                    })
                except json.JSONDecodeError:
                    # If JSON parsing fails, extract information using regex
                    text_response = response.text.strip()
                    
                    # Extract status
                    status_match = re.search(r'"status":\s*"([^"]+)"', text_response)
                    if status_match:
                        verification["status"] = status_match.group(1)
                        
                    # Extract confidence score
                    conf_match = re.search(r'"confidence_score":\s*([\d\.]+)', text_response)
                    if conf_match:
                        verification["confidence_score"] = float(conf_match.group(1))
                        
                    # Extract evidence
                    evidence_matches = re.findall(r'"([^"]+)"', text_response)
                    if evidence_matches:
                        verification["evidence"] = evidence_matches[:3]  # Take up to 3 matches
                        
                    verification["verification_method"] = "gemini_regex"
                    
        except Exception as e:
            print(f"Error using Gemini API for verification: {str(e)}")
            # Fall back to other verification methods
    
    # Check Wikipedia for evidence (if Gemini didn't provide evidence)
    if not verification["evidence"]:
        try:
            # Search Wikipedia
            wiki_results = wikipedia.search(claim_text, results=3)
            
            if wiki_results:
                # Get the first page
                try:
                    wiki_page = wikipedia.page(wiki_results[0], auto_suggest=False)
                    verification["sources"].append({
                        "name": "Wikipedia",
                        "url": wiki_page.url,
                        "retrieved": datetime.now().isoformat()
                    })
                    
                    # Check for keyword matches (simplified analysis)
                    key_terms = re.findall(r'\b\w{4,}\b', claim_text.lower())
                    content = wiki_page.content.lower()
                    
                    # Count matches
                    match_count = sum(1 for term in key_terms if term in content)
                    match_ratio = match_count / len(key_terms) if key_terms else 0
                    
                    if match_ratio > 0.7:
                        summary = wiki_page.summary[:500] + "..."
                        verification["evidence"].append(summary)
                        verification["confidence_score"] = 0.6 + match_ratio * 0.3
                except Exception as wiki_error:
                    print(f"Wikipedia page error: {str(wiki_error)}")
        except Exception as wiki_search_error:
            print(f"Wikipedia search error: {str(wiki_search_error)}")
    
    # Demonstration logic for specific claims
    if "vaccine" in claim_text.lower() and "autism" in claim_text.lower():
        verification["status"] = "False"
        verification["evidence"] = [
            "Multiple large studies have found no link between vaccines and autism.",
            "The original study suggesting a link was retracted due to serious procedural and ethical concerns."
        ]
        verification["sources"] = [
            {"name": "CDC", "url": "https://www.cdc.gov/vaccinesafety/concerns/autism.html"},
            {"name": "WHO", "url": "https://www.who.int/news-room/questions-and-answers/item/vaccines-and-immunization-myths-and-misconceptions"}
        ]
        verification["confidence_score"] = 0.95
        verification["verification_method"] = "demo_hardcoded"
    
    # Set verification status based on confidence score if still unverified
    if verification["status"] == "Unverified" and verification["evidence"]:
        if verification["confidence_score"] > 0.8:
            verification["status"] = "True"
        elif verification["confidence_score"] < 0.2:
            verification["status"] = "False"
        elif verification["evidence"]:
            verification["status"] = "Partially True"
    
    # Update the claim in our database if we have an ID
    if claim_id and claim_id in claims_db:
        claims_db[claim_id]["verification"] = verification
    
    return verification


# --- Monitoring & Alert Tools ---

@mcp.tool()
def setup_monitor(keywords: List[str], threshold: float = 0.6) -> Dict[str, Any]:
    """
    Set up a monitoring alert for specific keywords or topics.
    
    Args:
        keywords: List of keywords to monitor
        threshold: Confidence threshold for alerts (0-1)
        
    Returns:
        Monitor configuration
    """
    monitor_id = f"monitor_{len(keywords)}_{datetime.now().timestamp()}"
    
    monitor_config = {
        "id": monitor_id,
        "keywords": keywords,
        "threshold": threshold,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    
    # In production: Save to database
    
    return monitor_config


@mcp.tool()
def get_trending_misinfo(topic: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get trending misinformation on a specific topic or in general.
    
    Args:
        topic: Optional topic to filter by
        limit: Maximum number of results
        
    Returns:
        List of trending misinfo claims
    """
    # In production: Query database for claims with high spread but low veracity
    
    # Demo response
    trending = [
        {
            "claim": "5G technology is causing COVID-19 symptoms",
            "spread_score": 0.85,
            "truth_score": 0.05,
            "topic": "health",
            "first_seen": "2025-04-15"
        },
        {
            "claim": "Elections were rigged using secret algorithms",
            "spread_score": 0.92,
            "truth_score": 0.12,
            "topic": "politics",
            "first_seen": "2025-03-22"
        },
        {
            "claim": "Drinking bleach cures cancer",
            "spread_score": 0.75,
            "truth_score": 0.01,
            "topic": "health",
            "first_seen": "2025-02-07"
        },
        {
            "claim": "Climate change is a hoax created by scientists",
            "spread_score": 0.88,
            "truth_score": 0.04,
            "topic": "environment",
            "first_seen": "2025-01-30"
        },
        {
            "claim": "New cryptocurrency guaranteed to increase 1000% in value",
            "spread_score": 0.79,
            "truth_score": 0.10,
            "topic": "finance",
            "first_seen": "2025-04-05"
        }
    ]
    
    # Filter by topic if specified
    if topic:
        trending = [item for item in trending if topic.lower() in item["topic"].lower()]
    
    return trending[:limit]


# --- Analysis Pipeline Tools ---

@mcp.tool()
def analyze_source(url: str) -> Dict[str, Any]:
    """
    Complete pipeline to analyze a source: ingest, extract claims, and verify them.
    
    Args:
        url: URL to analyze
        
    Returns:
        Analysis results with source info and verified claims
    """
    # Step 1: Ingest content
    content_data = ingest_url(url)
    
    # Step 2: Extract claims
    claims = extract_claims(content_data["content"], url)
    
    # Step 3: Verify each claim
    verified_claims = []
    for claim in claims:
        verification = verify_claim(claim["text"], claim["id"])
        verified_claims.append({
            "claim_text": claim["text"],
            "confidence": claim["confidence"],
            "verification": verification
        })
    
    # Step 4: Compile source analysis
    analysis = {
        "url": url,
        "title": content_data["title"],
        "source_domain": content_data["source_domain"],
        "analysis_date": datetime.now().isoformat(),
        "claims_found": len(claims),
        "claims_verified": len(verified_claims),
        "verified_claims": verified_claims,
        "source_credibility": {
            "score": calculate_source_credibility(verified_claims),
            "reasoning": "Based on ratio of true versus false claims"
        }
    }
    
    return analysis


def calculate_source_credibility(verified_claims):
    """Helper function to calculate source credibility"""
    if not verified_claims:
        return 0.5
        
    total = len(verified_claims)
    true_count = sum(1 for vc in verified_claims if vc["verification"]["status"] == "True")
    false_count = sum(1 for vc in verified_claims if vc["verification"]["status"] == "False")
    
    # Simple weighted formula
    if total > 0:
        credibility = 0.5 + (true_count - false_count) / (2 * total)
        return max(0.01, min(0.99, credibility))  # Bound between 0.01 and 0.99
    else:
        return 0.5

# --- Demo Resource for Testing ---

@mcp.resource("truthlens://demo")
def get_demo_info() -> Dict[str, Any]:
    """Get information about the TruthLens platform"""
    return {
        "name": "TruthLens",
        "version": "0.1.0",
        "description": "Misinformation surveillance platform powered by Google Gemini",
        "capabilities": [
            "Web content ingestion",
            "Claim extraction (using Gemini)",
            "Claim verification (using Gemini)",
            "Misinformation monitoring"
        ],
        "demo_status": "active",
        "current_date": datetime.now().isoformat()
    }
if __name__ == "__main__":
    # redirect all Python logs to stderr so they don’t corrupt 
    # the JSON-RPC stream on stdout
    import logging, sys
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # start the MCP server loop
    mcp.run()
