import json
import os
from typing import List, Dict, Set
from datetime import datetime, timedelta

class SmartSearchManager:
    def __init__(self):
        self.cache_file = "search_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Load previous searches from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
            else:
                self.cache = {
                    "completed_searches": [],
                    "failed_searches": [],
                    "last_updated": None
                }
        except:
            self.cache = {
                "completed_searches": [],
                "failed_searches": [],
                "last_updated": None
            }
    
    def save_cache(self):
        """Save cache to file"""
        try:
            self.cache["last_updated"] = datetime.now().isoformat()
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except:
            pass
    
    def get_business_queries(self) -> List[str]:
        """Get optimized business type queries"""
        return [
            "financial advisor",
            "investment firm", 
            "trading company",
            "wealth management",
            "forex broker",
            "hedge fund",
            "private equity",
            "asset management",
            "financial planner",
            "investment advisor",
            "capital management",
            "securities firm",
            "brokerage firm",
            "financial services",
            "investment banking"
        ]
    
    def get_major_cities(self) -> List[str]:
        """Get major financial cities worldwide"""
        return [
            "New York", "London", "Tokyo", "Singapore", "Hong Kong",
            "Frankfurt", "Zurich", "Sydney", "Toronto", "Chicago",
            "Los Angeles", "San Francisco", "Boston", "Miami", "Dallas",
            "Houston", "Atlanta", "Seattle", "Denver", "Phoenix",
            "Paris", "Amsterdam", "Milan", "Madrid", "Barcelona",
            "Dubai", "Mumbai", "Shanghai", "Seoul", "Bangkok"
        ]
    
    def is_search_completed(self, query: str, location: str) -> bool:
        """Check if this search was already completed"""
        search_key = f"{query.lower()}_{location.lower()}"
        return search_key in self.cache["completed_searches"]
    
    def mark_search_completed(self, query: str, location: str, results_count: int):
        """Mark search as completed"""
        search_key = f"{query.lower()}_{location.lower()}"
        search_record = {
            "key": search_key,
            "query": query,
            "location": location,
            "results_count": results_count,
            "completed_at": datetime.now().isoformat()
        }
        
        # Remove from failed if it was there
        self.cache["failed_searches"] = [
            s for s in self.cache["failed_searches"] 
            if s.get("key") != search_key
        ]
        
        # Add to completed (avoid duplicates)
        existing = [s for s in self.cache["completed_searches"] if s.get("key") == search_key]
        if not existing:
            self.cache["completed_searches"].append(search_record)
        
        self.save_cache()
    
    def mark_search_failed(self, query: str, location: str, error: str):
        """Mark search as failed"""
        search_key = f"{query.lower()}_{location.lower()}"
        search_record = {
            "key": search_key,
            "query": query,
            "location": location,
            "error": error,
            "failed_at": datetime.now().isoformat()
        }
        
        # Add to failed (avoid duplicates)
        existing = [s for s in self.cache["failed_searches"] if s.get("key") == search_key]
        if not existing:
            self.cache["failed_searches"].append(search_record)
        
        self.save_cache()
    
    def get_next_searches(self, max_searches: int = 10) -> List[Dict]:
        """Get next searches to perform (avoiding completed ones)"""
        queries = self.get_business_queries()
        cities = self.get_major_cities()
        
        next_searches = []
        
        for query in queries:
            for city in cities:
                if len(next_searches) >= max_searches:
                    break
                
                if not self.is_search_completed(query, city):
                    next_searches.append({
                        "query": query,
                        "location": city,
                        "priority": self.calculate_priority(query, city)
                    })
            
            if len(next_searches) >= max_searches:
                break
        
        # Sort by priority (higher is better)
        next_searches.sort(key=lambda x: x["priority"], reverse=True)
        
        return next_searches[:max_searches]
    
    def calculate_priority(self, query: str, location: str) -> int:
        """Calculate search priority (higher = more important)"""
        priority = 0
        
        # High-value business types
        high_value_queries = ["hedge fund", "private equity", "investment banking", "asset management"]
        if any(hv in query.lower() for hv in high_value_queries):
            priority += 10
        
        # Major financial centers
        major_centers = ["New York", "London", "Tokyo", "Singapore", "Hong Kong", "Frankfurt"]
        if location in major_centers:
            priority += 5
        
        # US cities (often have more data available)
        us_cities = ["New York", "Chicago", "Los Angeles", "San Francisco", "Boston", "Miami"]
        if location in us_cities:
            priority += 3
        
        return priority
    
    def get_search_stats(self) -> Dict:
        """Get statistics about searches"""
        completed = len(self.cache["completed_searches"])
        failed = len(self.cache["failed_searches"])
        total_possible = len(self.get_business_queries()) * len(self.get_major_cities())
        
        total_results = sum(
            s.get("results_count", 0) 
            for s in self.cache["completed_searches"]
        )
        
        return {
            "completed_searches": completed,
            "failed_searches": failed,
            "total_possible": total_possible,
            "completion_rate": (completed / total_possible * 100) if total_possible > 0 else 0,
            "total_results_found": total_results,
            "average_results_per_search": (total_results / completed) if completed > 0 else 0
        }
    
    def reset_failed_searches(self):
        """Reset failed searches (to retry them)"""
        self.cache["failed_searches"] = []
        self.save_cache()
    
    def get_top_performing_searches(self, limit: int = 10) -> List[Dict]:
        """Get searches that found the most results"""
        completed = self.cache["completed_searches"]
        sorted_searches = sorted(
            completed, 
            key=lambda x: x.get("results_count", 0), 
            reverse=True
        )
        return sorted_searches[:limit]

# Usage example
if __name__ == "__main__":
    manager = SmartSearchManager()
    
    # Get next searches to perform
    next_searches = manager.get_next_searches(5)
    print("Next searches to perform:")
    for search in next_searches:
        print(f"- {search['query']} in {search['location']} (priority: {search['priority']})")
    
    # Get stats
    stats = manager.get_search_stats()
    print(f"\nSearch Statistics:")
    print(f"Completed: {stats['completed_searches']}")
    print(f"Failed: {stats['failed_searches']}")
    print(f"Completion Rate: {stats['completion_rate']:.1f}%")
    print(f"Total Results: {stats['total_results_found']}")