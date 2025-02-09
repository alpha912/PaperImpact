import pandas as pd
import numpy as np
from datetime import datetime

def read_journal_data(filepath):
    """Read SCImago journal data with robust CSV parsing"""
    try:
        # First try reading with pandas default parser
        return pd.read_csv(filepath, 
                          sep=None,  # Let pandas detect the separator
                          engine='python',  # Use python engine for more flexible parsing
                          quotechar='"',
                          encoding='utf-8')
    except Exception as e:
        try:
            # Fallback to manual separator with error handling
            return pd.read_csv(filepath,
                             sep=',',  # Try comma separator
                             quotechar='"',
                             encoding='utf-8',
                             on_bad_lines='skip')  # Skip problematic lines
        except UnicodeDecodeError:
            # Final fallback with different encoding
            return pd.read_csv(filepath,
                             sep=',',
                             quotechar='"',
                             encoding='latin-1',
                             on_bad_lines='skip')

def read_paper_data(filepath):
    """Read paper data with proper encoding and delimiter"""
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        # Ensure critical columns are properly mapped
        if 'Source title' in df.columns:
            df['journal_title'] = df['Source title']
        if 'Year' in df.columns:
            df['year'] = df['Year']
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to read paper data: {str(e)}")

class JournalImpactScorer:
    def __init__(self, scimago_path):
        """
        Initialize the scorer with SCImago journal rankings data.
        
        Parameters:
        scimago_path (str): Path to the SCImago journal rankings CSV file
        """
        self.scimago_df = read_journal_data(scimago_path)
        # Clean and prepare SCImago data with error handling
        self.scimago_df['SJR'] = pd.to_numeric(
            self.scimago_df['SJR'].str.replace(',', '.').fillna('0'), 
            errors='coerce'
        ).fillna(0)
        self.scimago_df['H index'] = pd.to_numeric(
            self.scimago_df['H index'].fillna('0'), 
            errors='coerce'
        ).fillna(0)
        # Cache clean journal titles for matching efficiency
        self.scimago_df['clean_title'] = self.scimago_df['Title'].str.lower().str.strip()
        
        # Calculate percentile ranks for different metrics
        self.sjr_percentiles = self.scimago_df['SJR'].rank(pct=True)
        self.h_index_percentiles = self.scimago_df['H index'].rank(pct=True)

    def match_journal(self, title, issn=None):
        """Enhanced journal matching with fuzzy matching fallback"""
        if not title:
            return None

        if issn is not None:
            # Try exact ISSN match first
            issn_match = self.scimago_df[self.scimago_df['Issn'].str.contains(
                str(issn), na=False, regex=False)]
            if not issn_match.empty:
                return issn_match.iloc[0]
        
        # Use cached clean_title for matching
        clean_title = title.lower().strip()
        exact_match = self.scimago_df[self.scimago_df['clean_title'] == clean_title]
        if not exact_match.empty:
            return exact_match.iloc[0]

        # If no exact match, try contains match (non-regex)
        partial_matches = self.scimago_df[
            self.scimago_df['clean_title'].str.contains(
                clean_title, na=False, regex=False
            )
        ]
        if not partial_matches.empty:
            return partial_matches.iloc[0]

        # If still no match, try fuzzy matching
        from thefuzz import fuzz
        best_match = None
        best_score = 0
        
        for idx, row in self.scimago_df.iterrows():
            score = fuzz.ratio(clean_title, row['clean_title'])
            if score > 85 and score > best_score:
                best_score = score
                best_match = row
        
        return best_match

    def calculate_impact_score(self, papers_df):
        """Calculate impact scores for papers using SCImago data."""
        required_columns = {
            'Source title': 'journal_title',
            'Year': 'year',
            'Cited by': 'citation_count',
            'Affiliations': 'affiliations'
        }

        # Create a copy to avoid modifying the original
        working_df = papers_df.copy()
        
        # Map columns based on availability
        for orig_col, new_col in required_columns.items():
            if orig_col in working_df.columns:
                working_df[new_col] = working_df[orig_col]
            elif new_col not in working_df.columns:
                working_df[new_col] = None

        # Initialize impact score components
        scores = pd.DataFrame(index=working_df.index)
        
        # 1. Journal Prestige (30% of total score)
        scores['journal_prestige'] = 0.0
        for idx, paper in working_df.iterrows():
            journal_data = self.match_journal(paper['journal_title'], paper.get('issn'))
            if journal_data is not None:
                # SJR score (15%)
                sjr_percentile = self.sjr_percentiles[journal_data.name]
                scores.at[idx, 'journal_prestige'] += sjr_percentile * 15
                
                # H-index contribution (10%)
                h_index_percentile = self.h_index_percentiles[journal_data.name]
                scores.at[idx, 'journal_prestige'] += h_index_percentile * 10
                
                # Quartile bonus (5%)
                quartile_scores = {'Q1': 5, 'Q2': 3, 'Q3': 1, 'Q4': 0}
                scores.at[idx, 'journal_prestige'] += quartile_scores.get(journal_data['SJR Best Quartile'], 0)
        
        # 2. Citation Impact (40% of total score)
        if 'citation_count' in working_df.columns:
            max_citations = working_df['citation_count'].max()
            scores['citation_score'] = (working_df['citation_count'] / max_citations) * 40 if max_citations > 0 else 0
        
        # 3. Recency Impact (20% of total score)
        if 'year' in working_df.columns:
            current_year = datetime.now().year
            max_age = current_year - working_df['year'].min()
            scores['recency_score'] = (1 - (current_year - working_df['year']) / max_age) * 20 if max_age > 0 else 20
        
        # 4. International Collaboration (10% of total score)
        if 'affiliations' in working_df.columns:
            working_df['num_affiliations'] = working_df['affiliations'].str.count(';') + 1
            max_affiliations = working_df['num_affiliations'].max()
            scores['collaboration_score'] = (working_df['num_affiliations'] / max_affiliations) * 10 if max_affiliations > 0 else 0
        
        # Calculate total and normalized scores
        scores['total_impact_score'] = scores.sum(axis=1)
        max_score = scores['total_impact_score'].max()
        scores['normalized_impact_score'] = (scores['total_impact_score'] / max_score) * 100 if max_score > 0 else 0
        
        # Collect validation stats without printing
        validation_stats = {
            'total_papers': len(papers_df),
            'scored_papers': len(scores[scores['normalized_impact_score'] > 0]),
            'unscored_papers': len(scores[scores['normalized_impact_score'] == 0]),
            'score_stats': scores['normalized_impact_score'].describe(),
            'unscored_samples': []
        }
        
        if validation_stats['unscored_papers'] > 0:
            unscored_df = papers_df[scores['normalized_impact_score'] == 0]
            validation_stats['unscored_samples'] = unscored_df.head()['journal_title'].tolist()

        # Simplified and correct binning logic
        bins = [0, 20, 40, 60, 80, 100]
        scores['impact_tier'] = pd.cut(
            scores['normalized_impact_score'],
            bins=bins,
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'],
            include_lowest=True,
            right=True
        )
        
        # Store tier distribution in validation stats
        validation_stats['tier_distribution'] = scores['impact_tier'].value_counts().to_dict()
        
        # Check for NaN values in impact tiers
        validation_stats['nan_tiers'] = scores['impact_tier'].isna().sum()
        
        # Combine with original data
        result_df = pd.concat([working_df, scores], axis=1)
        
        # Add validation stats to the result DataFrame as metadata
        result_df.attrs['validation_stats'] = validation_stats
        
        return result_df

    def generate_impact_report(self, result_df):
        """
        Generate a detailed impact analysis report.
        """
        # Get validation stats from DataFrame metadata
        validation_stats = result_df.attrs.get('validation_stats', {})
        
        # Get scored papers for highest/lowest calculation
        scored_papers = result_df[result_df['normalized_impact_score'] > 0]
        if len(scored_papers) > 0:
            highest_score_info = scored_papers.nlargest(1, 'normalized_impact_score')[['normalized_impact_score', 'journal_title']].iloc[0]
            lowest_score_info = scored_papers.nsmallest(1, 'normalized_impact_score')[['normalized_impact_score', 'journal_title']].iloc[0]
        else:
            highest_score_info = pd.Series({'normalized_impact_score': 0, 'journal_title': 'N/A'})
            lowest_score_info = pd.Series({'normalized_impact_score': 0, 'journal_title': 'N/A'})

        # Create the report
        report = {
            'total_papers': len(result_df),
            'avg_impact_score': result_df['normalized_impact_score'].mean(),
            'highest_score': highest_score_info['normalized_impact_score'],
            'highest_score_journal': highest_score_info['journal_title'],
            'lowest_score': lowest_score_info['normalized_impact_score'],
            'lowest_score_journal': lowest_score_info['journal_title'],
            'very_high_impact_papers': len(result_df[result_df['normalized_impact_score'] >= 80]),
            'high_impact_papers': len(result_df[(result_df['normalized_impact_score'] >= 60) & (result_df['normalized_impact_score'] < 80)]),
            'medium_impact_papers': len(result_df[(result_df['normalized_impact_score'] >= 40) & (result_df['normalized_impact_score'] < 60)]),
            'low_impact_papers': len(result_df[(result_df['normalized_impact_score'] >= 20) & (result_df['normalized_impact_score'] < 40)]),
            'very_low_impact_papers': len(result_df[result_df['normalized_impact_score'] < 20]),
            'international_collab_pct': result_df['international_collab'].mean() * 100 if 'international_collab' in result_df.columns else 0,
            'journal_distribution': result_df['journal_title'].value_counts().to_dict(),
            'year_distribution': result_df['year'].value_counts().to_dict(),
            'validation_stats': validation_stats  # Include validation stats in report
        }
        
        return report

# Usage example:
def main(scimago_path, papers_path):
    """
    Main function to run the impact score analysis.
    
    Parameters:
    scimago_path (str): Path to SCImago journal rankings CSV
    papers_path (str): Path to papers CSV file
    """
    # Initialize scorer with SCImago data
    scorer = JournalImpactScorer(scimago_path)
    
    # Load papers data
    papers_df = read_paper_data(papers_path)
    
    # Calculate impact scores
    results = scorer.calculate_impact_score(papers_df)
    
    # Generate report
    report = scorer.generate_impact_report(results)
    
    return results, report