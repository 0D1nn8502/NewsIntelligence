import json
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional 


class ProcessedNewsItem(BaseModel):
    title: str
    summary: str
    link: str
    locations: List[str]  # ["Ukraine", "Kyiv", "Eastern Europe"]
    urgency: str  # "High", "Medium", "Low"
    category: str  # "Conflict", "Politics", "Economics", "Natural Disaster"
    sentiment: str  # "Negative", "Neutral", "Positive"
    timestamp: str
    source: str
    confidence_score: float
    affected_population: Optional[int]
    keywords: List[str] 
    


class TopicEnum(str, Enum):
    
    """ The permissible topics """
    POLITICS = "politics"
    CLIMATE = "climate"
    CONFLICT = "conflict"
    ECONOMY = "economy" 
    HEALTH = "health"
    DISASTER = "disaster"
    INTERNATIONAL_RELATIONS = "international_relations" 



class ParsedNews(BaseModel):
    
    """ How a parsed Rss feed element object should look """
    
    locations: list[str]  # ["Nepal", "India"]
    topics: list[TopicEnum]  # ["climate", "disaster"] ;;;;;;;;;;;;;;;
    entities: list[str]  # ["UNICEF", "UN"]
    sentiment: str  # "negative", "neutral", "positive"
    


## Input token limits? ## 
class NewsParser: 
    
    """ Extracts structure for making SQL queries from given news items within api_limits 

        parse_feed () : From given titles and summaries, extracts 
    
    """
    
    def __init__(self, llm): 
        
        self.llm = llm 
        self.prompt = """

        Parse this news headline and summary into structured data.
        
        Headline: {title}
        Summary: {summary}
        
        Extract:
        - locations: List of countries/cities/regions mentioned
        - topics: From [politics, climate, conflict, economy, health, disaster, diplomacy]
        - entities: Organizations, people, companies mentioned
        - sentiment: positive/negative/neutral
        
        Return valid JSON only:
        {{"locations": ["Nepal"], "topics": ["climate"], "urgency": "high", "entities": ["UNICEF"], "sentiment": "negative"}}
        
        """

        

        