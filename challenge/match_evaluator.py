import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import jellyfish


class MatchEvaluator:
    """
    The MatchEvaluator class evaluates screening results against tenant-specific criteria.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the MatchEvaluator with a configuration.

        Args:
            config: A dictionary containing configuration parameters.
        """
        self.config = config

    def evaluate_tenant(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a tenant against pipeline data.

        Args:
            pipeline_data: Pipeline data containing screening results

        Returns:
            Dict containing the evaluation results
        """
        return self.evaluate_pipeline_data(pipeline_data)

    def evaluate_pipeline_data(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate pipeline data against the configured criteria.

        Args:
            pipeline_data: Pipeline data containing screening results.

        Returns:
            A dictionary containing the evaluation results.
        """
        # Placeholder for evaluation logic.  Replace with actual implementation.
        # This example simply returns the input data.
        return pipeline_data


class EnhancedTenantMatchEvaluator:
    """
    A class to evaluate the relevance of search results for tenant screening.
    """

    def evaluate_tenant(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a tenant against pipeline data.

        Args:
            pipeline_data: Pipeline data containing screening results

        Returns:
            Dict containing the evaluation results
        """
        return self.evaluate_pipeline_data(pipeline_data)

    # Classification buckets
    MATCH_CATEGORIES = {
        "HIGH_RELEVANCE": {"min_score": 0.8, "label": "Highly Relevant Match"},
        "MEDIUM_RELEVANCE": {"min_score": 0.6, "label": "Potentially Relevant Match"},
        "LOW_RELEVANCE": {"min_score": 0.4, "label": "Low Relevance Match"},
        "NOT_RELEVANT": {"min_score": 0.0, "label": "Not Relevant"}
    }

    def __init__(self, tenant_data: Dict[str, Any], threshold: float = 0.7):
        """
        Initialize with tenant data and matching threshold.

        Args:
            tenant_data: Dictionary containing tenant information
            threshold: Minimum score to consider a match relevant (0.0 to 1.0)
        """
        self.tenant_data = self._normalize_tenant_data(tenant_data)
        self.threshold = threshold

    def _normalize_tenant_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize tenant data for consistent comparison."""
        normalized = data.copy()

        # Normalize names
        for name_field in ['first_name', 'middle_name', 'last_name', 'full_name']:
            if name_field in normalized and normalized[name_field]:
                normalized[name_field] = self._normalize_name(normalized[name_field])

        # Extract all name parts for LATAM style names
        normalized['name_parts'] = set()
        for name_field in ['first_name', 'middle_name', 'last_name', 'full_name']:
            if name_field in normalized and normalized[name_field]:
                parts = normalized[name_field].split()
                normalized['name_parts'].update(parts)

        # Normalize date of birth if present
        if 'dob' in normalized and normalized['dob']:
            if isinstance(normalized['dob'], str):
                try:
                    # Try to parse date string in various formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                        try:
                            normalized['dob'] = datetime.strptime(normalized['dob'], fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        normalized['dob'] = None
                except Exception:
                    normalized['dob'] = None

        # Extract age if DOB is present
        if 'dob' in normalized and normalized['dob'] and isinstance(normalized['dob'], datetime):
            today = datetime.now()
            normalized['age'] = today.year - normalized['dob'].year - (
                    (today.month, today.day) < (normalized['dob'].month, normalized['dob'].day))

        return normalized

    def _normalize_name(self, name: str) -> str:
        """Normalize a name by removing special characters and converting to lowercase."""
        if not name:
            return ""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^\w\s]', '', name).lower()
        return normalized

    def _calculate_name_similarity(self, tenant_name: str, match_name: str) -> float:
        """
        Calculate similarity between two names using multiple methods.

        Args:
            tenant_name: The tenant's name
            match_name: The name from the search result

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not tenant_name or not match_name:
            return 0.0

        # Normalize both names
        tenant_name = self._normalize_name(tenant_name)
        match_name = self._normalize_name(match_name)

        # Use multiple similarity metrics and take the best score
        sequence_score = SequenceMatcher(None, tenant_name, match_name).ratio()
        jaro_winkler_score = jellyfish.jaro_winkler_similarity(tenant_name, match_name)

        # For LATAM names, check if all parts of one name are contained in the other
        tenant_parts = set(tenant_name.split())
        match_parts = set(match_name.split())

        # Calculate what percentage of tenant name parts are in the match name
        if tenant_parts:
            parts_overlap = len(tenant_parts.intersection(match_parts)) / len(tenant_parts)
        else:
            parts_overlap = 0.0

        # Return the best score
        return max(sequence_score, jaro_winkler_score, parts_overlap)

    def _compare_dates(self, date1: Optional[datetime], date2: Optional[datetime]) -> float:
        """
        Compare two dates and return a similarity score.

        Args:
            date1: First date
            date2: Second date

        Returns:
            float: 1.0 if dates match exactly, 0.0 if they don't match at all
        """
        if date1 is None or date2 is None:
            return 0.0

        if date1 == date2:
            return 1.0

        # Check if only the year matches
        if date1.year == date2.year:
            return 0.5

        return 0.0

    def _compare_locations(self, tenant_location: Optional[str], match_location: Optional[str]) -> float:
        """
        Compare two locations and return a similarity score.

        Args:
            tenant_location: Tenant's location
            match_location: Location from the search result

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        if not tenant_location or not match_location:
            return 0.0

        # Normalize locations
        tenant_location = self._normalize_name(tenant_location)
        match_location = self._normalize_name(match_location)

        # Simple string similarity for now
        # In a real implementation, you might use geocoding and distance calculation
        return SequenceMatcher(None, tenant_location, match_location).ratio()

    def _compare_nationalities(self, tenant_nationality: Optional[str], match_nationality: Optional[str]) -> float:
        """
        Compare nationalities and return a similarity score.

        Args:
            tenant_nationality: Tenant's nationality
            match_nationality: Nationality from the search result

        Returns:
            float: 1.0 if nationalities match, 0.0 otherwise
        """
        if not tenant_nationality or not match_nationality:
            return 0.0

        # Normalize nationalities
        tenant_nationality = self._normalize_name(tenant_nationality)
        match_nationality = self._normalize_name(match_nationality)

        # Check if nationalities match
        if tenant_nationality == match_nationality:
            return 1.0

        return 0.0

    def _compare_gender(self, tenant_gender: Optional[str], match_gender: Optional[str]) -> float:
        """
        Compare gender and return a similarity score.

        Args:
            tenant_gender: Tenant's gender
            match_gender: Gender from the search result

        Returns:
            float: 1.0 if genders match, 0.0 otherwise
        """
        if not tenant_gender or not match_gender:
            return 0.0

        # Normalize genders
        tenant_gender = tenant_gender.lower().strip()
        match_gender = match_gender.lower().strip()

        # Map common gender representations
        gender_map = {
            'm': 'male',
            'f': 'female',
            'male': 'male',
            'female': 'female',
            'man': 'male',
            'woman': 'female'
        }

        tenant_gender = gender_map.get(tenant_gender, tenant_gender)
        match_gender = gender_map.get(match_gender, match_gender)

        # Check if genders match
        if tenant_gender == match_gender:
            return 1.0

        return 0.0

    def _get_match_category(self, score: float) -> Dict[str, Any]:
        """
        Get the match category based on the relevance score.

        Args:
            score: Relevance score between 0.0 and 1.0

        Returns:
            Dict: Match category information
        """
        for category, info in sorted(
                self.MATCH_CATEGORIES.items(),
                key=lambda x: x[1]['min_score'],
                reverse=True
        ):
            if score >= info['min_score']:
                return {
                    'category': category,
                    'label': info['label'],
                    'score': score
                }

        # Fallback (should never reach here)
        return {
            'category': 'NOT_RELEVANT',
            'label': self.MATCH_CATEGORIES['NOT_RELEVANT']['label'],
            'score': score
        }

    def evaluate_match(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate if a search result is a relevant match for the tenant.

        Args:
            match_data: Dictionary containing information about the potential match

        Returns:
            Dict: Original match data with added evaluation fields
        """
        # Initialize result with original match data
        result = match_data.copy()

        # Initialize scoring variables
        name_score = 0.0
        dob_score = 0.0
        location_score = 0.0
        nationality_score = 0.0
        gender_score = 0.0

        match_reasons = []
        mismatch_reasons = []

        # Normalize match data
        normalized_match = self._normalize_tenant_data(match_data)

        # Compare full names if available
        if 'full_name' in normalized_match and 'full_name' in self.tenant_data:
            name_score = self._calculate_name_similarity(
                self.tenant_data['full_name'],
                normalized_match['full_name']
            )
        # Otherwise compare first and last names separately
        else:
            first_name_score = 0.0
            last_name_score = 0.0

            if 'first_name' in normalized_match and 'first_name' in self.tenant_data:
                first_name_score = self._calculate_name_similarity(
                    self.tenant_data['first_name'],
                    normalized_match['first_name']
                )

            if 'last_name' in normalized_match and 'last_name' in self.tenant_data:
                last_name_score = self._calculate_name_similarity(
                    self.tenant_data['last_name'],
                    normalized_match['last_name']
                )

            # For LATAM names, check if name parts overlap
            parts_score = 0.0
            if 'name_parts' in self.tenant_data and 'name_parts' in normalized_match:
                tenant_parts = self.tenant_data['name_parts']
                match_parts = normalized_match['name_parts']

                if tenant_parts and match_parts:
                    parts_score = len(tenant_parts.intersection(match_parts)) / max(len(tenant_parts), len(match_parts))

            # Take the best name score
            name_score = max(first_name_score, last_name_score, parts_score)

        # Compare date of birth
        if 'dob' in normalized_match and 'dob' in self.tenant_data:
            dob_score = self._compare_dates(self.tenant_data['dob'], normalized_match['dob'])

        # Compare location
        if 'location' in normalized_match and 'location' in self.tenant_data:
            location_score = self._compare_locations(
                self.tenant_data['location'],
                normalized_match['location']
            )

        # Compare nationality
        if 'nationality' in normalized_match and 'nationality' in self.tenant_data:
            nationality_score = self._compare_nationalities(
                self.tenant_data['nationality'],
                normalized_match['nationality']
            )

        # Compare gender
        if 'gender' in normalized_match and 'gender' in self.tenant_data:
            gender_score = self._compare_gender(
                self.tenant_data['gender'],
                normalized_match['gender']
            )

        # Calculate weighted relevance score
        # Weights can be adjusted based on importance of each factor
        name_weight = 0.5
        dob_weight = 0.2
        location_weight = 0.1
        nationality_weight = 0.1
        gender_weight = 0.1

        # Adjust weights if some factors are missing
        total_weight = name_weight
        if 'dob' in normalized_match and 'dob' in self.tenant_data:
            total_weight += dob_weight
        if 'location' in normalized_match and 'location' in self.tenant_data:
            total_weight += location_weight
        if 'nationality' in normalized_match and 'nationality' in self.tenant_data:
            total_weight += nationality_weight
        if 'gender' in normalized_match and 'gender' in self.tenant_data:
            total_weight += gender_weight

        # Normalize weights
        if total_weight > 0:
            name_weight = name_weight / total_weight
            dob_weight = dob_weight / total_weight if 'dob' in normalized_match and 'dob' in self.tenant_data else 0
            location_weight = location_weight / total_weight if 'location' in normalized_match and 'location' in self.tenant_data else 0
            nationality_weight = nationality_weight / total_weight if 'nationality' in normalized_match and 'nationality' in self.tenant_data else 0
            gender_weight = gender_weight / total_weight if 'gender' in normalized_match and 'gender' in self.tenant_data else 0

        # Calculate the weighted score
        relevance_score = (
                name_score * name_weight +
                dob_score * dob_weight +
                location_score * location_weight +
                nationality_score * nationality_weight +
                gender_score * gender_weight
        )

        # Add reasons for match or mismatch
        if name_score > 0.8:
            match_reasons.append(f"Name is a strong match ({name_score:.2f})")
        elif name_score > 0.5:
            match_reasons.append(f"Name is a partial match ({name_score:.2f})")
        else:
            mismatch_reasons.append(f"Name is not a good match ({name_score:.2f})")

        if dob_score == 1.0:
            match_reasons.append("Date of birth matches exactly")
        elif dob_score > 0:
            match_reasons.append("Date of birth partially matches")
        elif 'dob' in normalized_match and 'dob' in self.tenant_data:
            mismatch_reasons.append("Date of birth does not match")

        if location_score > 0.8:
            match_reasons.append(f"Location is a strong match ({location_score:.2f})")
        elif location_score > 0.5:
            match_reasons.append(f"Location is a partial match ({location_score:.2f})")

        if nationality_score == 1.0:
            match_reasons.append("Nationality matches exactly")
        elif 'nationality' in normalized_match and 'nationality' in self.tenant_data:
            mismatch_reasons.append("Nationality does not match")

        if gender_score == 1.0:
            match_reasons.append("Gender matches")
        elif 'gender' in normalized_match and 'gender' in self.tenant_data:
            mismatch_reasons.append("Gender does not match")

        # Get the match category
        match_category = self._get_match_category(relevance_score)

        # Add evaluation results to the match data
        result['relevance_score'] = relevance_score
        result['match_category'] = match_category['category']
        result['match_label'] = match_category['label']
        result['match_reasons'] = match_reasons
        result['mismatch_reasons'] = mismatch_reasons

        # Add date string handling before returning the result
        if 'dob' in result and isinstance(result['dob'], datetime):
            result['dob'] = result['dob'].strftime('%Y-%m-%d')

        return result

    def evaluate_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate a list of potential matches.

        Args:
            matches: List of dictionaries containing potential match data

        Returns:
            List of dictionaries with evaluation results
        """
        return [self.evaluate_match(match) for match in matches]

    def extract_matches_from_pipeline(self, pipeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract matches from the pipeline data where "$.pipeline.type == 'refinitiv-blacklist'".

        Args:
            pipeline_data: Pipeline data containing screening results

        Returns:
            List of matches from the Refinitiv blacklist
        """
        matches = []

        # Navigate through the pipeline data to find the refinitiv-blacklist step
        if 'pipeline' in pipeline_data:
            pipeline_steps = pipeline_data['pipeline']
            if isinstance(pipeline_steps, list):
                for step in pipeline_steps:
                    if step.get('type') == 'refinitiv-blacklist':
                        if 'results' in step:
                            matches.extend(step['results'])
            elif isinstance(pipeline_steps, dict) and pipeline_steps.get('type') == 'refinitiv-blacklist':
                if 'results' in pipeline_steps:
                    matches.extend(pipeline_steps['results'])

        return matches

    def evaluate_pipeline_data(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract matches from pipeline data and evaluate them.

        Args:
            pipeline_data: Pipeline data containing screening results

        Returns:
            Dict containing the original pipeline data and evaluated matches
        """
        # Extract matches from the pipeline data
        matches = self.extract_matches_from_pipeline(pipeline_data)

        # Evaluate the matches
        evaluated_matches = self.evaluate_matches(matches)

        # Return the results
        return {
            'original_pipeline_data': pipeline_data,
            'evaluated_matches': evaluated_matches,
            'match_counts': {
                category: len([m for m in evaluated_matches if m['match_category'] == category])
                for category in self.MATCH_CATEGORIES
            }
        }
